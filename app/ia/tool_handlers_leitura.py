import json
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import crud, models
from . import relatorios


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
    uid = int(user.id)
    if v.responsavel_id == uid:
        return True
    if v.transporte and v.transporte.motorista_id == uid:
        return True
    if any(p.id == uid for p in (v.participantes or [])):
        return True
    return False


def _sanitize_usuario(u: models.Usuario):
    return {
        "id": u.id,
        "nome": u.nome,
        "email": u.email,
        "tipousuario": u.tipousuario,
        "tem_cnh": bool(getattr(u, "tem_cnh", False)),
    }


def _sanitize_veiculo(v: models.Veiculo):
    return {"id": v.id, "placa": v.placa, "modelo": v.modelo, "marca": v.marca, "ano": v.ano}


def _sanitize_viagem(v: models.Viagem):
    return {
        "id": v.id,
        "status": v.status,
        "motivo": v.motivo,
        "clientes": list(getattr(v, "clientes", []) or []),
        "data_hora_prevista_saida": v.data_hora_prevista_saida.isoformat() if v.data_hora_prevista_saida else None,
        "data_hora_prevista_retorno": v.data_hora_prevista_retorno.isoformat() if v.data_hora_prevista_retorno else None,
        "responsavel_id": v.responsavel_id,
    }


def _sanitize_despesa(d: models.Despesa):
    return {
        "id": d.id,
        "viagem_id": d.viagem_id,
        "descricao": d.descricao,
        "valor": float(d.valor),
        "forma_pagamento": d.forma_pagamento,
        "data_registro": d.data_registro.isoformat() if d.data_registro else None,
    }


def _sanitize_viagem_detalhada(v: models.Viagem, *, incluir_despesas: bool, incluir_atividades: bool):
    transporte = None
    if getattr(v, "transporte", None):
        t = v.transporte
        transporte = {
            "id": t.id,
            "veiculo_id": t.veiculo_id,
            "motorista_id": t.motorista_id,
            "km_saida": t.km_saida,
            "km_chegada": t.km_chegada,
            "veiculo": _sanitize_veiculo(t.veiculo) if getattr(t, "veiculo", None) else None,
            "motorista": _sanitize_usuario(t.motorista) if getattr(t, "motorista", None) else None,
        }

    despesas = []
    if incluir_despesas:
        for d in getattr(v, "despesas", []) or []:
            despesas.append(
                {
                    "id": d.id,
                    "viagem_id": d.viagem_id,
                    "descricao": d.descricao,
                    "valor": float(d.valor),
                    "forma_pagamento": d.forma_pagamento,
                    "tipo_pagamento": getattr(d, "tipo_pagamento", None),
                    "criado_por_id": getattr(d, "criado_por_id", None),
                    "pago_por_id": getattr(d, "pago_por_id", None),
                    "registrado_para_id": getattr(d, "registrado_para_id", None),
                    "comprovante_url": getattr(d, "comprovante_url", None),
                    "data_registro": d.data_registro.isoformat() if getattr(d, "data_registro", None) else None,
                }
            )

    atividades = []
    if incluir_atividades:
        for a in getattr(v, "atividades", []) or []:
            pausas = []
            for p in getattr(a, "pausas", []) or []:
                pausas.append(
                    {
                        "id": p.id,
                        "atividade_id": p.atividade_id,
                        "motivo": p.motivo,
                        "inicio": p.inicio.isoformat() if getattr(p, "inicio", None) else None,
                        "fim": p.fim.isoformat() if getattr(p, "fim", None) else None,
                    }
                )
            atividades.append(
                {
                    "id": a.id,
                    "viagem_id": a.viagem_id,
                    "usuario_id": a.usuario_id,
                    "descricao": a.descricao,
                    "ordem": getattr(a, "ordem", None),
                    "inicio": a.inicio.isoformat() if getattr(a, "inicio", None) else None,
                    "fim": a.fim.isoformat() if getattr(a, "fim", None) else None,
                    "status": a.status,
                    "pausas": pausas,
                }
            )

    return {
        "id": v.id,
        "status": v.status,
        "motivo": v.motivo,
        "clientes": list(getattr(v, "clientes", []) or []),
        "data_criacao": v.data_criacao.isoformat() if getattr(v, "data_criacao", None) else None,
        "data_hora_prevista_saida": v.data_hora_prevista_saida.isoformat() if getattr(v, "data_hora_prevista_saida", None) else None,
        "data_hora_prevista_retorno": v.data_hora_prevista_retorno.isoformat() if getattr(v, "data_hora_prevista_retorno", None) else None,
        "data_hora_real_saida": v.data_hora_real_saida.isoformat() if getattr(v, "data_hora_real_saida", None) else None,
        "data_hora_real_chegada": v.data_hora_real_chegada.isoformat() if getattr(v, "data_hora_real_chegada", None) else None,
        "meio_transporte": v.meio_transporte,
        "obs_interna": getattr(v, "obs_interna", None),
        "obs_geral": getattr(v, "obs_geral", None),
        "responsavel_id": getattr(v, "responsavel_id", None),
        "participantes": [_sanitize_usuario(u) for u in (getattr(v, "participantes", None) or [])],
        "transporte": transporte,
        "despesas": despesas,
        "atividades": atividades,
    }


