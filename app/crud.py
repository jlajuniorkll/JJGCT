import json

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from . import models, schemas
from datetime import datetime, timezone
from .ia.client import encrypt_secret


def _utcnow_naive():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_app_config_schema(engine):
    dialect = engine.dialect.name
    columns = [
        ("ia_provider", "text", "'anthropic'", True),
        ("ia_model_anthropic", "text", "'claude-sonnet-4-6'", True),
        ("ia_model_gemini", "text", "'gemini-2.5-flash'", True),
        ("anthropic_api_key_enc", "text", None, False),
        ("anthropic_api_key_last4", "text", None, False),
        ("gemini_api_key_enc", "text", None, False),
        ("gemini_api_key_last4", "text", None, False),
        ("report_include_receipts", "boolean", "true", True),
        ("trip_allow_manual_arrival_datetime", "boolean", "false", True),
    ]

    with engine.begin() as conn:
        if dialect == "sqlite":
            existing = set()
            try:
                rows = conn.execute(text("PRAGMA table_info(app_config)")).fetchall()
                existing = {r[1] for r in rows}
            except Exception:
                return

            for name, coltype, default_sql, not_null in columns:
                if name in existing:
                    continue
                pieces = [f"ALTER TABLE app_config ADD COLUMN {name} {coltype}"]
                if default_sql is not None:
                    pieces.append(f"DEFAULT {default_sql}")
                if not_null:
                    pieces.append("NOT NULL")
                conn.execute(text(" ".join(pieces)))
            return

        if dialect == "postgresql":
            for name, coltype, default_sql, not_null in columns:
                default_part = f"DEFAULT {default_sql}" if default_sql is not None else ""
                not_null_part = "NOT NULL" if not_null else ""
                conn.execute(
                    text(
                        "DO $$\n"
                        "BEGIN\n"
                        "  IF NOT EXISTS (\n"
                        "    SELECT 1 FROM information_schema.columns\n"
                        f"    WHERE table_name = 'app_config' AND column_name = '{name}'\n"
                        "  ) THEN\n"
                        f"    ALTER TABLE app_config ADD COLUMN {name} {coltype} {default_part} {not_null_part};\n"
                        "  END IF;\n"
                        "END $$;"
                    )
                )
            return

# Funções CRUD para Usuário
def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_usuario_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    # Em um ambiente de produção, a senha deve ser "hasheada"
    db_usuario = models.Usuario(
        email=usuario.email, 
        senha=usuario.senha, 
        nome=usuario.nome, 
        tipousuario=usuario.tipousuario,
        tem_cnh=usuario.tem_cnh
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def update_usuario(db: Session, usuario_id: int, usuario: schemas.UsuarioUpdate):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None

    if usuario.email is not None and usuario.email != db_usuario.email:
        existing = get_usuario_by_email(db, usuario.email)
        if existing and existing.id != db_usuario.id:
            raise ValueError("Email already registered")
        db_usuario.email = usuario.email

    if usuario.nome is not None:
        db_usuario.nome = usuario.nome

    if usuario.tipousuario is not None:
        db_usuario.tipousuario = usuario.tipousuario

    if usuario.tem_cnh is not None:
        db_usuario.tem_cnh = usuario.tem_cnh

    if usuario.senha is not None:
        db_usuario.senha = usuario.senha

    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def delete_usuario(db: Session, usuario_id: int):
    db_usuario = get_usuario(db, usuario_id)
    if not db_usuario:
        return None

    if getattr(db_usuario, 'viagens', None):
        if len(db_usuario.viagens) > 0:
            raise ValueError("Usuário possui viagens vinculadas")

    db.delete(db_usuario)
    db.commit()
    return db_usuario

# Funções CRUD para Veículo
def get_veiculo(db: Session, veiculo_id: int):
    return db.query(models.Veiculo).filter(models.Veiculo.id == veiculo_id).first()

def get_veiculo_by_placa(db: Session, placa: str):
    return db.query(models.Veiculo).filter(models.Veiculo.placa == placa).first()

def get_veiculos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Veiculo).offset(skip).limit(limit).all()

