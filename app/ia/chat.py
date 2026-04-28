import base64
import json
import os
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from sqlalchemy.orm import Session

from .. import crud, models
from .client import decrypt_secret, get_client
from .image_utils import redimensionar_e_codificar
from .prompts import PROMPT_CHAT_SYSTEM
from .tool_handlers_leitura import dispatch_tool as dispatch_tool_leitura
from .tool_handlers_escrita import dispatch_tool_escrita
from .tools_escrita import TOOLS_ESCRITA
from .tools_leitura import TOOLS_LEITURA

ALL_TOOLS = list(TOOLS_LEITURA or []) + list(TOOLS_ESCRITA or [])


def _dispatch_tool(db: Session, usuario_logado: models.Usuario, tool_name: str, tool_args: dict):
    if tool_name in {"criar_despesa", "criar_atividade"}:
        return dispatch_tool_escrita(db, usuario_logado, tool_name, tool_args)
    return dispatch_tool_leitura(db, usuario_logado, tool_name, tool_args)


def _get_anthropic_key(db: Session) -> str | None:
    cfg = crud.get_app_config(db)
    enc = getattr(cfg, "anthropic_api_key_enc", None)
    env_key = os.getenv("ANTHROPIC_API_KEY")
    if env_key:
        return str(env_key).strip() or None
    if not enc:
        return None
    try:
        return decrypt_secret(enc)
    except Exception:
        return None


def _get_gemini_key(db: Session) -> str | None:
    cfg = crud.get_app_config(db)
    enc = getattr(cfg, "gemini_api_key_enc", None)
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if env_key:
        return str(env_key).strip() or None
    if not enc:
        return None
    try:
        return decrypt_secret(enc)
    except Exception:
        return None


def _select_providers(db: Session):
    cfg = crud.get_app_config(db)
    pref = str(getattr(cfg, "ia_provider", "gemini") or "gemini").lower()
    if pref not in {"anthropic", "gemini"}:
        pref = "gemini"

    anth_available = bool(_get_anthropic_key(db))
    gem_available = bool(_get_gemini_key(db))

    if anth_available and gem_available:
        return [pref, "anthropic" if pref == "gemini" else "gemini"]
    if gem_available:
        return ["gemini"]
    if anth_available:
        return ["anthropic"]
    return []


def _build_user_content(text: str, anexos: list[dict] | None):
    blocks: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for a in anexos or []:
        try:
            raw = base64.b64decode(str(a.get("base64") or ""), validate=False)
        except Exception:
            continue
        if not raw:
            continue
        try:
            b64, media_type = redimensionar_e_codificar(raw)
        except Exception:
            continue
        blocks.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            }
        )
    return blocks


def _normalize_history(historico: list[dict] | None):
    out: list[dict[str, Any]] = []
    for item in historico or []:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"}:
            continue
        if not isinstance(content, str):
            continue
        txt = content.strip()
        if not txt:
            continue
        out.append({"role": role, "content": [{"type": "text", "text": txt}]})
    return out


def _gemini_function_declarations():
    allowed_keys = {
        "type",
        "properties",
        "required",
        "description",
        "enum",
        "items",
        "format",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "minLength",
        "maxLength",
        "pattern",
        "nullable",
    }

    def _sanitize_schema(node: Any):
        if isinstance(node, list):
            return [_sanitize_schema(x) for x in node]
        if not isinstance(node, dict):
            return node
        cleaned: dict[str, Any] = {}
        for k, v in node.items():
            if k not in allowed_keys:
                continue
            if k == "properties" and isinstance(v, dict):
                cleaned[k] = {str(pk): _sanitize_schema(pv) for pk, pv in v.items()}
                continue
            if k == "items":
                cleaned[k] = _sanitize_schema(v)
                continue
            if k == "required" and isinstance(v, list):
                cleaned[k] = [str(x) for x in v if isinstance(x, (str, int))]
                continue
            cleaned[k] = v
        if cleaned.get("type") is None:
            cleaned["type"] = "object"
        return cleaned

    decls: list[dict[str, Any]] = []
    for t in ALL_TOOLS or []:
        if not isinstance(t, dict):
            continue
        name = t.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        schema = t.get("input_schema")
        if not isinstance(schema, dict):
            schema = {"type": "object", "properties": {}}
        schema = _sanitize_schema(schema)
        decls.append(
            {
                "name": name,
                "description": str(t.get("description") or "").strip(),
                "parameters": schema,
            }
        )
    return decls


