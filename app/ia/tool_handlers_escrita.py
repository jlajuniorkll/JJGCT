import json
from typing import Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .. import crud, models
from . import proposals


def _parse_json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        if not isinstance(parsed, list):
            return []
        return [str(x) for x in parsed if str(x).strip()]
    except json.JSONDecodeError:
        return []


def _user_is_participant(user: models.Usuario, viagem: models.Viagem) -> bool:
    uid = int(getattr(user, "id", 0) or 0)
    return any(int(getattr(u, "id", 0) or 0) == uid for u in (getattr(viagem, "participantes", None) or []))


def _status_allows_mutation(db: Session, viagem: models.Viagem) -> bool:
    cfg = crud.get_app_config(db)
    allowed = _parse_json_list(getattr(cfg, "trip_activity_expense_allowed_statuses", None))
    return str(getattr(viagem, "status", "") or "") in allowed


def _categorias_permitidas(db: Session) -> list[str]:
    cfg = crud.get_app_config(db)
    return _parse_json_list(getattr(cfg, "expense_description_options", None))


def _expense_photo_required(db: Session) -> bool:
    cfg = crud.get_app_config(db)
    return bool(getattr(cfg, "expense_photo_required", False))


def _fmt_brl(valor: float) -> str:
    try:
        v = float(valor)
    except Exception:
        return "R$ ?"
    s = f"{v:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def criar_despesa(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id", "valor", "descricao", "forma_pagamento"):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    try:
        valor = float(args.get("valor"))
    except Exception:
        return {"erro": "valor inválido."}
    if valor <= 0:
        return {"erro": "valor inválido (deve ser maior que zero)."}

    descricao = str(args.get("descricao") or "").strip()
    forma_pagamento = str(args.get("forma_pagamento") or "").strip()

    if not descricao:
        return {"erro": "descricao inválida."}
    if not forma_pagamento:
        return {"erro": "forma_pagamento inválida."}

    categorias = _categorias_permitidas(db)
    if categorias and descricao not in categorias:
        lookup = {str(c).strip().lower(): str(c).strip() for c in categorias if str(c).strip()}
        mapped = lookup.get(descricao.lower())
        if mapped:
            descricao = mapped
        else:
            return {"erro": "Descrição/categoria inválida para despesa."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if not _status_allows_mutation(db, db_viagem):
        return {"erro": "Você não tem permissão para isso.", "detalhe": "Despesas não permitidas para este status de viagem."}

    comprovante_url = args.get("comprovante_url")
    comprovante_url = str(comprovante_url).strip() if comprovante_url is not None else None
    if _expense_photo_required(db) and not comprovante_url:
        return {"erro": "campos faltando: comprovante_url"}

    tipo_pagamento = str(args.get("tipo_pagamento") or "INDIVIDUAL").strip().upper()
    if tipo_pagamento not in {"INDIVIDUAL", "COMPARTILHADO"}:
        return {"erro": "tipo_pagamento inválido (use INDIVIDUAL ou COMPARTILHADO)."}

    registrado_para_id = args.get("registrado_para_id")
    if registrado_para_id is None:
        registrado_para_id = int(usuario_logado.id)
    else:
        try:
            registrado_para_id = int(registrado_para_id)
        except Exception:
            return {"erro": "registrado_para_id inválido."}

    args_validados = {
        "viagem_id": viagem_id,
        "valor": valor,
        "descricao": descricao,
        "forma_pagamento": forma_pagamento,
        "tipo_pagamento": tipo_pagamento,
        "registrado_para_id": registrado_para_id,
        "comprovante_url": comprovante_url or None,
    }

    resumo = (
        f"Criar despesa na Viagem #{viagem_id}\n"
        f"- Valor: {_fmt_brl(valor)}\n"
        f"- Descrição: {descricao}\n"
        f"- Forma de pagamento: {forma_pagamento}\n"
        f"- Tipo: {tipo_pagamento}\n"
        f"- Registrado para: usuário #{registrado_para_id}\n"
        f"- Comprovante: {'sim' if comprovante_url else 'não'}"
    )

    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="criar_despesa",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


def criar_atividade(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id", "descricao"):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    descricao = str(args.get("descricao") or "").strip()
    if not descricao:
        return {"erro": "descricao inválida."}

    usuario_id = args.get("usuario_id")
    if usuario_id is None:
        usuario_id = int(usuario_logado.id)
    else:
        try:
            usuario_id = int(usuario_id)
        except Exception:
            return {"erro": "usuario_id inválido."}
        if getattr(usuario_logado, "tipousuario", None) != "admin" and usuario_id != int(usuario_logado.id):
            return {"erro": "Você não tem permissão para isso."}

    ordem = args.get("ordem")
    if ordem is None:
        ordem_int = None
    else:
        try:
            ordem_int = int(ordem)
        except Exception:
            return {"erro": "ordem inválida."}
        if ordem_int < 1:
            return {"erro": "ordem inválida (mínimo 1)."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if not _status_allows_mutation(db, db_viagem):
        return {"erro": "Você não tem permissão para isso.", "detalhe": "Atividades não permitidas para este status de viagem."}

    args_validados = {
        "viagem_id": viagem_id,
        "descricao": descricao,
        "usuario_id": usuario_id,
        "ordem": ordem_int,
    }

    resumo = (
        f"Criar atividade na Viagem #{viagem_id}\n"
        f"- Descrição: {descricao}\n"
        f"- Usuário: #{usuario_id}"
        + (f"\n- Ordem: {ordem_int}" if ordem_int else "")
    )

    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="criar_atividade",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


def iniciar_atividade(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id", "atividade_id"):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    try:
        atividade_id = int(args.get("atividade_id"))
    except Exception:
        return {"erro": "atividade_id inválido."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if not _status_allows_mutation(db, db_viagem):
        return {"erro": "Você não tem permissão para isso.", "detalhe": "Atividades não permitidas para este status de viagem."}

    atividade = crud.get_atividade(db, atividade_id)
    if not atividade:
        return {"erro": "Atividade não encontrada."}
    if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
        return {"erro": "Atividade não pertence a esta viagem."}

    status = str(getattr(atividade, "status", "") or "")
    if status == "finalizada":
        return {"erro": "Atividade já está finalizada."}
    if status != "pendente":
        return {"erro": "Atividade não está pendente para iniciar."}

    args_validados = {"viagem_id": viagem_id, "atividade_id": atividade_id}
    resumo = (
        f"Iniciar atividade #{atividade_id} na Viagem #{viagem_id}\n"
        f"- Descrição: {getattr(atividade, 'descricao', '')}"
    )
    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="iniciar_atividade",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


def pausar_atividade(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id", "atividade_id", "motivo"):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    try:
        atividade_id = int(args.get("atividade_id"))
    except Exception:
        return {"erro": "atividade_id inválido."}

    motivo = str(args.get("motivo") or "").strip()
    if not motivo:
        return {"erro": "motivo inválido."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if not _status_allows_mutation(db, db_viagem):
        return {"erro": "Você não tem permissão para isso.", "detalhe": "Atividades não permitidas para este status de viagem."}

    atividade = crud.get_atividade(db, atividade_id)
    if not atividade:
        return {"erro": "Atividade não encontrada."}
    if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
        return {"erro": "Atividade não pertence a esta viagem."}

    status = str(getattr(atividade, "status", "") or "")
    if status != "ativa":
        return {"erro": "Atividade não está ativa para pausar."}

    open_pause = (
        db.query(models.Pausa)
        .filter(models.Pausa.atividade_id == atividade_id)
        .filter(models.Pausa.fim.is_(None))
        .first()
    )
    if open_pause:
        return {"erro": "Já existe uma pausa em aberto para esta atividade.", "pausa_id": int(open_pause.id)}

    args_validados = {"viagem_id": viagem_id, "atividade_id": atividade_id, "motivo": motivo}
    resumo = (
        f"Pausar atividade #{atividade_id} na Viagem #{viagem_id}\n"
        f"- Motivo: {motivo}"
    )
    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="pausar_atividade",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


def finalizar_pausa(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id", "pausa_id"):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    try:
        pausa_id = int(args.get("pausa_id"))
    except Exception:
        return {"erro": "pausa_id inválido."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if not _status_allows_mutation(db, db_viagem):
        return {"erro": "Você não tem permissão para isso.", "detalhe": "Atividades não permitidas para este status de viagem."}

    pausa = db.query(models.Pausa).filter(models.Pausa.id == pausa_id).first()
    if not pausa:
        return {"erro": "Pausa não encontrada."}

    atividade = crud.get_atividade(db, int(getattr(pausa, "atividade_id", 0) or 0))
    if not atividade:
        return {"erro": "Atividade da pausa não encontrada."}
    if int(getattr(atividade, "viagem_id", 0) or 0) != viagem_id:
        return {"erro": "Pausa não pertence a esta viagem."}

    if getattr(pausa, "fim", None) is not None:
        return {"erro": "Pausa já está finalizada."}

    args_validados = {"viagem_id": viagem_id, "pausa_id": pausa_id}
    resumo = f"Finalizar pausa #{pausa_id} (retomar atividade #{int(getattr(pausa, 'atividade_id', 0) or 0)}) na Viagem #{viagem_id}"
    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="finalizar_pausa",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


def finalizar_viagem(db: Session, usuario_logado: models.Usuario, args: dict[str, Any]):
    missing: list[str] = []
    for k in ("viagem_id",):
        if args.get(k) is None or (isinstance(args.get(k), str) and not str(args.get(k)).strip()):
            missing.append(k)
    if missing:
        return {"erro": "campos faltando: " + ", ".join(missing)}

    try:
        viagem_id = int(args.get("viagem_id"))
    except Exception:
        return {"erro": "viagem_id inválido."}

    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        return {"erro": "Viagem não encontrada."}
    if not _user_is_participant(usuario_logado, db_viagem):
        return {"erro": "Você não tem permissão para isso."}
    if str(getattr(db_viagem, "status", "") or "") != "em_andamento":
        return {"erro": "A chegada só pode ser registrada para viagens em andamento."}

    pendentes = [a for a in (getattr(db_viagem, "atividades", None) or []) if str(getattr(a, "status", "") or "") != "finalizada"]
    if pendentes:
        return {
            "erro": "Ainda existem atividades não finalizadas. Finalize todas antes de encerrar a viagem.",
            "atividades_pendentes": [
                {"id": int(a.id), "descricao": str(a.descricao), "status": str(a.status)} for a in pendentes
            ],
        }

    cfg = crud.get_app_config(db)
    allow_manual_dt = bool(getattr(cfg, "trip_allow_manual_arrival_datetime", False))

    data_hora_real_chegada = None
    dt_raw = args.get("data_hora_real_chegada")
    if dt_raw is not None:
        if not allow_manual_dt:
            return {"erro": "Configuração não permite informar data/hora de chegada manualmente."}
        s = str(dt_raw or "").strip()
        if s:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(s)
            except Exception:
                return {"erro": "data_hora_real_chegada inválida."}
            if getattr(dt, "tzinfo", None) is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            data_hora_real_chegada = dt

    km_chegada = args.get("km_chegada")
    needs_km = str(getattr(db_viagem, "meio_transporte", "") or "") in {"carro empresa", "carro próprio"}
    if needs_km and km_chegada is None:
        return {"erro": "campos faltando: km_chegada"}

    km_chegada_f = None
    if km_chegada is not None:
        try:
            km_chegada_f = float(km_chegada)
        except Exception:
            return {"erro": "km_chegada inválido."}
        if km_chegada_f <= 0:
            return {"erro": "km_chegada inválido."}
        if getattr(db_viagem, "transporte", None) and getattr(db_viagem.transporte, "km_saida", None) is not None:
            try:
                km_saida = float(db_viagem.transporte.km_saida)
            except Exception:
                km_saida = None
            if km_saida is not None and km_chegada_f < km_saida:
                return {"erro": "km_chegada inválido (deve ser maior ou igual ao km de saída)."}

    args_validados = {"viagem_id": viagem_id, "km_chegada": km_chegada_f, "data_hora_real_chegada": data_hora_real_chegada.isoformat() if data_hora_real_chegada else None}
    resumo = (
        f"Finalizar viagem #{viagem_id} (registrar chegada)\n"
        + (f"- KM chegada: {km_chegada_f}" if km_chegada_f is not None else "- KM chegada: (não informado)")
        + (f"\n- Chegada: {data_hora_real_chegada.isoformat()}" if data_hora_real_chegada else "")
    )
    prop = proposals.criar_proposta(
        usuario_id=int(usuario_logado.id),
        ferramenta="finalizar_viagem",
        args_validados=args_validados,
        resumo_legivel=resumo,
    )
    return prop.to_dict()


TOOL_DISPATCH_ESCRITA = {
    "criar_despesa": criar_despesa,
    "criar_atividade": criar_atividade,
    "iniciar_atividade": iniciar_atividade,
    "pausar_atividade": pausar_atividade,
    "finalizar_pausa": finalizar_pausa,
    "finalizar_viagem": finalizar_viagem,
}


def dispatch_tool_escrita(db: Session, usuario_logado: models.Usuario, tool_name: str, tool_args: dict):
    fn = TOOL_DISPATCH_ESCRITA.get(tool_name)
    if not fn:
        return {"erro": f"Ferramenta desconhecida: {tool_name}"}
    return fn(db, usuario_logado, tool_args or {})