def create_veiculo(db: Session, veiculo: schemas.VeiculoCreate):
    db_veiculo = models.Veiculo(**veiculo.dict())
    db.add(db_veiculo)
    db.commit()
    db.refresh(db_veiculo)
    return db_veiculo


def update_veiculo(db: Session, veiculo_id: int, veiculo: schemas.VeiculoUpdate):
    db_veiculo = get_veiculo(db, veiculo_id)
    if not db_veiculo:
        return None

    if veiculo.placa is not None and veiculo.placa != db_veiculo.placa:
        existing = get_veiculo_by_placa(db, veiculo.placa)
        if existing and existing.id != db_veiculo.id:
            raise ValueError("Placa already registered")
        db_veiculo.placa = veiculo.placa

    if veiculo.modelo is not None:
        db_veiculo.modelo = veiculo.modelo

    if veiculo.marca is not None:
        db_veiculo.marca = veiculo.marca

    if veiculo.ano is not None:
        db_veiculo.ano = veiculo.ano

    db.commit()
    db.refresh(db_veiculo)
    return db_veiculo


def delete_veiculo(db: Session, veiculo_id: int):
    db_veiculo = get_veiculo(db, veiculo_id)
    if not db_veiculo:
        return None

    linked = db.query(models.TransporteViagem).filter(models.TransporteViagem.veiculo_id == veiculo_id).first()
    if linked:
        raise ValueError("Veículo possui viagens vinculadas")

    db.delete(db_veiculo)
    db.commit()
    return db_veiculo


def get_app_config(db: Session):
    cfg = db.query(models.AppConfig).filter(models.AppConfig.id == 1).first()
    if cfg:
        return cfg

    cfg = models.AppConfig(id=1)
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


def update_app_config(db: Session, payload: schemas.AppConfigUpdate):
    cfg = get_app_config(db)

    if payload.expense_photo_required is not None:
        cfg.expense_photo_required = payload.expense_photo_required

    if payload.report_include_receipts is not None:
        cfg.report_include_receipts = payload.report_include_receipts

    if payload.trip_allow_manual_arrival_datetime is not None:
        cfg.trip_allow_manual_arrival_datetime = payload.trip_allow_manual_arrival_datetime

    if payload.expense_description_options is not None:
        cfg.expense_description_options = json.dumps(payload.expense_description_options)

    if payload.activity_edit_delete_allowed_statuses is not None:
        cfg.activity_edit_delete_allowed_statuses = json.dumps(payload.activity_edit_delete_allowed_statuses)

    if payload.ia_provider is not None:
        cfg.ia_provider = payload.ia_provider

    if payload.ia_model_anthropic is not None:
        cfg.ia_model_anthropic = payload.ia_model_anthropic

    if payload.ia_model_gemini is not None:
        cfg.ia_model_gemini = payload.ia_model_gemini

    if payload.anthropic_api_key is not None:
        raw = str(payload.anthropic_api_key or "").strip()
        if raw:
            cfg.anthropic_api_key_enc = encrypt_secret(raw)
            cfg.anthropic_api_key_last4 = raw[-4:] if len(raw) >= 4 else raw
        else:
            cfg.anthropic_api_key_enc = None
            cfg.anthropic_api_key_last4 = None

    if payload.gemini_api_key is not None:
        raw = str(payload.gemini_api_key or "").strip()
        if raw:
            cfg.gemini_api_key_enc = encrypt_secret(raw)
            cfg.gemini_api_key_last4 = raw[-4:] if len(raw) >= 4 else raw
        else:
            cfg.gemini_api_key_enc = None
            cfg.gemini_api_key_last4 = None

    if payload.trip_edit_blocked_statuses is not None:
        cfg.trip_edit_blocked_statuses = json.dumps(payload.trip_edit_blocked_statuses)

    if payload.trip_activity_expense_allowed_statuses is not None:
        cfg.trip_activity_expense_allowed_statuses = json.dumps(payload.trip_activity_expense_allowed_statuses)

    if payload.trips_show_all_admin is not None:
        cfg.trips_show_all_admin = payload.trips_show_all_admin

    if payload.trips_show_all_colaborador is not None:
        cfg.trips_show_all_colaborador = payload.trips_show_all_colaborador

    db.commit()
    db.refresh(cfg)
    return cfg


