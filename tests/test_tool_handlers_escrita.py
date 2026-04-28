from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud, models
from app.ia.tool_handlers_escrita import dispatch_tool_escrita


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_criar_despesa_retorna_campos_faltando():
    db = _make_session()
    user = models.Usuario(nome="U", email="u@x.com", senha="x", tipousuario="colaborador")
    db.add(user)
    db.commit()
    db.refresh(user)

    out = dispatch_tool_escrita(db, user, "criar_despesa", {"viagem_id": 1})
    assert isinstance(out, dict)
    assert "erro" in out
    assert "campos faltando" in str(out["erro"])


def test_criar_despesa_cria_proposta_quando_valida():
    db = _make_session()
    cfg = crud.get_app_config(db)
    cfg.trip_activity_expense_allowed_statuses = '["em_andamento"]'
    cfg.expense_description_options = '["Combustível"]'
    db.commit()

    user = models.Usuario(nome="U", email="u@x.com", senha="x", tipousuario="colaborador")
    db.add(user)
    db.commit()
    db.refresh(user)

    viagem = models.Viagem(
        motivo="Teste",
        data_hora_prevista_saida=None,
        data_hora_prevista_retorno=None,
        meio_transporte="carro",
        status="em_andamento",
        participantes=[user],
        responsavel_id=user.id,
    )
    db.add(viagem)
    db.commit()
    db.refresh(viagem)

    out = dispatch_tool_escrita(
        db,
        user,
        "criar_despesa",
        {
            "viagem_id": viagem.id,
            "valor": 10.5,
            "descricao": "Combustível",
            "forma_pagamento": "PIX",
            "tipo_pagamento": "INDIVIDUAL",
        },
    )
    assert isinstance(out, dict)
    assert isinstance(out.get("id_proposta"), str)
    assert out.get("ferramenta") == "criar_despesa"