def listar_usuarios(db: Session, usuario_logado: models.Usuario, args: dict):
    limit = args.get("limit", 20)
    query = args.get("query")
    users = crud.ia_listar_usuarios(db, query=query, limit=limit)
    return [_sanitize_usuario(u) for u in users]


def listar_veiculos(db: Session, usuario_logado: models.Usuario, args: dict):
    limit = args.get("limit", 20)
    query = args.get("query")
    items = crud.ia_listar_veiculos(db, query=query, limit=limit)
    return [_sanitize_veiculo(v) for v in items]


def listar_viagens(db: Session, usuario_logado: models.Usuario, args: dict):
    limit = max(1, min(int(args.get("limit") or 20), 100))
    status = args.get("status")
    responsavel_id = args.get("responsavel_id")
    periodo_inicio = _parse_iso_dt(args.get("periodo_inicio"))
    periodo_fim = _parse_iso_dt(args.get("periodo_fim"))

    q = crud.ia_listar_viagens_query(
        db,
        status=str(status) if status else None,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        responsavel_id=int(responsavel_id) if responsavel_id is not None else None,
    )

    if not _user_can_view_all_trips(db, usuario_logado):
        uid = int(usuario_logado.id)
        q = q.filter(
            or_(
                models.Viagem.responsavel_id == uid,
                models.Viagem.participantes.any(models.Usuario.id == uid),
                models.Viagem.transporte.has(models.TransporteViagem.motorista_id == uid),
            )
        )

    viagens = q.order_by(models.Viagem.data_criacao.desc()).limit(limit).all()
    return [_sanitize_viagem(v) for v in viagens]


def obter_viagem_detalhes(db: Session, usuario_logado: models.Usuario, args: dict):
    viagem_id = args.get("viagem_id")
    if viagem_id is None:
        return {"erro": "Informe viagem_id."}
    try:
        viagem_id = int(viagem_id)
    except Exception:
        return {"erro": "viagem_id inválido."}

    if not _user_can_view_viagem(db, usuario_logado, viagem_id):
        return {"erro": "Você não tem permissão para isso."}

    incluir_despesas = bool(args.get("incluir_despesas", True))
    incluir_atividades = bool(args.get("incluir_atividades", True))

    v = crud.get_viagem(db, viagem_id)
    if not v:
        return {"erro": "Viagem não encontrada."}

    v.participantes
    if getattr(v, "transporte", None):
        _ = v.transporte.veiculo
        _ = v.transporte.motorista
    if incluir_despesas:
        v.despesas
    if incluir_atividades:
        v.atividades
        for a in getattr(v, "atividades", []) or []:
            a.pausas

    return _sanitize_viagem_detalhada(v, incluir_despesas=incluir_despesas, incluir_atividades=incluir_atividades)