def update_atividade(db: Session, atividade_id: int, payload: schemas.AtividadeUpdate):
    db_atividade = get_atividade(db, atividade_id=atividade_id)
    if not db_atividade:
        return None

    if payload.descricao is not None:
        db_atividade.descricao = payload.descricao

    db.commit()
    db.refresh(db_atividade)
    return db_atividade


def delete_atividade(db: Session, atividade_id: int):
    db_atividade = get_atividade(db, atividade_id=atividade_id)
    if not db_atividade:
        return None

    db.query(models.Pausa).filter(models.Pausa.atividade_id == atividade_id).delete()
    db.delete(db_atividade)
    db.commit()
    return db_atividade

# Funções CRUD para Viagem
def get_viagem(db: Session, viagem_id: int):
    return db.query(models.Viagem).filter(models.Viagem.id == viagem_id).first()

def get_viagens(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Viagem)
        .order_by(models.Viagem.data_criacao.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_viagens_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 100, order: str = "desc"):
    q = db.query(models.Viagem).filter(
        or_(
            models.Viagem.responsavel_id == user_id,
            models.Viagem.participantes.any(models.Usuario.id == user_id),
            models.Viagem.transporte.has(models.TransporteViagem.motorista_id == user_id),
        )
    )
    if order == "asc":
        q = q.order_by(models.Viagem.data_criacao.asc())
    else:
        q = q.order_by(models.Viagem.data_criacao.desc())
    return q.offset(skip).limit(limit).all()

def create_viagem(db: Session, viagem: schemas.ViagemCreate):
    clientes = [str(c).strip() for c in (viagem.clientes or []) if str(c).strip()]
    if not clientes:
        raise ValueError("A viagem deve ter pelo menos um cliente.")

    # Verificar se todos os participantes existem
    participantes = []
    for usuario_id in viagem.participantes_ids:
        usuario = get_usuario(db, usuario_id)
        if not usuario:
            raise ValueError(f"Usuário com ID {usuario_id} não encontrado.")
        participantes.append(usuario)

    responsavel_id = getattr(viagem, "responsavel_id", None)
    if responsavel_id is None and viagem.transporte and viagem.transporte.motorista_id:
        responsavel_id = viagem.transporte.motorista_id

    if responsavel_id is None:
        responsavel_id = viagem.participantes_ids[0] if viagem.participantes_ids else None

    if responsavel_id is not None and responsavel_id not in viagem.participantes_ids:
        usuario = get_usuario(db, responsavel_id)
        if not usuario:
            raise ValueError("Responsável inválido")
        participantes.append(usuario)

    db_viagem = models.Viagem(
        responsavel_id=responsavel_id,
        motivo=viagem.motivo,
        data_hora_prevista_saida=viagem.data_hora_prevista_saida,
        data_hora_prevista_retorno=viagem.data_hora_prevista_retorno,
        meio_transporte=viagem.meio_transporte,
        obs_interna=viagem.obs_interna,
        obs_geral=viagem.obs_geral,
        participantes=participantes
    )
    db_viagem.clientes_itens = [models.ViagemCliente(nome=nome) for nome in clientes]
    
    if viagem.transporte:
        # Verificar se veículo e motorista existem
        if viagem.transporte.veiculo_id:
            veiculo = get_veiculo(db, viagem.transporte.veiculo_id)
            if not veiculo:
                raise ValueError(f"Veículo com ID {viagem.transporte.veiculo_id} não encontrado.")
        
        if viagem.transporte.motorista_id:
            motorista = get_usuario(db, viagem.transporte.motorista_id)
            if not motorista:
                raise ValueError(f"Motorista com ID {viagem.transporte.motorista_id} não encontrado.")
            if motorista.id not in {u.id for u in participantes}:
                participantes.append(motorista)

        db_transporte = models.TransporteViagem(**viagem.transporte.dict())
        db_viagem.transporte = db_transporte

    db.add(db_viagem)
    db.commit()
    db.refresh(db_viagem)
    return db_viagem


