from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from .prompts import PRECO_CACHE_READ_POR_MTOK, PRECO_INPUT_POR_MTOK, PRECO_OUTPUT_POR_MTOK


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _truncate(s: str | None, limit: int) -> str | None:
    if not s:
        return None
    s = str(s)
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)] + "…"


def _json_safe(value: Any):
    if value is None:
        return None
    try:
        json.dumps(value, ensure_ascii=False, default=str)
        return value
    except Exception:
        try:
            return json.loads(json.dumps(value, default=str))
        except Exception:
            return None


def _get_price(mapping: Any, provider: str) -> float:
    if isinstance(mapping, dict):
        try:
            v = mapping.get(provider)
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
    try:
        return float(mapping)
    except Exception:
        return 0.0


def estimar_custo_usd(
    provider: str | None,
    tokens_input: int | None,
    tokens_output: int | None,
    tokens_cache_read: int | None,
) -> float | None:
    prov = str(provider or "").lower().strip()
    if not prov:
        return None

    ti = int(tokens_input or 0)
    to = int(tokens_output or 0)
    tcr = int(tokens_cache_read or 0)

    if ti <= 0 and to <= 0 and tcr <= 0:
        return 0.0

    price_in = _get_price(PRECO_INPUT_POR_MTOK, prov)
    price_out = _get_price(PRECO_OUTPUT_POR_MTOK, prov)
    price_cache = _get_price(PRECO_CACHE_READ_POR_MTOK, prov)

    return (ti / 1_000_000.0) * price_in + (to / 1_000_000.0) * price_out + (tcr / 1_000_000.0) * price_cache


def registrar_ia_log(
    db: Session,
    *,
    usuario_id: int | None,
    tipo: str,
    mensagem_usuario: str | None,
    ferramentas_chamadas: Any,
    tokens_input: int | None,
    tokens_output: int | None,
    tokens_cache_read: int | None,
    latencia_ms: int | None,
    sucesso: bool,
    erro: str | None,
    provider: str | None,
) -> None:
    try:
        log = models.IALog(
            usuario_id=int(usuario_id) if usuario_id is not None else None,
            tipo=str(tipo or "").strip() or "chat",
            mensagem_usuario=_truncate(mensagem_usuario, 4000),
            ferramentas_chamadas=_json_safe(ferramentas_chamadas),
            tokens_input=_coerce_int(tokens_input),
            tokens_output=_coerce_int(tokens_output),
            tokens_cache_read=_coerce_int(tokens_cache_read),
            custo_estimado_usd=_coerce_float(estimar_custo_usd(provider, tokens_input, tokens_output, tokens_cache_read)),
            latencia_ms=_coerce_int(latencia_ms),
            sucesso=bool(sucesso),
            erro=_truncate(erro, 400),
        )
        db.add(log)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