def listar_despesas(db: Session, usuario_logado: models.Usuario, args: dict):
    viagem_id = args.get("viagem_id")
    if viagem_id is None:
        return {"erro": "Informe viagem_id para listar despesas."}
    try:
        viagem_id = int(viagem_id)
    except Exception:
        return {"erro": "viagem_id inválido."}

    if not _user_can_view_viagem(db, usuario_logado, viagem_id):
        return {"erro": "Você não tem permissão para isso."}

    limit = max(1, min(int(args.get("limit") or 50), 200))
    categoria = args.get("categoria")
    periodo_inicio = _parse_iso_dt(args.get("periodo_inicio"))
    periodo_fim = _parse_iso_dt(args.get("periodo_fim"))

    q = crud.ia_listar_despesas_query(
        db,
        viagem_id=viagem_id,
        categoria=str(categoria) if categoria else None,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
    )
    despesas = q.order_by(models.Despesa.data_registro.desc()).limit(limit).all()
    return [_sanitize_despesa(d) for d in despesas]


def buscar_atividades(db: Session, usuario_logado: models.Usuario, args: dict):
    query = str(args.get("query") or "").strip()
    if not query:
        return {"erro": "Informe query."}

    viagem_id = args.get("viagem_id")
    limit = args.get("limit", 20)
    try:
        limit = int(limit)
    except Exception:
        limit = 20
    limit = max(1, min(limit, 50))

    viagem_ids: list[int] | None = None
    if viagem_id is not None:
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        viagem_ids = [viagem_id]
    else:
        if not _user_can_view_all_trips(db, usuario_logado):
            uid = int(usuario_logado.id)
            viagem_ids = [v.id for v in crud.get_viagens_for_user(db, user_id=uid, limit=500)]

    needle = f"%{query}%"
    q = db.query(models.Atividade).filter(models.Atividade.descricao.ilike(needle))
    if viagem_ids is not None:
        if not viagem_ids:
            return []
        q = q.filter(models.Atividade.viagem_id.in_(viagem_ids))

    atividades = (
        q.order_by(models.Atividade.viagem_id.asc(), models.Atividade.ordem.asc(), models.Atividade.id.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": int(a.id),
            "viagem_id": int(a.viagem_id),
            "descricao": str(a.descricao),
            "status": str(a.status),
            "ordem": int(a.ordem) if getattr(a, "ordem", None) is not None else None,
        }
        for a in atividades
    ]


def buscar_categorias_despesa(db: Session, usuario_logado: models.Usuario, args: dict):
    cfg = crud.get_app_config(db)
    raw = getattr(cfg, "expense_description_options", None) or "[]"
    try:
        data = json.loads(raw) if isinstance(raw, str) else []
    except Exception:
        data = []
    if not isinstance(data, list):
        data = []
    categorias = [str(c).strip() for c in data if str(c).strip()]
    return categorias


