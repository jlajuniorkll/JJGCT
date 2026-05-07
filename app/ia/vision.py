import os
import json
import socket
import urllib.request
import urllib.error
import urllib.parse
from typing import Any

from .client import get_client
from .image_utils import redimensionar_e_codificar
from .prompts import PROMPT_EXTRACAO_COMPROVANTE_SYSTEM


class IAIndisponivelError(Exception):
    pass


class IACreditosInsuficientesError(Exception):
    pass


class IAQuotaError(Exception):
    pass


def _coerce_float(value: Any):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        s = s.replace("R$", "").strip()
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _parse_json_object(text: str):
    if not isinstance(text, str):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end <= start:
        return None
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except Exception:
        return None


def _parse_first_json_object(text: str):
    if not isinstance(text, str):
        return None
    s = text.strip()
    if not s:
        return None

    if "```" in s:
        start = s.find("```")
        end = s.find("```", start + 3)
        if start >= 0 and end > start:
            inner = s[start + 3 : end].strip()
            if inner.lower().startswith("json"):
                inner = inner[4:].strip()
            s = inner

    decoder = json.JSONDecoder()
    limit = min(len(s), 20000)
    for i in range(limit):
        if s[i] != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(s[i:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def _gemini_extract(imagem_bytes: bytes, categorias_validas: list[str], api_key: str | None, model: str | None):
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise IAIndisponivelError("GEMINI_API_KEY ausente")

    key = str(key).strip()
    if any(ch.isspace() for ch in key):
        raise IAIndisponivelError("Chave inválida (Gemini)")

    model = str(model or os.getenv("IA_MODELO_VISAO_GEMINI") or "gemini-2.5-flash").strip()
    if any(ch.isspace() for ch in model):
        raise IAIndisponivelError("Modelo Gemini inválido ou indisponível")

    categorias = [str(c) for c in (categorias_validas or []) if str(c).strip()]
    if "Outros" not in categorias:
        categorias.append("Outros")

    b64, media_type = redimensionar_e_codificar(imagem_bytes)

    prompt = (
        "Extraia dados deste comprovante brasileiro.\n"
        "Retorne APENAS JSON válido, sem markdown e sem explicações.\n"
        "Use somente estas chaves: valor, descricao, forma_pagamento, data_emissao, estabelecimento, avisos.\n"
        f"Categorias válidas (escolha exatamente uma para 'descricao'): {', '.join(categorias)}\n"
        "'descricao' deve ser exatamente uma das categorias válidas acima.\n"
        "Se você não tiver certeza da categoria, use 'Outros' e inclua um aviso curto.\n"
        "forma_pagamento: DINHEIRO | CARTAO_CREDITO | CARTAO_DEBITO | PIX | OUTRO | \"\".\n"
        "Se não conseguir extrair um campo, use \"\" (string vazia) e avisos com uma explicação curta.\n"
        "A resposta deve ser curta e direta.\n"
    )

    def _safe_call_model(model_name: str, body_obj: dict):
        model_q = urllib.parse.quote(model_name, safe="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._")
        key_q = urllib.parse.quote(key, safe="")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_q}:generateContent?key={key_q}"
        req = urllib.request.Request(
            url,
            data=json.dumps(body_obj).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="ignore")
            low = raw.lower()
            if e.code == 429 or "quota exceeded" in low:
                raise IAQuotaError("Limite/quota do Gemini atingido")
            if e.code == 400:
                msg = ""
                try:
                    obj = json.loads(raw) if raw else None
                    if isinstance(obj, dict):
                        err = obj.get("error")
                        if isinstance(err, dict) and isinstance(err.get("message"), str):
                            msg = err["message"].strip()
                except Exception:
                    msg = ""
                msg = msg or (raw.strip()[:400] if raw else "")
                raise IAIndisponivelError(f"Requisição inválida ao Gemini: {msg or 'HTTP 400'}")
            if e.code in (401, 403):
                raise IAIndisponivelError("Chave inválida ou sem permissão (Gemini)")
            if e.code == 404:
                raise IAIndisponivelError(f"Modelo Gemini inválido ou indisponível ({model_name})")
            if "insufficient" in low or "billing" in low or "quota" in low:
                raise IACreditosInsuficientesError(raw[:400])
            raise

    def _extract_with_model(model_name: str):
        body_base = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": media_type, "data": b64}},
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        bodies_to_try = [
            {**body_base, "generationConfig": {**(body_base.get("generationConfig") or {}), "responseMimeType": "application/json"}},
            {**body_base, "generationConfig": {**(body_base.get("generationConfig") or {}), "response_mime_type": "application/json"}},
            body_base,
        ]
        last_err: Exception | None = None
        for b in bodies_to_try:
            try:
                return _safe_call_model(model_name, b)
            except IAQuotaError:
                raise
            except IAIndisponivelError as e:
                msg = str(e or "").lower()
                if msg.startswith("requisição inválida ao gemini:") and (
                    "unknown name" in msg
                    or "invalid json payload" in msg
                    or "responsemimetype" in msg
                    or "response_mime_type" in msg
                    or "cannot find field" in msg
                ):
                    last_err = e
                    continue
                raise
            except Exception as e:
                last_err = e
                raise
        if last_err is not None:
            raise last_err
        return _safe_call_model(model_name, body_base)

    model_used = model
    payload = _extract_with_model(model_used)

    pf = payload.get("promptFeedback") if isinstance(payload, dict) else None
    if isinstance(pf, dict):
        block_reason = pf.get("blockReason")
        if block_reason:
            raise IAIndisponivelError(f"Gemini bloqueou o conteúdo ({block_reason})")

    def _parse_payload(p: dict):
        candidates = p.get("candidates") if isinstance(p, dict) else None
        if not isinstance(candidates, list) or not candidates:
            return None, None, False, False, []

        parsed: dict | None = None
        text_parts: list[str] = []
        finish_reason: str | None = None
        saw_function_call = False
        saw_text = False

        for cand in candidates:
            if not isinstance(cand, dict):
                continue
            if finish_reason is None and isinstance(cand.get("finishReason"), str):
                finish_reason = cand.get("finishReason")
            content = cand.get("content") or {}
            parts = content.get("parts") if isinstance(content, dict) else None
            if not isinstance(parts, list):
                continue
            for part in parts:
                if not isinstance(part, dict):
                    continue
                if isinstance(part.get("text"), str):
                    saw_text = True
                    text_parts.append(part["text"])
                    continue
                fc = part.get("functionCall")
                if isinstance(fc, dict):
                    saw_function_call = True
                    args = fc.get("args") or fc.get("arguments")
                    if isinstance(args, dict):
                        parsed = args
                        break
                    if isinstance(args, str):
                        parsed = _parse_json_object(args)
                        if isinstance(parsed, dict):
                            break
            if parsed is not None or text_parts:
                break

        if parsed is None:
            raw_text = "\n".join(text_parts).strip()
            if raw_text:
                parsed = _parse_first_json_object(raw_text) or _parse_json_object(raw_text)

        return parsed if isinstance(parsed, dict) else None, finish_reason, saw_text, saw_function_call, text_parts

    parsed, finish_reason, saw_text, saw_function_call, text_parts = _parse_payload(payload)

    if parsed is None and saw_text and finish_reason in {"MAX_TOKENS", "STOP"}:
        retry_prompt = (
            "Retorne APENAS JSON válido com as chaves: valor, descricao, forma_pagamento, data_emissao, estabelecimento, avisos. "
            f"'descricao' deve ser exatamente uma destas categorias: {', '.join(categorias)}"
        )
        retry_body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": retry_prompt},
                        {"inline_data": {"mime_type": media_type, "data": b64}},
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        retry_payload = _safe_call_model(model_used, retry_body)
        parsed, finish_reason, saw_text, saw_function_call, text_parts = _parse_payload(retry_payload)

    if not isinstance(parsed, dict) or not parsed:
        meta = []
        if finish_reason:
            meta.append(f"finishReason={finish_reason}")
        meta.append(f"hasText={bool(saw_text)}")
        meta.append(f"hasFunctionCall={bool(saw_function_call)}")
        raise IAIndisponivelError("Não foi possível extrair dados do comprovante com o Gemini (" + ", ".join(meta) + ")")

    return parsed


def test_conexao_ia(provider: str, api_key: str | None, model: str | None):
    prov = str(provider or "anthropic").lower()
    if prov == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            return False, "GEMINI_API_KEY ausente"
        key = str(key).strip()
        if any(ch.isspace() for ch in key):
            return False, "Chave inválida (Gemini)"

        model = str(model or os.getenv("IA_MODELO_VISAO_GEMINI") or "gemini-2.5-flash").strip()
        if any(ch.isspace() for ch in model):
            return False, "Modelo Gemini inválido ou indisponível"

        model_q = urllib.parse.quote(model, safe="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._")
        key_q = urllib.parse.quote(key, safe="")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_q}:generateContent?key={key_q}"
        body = {
            "contents": [{"role": "user", "parts": [{"text": "ping"}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 10},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as _:
                return True, "Conexão OK"
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            if e.code == 429:
                return False, "Limite/quota do Gemini atingido"
            if e.code in (401, 403):
                return False, "Chave inválida ou sem permissão (Gemini)"
            if e.code == 404:
                return False, "Modelo Gemini inválido ou indisponível"
            if "quota" in body.lower() or "billing" in body.lower() or "insufficient" in body.lower():
                return False, "Limite/quota do Gemini atingido"
            return False, f"Falha ao testar Gemini (HTTP {e.code})"
        except socket.timeout:
            return False, "Timeout ao testar Gemini"
        except Exception as e:
            return False, f"Falha ao testar Gemini ({type(e).__name__})"

    client = get_client(api_key=api_key)
    if client is None:
        return False, "ANTHROPIC_API_KEY ausente"
    model = model or os.getenv("IA_MODELO_VISAO") or "claude-sonnet-4-6"
    try:
        client.messages.create(
            model=model,
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": [{"type": "text", "text": "ping"}]}],
            timeout=20.0,
        )
        return True, "Conexão OK"
    except TypeError:
        try:
            client.messages.create(
                model=model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": [{"type": "text", "text": "ping"}]}],
            )
            return True, "Conexão OK"
        except Exception as e:
            msg = str(e or "").strip()
            if not msg:
                msg = f"Falha ao testar Anthropic ({type(e).__name__})"
            return False, msg[:400] or "Falha ao testar Anthropic"
    except Exception as e:
        msg = str(e or "").strip()
        if not msg:
            msg = f"Falha ao testar Anthropic ({type(e).__name__})"
        return False, msg[:400] or "Falha ao testar Anthropic"


def extrair_dados_comprovante(
    imagem_bytes: bytes,
    categorias_validas: list[str],
    provider: str = "anthropic",
    api_key: str | None = None,
    model: str | None = None,
):
    provider = str(provider or "anthropic").lower()
    categorias = [str(c) for c in (categorias_validas or []) if str(c).strip()]
    if "Outros" not in categorias:
        categorias.append("Outros")
    if provider == "gemini":
        tool_input = _gemini_extract(imagem_bytes, categorias_validas=categorias_validas, api_key=api_key, model=model)
    else:
        client = get_client(api_key=api_key)
        if client is None:
            raise IAIndisponivelError("ANTHROPIC_API_KEY ausente")

        model = model or os.getenv("IA_MODELO_VISAO") or "claude-sonnet-4-6"

        b64, media_type = redimensionar_e_codificar(imagem_bytes)

        tool = {
            "name": "responder_dados_comprovante",
            "description": "Retorna dados extraídos do comprovante com confiança por campo.",
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "valor": {"type": ["number", "null"]},
                    "descricao": {"type": ["string", "null"]},
                    "forma_pagamento": {
                        "type": ["string", "null"],
                        "enum": ["DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "OUTRO"],
                    },
                    "data_emissao": {"type": ["string", "null"]},
                    "estabelecimento": {"type": ["string", "null"]},
                    "confianca": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "valor": {"type": "number"},
                            "descricao": {"type": "number"},
                            "forma_pagamento": {"type": "number"},
                            "data_emissao": {"type": "number"},
                            "estabelecimento": {"type": "number"},
                        },
                        "required": ["valor", "descricao", "forma_pagamento", "data_emissao", "estabelecimento"],
                    },
                    "avisos": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "valor",
                    "descricao",
                    "forma_pagamento",
                    "data_emissao",
                    "estabelecimento",
                    "confianca",
                    "avisos",
                ],
            },
        }

        system = PROMPT_EXTRACAO_COMPROVANTE_SYSTEM
        user_text = (
            "Extraia os campos do comprovante.\n"
            f"Categorias válidas (escolha exatamente uma): {', '.join(categorias)}\n"
            "Se a categoria não for encontrada, use 'Outros' e inclua um aviso."
        )

        try:
            resp = client.messages.create(
                model=model,
                max_tokens=700,
                temperature=0,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        ],
                    }
                ],
                tools=[tool],
                tool_choice={"type": "tool", "name": "responder_dados_comprovante"},
                timeout=30.0,
            )
        except TypeError:
            resp = client.messages.create(
                model=model,
                max_tokens=700,
                temperature=0,
                system=system,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        ],
                    }
                ],
                tools=[tool],
                tool_choice={"type": "tool", "name": "responder_dados_comprovante"},
            )

        tool_input = None
        for block in getattr(resp, "content", []) or []:
            btype = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
            if btype != "tool_use":
                continue
            name = getattr(block, "name", None) or (block.get("name") if isinstance(block, dict) else None)
            if name == "responder_dados_comprovante":
                tool_input = getattr(block, "input", None) or (block.get("input") if isinstance(block, dict) else None)
                break

        if not isinstance(tool_input, dict):
            tool_input = {}

    valor = _coerce_float(tool_input.get("valor"))
    descricao = tool_input.get("descricao")
    forma = tool_input.get("forma_pagamento")
    data_emissao = tool_input.get("data_emissao")
    estabelecimento = tool_input.get("estabelecimento")
    confianca = tool_input.get("confianca") if isinstance(tool_input.get("confianca"), dict) else {}
    avisos = tool_input.get("avisos") if isinstance(tool_input.get("avisos"), list) else []

    if descricao is not None and descricao not in categorias:
        descricao = "Outros"

    def _conf(key: str):
        try:
            return float(confianca.get(key, 0.0))
        except Exception:
            return 0.0

    result = {
        "valor": valor,
        "descricao": descricao,
        "forma_pagamento": forma if forma in {"DINHEIRO", "CARTAO_CREDITO", "CARTAO_DEBITO", "PIX", "OUTRO"} else None,
        "data_emissao": str(data_emissao) if data_emissao else None,
        "estabelecimento": str(estabelecimento) if estabelecimento else None,
        "confianca": {
            "valor": _conf("valor"),
            "descricao": _conf("descricao"),
            "forma_pagamento": _conf("forma_pagamento"),
            "data_emissao": _conf("data_emissao"),
            "estabelecimento": _conf("estabelecimento"),
        },
        "avisos": [str(a) for a in avisos],
    }
    return result