def update_viagem(db: Session, viagem_id: int, viagem: schemas.ViagemUpdate):
    db_viagem = get_viagem(db, viagem_id)
    if not db_viagem:
        return None

    if viagem.motivo is not None:
        db_viagem.motivo = viagem.motivo
    if viagem.clientes is not None:
        clientes = [str(c).strip() for c in (viagem.clientes or []) if str(c).strip()]
        if not clientes:
            raise ValueError("A viagem deve ter pelo menos um cliente.")
        db_viagem.clientes_itens = [models.ViagemCliente(nome=nome) for nome in clientes]
    if viagem.data_hora_prevista_saida is not None:
        db_viagem.data_hora_prevista_saida = viagem.data_hora_prevista_saida
    if viagem.data_hora_prevista_retorno is not None:
        db_viagem.data_hora_prevista_retorno = viagem.data_hora_prevista_retorno
    if viagem.meio_transporte is not None:
        db_viagem.meio_transporte = viagem.meio_transporte
    if viagem.obs_interna is not None:
        db_viagem.obs_interna = viagem.obs_interna
    if viagem.obs_geral is not None:
        db_viagem.obs_geral = viagem.obs_geral

    if viagem.responsavel_id is not None:
        resp = get_usuario(db, viagem.responsavel_id)
        if not resp:
            raise ValueError("Responsável inválido")
        db_viagem.responsavel_id = viagem.responsavel_id

    if viagem.participantes_ids is not None:
        if len(viagem.participantes_ids) == 0:
            raise ValueError("A viagem deve ter pelo menos um participante.")
        participantes = []
        for usuario_id in viagem.participantes_ids:
            usuario = get_usuario(db, usuario_id)
            if not usuario:
                raise ValueError(f"Usuário com ID {usuario_id} não encontrado.")
            participantes.append(usuario)
        db_viagem.participantes = participantes

    if db_viagem.responsavel_id is not None:
        participant_ids = {u.id for u in db_viagem.participantes}
        if db_viagem.responsavel_id not in participant_ids:
            resp = get_usuario(db, db_viagem.responsavel_id)
            if not resp:
                raise ValueError("Responsável inválido")
            db_viagem.participantes.append(resp)

    effective_meio = db_viagem.meio_transporte
    requires_transport = effective_meio in ["carro empresa", "carro próprio"]

    if requires_transport:
        if viagem.transporte:
            if db_viagem.transporte is None:
                db_viagem.transporte = models.TransporteViagem(**viagem.transporte.dict())
            else:
                if viagem.transporte.veiculo_id is not None:
                    db_viagem.transporte.veiculo_id = viagem.transporte.veiculo_id
                if viagem.transporte.motorista_id is not None:
                    db_viagem.transporte.motorista_id = viagem.transporte.motorista_id
                if viagem.transporte.km_saida is not None:
                    db_viagem.transporte.km_saida = viagem.transporte.km_saida
                if viagem.transporte.km_chegada is not None:
                    db_viagem.transporte.km_chegada = viagem.transporte.km_chegada

        if db_viagem.transporte is None:
            raise ValueError("Informações de transporte são obrigatórias para este meio de transporte.")

        if not all([db_viagem.transporte.veiculo_id, db_viagem.transporte.motorista_id]):
            raise ValueError("Veículo e motorista são obrigatórios para este meio de transporte.")

        participant_ids = {u.id for u in db_viagem.participantes}
        if db_viagem.transporte.motorista_id not in participant_ids:
            motorista = get_usuario(db, db_viagem.transporte.motorista_id)
            if not motorista:
                raise ValueError("Motorista inválido")
            db_viagem.participantes.append(motorista)

    else:
        if db_viagem.transporte is not None:
            db.delete(db_viagem.transporte)
            db_viagem.transporte = None

    db.commit()
    db.refresh(db_viagem)
    return db_viagem