def _gemini_call(api_key: str, model: str, body: dict):
    model_q = urllib.parse.quote(str(model), safe="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._")
    key_q = urllib.parse.quote(str(api_key), safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_q}:generateContent?key={key_q}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        low = raw.lower()
        if e.code in (401, 403):
            raise ValueError("Chave inválida ou sem permissão (Gemini)")
        if e.code == 404:
            raise ValueError(f"Modelo Gemini inválido ou indisponível ({model})")
        if e.code == 429 or "quota exceeded" in low:
            raise ValueError("Limite/quota do Gemini atingido")
        if "insufficient" in low or "billing" in low:
            raise ValueError("Créditos insuficientes no provedor de IA")
        raise ValueError(raw[:400] or f"Erro HTTP {e.code} no Gemini")
    except Exception as e:
        raise ValueError(str(e)[:400] or "Falha ao chamar Gemini")


def _normalize_history_gemini(historico: list[dict] | None):
    out: list[dict[str, Any]] = []
    for item in historico or []:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"}:
            continue
        if not isinstance(content, str):
            continue
        txt = content.strip()
        if not txt:
            continue
        out.append({"role": "user" if role == "user" else "model", "parts": [{"text": txt}]})
    return out


def _build_user_parts_gemini(text: str, anexos: list[dict] | None):
    parts: list[dict[str, Any]] = [{"text": text}]
    for a in anexos or []:
        try:
            raw = base64.b64decode(str(a.get("base64") or ""), validate=False)
        except Exception:
            continue
        if not raw:
            continue
        try:
            b64, media_type = redimensionar_e_codificar(raw)
        except Exception:
            continue
        parts.append({"inline_data": {"mime_type": media_type, "data": b64}})
    return parts


def _summarize_tool_result(tool_name: str, result: Any) -> str:
    if isinstance(result, dict) and isinstance(result.get("erro"), str):
        return str(result["erro"])
    if tool_name == "listar_viagens" and isinstance(result, list):
        return f"listou {len(result)} viagens"
    if tool_name == "obter_viagem_detalhes" and isinstance(result, dict):
        vid = result.get("id")
        return f"carregou detalhes da viagem #{vid}" if vid else "carregou detalhes da viagem"
    if tool_name == "listar_despesas" and isinstance(result, list):
        return f"listou {len(result)} despesas"
    if tool_name == "listar_usuarios" and isinstance(result, list):
        return f"listou {len(result)} usuários"
    if tool_name == "listar_veiculos" and isinstance(result, list):
        return f"listou {len(result)} veículos"
    if tool_name == "buscar_categorias_despesa" and isinstance(result, list):
        return f"carregou {len(result)} categorias"
    if tool_name == "consultar_metrica":
        return "consultou uma métrica"
    if tool_name == "gerar_relatorio":
        return "gerou um relatório"
    return "executou uma ferramenta"


