from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud, models
from app.api.endpoints.ia import logs_ia_admin, metricas_ia_admin
from app.ia.audit import estimar_custo_usd, registrar_ia_log


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def test_estimativa_custo_anthropic():
    cost = estimar_custo_usd("anthropic", 1_000_000, 1_000_000, 1_000_000)
    assert cost is not None
    assert abs(cost - 18.3) < 1e-6


def test_admin_endpoints_bloqueiam_nao_admin():
    db = _make_session()
    u = models.Usuario(nome="U", email="u@x.com", senha="x", tipousuario="colaborador")
    db.add(u)
    db.commit()
    db.refresh(u)

    try:
        metricas_ia_admin(x_user_id=u.id, db=db)
        assert False
    except HTTPException as e:
        assert e.status_code == 403

    try:
        logs_ia_admin(x_user_id=u.id, db=db)
        assert False
    except HTTPException as e:
        assert e.status_code == 403


def test_admin_endpoints_retornam_metricas_e_logs():
    db = _make_session()
    admin = models.Usuario(nome="Admin", email="a@x.com", senha="x", tipousuario="admin")
    db.add(admin)
    db.commit()
    db.refresh(admin)

    crud.get_app_config(db)

    registrar_ia_log(
        db,
        usuario_id=admin.id,
        tipo="chat",
        mensagem_usuario="Oi",
        ferramentas_chamadas=[{"nome": "listar_viagens", "args": {}, "resultado_resumo": "ok"}],
        tokens_input=10,
        tokens_output=20,
        tokens_cache_read=0,
        latencia_ms=123,
        sucesso=True,
        erro=None,
        provider="anthropic",
    )

    m = metricas_ia_admin(x_user_id=admin.id, db=db)
    assert isinstance(m, dict)
    assert m["total_chamadas"] == 1
    assert m["total_tokens"] == 30
    assert isinstance(m["custo_total_usd"], float)

    l = logs_ia_admin(x_user_id=admin.id, db=db, limit=50, offset=0)
    assert isinstance(l, dict)
    assert l["total"] == 1
    assert len(l["items"]) == 1
    assert l["items"][0]["mensagem_resumo"] == "Oi"