def registrar_saida_real(db: Session, viagem_id: int, km_saida: float = None):
    db_viagem = get_viagem(db, viagem_id)
    if db_viagem:
        db_viagem.data_hora_real_saida = _utcnow_naive()
        db_viagem.status = "em_andamento"
        if km_saida is not None and db_viagem.transporte:
            db_viagem.transporte.km_saida = km_saida
        db.commit()
        db.refresh(db_viagem)
    return db_viagem

def registrar_chegada_real(db: Session, viagem_id: int, km_chegada: float = None):
    db_viagem = get_viagem(db, viagem_id)
    if db_viagem:
        db_viagem.data_hora_real_chegada = _utcnow_naive()
        db_viagem.status = "finalizada"
        if km_chegada is not None and db_viagem.transporte:
            db_viagem.transporte.km_chegada = km_chegada
        db.commit()
        db.refresh(db_viagem)
    return db_viagem


def cancelar_viagem(db: Session, viagem_id: int):
    db_viagem = get_viagem(db, viagem_id)
    if db_viagem:
        if db_viagem.status == "finalizada":
            raise ValueError("Viagem já finalizada")
        db_viagem.status = "cancelada"
        db.commit()
        db.refresh(db_viagem)
    return db_viagem

# Funções CRUD para Despesa
def get_despesa(db: Session, despesa_id: int):
    return db.query(models.Despesa).filter(models.Despesa.id == despesa_id).first()


def create_despesa(db: Session, despesa: schemas.DespesaCreate, viagem_id: int, comprovante_url: str):
    db_despesa = models.Despesa(**despesa.dict(), viagem_id=viagem_id, comprovante_url=comprovante_url)
    db.add(db_despesa)
    db.commit()
    db.refresh(db_despesa)
    return db_despesa


def update_despesa(db: Session, despesa_id: int, despesa: schemas.DespesaUpdate):
    db_despesa = get_despesa(db, despesa_id)
    if not db_despesa:
        return None

    if despesa.valor is not None:
        db_despesa.valor = despesa.valor

    if despesa.forma_pagamento is not None:
        db_despesa.forma_pagamento = despesa.forma_pagamento

    if despesa.descricao is not None:
        db_despesa.descricao = despesa.descricao

    if despesa.criado_por_id is not None and db_despesa.criado_por_id is None:
        db_despesa.criado_por_id = despesa.criado_por_id

    if despesa.pago_por_id is not None:
        db_despesa.pago_por_id = despesa.pago_por_id

    if despesa.tipo_pagamento is not None:
        db_despesa.tipo_pagamento = despesa.tipo_pagamento

    if despesa.registrado_para_id is not None:
        db_despesa.registrado_para_id = despesa.registrado_para_id

    if despesa.comprovante_url is not None:
        db_despesa.comprovante_url = despesa.comprovante_url

    db.commit()
    db.refresh(db_despesa)
    return db_despesa


def delete_despesa(db: Session, despesa_id: int):
    db_despesa = get_despesa(db, despesa_id)
    if not db_despesa:
        return None

    db.delete(db_despesa)
    db.commit()
    return db_despesa


def get_despesa_rateios(db: Session, despesa_id: int):
    return (
        db.query(models.DespesaRateio)
        .filter(models.DespesaRateio.despesa_id == despesa_id)
        .all()
    )


def replace_despesa_rateios(db: Session, despesa_id: int, rateios: list[schemas.DespesaRateioBase]):
    db_despesa = get_despesa(db, despesa_id)
    if not db_despesa:
        return None

    seen = set()
    total = 0.0
    for r in rateios:
        if r.usuario_id in seen:
            raise ValueError("Usuário duplicado no rateio")
        seen.add(r.usuario_id)
        if r.valor < 0:
            raise ValueError("Valor de rateio inválido")
        total += float(r.valor)

    if db_despesa.tipo_pagamento == "COMPARTILHADO":
        if abs(total - float(db_despesa.valor)) > 0.01:
            raise ValueError("Somatório do rateio deve ser igual ao valor total")
        if len(rateios) < 2:
            raise ValueError("Despesa compartilhada deve ter rateio para pelo menos 2 participantes")

    db.query(models.DespesaRateio).filter(models.DespesaRateio.despesa_id == despesa_id).delete()
    for r in rateios:
        db.add(models.DespesaRateio(despesa_id=despesa_id, usuario_id=r.usuario_id, valor=r.valor))

    db.commit()
    return get_despesa_rateios(db, despesa_id)

