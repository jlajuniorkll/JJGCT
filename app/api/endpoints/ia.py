import json
import logging
import os
import time
from datetime import datetime, timezone
from math import ceil

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ... import crud, models, schemas
from ...database import SessionLocal
from ...ia.client import decrypt_secret
from ...ia.chat import processar_mensagem
from ...ia import proposals
from ...ia.vision import IAIndisponivelError, IAQuotaError, IACreditosInsuficientesError, extrair_dados_comprovante
from ...ia.audit import registrar_ia_log

router = APIRouter()

logger = logging.getLogger(__name__)

_RATE_LIMIT_PER_HOUR = 20
_RATE_LIMIT_CHAT_PER_HOUR = 60
_WINDOW_SECONDS = 60 * 60
_calls_by_user: dict[int, list[float]] = {}
_chat_calls_by_user: dict[int, list[float]] = {}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _require_auth(db: Session, x_user_id: int | None):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = crud.get_usuario(db, usuario_id=x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def _require_admin(user: models.Usuario):
    if not user or str(getattr(user, "tipousuario", "") or "") != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores.")


def _check_rate_limit(user_id: int):
    now = time.time()
    bucket = _calls_by_user.get(user_id) or []
    bucket = [t for t in bucket if now - t < _WINDOW_SECONDS]
    if len(bucket) >= _RATE_LIMIT_PER_HOUR:
        raise HTTPException(status_code=429, detail="Limite de uso da IA atingido. Tente novamente mais tarde.")
    bucket.append(now)
    _calls_by_user[user_id] = bucket


def _check_rate_limit_chat(user_id: int):
    now = time.time()
    bucket = _chat_calls_by_user.get(user_id) or []
    bucket = [t for t in bucket if now - t < _WINDOW_SECONDS]
    if len(bucket) >= _RATE_LIMIT_CHAT_PER_HOUR:
        raise HTTPException(status_code=429, detail="Limite de uso da IA atingido. Tente novamente mais tarde.")
    bucket.append(now)
    _chat_calls_by_user[user_id] = bucket


@router.post("/extrair-comprovante")
async def extrair_comprovante(
    file: UploadFile = File(...),
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)
    _check_rate_limit(user.id)
    start = time.time()
    provider_usado: str | None = None
    model_usado: str | None = None
    providers_tentados: list[str] = []

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo inválido. Envie uma imagem.")

    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Imagem muito grande. Máximo 8MB.")

    cfg = crud.get_app_config(db)
    try:
        categorias = json.loads(getattr(cfg, "expense_description_options", None) or "[]")
        if not isinstance(categorias, list):
            categorias = []
    except json.JSONDecodeError:
        categorias = []
    categorias = [str(c) for c in categorias if str(c).strip()]
    pref = str(getattr(cfg, "ia_provider", "gemini") or "gemini").lower()
    if pref not in {"anthropic", "gemini"}:
        pref = "gemini"

    anth_token = getattr(cfg, "anthropic_api_key_enc", None)
    gem_token = getattr(cfg, "gemini_api_key_enc", None)
    env_anth = os.getenv("ANTHROPIC_API_KEY")
    env_gem = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    anth_available = bool(anth_token or env_anth)
    gem_available = bool(gem_token or env_gem)

    providers: list[str] = []
    if anth_available and gem_available:
        providers = [pref, "anthropic" if pref == "gemini" else "gemini"]
    elif gem_available:
        providers = ["gemini"]
    elif anth_available:
        providers = ["anthropic"]
    else:
        lat_ms = int((time.time() - start) * 1000)
        registrar_ia_log(
            db,
            usuario_id=int(user.id),
            tipo="extracao",
            mensagem_usuario=None,
            ferramentas_chamadas={"providers_tentados": [], "provider_usado": None, "model": None},
            tokens_input=0,
            tokens_output=0,
            tokens_cache_read=0,
            latencia_ms=lat_ms,
            sucesso=False,
            erro="IA indisponível: nenhuma chave configurada",
            provider=None,
        )
        raise HTTPException(status_code=503, detail="IA indisponível: nenhuma chave configurada")

    last_exception: Exception | None = None
    credit_issue: str | None = None

    for provider in providers:
        providers_tentados.append(provider)
        model = (
            str(getattr(cfg, "ia_model_gemini", None) or (os.getenv("IA_MODELO_VISAO_GEMINI") or "gemini-2.5-flash"))
            if provider == "gemini"
            else str(getattr(cfg, "ia_model_anthropic", None) or (os.getenv("IA_MODELO_VISAO") or "claude-sonnet-4-6"))
        )

        token = gem_token if provider == "gemini" else anth_token
        try:
            api_key = decrypt_secret(token) if token else None
        except ValueError as err:
            last_exception = err
            continue

        try:
            result = extrair_dados_comprovante(
                raw,
                categorias_validas=categorias,
                provider=provider,
                api_key=api_key,
                model=model,
            )
            provider_usado = provider
            model_usado = model
            lat_ms = int((time.time() - start) * 1000)
            registrar_ia_log(
                db,
                usuario_id=int(user.id),
                tipo="extracao",
                mensagem_usuario=None,
                ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": provider_usado, "model": model_usado},
                tokens_input=0,
                tokens_output=0,
                tokens_cache_read=0,
                latencia_ms=lat_ms,
                sucesso=True,
                erro=None,
                provider=provider_usado,
            )
            return result
        except IAIndisponivelError as err:
            last_exception = err
            continue
        except IAQuotaError as err:
            last_exception = err
            continue
        except IACreditosInsuficientesError as err:
            credit_issue = str(err)[:400] or credit_issue
            last_exception = err
            continue
        except Exception as err:
            last_exception = err
            raw_msg = str(err) or ""
            msg_lower = raw_msg.lower()
            if "credit balance is too low" in msg_lower or "purchase credits" in msg_lower or "plans & billing" in msg_lower:
                credit_issue = "Créditos insuficientes na Anthropic. Acesse Plans & Billing e adicione créditos para usar a extração."
            continue

    if credit_issue:
        lat_ms = int((time.time() - start) * 1000)
        registrar_ia_log(
            db,
            usuario_id=int(user.id),
            tipo="extracao",
            mensagem_usuario=None,
            ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": None, "model": None},
            tokens_input=0,
            tokens_output=0,
            tokens_cache_read=0,
            latencia_ms=lat_ms,
            sucesso=False,
            erro=credit_issue,
            provider=None,
        )
        raise HTTPException(status_code=402, detail=credit_issue)
    if isinstance(last_exception, ValueError):
        lat_ms = int((time.time() - start) * 1000)
        registrar_ia_log(
            db,
            usuario_id=int(user.id),
            tipo="extracao",
            mensagem_usuario=None,
            ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": None, "model": None},
            tokens_input=0,
            tokens_output=0,
            tokens_cache_read=0,
            latencia_ms=lat_ms,
            sucesso=False,
            erro=str(last_exception),
            provider=None,
        )
        raise HTTPException(status_code=503, detail=str(last_exception))
    if isinstance(last_exception, IAIndisponivelError):
        msg = str(last_exception or "").strip()
        if not msg:
            msg = "IA indisponível"
        lat_ms = int((time.time() - start) * 1000)
        registrar_ia_log(
            db,
            usuario_id=int(user.id),
            tipo="extracao",
            mensagem_usuario=None,
            ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": None, "model": None},
            tokens_input=0,
            tokens_output=0,
            tokens_cache_read=0,
            latencia_ms=lat_ms,
            sucesso=False,
            erro=msg,
            provider=None,
        )
        raise HTTPException(status_code=503, detail=msg)
    if isinstance(last_exception, IAQuotaError):
        msg = str(last_exception or "").strip() or "Limite/quota da IA atingido"
        lat_ms = int((time.time() - start) * 1000)
        registrar_ia_log(
            db,
            usuario_id=int(user.id),
            tipo="extracao",
            mensagem_usuario=None,
            ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": None, "model": None},
            tokens_input=0,
            tokens_output=0,
            tokens_cache_read=0,
            latencia_ms=lat_ms,
            sucesso=False,
            erro=msg,
            provider=None,
        )
        raise HTTPException(status_code=429, detail=msg)

    logger.exception("Erro ao extrair dados do comprovante: %s", type(last_exception).__name__ if last_exception else "Unknown")
    lat_ms = int((time.time() - start) * 1000)
    registrar_ia_log(
        db,
        usuario_id=int(user.id),
        tipo="extracao",
        mensagem_usuario=None,
        ferramentas_chamadas={"providers_tentados": providers_tentados, "provider_usado": None, "model": None},
        tokens_input=0,
        tokens_output=0,
        tokens_cache_read=0,
        latencia_ms=lat_ms,
        sucesso=False,
        erro=(str(last_exception)[:400] if last_exception else "Falha ao processar o comprovante"),
        provider=None,
    )
    raise HTTPException(status_code=500, detail=(str(last_exception)[:400] if last_exception else "Falha ao processar o comprovante"))


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_ia(
    payload: schemas.ChatRequest,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)
    _check_rate_limit_chat(user.id)
    start = time.time()
    result: dict | None = None
    erro: str | None = None
    try:
        result = processar_mensagem(
            historico=[h.dict() for h in (payload.historico or [])],
            nova_mensagem=payload.mensagem,
            anexos=[a.dict() for a in (payload.anexos or [])] if payload.anexos else None,
            contexto=payload.contexto.dict() if payload.contexto else None,
            usuario_logado=user,
            db=db,
            max_tool_iterations=5,
        )
        return result
    except Exception as e:
        erro = str(e)[:400] or "Erro ao processar IA"
        raise
    finally:
        lat_ms = int((time.time() - start) * 1000)
        tools = (result or {}).get("ferramentas_chamadas") if isinstance(result, dict) else None
        tokens = (result or {}).get("tokens_consumidos") if isinstance(result, dict) else None
        msg = (result or {}).get("mensagem") if isinstance(result, dict) else None
        rels = (result or {}).get("relatorios") if isinstance(result, dict) else None
        provider = (result or {}).get("_ia_provider") if isinstance(result, dict) else None

        ti = tokens.get("input") if isinstance(tokens, dict) else 0
        to = tokens.get("output") if isinstance(tokens, dict) else 0
        tcr = tokens.get("cache_read") if isinstance(tokens, dict) else 0

        tipo = "relatorio" if isinstance(rels, list) and rels else "chat"
        sucesso = erro is None and not (isinstance(msg, str) and msg.strip().lower().startswith("ia indisponível"))
        registrar_ia_log(
            db,
            usuario_id=int(getattr(user, "id", 0) or 0),
            tipo=tipo,
            mensagem_usuario=payload.mensagem,
            ferramentas_chamadas=tools,
            tokens_input=ti,
            tokens_output=to,
            tokens_cache_read=tcr,
            latencia_ms=lat_ms,
            sucesso=sucesso,
            erro=erro or (msg if isinstance(msg, str) and msg.strip().lower().startswith("ia indisponível") else None),
            provider=provider if isinstance(provider, str) else None,
        )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if getattr(dt, "tzinfo", None) is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _percentile(values: list[int], p: float) -> int | None:
    if not values:
        return None
    xs = sorted(int(x) for x in values)
    k = int(ceil((p / 100.0) * len(xs))) - 1
    if k < 0:
        k = 0
    if k >= len(xs):
        k = len(xs) - 1
    return xs[k]


@router.get("/admin/metricas", response_model=schemas.IAMetricasResponse)
def metricas_ia_admin(
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)
    _require_admin(user)

    dt_ini = _parse_dt(periodo_inicio)
    dt_fim = _parse_dt(periodo_fim)

    q = db.query(models.IALog)
    if dt_ini is not None:
        q = q.filter(models.IALog.criado_em >= dt_ini)
    if dt_fim is not None:
        q = q.filter(models.IALog.criado_em <= dt_fim)

    logs = q.order_by(desc(models.IALog.criado_em)).all()

    total_chamadas = len(logs)
    total_tokens = sum(int((l.tokens_input or 0) + (l.tokens_output or 0) + (l.tokens_cache_read or 0)) for l in logs)
    custo_total_usd = float(sum(float(l.custo_estimado_usd or 0.0) for l in logs))
    taxa_sucesso = (sum(1 for l in logs if bool(l.sucesso)) / total_chamadas) if total_chamadas else 0.0

    latencias = [int(l.latencia_ms) for l in logs if l.latencia_ms is not None]
    latencia_p50 = _percentile(latencias, 50)
    latencia_p95 = _percentile(latencias, 95)

    ferramentas_count: dict[str, int] = {}
    usuarios_count: dict[int, int] = {}

    for l in logs:
        uid = int(l.usuario_id) if l.usuario_id is not None else 0
        usuarios_count[uid] = usuarios_count.get(uid, 0) + 1
        tools = l.ferramentas_chamadas
        if isinstance(tools, list):
            for t in tools:
                if not isinstance(t, dict):
                    continue
                nome = t.get("nome")
                if isinstance(nome, str) and nome.strip():
                    ferramentas_count[nome] = ferramentas_count.get(nome, 0) + 1

    usuarios = db.query(models.Usuario).filter(models.Usuario.id.in_([u for u in usuarios_count.keys() if u > 0])).all() if usuarios_count else []
    nome_por_id = {int(u.id): str(getattr(u, "nome", "") or "") for u in usuarios}

    ferramentas_top = [{"nome": k, "count": int(v)} for k, v in sorted(ferramentas_count.items(), key=lambda x: x[1], reverse=True)[:10]]
    usuarios_top = [
        {"nome": (nome_por_id.get(uid) or f"Usuário #{uid}"), "count": int(cnt)}
        for uid, cnt in sorted(((k, v) for k, v in usuarios_count.items() if k > 0), key=lambda x: x[1], reverse=True)[:10]
    ]

    return {
        "total_chamadas": total_chamadas,
        "total_tokens": total_tokens,
        "custo_total_usd": custo_total_usd,
        "ferramentas_top": ferramentas_top,
        "usuarios_top": usuarios_top,
        "taxa_sucesso": taxa_sucesso,
        "latencia_p50": latencia_p50,
        "latencia_p95": latencia_p95,
    }


@router.get("/admin/logs", response_model=schemas.IALogsResponse)
def logs_ia_admin(
    usuario_id: int | None = None,
    tipo: str | None = None,
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
    limit: int | None = 50,
    offset: int | None = 0,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)
    _require_admin(user)

    dt_ini = _parse_dt(periodo_inicio)
    dt_fim = _parse_dt(periodo_fim)

    lim = int(limit or 50)
    if lim < 1:
        lim = 1
    if lim > 200:
        lim = 200
    off = int(offset or 0)
    if off < 0:
        off = 0

    q = db.query(models.IALog)
    if usuario_id is not None:
        q = q.filter(models.IALog.usuario_id == int(usuario_id))
    if tipo:
        q = q.filter(models.IALog.tipo == str(tipo))
    if dt_ini is not None:
        q = q.filter(models.IALog.criado_em >= dt_ini)
    if dt_fim is not None:
        q = q.filter(models.IALog.criado_em <= dt_fim)

    total = q.count()
    items = q.order_by(desc(models.IALog.criado_em)).offset(off).limit(lim).all()

    user_ids = [int(i.usuario_id) for i in items if i.usuario_id is not None]
    usuarios = db.query(models.Usuario).filter(models.Usuario.id.in_(user_ids)).all() if user_ids else []
    nome_por_id = {int(u.id): str(getattr(u, "nome", "") or "") for u in usuarios}

    def _msg_resumo(v: str | None):
        if not v:
            return None
        s = str(v).strip().replace("\n", " ")
        if len(s) <= 140:
            return s
        return s[:139] + "…"

    logs = []
    for i in items:
        logs.append(
            {
                "id": int(i.id),
                "criado_em": i.criado_em,
                "tipo": str(i.tipo),
                "usuario_id": int(i.usuario_id) if i.usuario_id is not None else None,
                "usuario_nome": nome_por_id.get(int(i.usuario_id)) if i.usuario_id is not None else None,
                "mensagem_resumo": _msg_resumo(i.mensagem_usuario),
                "ferramentas_chamadas": i.ferramentas_chamadas if isinstance(i.ferramentas_chamadas, list) else [],
                "tokens_input": int(i.tokens_input or 0),
                "tokens_output": int(i.tokens_output or 0),
                "tokens_cache_read": int(i.tokens_cache_read or 0),
                "custo_estimado_usd": float(i.custo_estimado_usd or 0.0),
                "latencia_ms": int(i.latencia_ms or 0),
                "sucesso": bool(i.sucesso),
                "erro": str(i.erro) if i.erro else None,
            }
        )

    return {"total": total, "limit": lim, "offset": off, "items": logs}


def _parse_json_list(value: str | None) -> list[str]:
    try:
        data = json.loads(value or "[]")
        if not isinstance(data, list):
            return []
        return [str(x).strip() for x in data if str(x).strip()]
    except json.JSONDecodeError:
        return []


def _user_is_participant(user: models.Usuario, viagem: models.Viagem) -> bool:
    uid = int(getattr(user, "id", 0) or 0)
    return any(int(getattr(u, "id", 0) or 0) == uid for u in (getattr(viagem, "participantes", None) or []))


def _trip_status_allows_mutation(db: Session, viagem: models.Viagem) -> bool:
    cfg = crud.get_app_config(db)
    allowed = _parse_json_list(getattr(cfg, "trip_activity_expense_allowed_statuses", None))
    return str(getattr(viagem, "status", "") or "") in allowed


@router.post("/confirmar-acao", response_model=schemas.IAConfirmarAcaoResponse)
def confirmar_acao_ia(
    payload: schemas.IAConfirmarAcaoRequest,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)

    prop = proposals.obter_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
    if not prop:
        raise HTTPException(status_code=410, detail="Proposta expirada ou não encontrada.")

    ferramenta = str(prop.ferramenta or "")
    args = dict(prop.args_validados or {})

    viagem_id = args.get("viagem_id")
    try:
        viagem_id = int(viagem_id)
    except Exception:
        raise HTTPException(status_code=400, detail="viagem_id inválido na proposta.")

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem não encontrada.")
    if not _user_is_participant(user, db_viagem):
        raise HTTPException(status_code=403, detail="Você não tem permissão para isso.")
    if not _trip_status_allows_mutation(db, db_viagem):
        raise HTTPException(status_code=400, detail="Ação não permitida para este status de viagem.")

    if ferramenta == "criar_despesa":
        cfg = crud.get_app_config(db)
        categorias = _parse_json_list(getattr(cfg, "expense_description_options", None))

        valor = args.get("valor")
        descricao = str(args.get("descricao") or "").strip()
        forma_pagamento = str(args.get("forma_pagamento") or "").strip()
        tipo_pagamento = str(args.get("tipo_pagamento") or "INDIVIDUAL").strip().upper()
        registrado_para_id = args.get("registrado_para_id")
        comprovante_url = str(args.get("comprovante_url") or "").strip()

        if categorias and descricao not in categorias:
            lookup = {str(c).strip().lower(): str(c).strip() for c in categorias if str(c).strip()}
            mapped = lookup.get(descricao.lower())
            if mapped:
                descricao = mapped
            else:
                raise HTTPException(status_code=400, detail="Descrição/categoria inválida para despesa.")

        try:
            valor = float(valor)
        except Exception:
            raise HTTPException(status_code=400, detail="valor inválido.")
        if valor <= 0:
            raise HTTPException(status_code=400, detail="valor inválido.")

        if not forma_pagamento:
            raise HTTPException(status_code=400, detail="forma_pagamento inválida.")
        if tipo_pagamento not in {"INDIVIDUAL", "COMPARTILHADO"}:
            raise HTTPException(status_code=400, detail="tipo_pagamento inválido.")

        if registrado_para_id is None:
            registrado_para_id = int(user.id)
        else:
            try:
                registrado_para_id = int(registrado_para_id)
            except Exception:
                raise HTTPException(status_code=400, detail="registrado_para_id inválido.")

        if bool(getattr(cfg, "expense_photo_required", False)) and not comprovante_url:
            raise HTTPException(status_code=400, detail="Comprovante é obrigatório.")

        despesa = schemas.DespesaCreate(
            valor=valor,
            forma_pagamento=forma_pagamento,
            descricao=descricao,
            criado_por_id=int(user.id),
            pago_por_id=int(user.id),
            tipo_pagamento=tipo_pagamento,
            registrado_para_id=registrado_para_id,
        )
        created = crud.create_despesa(db=db, despesa=despesa, viagem_id=viagem_id, comprovante_url=comprovante_url)
        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "despesa",
                "id": int(created.id),
                "viagem_id": int(created.viagem_id),
                "descricao": created.descricao,
                "valor": float(created.valor),
            },
        }

    if ferramenta == "criar_atividade":
        descricao = str(args.get("descricao") or "").strip()
        usuario_id = args.get("usuario_id")
        ordem = args.get("ordem")

        if not descricao:
            raise HTTPException(status_code=400, detail="descricao inválida.")

        if usuario_id is None:
            usuario_id = int(user.id)
        else:
            try:
                usuario_id = int(usuario_id)
            except Exception:
                raise HTTPException(status_code=400, detail="usuario_id inválido.")
            if getattr(user, "tipousuario", None) != "admin" and usuario_id != int(user.id):
                raise HTTPException(status_code=403, detail="Você não tem permissão para isso.")

        ordem_int = None
        if ordem is not None:
            try:
                ordem_int = int(ordem)
            except Exception:
                raise HTTPException(status_code=400, detail="ordem inválida.")
            if ordem_int < 1:
                raise HTTPException(status_code=400, detail="ordem inválida.")

        atividade = schemas.AtividadeCreate(descricao=descricao, usuario_id=usuario_id)
        created = crud.create_atividade(db=db, atividade=atividade, viagem_id=viagem_id)

        if ordem_int is not None:
            atividades = (
                db.query(models.Atividade)
                .filter(models.Atividade.viagem_id == viagem_id)
                .order_by(models.Atividade.ordem, models.Atividade.id)
                .all()
            )
            ids = [int(a.id) for a in atividades]
            if int(created.id) in ids:
                ids.remove(int(created.id))
            idx = max(0, min(ordem_int - 1, len(ids)))
            ids.insert(idx, int(created.id))
            crud.reorder_atividades(db=db, viagem_id=viagem_id, atividade_ids=ids)

        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "atividade",
                "id": int(created.id),
                "viagem_id": int(created.viagem_id),
                "descricao": created.descricao,
                "usuario_id": int(created.usuario_id),
            },
        }

    if ferramenta == "iniciar_atividade":
        atividade_id = args.get("atividade_id")
        try:
            atividade_id = int(atividade_id)
        except Exception:
            raise HTTPException(status_code=400, detail="atividade_id inválido.")

        atividade = crud.get_atividade(db, atividade_id)
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
            raise HTTPException(status_code=400, detail="Atividade não pertence a esta viagem.")

        status = str(getattr(atividade, "status", "") or "")
        if status == "finalizada":
            raise HTTPException(status_code=400, detail="Atividade já está finalizada.")
        if status != "pendente":
            raise HTTPException(status_code=400, detail="Atividade não está pendente para iniciar.")

        updated = crud.iniciar_atividade(db, atividade_id)
        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "atividade_iniciada",
                "id": int(updated.id),
                "viagem_id": int(updated.viagem_id),
                "status": str(updated.status),
                "inicio": updated.inicio.isoformat() if getattr(updated, "inicio", None) else None,
            },
        }

    if ferramenta == "pausar_atividade":
        atividade_id = args.get("atividade_id")
        motivo = str(args.get("motivo") or "").strip()
        if not motivo:
            raise HTTPException(status_code=400, detail="motivo inválido.")
        try:
            atividade_id = int(atividade_id)
        except Exception:
            raise HTTPException(status_code=400, detail="atividade_id inválido.")

        atividade = crud.get_atividade(db, atividade_id)
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade não encontrada.")
        if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
            raise HTTPException(status_code=400, detail="Atividade não pertence a esta viagem.")

        status = str(getattr(atividade, "status", "") or "")
        if status != "ativa":
            raise HTTPException(status_code=400, detail="Atividade não está ativa para pausar.")

        open_pause = (
            db.query(models.Pausa)
            .filter(models.Pausa.atividade_id == atividade_id)
            .filter(models.Pausa.fim.is_(None))
            .first()
        )
        if open_pause:
            raise HTTPException(status_code=400, detail="Já existe uma pausa em aberto para esta atividade.")

        pausa = crud.create_pausa(db, pausa=schemas.PausaCreate(motivo=motivo), atividade_id=atividade_id)
        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "pausa",
                "id": int(pausa.id),
                "viagem_id": int(viagem_id),
                "atividade_id": int(pausa.atividade_id),
                "motivo": str(pausa.motivo),
                "inicio": pausa.inicio.isoformat() if getattr(pausa, "inicio", None) else None,
            },
        }

    if ferramenta == "finalizar_pausa":
        pausa_id = args.get("pausa_id")
        try:
            pausa_id = int(pausa_id)
        except Exception:
            raise HTTPException(status_code=400, detail="pausa_id inválido.")

        pausa = db.query(models.Pausa).filter(models.Pausa.id == pausa_id).first()
        if not pausa:
            raise HTTPException(status_code=404, detail="Pausa não encontrada.")

        atividade = crud.get_atividade(db, int(getattr(pausa, "atividade_id", 0) or 0))
        if not atividade:
            raise HTTPException(status_code=404, detail="Atividade da pausa não encontrada.")
        if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
            raise HTTPException(status_code=400, detail="Pausa não pertence a esta viagem.")

        if getattr(pausa, "fim", None) is not None:
            raise HTTPException(status_code=400, detail="Pausa já está finalizada.")

        updated = crud.finalizar_pausa(db, pausa_id)
        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "pausa_finalizada",
                "id": int(updated.id),
                "viagem_id": int(viagem_id),
                "atividade_id": int(updated.atividade_id),
                "fim": updated.fim.isoformat() if getattr(updated, "fim", None) else None,
            },
        }

    if ferramenta == "finalizar_viagem":
        if str(getattr(db_viagem, "status", "") or "") != "em_andamento":
            raise HTTPException(status_code=400, detail="A chegada só pode ser registrada para viagens em andamento")

        for atividade in getattr(db_viagem, "atividades", []) or []:
            if str(getattr(atividade, "status", "") or "") != "finalizada":
                raise HTTPException(status_code=400, detail=f"A atividade '{atividade.descricao}' ainda não foi finalizada.")

        cfg = crud.get_app_config(db)
        allow_manual_dt = bool(getattr(cfg, "trip_allow_manual_arrival_datetime", False))
        data_hora_real_chegada = args.get("data_hora_real_chegada")
        chegada_naive_utc = None
        if data_hora_real_chegada is not None:
            if not allow_manual_dt:
                raise HTTPException(status_code=400, detail="Configuração não permite informar data/hora de chegada manualmente.")
            s = str(data_hora_real_chegada or "").strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                from datetime import datetime, timezone

                dt = datetime.fromisoformat(s)
            except Exception:
                raise HTTPException(status_code=400, detail="data_hora_real_chegada inválida.")
            if getattr(dt, "tzinfo", None) is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            chegada_naive_utc = dt

        km_chegada = args.get("km_chegada")
        if str(getattr(db_viagem, "meio_transporte", "") or "") in {"carro empresa", "carro próprio"}:
            if km_chegada is None:
                raise HTTPException(status_code=400, detail="KM de chegada é obrigatório para este meio de transporte.")

        km_chegada_f = None
        if km_chegada is not None:
            try:
                km_chegada_f = float(km_chegada)
            except Exception:
                raise HTTPException(status_code=400, detail="km_chegada inválido.")
            if km_chegada_f <= 0:
                raise HTTPException(status_code=400, detail="km_chegada inválido.")

            if getattr(db_viagem, "transporte", None) and getattr(db_viagem.transporte, "km_saida", None) is not None:
                try:
                    km_saida = float(db_viagem.transporte.km_saida)
                except Exception:
                    km_saida = None
                if km_saida is not None and km_chegada_f < km_saida:
                    raise HTTPException(status_code=400, detail="km_chegada inválido (deve ser maior ou igual ao km de saída).")

        updated = crud.registrar_chegada_real(db, viagem_id=viagem_id, km_chegada=km_chegada_f, data_hora_real_chegada=chegada_naive_utc)
        if not updated:
            raise HTTPException(status_code=404, detail="Viagem não encontrada.")

        proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
        return {
            "sucesso": True,
            "registro_criado": {
                "tipo": "viagem_finalizada",
                "id": int(updated.id),
                "viagem_id": int(viagem_id),
                "status": str(updated.status),
                "data_hora_real_chegada": updated.data_hora_real_chegada.isoformat() if getattr(updated, "data_hora_real_chegada", None) else None,
                "km_chegada": float(getattr(getattr(updated, "transporte", None), "km_chegada", 0.0) or 0.0) if getattr(updated, "transporte", None) else None,
            },
        }

    raise HTTPException(status_code=400, detail="Ferramenta inválida na proposta.")


@router.post("/cancelar-acao", response_model=schemas.IACancelarAcaoResponse)
def cancelar_acao_ia(
    payload: schemas.IACancelarAcaoRequest,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = _require_auth(db, x_user_id)
    ok = proposals.cancelar_proposta(usuario_id=int(user.id), id_proposta=str(payload.id_proposta))
    return {"sucesso": bool(ok)}
