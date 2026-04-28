from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import crud, models


class TipoRelatorio(str, Enum):
    despesas_por_viagem = "despesas_por_viagem"
    despesas_por_categoria = "despesas_por_categoria"
    despesas_por_usuario = "despesas_por_usuario"
    custo_por_km = "custo_por_km"
    horas_atividade_por_usuario = "horas_atividade_por_usuario"
    viagens_por_status = "viagens_por_status"


@dataclass(frozen=True)
class Periodo:
    inicio: datetime | None
    fim: datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "inicio": self.inicio.isoformat() if self.inicio else None,
            "fim": self.fim.isoformat() if self.fim else None,
        }


def _parse_iso_dt(value: str | None):
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _user_can_view_all_trips(db: Session, user: models.Usuario) -> bool:
    return getattr(user, "tipousuario", None) == "admin"


def _user_can_view_viagem(db: Session, user: models.Usuario, viagem_id: int) -> bool:
    if _user_can_view_all_trips(db, user):
        return True
    v = crud.get_viagem(db, viagem_id)
    if not v:
        return False
    uid = int(getattr(user, "id", 0) or 0)
    if int(getattr(v, "responsavel_id", 0) or 0) == uid:
        return True
    if getattr(v, "transporte", None) and int(getattr(v.transporte, "motorista_id", 0) or 0) == uid:
        return True
    return any(int(getattr(p, "id", 0) or 0) == uid for p in (getattr(v, "participantes", None) or []))


def _allowed_viagem_ids(db: Session, user: models.Usuario) -> list[int] | None:
    if _user_can_view_all_trips(db, user):
        return None
    uid = int(getattr(user, "id", 0) or 0)
    viagens = crud.get_viagens_for_user(db, user_id=uid, limit=500)
    return [int(v.id) for v in viagens]


def _periodo_from_filtros(filtros: dict[str, Any]) -> Periodo:
    return Periodo(
        inicio=_parse_iso_dt(filtros.get("periodo_inicio")),
        fim=_parse_iso_dt(filtros.get("periodo_fim")),
    )


def _report_base(*, tipo: TipoRelatorio, titulo: str, periodo: Periodo, grafico_sugerido: str):
    return {
        "tipo": str(tipo.value),
        "titulo": str(titulo),
        "periodo": periodo.to_dict(),
        "dados": [],
        "grafico_sugerido": str(grafico_sugerido),
        "resumo_textual": "",
        "totais": {},
    }


