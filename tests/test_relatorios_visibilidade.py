from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.ia import relatorios


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_relatorio_despesas_por_viagem_respeita_visibilidade_colaborador():
    db = _make_session()
    admin = models.Usuario(nome="Admin", email="a@x.com", senha="x", tipousuario="admin")
    u1 = models.Usuario(nome="U1", email="u1@x.com", senha="x", tipousuario="colaborador")
    u2 = models.Usuario(nome="U2", email="u2@x.com", senha="x", tipousuario="colaborador")
    db.add_all([admin, u1, u2])
    db.commit()
    db.refresh(u1)
    db.refresh(u2)
    db.refresh(admin)

    v1 = models.Viagem(motivo="V1", data_hora_prevista_saida=None, data_hora_prevista_retorno=None, meio_transporte="carro", status="em_andamento", participantes=[u1], responsavel_id=u1.id)
    v2 = models.Viagem(motivo="V2", data_hora_prevista_saida=None, data_hora_prevista_retorno=None, meio_transporte="carro", status="em_andamento", participantes=[u2], responsavel_id=u2.id)
    db.add_all([v1, v2])
    db.commit()
    db.refresh(v1)
    db.refresh(v2)

    db.add_all(
        [
            models.Despesa(viagem_id=v1.id, valor=100.0, forma_pagamento="PIX", descricao="Combustível"),
            models.Despesa(viagem_id=v2.id, valor=200.0, forma_pagamento="PIX", descricao="Hospedagem"),
        ]
    )
    db.commit()

    r_colab = relatorios.despesas_por_viagem(db, {}, u1)
    assert isinstance(r_colab, dict)
    labels = [d.get("label") for d in (r_colab.get("dados") or [])]
    assert any(f"Viagem #{v1.id}" in str(x) for x in labels)
    assert not any(f"Viagem #{v2.id}" in str(x) for x in labels)

    r_admin = relatorios.despesas_por_viagem(db, {}, admin)
    labels_admin = [d.get("label") for d in (r_admin.get("dados") or [])]
    assert any(f"Viagem #{v1.id}" in str(x) for x in labels_admin)
    assert any(f"Viagem #{v2.id}" in str(x) for x in labels_admin)
