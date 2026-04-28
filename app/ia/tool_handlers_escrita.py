import json
from typing import Any

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


TOOL_DISPATCH_ESCRITA = {
    "criar_despesa": criar_despesa,
    "criar_atividade": criar_atividade,
}


def dispatch_tool_escrita(db: Session, usuario_logado: models.Usuario, tool_name: str, tool_args: dict):
    fn = TOOL_DISPATCH_ESCRITA.get(tool_name)
    if not fn:
        return {"erro": f"Ferramenta desconhecida: {tool_name}"}
    return fn(db, usuario_logado, tool_args or {})
