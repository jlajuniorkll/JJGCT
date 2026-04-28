import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from threading import RLock


_TTL_SECONDS = 10 * 60


@dataclass(frozen=True)
class ProposalRecord:
    id_proposta: str
    usuario_id: int
    ferramenta: str
    args_validados: dict[str, Any]
    resumo_legivel: str
    criado_em_ts: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_proposta": self.id_proposta,
            "usuario_id": self.usuario_id,
            "ferramenta": self.ferramenta,
            "args_validados": self.args_validados,
            "resumo_legivel": self.resumo_legivel,
            "criado_em": datetime.fromtimestamp(self.criado_em_ts).isoformat(),
        }


_lock = RLock()
_by_user: dict[int, dict[str, ProposalRecord]] = {}


def _purge_expired_locked(now: float) -> None:
    expired_user_ids: list[int] = []
    for uid, proposals in _by_user.items():
        expired_ids = [pid for pid, p in proposals.items() if now - p.criado_em_ts > _TTL_SECONDS]
        for pid in expired_ids:
            proposals.pop(pid, None)
        if not proposals:
            expired_user_ids.append(uid)
    for uid in expired_user_ids:
        _by_user.pop(uid, None)


def criar_proposta(*, usuario_id: int, ferramenta: str, args_validados: dict[str, Any], resumo_legivel: str) -> ProposalRecord:
    now = time.time()
    record = ProposalRecord(
        id_proposta=str(uuid.uuid4()),
        usuario_id=int(usuario_id),
        ferramenta=str(ferramenta),
        args_validados=args_validados or {},
        resumo_legivel=str(resumo_legivel or "").strip(),
        criado_em_ts=now,
    )
    with _lock:
        _purge_expired_locked(now)
        bucket = _by_user.get(record.usuario_id)
        if bucket is None:
            bucket = {}
            _by_user[record.usuario_id] = bucket
        bucket[record.id_proposta] = record
    return record


def obter_proposta(*, usuario_id: int, id_proposta: str) -> ProposalRecord | None:
    now = time.time()
    with _lock:
        _purge_expired_locked(now)
        bucket = _by_user.get(int(usuario_id))
        if not bucket:
            return None
        return bucket.get(str(id_proposta))


def cancelar_proposta(*, usuario_id: int, id_proposta: str) -> bool:
    now = time.time()
    with _lock:
        _purge_expired_locked(now)
        bucket = _by_user.get(int(usuario_id))
        if not bucket:
            return False
        removed = bucket.pop(str(id_proposta), None) is not None
        if not bucket:
            _by_user.pop(int(usuario_id), None)
        return removed