def _processar_mensagem_anthropic(
    *,
    historico: list[dict] | None,
    nova_mensagem: str,
    anexos: list[dict] | None,
    usuario_logado: models.Usuario,
    db: Session,
    contexto: dict | None,
    max_tool_iterations: int,
):
    key = _get_anthropic_key(db)
    client = get_client(api_key=key)
    if client is None:
        raise ValueError("IA indisponível")

    cfg = crud.get_app_config(db)
    model = str(getattr(cfg, "ia_model_anthropic", None) or (os.getenv("IA_MODELO_CHAT") or "claude-sonnet-4-6")).strip()

    ctx_viagem_id = None
    if isinstance(contexto, dict):
        ctx_viagem_id = contexto.get("viagem_id")
    if ctx_viagem_id is not None:
        try:
            ctx_viagem_id = int(ctx_viagem_id)
        except Exception:
            ctx_viagem_id = None

    user_text = str(nova_mensagem or "").strip()
    if ctx_viagem_id is not None:
        user_text = f"{user_text}\n\nContexto da tela: viagem_id={ctx_viagem_id}"

    messages: list[dict[str, Any]] = _normalize_history(historico)
    messages.append({"role": "user", "content": _build_user_content(user_text, anexos)})

    system = [
        {
            "type": "text",
            "text": PROMPT_CHAT_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    tokens_in = 0
    tokens_out = 0
    cache_read = 0
    ferramentas_chamadas: list[dict[str, Any]] = []
    acoes_pendentes: list[dict[str, Any]] = []
    relatorios_gerados: list[dict[str, Any]] = []

    for _ in range(max(1, int(max_tool_iterations or 5))):
        resp = client.messages.create(
            model=model,
            system=system,
            messages=messages,
            tools=ALL_TOOLS,
            max_tokens=800,
            temperature=0.2,
        )

        usage = getattr(resp, "usage", None)
        if usage is not None:
            tokens_in += int(getattr(usage, "input_tokens", 0) or 0)
            tokens_out += int(getattr(usage, "output_tokens", 0) or 0)
            cache_read += int(getattr(usage, "cache_read_input_tokens", 0) or 0)

        content = list(getattr(resp, "content", []) or [])
        messages.append({"role": "assistant", "content": content})

        tool_uses = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        if not tool_uses:
            text_parts = [b.get("text") for b in content if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
            final_text = "\n".join([t.strip() for t in text_parts if t and t.strip()]).strip()
            if not final_text:
                final_text = "Não consegui responder agora. Tente novamente."
            return {
                "mensagem": final_text,
                "ferramentas_chamadas": ferramentas_chamadas,
                "acoes_pendentes": acoes_pendentes or None,
                "relatorios": relatorios_gerados or None,
                "tokens_consumidos": {"input": tokens_in, "output": tokens_out, "cache_read": cache_read or None},
                "_ia_provider": "anthropic",
                "_ia_model": model,
            }

        tool_results_blocks: list[dict[str, Any]] = []
        for tu in tool_uses:
            tool_name = tu.get("name")
            tool_input = tu.get("input") or {}
            tool_use_id = tu.get("id")

            result = _dispatch_tool(db, usuario_logado, str(tool_name), tool_input if isinstance(tool_input, dict) else {})
            resumo = _summarize_tool_result(str(tool_name), result)
            ferramentas_chamadas.append({"nome": str(tool_name), "args": tool_input if isinstance(tool_input, dict) else {}, "resultado_resumo": resumo})

            if isinstance(result, dict) and isinstance(result.get("id_proposta"), str):
                pid = result.get("id_proposta")
                if pid and not any(a.get("id_proposta") == pid for a in acoes_pendentes):
                    acoes_pendentes.append(result)

            if str(tool_name) == "gerar_relatorio" and isinstance(result, dict) and not isinstance(result.get("erro"), str):
                relatorios_gerados.append(result)

            tool_results_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        messages.append({"role": "user", "content": tool_results_blocks})

    return {
        "mensagem": "Não consegui concluir a resposta agora. Tente refinar a pergunta (ex: informe viagem e período).",
        "ferramentas_chamadas": ferramentas_chamadas,
        "acoes_pendentes": acoes_pendentes or None,
        "relatorios": relatorios_gerados or None,
        "tokens_consumidos": {"input": tokens_in, "output": tokens_out, "cache_read": cache_read or None},
        "_ia_provider": "anthropic",
        "_ia_model": model,
    }


def _processar_mensagem_gemini(
    *,
    historico: list[dict] | None,
    nova_mensagem: str,
    anexos: list[dict] | None,
    usuario_logado: models.Usuario,
    db: Session,
    contexto: dict | None,
    max_tool_iterations: int,
):
    key = _get_gemini_key(db)
    if not key:
        raise ValueError("IA indisponível")

    cfg = crud.get_app_config(db)
    model = str(getattr(cfg, "ia_model_gemini", None) or (os.getenv("IA_MODELO_CHAT_GEMINI") or "gemini-2.5-flash")).strip()

    ctx_viagem_id = None
    if isinstance(contexto, dict):
        ctx_viagem_id = contexto.get("viagem_id")
    if ctx_viagem_id is not None:
        try:
            ctx_viagem_id = int(ctx_viagem_id)
        except Exception:
            ctx_viagem_id = None

    user_text = str(nova_mensagem or "").strip()
    if ctx_viagem_id is not None:
        user_text = f"{user_text}\n\nContexto da tela: viagem_id={ctx_viagem_id}"

    contents: list[dict[str, Any]] = _normalize_history_gemini(historico)
    contents.append({"role": "user", "parts": _build_user_parts_gemini(user_text, anexos)})

    function_declarations = _gemini_function_declarations()

    tokens_in = 0
    tokens_out = 0
    ferramentas_chamadas: list[dict[str, Any]] = []
    acoes_pendentes: list[dict[str, Any]] = []
    relatorios_gerados: list[dict[str, Any]] = []

    for _ in range(max(1, int(max_tool_iterations or 5))):
        body = {
            "systemInstruction": {"parts": [{"text": PROMPT_CHAT_SYSTEM}]},
            "contents": contents,
            "tools": [{"functionDeclarations": function_declarations}],
            "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
        }
        resp = _gemini_call(key, model, body)

        usage = resp.get("usageMetadata") if isinstance(resp, dict) else None
        if isinstance(usage, dict):
            tokens_in += int(usage.get("promptTokenCount") or 0)
            tokens_out += int(usage.get("candidatesTokenCount") or 0)

        candidates = resp.get("candidates") if isinstance(resp, dict) else None
        content = None
        if isinstance(candidates, list) and candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content")

        parts = content.get("parts") if isinstance(content, dict) else None
        if not isinstance(parts, list):
            return {
                "mensagem": "Não consegui responder agora, tente novamente.",
                "ferramentas_chamadas": ferramentas_chamadas,
                "acoes_pendentes": acoes_pendentes or None,
                "tokens_consumidos": {"input": tokens_in, "output": tokens_out, "cache_read": None},
                "_ia_provider": "gemini",
                "_ia_model": model,
            }

        function_calls = [p.get("functionCall") for p in parts if isinstance(p, dict) and isinstance(p.get("functionCall"), dict)]
        if not function_calls:
            texts = [p.get("text") for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)]
            final_text = "\n".join([t.strip() for t in texts if t and t.strip()]).strip()
            if not final_text:
                final_text = "Não consegui responder agora, tente novamente."
            contents.append({"role": "model", "parts": [{"text": final_text}]})
            return {
                "mensagem": final_text,
                "ferramentas_chamadas": ferramentas_chamadas,
                "acoes_pendentes": acoes_pendentes or None,
                "relatorios": relatorios_gerados or None,
                "tokens_consumidos": {"input": tokens_in, "output": tokens_out, "cache_read": None},
                "_ia_provider": "gemini",
                "_ia_model": model,
            }

        tool_response_parts: list[dict[str, Any]] = []
        for fc in function_calls:
            tool_name = fc.get("name")
            tool_args = fc.get("args") if isinstance(fc.get("args"), dict) else {}

            result = _dispatch_tool(db, usuario_logado, str(tool_name), tool_args)
            resumo = _summarize_tool_result(str(tool_name), result)
            ferramentas_chamadas.append({"nome": str(tool_name), "args": tool_args, "resultado_resumo": resumo})

            if isinstance(result, dict) and isinstance(result.get("id_proposta"), str):
                pid = result.get("id_proposta")
                if pid and not any(a.get("id_proposta") == pid for a in acoes_pendentes):
                    acoes_pendentes.append(result)

            if str(tool_name) == "gerar_relatorio" and isinstance(result, dict) and not isinstance(result.get("erro"), str):
                relatorios_gerados.append(result)

            tool_response_parts.append(
                {
                    "functionResponse": {
                        "name": str(tool_name),
                        "response": {"result": result},
                    }
                }
            )

        contents.append({"role": "user", "parts": tool_response_parts})

    return {
        "mensagem": "Não consegui concluir a resposta agora. Tente refinar a pergunta (ex: informe viagem e período).",
        "ferramentas_chamadas": ferramentas_chamadas,
        "acoes_pendentes": acoes_pendentes or None,
        "relatorios": relatorios_gerados or None,
        "tokens_consumidos": {"input": tokens_in, "output": tokens_out, "cache_read": None},
        "_ia_provider": "gemini",
        "_ia_model": model,
    }


def processar_mensagem(
    *,
    historico: list[dict] | None,
    nova_mensagem: str,
    anexos: list[dict] | None,
    usuario_logado: models.Usuario,
    db: Session,
    contexto: dict | None = None,
    max_tool_iterations: int = 5,
):
    providers = _select_providers(db)
    if not providers:
        return {
            "mensagem": "IA indisponível: nenhuma chave configurada",
            "ferramentas_chamadas": [],
            "acoes_pendentes": None,
            "relatorios": None,
            "tokens_consumidos": {"input": 0, "output": 0, "cache_read": 0},
            "_ia_provider": None,
            "_ia_model": None,
        }

    last_error: str | None = None
    for provider in providers:
        try:
            if provider == "gemini":
                return _processar_mensagem_gemini(
                    historico=historico,
                    nova_mensagem=nova_mensagem,
                    anexos=anexos,
                    usuario_logado=usuario_logado,
                    db=db,
                    contexto=contexto,
                    max_tool_iterations=max_tool_iterations,
                )
            return _processar_mensagem_anthropic(
                historico=historico,
                nova_mensagem=nova_mensagem,
                anexos=anexos,
                usuario_logado=usuario_logado,
                db=db,
                contexto=contexto,
                max_tool_iterations=max_tool_iterations,
            )
        except Exception as e:
            last_error = str(e)[:200] or last_error
            continue

    return {
        "mensagem": "Não consegui responder agora, tente novamente." if not last_error else ("IA indisponível: " + last_error),
        "ferramentas_chamadas": [],
        "acoes_pendentes": None,
        "relatorios": None,
        "tokens_consumidos": {"input": 0, "output": 0, "cache_read": 0},
        "_ia_provider": None,
        "_ia_model": None,
    }