# Funções CRUD para Atividade
def get_atividade(db: Session, atividade_id: int):
    return db.query(models.Atividade).filter(models.Atividade.id == atividade_id).first()

def create_atividade(db: Session, atividade: schemas.AtividadeCreate, viagem_id: int):
    max_ordem = db.query(func.max(models.Atividade.ordem)).filter(models.Atividade.viagem_id == viagem_id).scalar()
    if max_ordem is None:
        max_ordem = db.query(models.Atividade).filter(models.Atividade.viagem_id == viagem_id).count()
    next_ordem = int(max_ordem) + 1
    db_atividade = models.Atividade(**atividade.dict(), viagem_id=viagem_id, ordem=next_ordem)
    db.add(db_atividade)
    db.commit()
    db.refresh(db_atividade)
    return db_atividade

def iniciar_atividade(db: Session, atividade_id: int):
    db_atividade = get_atividade(db, atividade_id)
    if db_atividade:
        db_atividade.inicio = _utcnow_naive()
        db_atividade.status = "ativa"
        db.commit()
        db.refresh(db_atividade)
    return db_atividade

def finalizar_atividade(db: Session, atividade_id: int):
    db_atividade = get_atividade(db, atividade_id)
    if db_atividade:
        db_atividade.fim = _utcnow_naive()
        db_atividade.status = "finalizada"
        db.commit()
        db.refresh(db_atividade)
    return db_atividade

# Funções CRUD para Pausa
def create_pausa(db: Session, pausa: schemas.PausaCreate, atividade_id: int):
    db_pausa = models.Pausa(motivo=pausa.motivo, inicio=_utcnow_naive(), atividade_id=atividade_id)
    db_atividade = get_atividade(db, atividade_id)
    if db_atividade:
        db_atividade.status = "pausada"
    db.add(db_pausa)
    db.commit()
    db.refresh(db_pausa)
    return db_pausa

def finalizar_pausa(db: Session, pausa_id: int):
    db_pausa = db.query(models.Pausa).filter(models.Pausa.id == pausa_id).first()
    if db_pausa:
        db_pausa.fim = _utcnow_naive()
        db_atividade = get_atividade(db, db_pausa.atividade_id)
        if db_atividade:
            db_atividade.status = "ativa"
        db.commit()
        db.refresh(db_pausa)
    return db_pausa


def reorder_atividades(db: Session, viagem_id: int, atividade_ids: list[int]):
    atividades = (
        db.query(models.Atividade)
        .filter(models.Atividade.viagem_id == viagem_id)
        .order_by(models.Atividade.ordem, models.Atividade.id)
        .all()
    )
    if not atividades:
        return []

    existing_ids = [a.id for a in atividades]
    existing_set = set(existing_ids)

    seen = set()
    requested = []
    for aid in atividade_ids or []:
        if aid in seen:
            continue
        seen.add(aid)
        if aid in existing_set:
            requested.append(aid)

    final_ids = requested + [aid for aid in existing_ids if aid not in seen]
    by_id = {a.id: a for a in atividades}

    for idx, aid in enumerate(final_ids, start=1):
        by_id[aid].ordem = idx

    db.commit()
    return [by_id[aid] for aid in final_ids]


def ia_listar_usuarios(db: Session, query: str | None = None, limit: int = 20):
    q = db.query(models.Usuario)
    if query:
        needle = f"%{str(query).strip()}%"
        if needle != "%%":
            q = q.filter(or_(models.Usuario.nome.ilike(needle), models.Usuario.email.ilike(needle)))
    limit = max(1, min(int(limit or 20), 50))
    return q.order_by(models.Usuario.nome.asc()).limit(limit).all()