def consultar_metrica(db: Session, usuario_logado: models.Usuario, args: dict):
    tipo = args.get("tipo")
    filtros = args.get("filtros") or {}
    if not isinstance(filtros, dict):
        filtros = {}

    if tipo == "total_despesas_viagem":
        viagem_id = filtros.get("viagem_id")
        if viagem_id is None:
            return {"erro": "Informe filtros.viagem_id."}
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        total = crud.ia_total_despesas_viagem(db, viagem_id)
        return {"viagem_id": viagem_id, "total": total}

    if tipo == "custo_por_km":
        viagem_id = filtros.get("viagem_id")
        if viagem_id is None:
            return {"erro": "Informe filtros.viagem_id."}
        try:
            viagem_id = int(viagem_id)
        except Exception:
            return {"erro": "viagem_id inválido."}
        if not _user_can_view_viagem(db, usuario_logado, viagem_id):
            return {"erro": "Você não tem permissão para isso."}
        total = crud.ia_total_despesas_viagem(db, viagem_id)
        km_saida, km_chegada = crud.ia_get_transporte_kms(db, viagem_id)
        if km_saida is None or km_chegada is None:
            return {"erro": "KM de saída/chegada não informado para essa viagem."}
        distancia = float(km_chegada) - float(km_saida)
        if distancia <= 0:
            return {"erro": "Distância inválida (km_chegada deve ser maior que km_saida)."}
        return {"viagem_id": viagem_id, "total_despesas": total, "distancia_km": distancia, "custo_por_km": total / distancia}

    if tipo == "ranking_categorias":
        periodo_inicio = _parse_iso_dt(filtros.get("periodo_inicio"))
        periodo_fim = _parse_iso_dt(filtros.get("periodo_fim"))
        viagem_id = filtros.get("viagem_id")
        limit = filtros.get("limit", 10)

        viagem_ids: list[int] | None = None
        if viagem_id is not None:
            try:
                viagem_id = int(viagem_id)
            except Exception:
                return {"erro": "viagem_id inválido."}
            if not _user_can_view_viagem(db, usuario_logado, viagem_id):
                return {"erro": "Você não tem permissão para isso."}
            viagem_ids = [viagem_id]
        elif not _user_can_view_all_trips(db, usuario_logado):
            uid = int(usuario_logado.id)
            viagem_ids = [v.id for v in crud.get_viagens_for_user(db, user_id=uid, limit=500)]

        rows = crud.ia_ranking_categorias(db, viagem_ids=viagem_ids, periodo_inicio=periodo_inicio, periodo_fim=periodo_fim, limit=limit)
        return [{"categoria": r[0], "total": float(r[1] or 0.0)} for r in rows]

    if tipo == "horas_atividade_usuario":
        usuario_id = filtros.get("usuario_id", usuario_logado.id)
        try:
            usuario_id = int(usuario_id)
        except Exception:
            return {"erro": "usuario_id inválido."}
        if getattr(usuario_logado, "tipousuario", None) != "admin" and usuario_id != int(usuario_logado.id):
            return {"erro": "Você não tem permissão para isso."}

        periodo_inicio = _parse_iso_dt(filtros.get("periodo_inicio"))
        periodo_fim = _parse_iso_dt(filtros.get("periodo_fim"))
        atividades = crud.ia_listar_atividades_usuario(db, usuario_id=usuario_id, periodo_inicio=periodo_inicio, periodo_fim=periodo_fim)
        total_seconds = 0.0
        for a in atividades:
            if not a.inicio or not a.fim:
                continue
            delta = a.fim - a.inicio
            total_seconds += max(0.0, float(delta.total_seconds()))
        return {"usuario_id": usuario_id, "total_horas": total_seconds / 3600.0}

    return {"erro": "Tipo de métrica inválido."}


def gerar_relatorio(db: Session, usuario_logado: models.Usuario, args: dict):
    tipo = args.get("tipo")
    if not tipo:
        return {"erro": "Informe tipo."}

    filtros = {
        "periodo_inicio": args.get("periodo_inicio"),
        "periodo_fim": args.get("periodo_fim"),
        "viagem_id": args.get("viagem_id"),
        "usuario_id": args.get("usuario_id"),
        "agrupar_por": args.get("agrupar_por"),
        "limit": args.get("limit"),
    }
    return relatorios.gerar(db, tipo=str(tipo), filtros=filtros, usuario_logado=usuario_logado)


TOOL_DISPATCH = {
    "listar_usuarios": listar_usuarios,
    "listar_veiculos": listar_veiculos,
    "listar_viagens": listar_viagens,
    "obter_viagem_detalhes": obter_viagem_detalhes,
    "listar_despesas": listar_despesas,
    "buscar_atividades": buscar_atividades,
    "buscar_categorias_despesa": buscar_categorias_despesa,
    "consultar_metrica": consultar_metrica,
    "gerar_relatorio": gerar_relatorio,
}


def dispatch_tool(db: Session, usuario_logado: models.Usuario, tool_name: str, tool_args: dict):
    fn = TOOL_DISPATCH.get(tool_name)
    if not fn:
        return {"erro": f"Ferramenta desconhecida: {tool_name}"}
    return fn(db, usuario_logado, tool_args or {})