def despesas_por_viagem(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.despesas_por_viagem
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Despesas por viagem", periodo=periodo, grafico_sugerido="barra")

    viagem_id = filtros.get("viagem_id")
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        allowed_ids: list[int] | None = [viagem_id]
    else:
        allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    q = (
        db.query(
            models.Viagem.id.label("viagem_id"),
            models.Viagem.motivo.label("motivo"),
            func.coalesce(func.sum(models.Despesa.valor), 0.0).label("total"),
        )
        .join(models.Despesa, models.Despesa.viagem_id == models.Viagem.id)
    )
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        q = q.filter(models.Viagem.id.in_(allowed_ids))
    if periodo.inicio is not None:
        q = q.filter(models.Despesa.data_registro >= periodo.inicio)
    if periodo.fim is not None:
        q = q.filter(models.Despesa.data_registro <= periodo.fim)

    rows = q.group_by(models.Viagem.id, models.Viagem.motivo).order_by(func.sum(models.Despesa.valor).desc()).all()
    dados = []
    total_geral = 0.0
    for r in rows:
        vid = int(r[0])
        motivo = str(r[1] or "").strip()
        total = float(r[2] or 0.0)
        total_geral += total
        label = f"Viagem #{vid}" + (f" — {motivo}" if motivo else "")
        dados.append({"label": label, "valor": total, "viagem_id": vid})

    base["dados"] = dados
    base["totais"] = {"total_geral": float(total_geral)}
    base["resumo_textual"] = (
        f"Total de despesas: R$ {total_geral:.2f}".replace(".", ",") + (f" em {len(dados)} viagem(ns)." if dados else ".")
    )
    return base


def despesas_por_categoria(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.despesas_por_categoria
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Despesas por categoria", periodo=periodo, grafico_sugerido="pizza")

    viagem_id = filtros.get("viagem_id")
    allowed_ids: list[int] | None
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        allowed_ids = [viagem_id]
    else:
        allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    limit = filtros.get("limit", 10)
    try:
        limit = int(limit)
    except Exception:
        limit = 10
    limit = max(1, min(limit, 20))

    q = db.query(
        models.Despesa.descricao.label("categoria"),
        func.coalesce(func.sum(models.Despesa.valor), 0.0).label("total"),
    )
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        q = q.filter(models.Despesa.viagem_id.in_(allowed_ids))
    if periodo.inicio is not None:
        q = q.filter(models.Despesa.data_registro >= periodo.inicio)
    if periodo.fim is not None:
        q = q.filter(models.Despesa.data_registro <= periodo.fim)

    rows = q.group_by(models.Despesa.descricao).order_by(func.sum(models.Despesa.valor).desc()).limit(limit).all()
    dados = []
    total_geral = 0.0
    for r in rows:
        categoria = str(r[0] or "").strip() or "Sem categoria"
        total = float(r[1] or 0.0)
        total_geral += total
        dados.append({"label": categoria, "valor": total, "categoria": categoria})

    base["dados"] = dados
    base["totais"] = {"total_geral": float(total_geral)}
    base["resumo_textual"] = (
        f"Total de despesas (top {len(dados)}): R$ {total_geral:.2f}".replace(".", ",") if dados else "Sem despesas no período."
    )
    return base


def despesas_por_usuario(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.despesas_por_usuario
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Despesas por usuário", periodo=periodo, grafico_sugerido="barra")

    viagem_id = filtros.get("viagem_id")
    allowed_ids: list[int] | None
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        allowed_ids = [viagem_id]
    else:
        allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    agrupar_por = str(filtros.get("agrupar_por") or "").strip().lower()
    if agrupar_por not in {"pago_por", "registrado_para"}:
        agrupar_por = "pago_por"

    if agrupar_por == "registrado_para":
        user_fk = models.Despesa.registrado_para_id
        titulo = "Despesas por usuário (registrado para)"
    else:
        user_fk = models.Despesa.pago_por_id
        titulo = "Despesas por usuário (quem pagou)"
    base["titulo"] = titulo

    q = (
        db.query(
            user_fk.label("usuario_id"),
            func.coalesce(func.sum(models.Despesa.valor), 0.0).label("total"),
        )
        .select_from(models.Despesa)
    )
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        q = q.filter(models.Despesa.viagem_id.in_(allowed_ids))
    if periodo.inicio is not None:
        q = q.filter(models.Despesa.data_registro >= periodo.inicio)
    if periodo.fim is not None:
        q = q.filter(models.Despesa.data_registro <= periodo.fim)

    rows = q.group_by(user_fk).order_by(func.sum(models.Despesa.valor).desc()).all()
    user_ids = [int(r[0]) for r in rows if r[0] is not None]
    users_by_id: dict[int, models.Usuario] = {}
    if user_ids:
        for u in db.query(models.Usuario).filter(models.Usuario.id.in_(user_ids)).all():
            users_by_id[int(u.id)] = u

    dados = []
    total_geral = 0.0
    for r in rows:
        uid = r[0]
        total = float(r[1] or 0.0)
        total_geral += total
        if uid is None:
            dados.append({"label": "Não informado", "valor": total, "usuario_id": None})
            continue
        uid_int = int(uid)
        u = users_by_id.get(uid_int)
        nome = str(getattr(u, "nome", "") or "").strip()
        label = f"Usuário #{uid_int}" + (f" — {nome}" if nome else "")
        dados.append({"label": label, "valor": total, "usuario_id": uid_int})

    base["dados"] = dados
    base["totais"] = {"total_geral": float(total_geral)}
    base["resumo_textual"] = (
        f"Total de despesas: R$ {total_geral:.2f}".replace(".", ",") + (f" em {len(dados)} usuário(s)." if dados else ".")
    )
    return base


def custo_por_km(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.custo_por_km
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Custo por km por viagem", periodo=periodo, grafico_sugerido="barra")

    viagem_id = filtros.get("viagem_id")
    allowed_ids: list[int] | None
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        allowed_ids = [viagem_id]
    else:
        allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    despesas_q = db.query(
        models.Despesa.viagem_id.label("viagem_id"),
        func.coalesce(func.sum(models.Despesa.valor), 0.0).label("total_despesas"),
    )
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        despesas_q = despesas_q.filter(models.Despesa.viagem_id.in_(allowed_ids))
    if periodo.inicio is not None:
        despesas_q = despesas_q.filter(models.Despesa.data_registro >= periodo.inicio)
    if periodo.fim is not None:
        despesas_q = despesas_q.filter(models.Despesa.data_registro <= periodo.fim)
    despesas_sub = despesas_q.group_by(models.Despesa.viagem_id).subquery()

    q = (
        db.query(
            models.Viagem.id.label("viagem_id"),
            models.Viagem.motivo.label("motivo"),
            models.TransporteViagem.km_saida.label("km_saida"),
            models.TransporteViagem.km_chegada.label("km_chegada"),
            despesas_sub.c.total_despesas.label("total_despesas"),
        )
        .join(models.TransporteViagem, models.TransporteViagem.viagem_id == models.Viagem.id)
        .join(despesas_sub, despesas_sub.c.viagem_id == models.Viagem.id)
    )
    if allowed_ids is not None:
        q = q.filter(models.Viagem.id.in_(allowed_ids))

    rows = q.order_by(despesas_sub.c.total_despesas.desc()).all()
    dados = []
    for r in rows:
        vid = int(r[0])
        motivo = str(r[1] or "").strip()
        km_saida = r[2]
        km_chegada = r[3]
        total = float(r[4] or 0.0)
        if km_saida is None or km_chegada is None:
            continue
        distancia = float(km_chegada) - float(km_saida)
        if distancia <= 0:
            continue
        valor = total / distancia
        label = f"Viagem #{vid}" + (f" — {motivo}" if motivo else "")
        dados.append(
            {
                "label": label,
                "valor": float(valor),
                "viagem_id": vid,
                "total_despesas": float(total),
                "distancia_km": float(distancia),
            }
        )

    base["dados"] = dados
    base["totais"] = {"viagens_com_km": len(dados)}
    base["resumo_textual"] = "Comparação de custo por km por viagem." if dados else "Sem viagens com KM válido no período."
    return base


def horas_atividade_por_usuario(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.horas_atividade_por_usuario
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Horas de atividade por usuário", periodo=periodo, grafico_sugerido="barra")

    viagem_id = filtros.get("viagem_id")
    allowed_ids: list[int] | None
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        allowed_ids = [viagem_id]
    else:
        allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    q = db.query(models.Atividade)
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        q = q.filter(models.Atividade.viagem_id.in_(allowed_ids))
    if periodo.inicio is not None:
        q = q.filter(models.Atividade.inicio >= periodo.inicio)
    if periodo.fim is not None:
        q = q.filter(models.Atividade.inicio <= periodo.fim)
    atividades = q.order_by(models.Atividade.inicio.desc()).limit(5000).all()

    totals_by_user: dict[int, float] = {}
    for a in atividades:
        if not a.inicio or not a.fim:
            continue
        total = max(0.0, float((a.fim - a.inicio).total_seconds()))
        for p in getattr(a, "pausas", None) or []:
            if not p.inicio or not p.fim:
                continue
            total -= max(0.0, float((p.fim - p.inicio).total_seconds()))
        total = max(0.0, total)
        uid = int(getattr(a, "usuario_id", 0) or 0)
        if uid <= 0:
            continue
        totals_by_user[uid] = totals_by_user.get(uid, 0.0) + total

    users_by_id: dict[int, models.Usuario] = {}
    if totals_by_user:
        ids = list(totals_by_user.keys())
        for u in db.query(models.Usuario).filter(models.Usuario.id.in_(ids)).all():
            users_by_id[int(u.id)] = u

    rows = sorted(totals_by_user.items(), key=lambda kv: kv[1], reverse=True)
    dados = []
    total_horas = 0.0
    for uid, seconds in rows:
        horas = float(seconds) / 3600.0
        total_horas += horas
        u = users_by_id.get(uid)
        nome = str(getattr(u, "nome", "") or "").strip()
        label = f"Usuário #{uid}" + (f" — {nome}" if nome else "")
        dados.append({"label": label, "valor": float(horas), "usuario_id": int(uid)})

    base["dados"] = dados
    base["totais"] = {"total_horas": float(total_horas)}
    base["resumo_textual"] = "Soma de horas de atividades (descontando pausas)." if dados else "Sem atividades no período."
    return base


def viagens_por_status(db: Session, filtros: dict[str, Any], usuario_logado: models.Usuario):
    tipo = TipoRelatorio.viagens_por_status
    periodo = _periodo_from_filtros(filtros)
    base = _report_base(tipo=tipo, titulo="Viagens por status", periodo=periodo, grafico_sugerido="barra")

    allowed_ids = _allowed_viagem_ids(db, usuario_logado)

    q = db.query(models.Viagem.status.label("status"), func.count(models.Viagem.id).label("qtd"))
    if allowed_ids is not None:
        if not allowed_ids:
            base["resumo_textual"] = "Nenhuma viagem disponível para gerar o relatório."
            return base
        q = q.filter(models.Viagem.id.in_(allowed_ids))
    if periodo.inicio is not None:
        q = q.filter(models.Viagem.data_hora_prevista_saida >= periodo.inicio)
    if periodo.fim is not None:
        q = q.filter(models.Viagem.data_hora_prevista_saida <= periodo.fim)

    rows = q.group_by(models.Viagem.status).order_by(func.count(models.Viagem.id).desc()).all()
    dados = []
    total = 0
    for status, qtd in rows:
        label = str(status or "").strip() or "Sem status"
        valor = int(qtd or 0)
        total += valor
        dados.append({"label": label, "valor": valor, "status": label})

    base["dados"] = dados
    base["totais"] = {"total_viagens": int(total)}
    base["resumo_textual"] = f"Total de viagens: {total}." if total else "Sem viagens no período."
    return base


RELATORIOS = {
    TipoRelatorio.despesas_por_viagem: despesas_por_viagem,
    TipoRelatorio.despesas_por_categoria: despesas_por_categoria,
    TipoRelatorio.despesas_por_usuario: despesas_por_usuario,
    TipoRelatorio.custo_por_km: custo_por_km,
    TipoRelatorio.horas_atividade_por_usuario: horas_atividade_por_usuario,
    TipoRelatorio.viagens_por_status: viagens_por_status,
}


def gerar(db: Session, *, tipo: str, filtros: dict[str, Any], usuario_logado: models.Usuario):
    try:
        t = TipoRelatorio(str(tipo))
    except Exception:
        return {"erro": "Tipo de relatório inválido."}
    fn = RELATORIOS.get(t)
    if not fn:
        return {"erro": "Tipo de relatório inválido."}
    filtros = filtros if isinstance(filtros, dict) else {}
    return fn(db, filtros, usuario_logado)