def ia_listar_veiculos(db: Session, query: str | None = None, limit: int = 20):
    q = db.query(models.Veiculo)
    if query:
        needle = f"%{str(query).strip()}%"
        if needle != "%%":
            q = q.filter(
                or_(
                    models.Veiculo.placa.ilike(needle),
                    models.Veiculo.modelo.ilike(needle),
                    models.Veiculo.marca.ilike(needle),
                )
            )
    limit = max(1, min(int(limit or 20), 50))
    return q.order_by(models.Veiculo.placa.asc()).limit(limit).all()


def ia_listar_viagens_query(
    db: Session,
    *,
    status: str | None = None,
    periodo_inicio=None,
    periodo_fim=None,
    responsavel_id: int | None = None,
):
    q = db.query(models.Viagem)
    if status:
        q = q.filter(models.Viagem.status == str(status))
    if responsavel_id is not None:
        q = q.filter(models.Viagem.responsavel_id == responsavel_id)
    if periodo_inicio is not None:
        q = q.filter(models.Viagem.data_hora_prevista_saida >= periodo_inicio)
    if periodo_fim is not None:
        q = q.filter(models.Viagem.data_hora_prevista_saida <= periodo_fim)
    return q


def ia_listar_despesas_query(
    db: Session,
    *,
    viagem_id: int,
    categoria: str | None = None,
    periodo_inicio=None,
    periodo_fim=None,
):
    q = db.query(models.Despesa).filter(models.Despesa.viagem_id == viagem_id)
    if categoria:
        q = q.filter(models.Despesa.descricao == str(categoria))
    if periodo_inicio is not None:
        q = q.filter(models.Despesa.data_registro >= periodo_inicio)
    if periodo_fim is not None:
        q = q.filter(models.Despesa.data_registro <= periodo_fim)
    return q


def ia_total_despesas_viagem(db: Session, viagem_id: int) -> float:
    total = db.query(func.coalesce(func.sum(models.Despesa.valor), 0.0)).filter(models.Despesa.viagem_id == viagem_id).scalar()
    return float(total or 0.0)


def ia_ranking_categorias(
    db: Session,
    *,
    viagem_ids: list[int] | None = None,
    periodo_inicio=None,
    periodo_fim=None,
    limit: int = 10,
):
    q = db.query(
        models.Despesa.descricao.label("categoria"),
        func.coalesce(func.sum(models.Despesa.valor), 0.0).label("total"),
    )
    if viagem_ids is not None:
        if not viagem_ids:
            return []
        q = q.filter(models.Despesa.viagem_id.in_(viagem_ids))
    if periodo_inicio is not None:
        q = q.filter(models.Despesa.data_registro >= periodo_inicio)
    if periodo_fim is not None:
        q = q.filter(models.Despesa.data_registro <= periodo_fim)
    limit = max(1, min(int(limit or 10), 20))
    return (
        q.group_by(models.Despesa.descricao)
        .order_by(func.sum(models.Despesa.valor).desc())
        .limit(limit)
        .all()
    )


def ia_get_transporte_kms(db: Session, viagem_id: int):
    viagem = get_viagem(db, viagem_id)
    if not viagem or not viagem.transporte:
        return None, None
    return viagem.transporte.km_saida, viagem.transporte.km_chegada


def ia_listar_atividades_usuario(
    db: Session,
    *,
    usuario_id: int,
    periodo_inicio=None,
    periodo_fim=None,
    limit: int = 5000,
):
    q = db.query(models.Atividade).filter(models.Atividade.usuario_id == usuario_id)
    if periodo_inicio is not None:
        q = q.filter(models.Atividade.inicio >= periodo_inicio)
    if periodo_fim is not None:
        q = q.filter(models.Atividade.inicio <= periodo_fim)
    limit = max(1, min(int(limit or 5000), 5000))
    return q.order_by(models.Atividade.inicio.desc()).limit(limit).all()
