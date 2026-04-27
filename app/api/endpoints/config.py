import json

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ... import crud, schemas
from ...database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _require_admin(db: Session, x_user_id: int | None):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = crud.get_usuario(db, usuario_id=x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    if user.tipousuario != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user


def _to_schema(cfg) -> schemas.AppConfig:
    try:
        statuses = json.loads(cfg.trip_edit_blocked_statuses or "[]")
        if not isinstance(statuses, list):
            statuses = []
    except json.JSONDecodeError:
        statuses = []
    try:
        expense_desc = json.loads(getattr(cfg, "expense_description_options", None) or "[]")
        if not isinstance(expense_desc, list):
            expense_desc = []
    except json.JSONDecodeError:
        expense_desc = []
    try:
        act_statuses = json.loads(getattr(cfg, "activity_edit_delete_allowed_statuses", None) or "[]")
        if not isinstance(act_statuses, list):
            act_statuses = []
    except json.JSONDecodeError:
        act_statuses = []
    try:
        mutation_statuses = json.loads(cfg.trip_activity_expense_allowed_statuses or "[]")
        if not isinstance(mutation_statuses, list):
            mutation_statuses = []
    except json.JSONDecodeError:
        mutation_statuses = []
    return schemas.AppConfig(
        expense_photo_required=bool(cfg.expense_photo_required),
        expense_description_options=[str(s) for s in expense_desc],
        activity_edit_delete_allowed_statuses=[str(s) for s in act_statuses],
        trip_edit_blocked_statuses=[str(s) for s in statuses],
        trip_activity_expense_allowed_statuses=[str(s) for s in mutation_statuses],
        trips_show_all_admin=bool(getattr(cfg, "trips_show_all_admin", True)),
        trips_show_all_colaborador=bool(getattr(cfg, "trips_show_all_colaborador", True)),
    )


@router.get("/", response_model=schemas.AppConfig)
def read_config(x_user_id: int | None = Header(default=None), db: Session = Depends(get_db)):
    cfg = crud.get_app_config(db)
    return _to_schema(cfg)


@router.put("/", response_model=schemas.AppConfig)
def update_config(
    payload: schemas.AppConfigUpdate,
    x_user_id: int | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(db, x_user_id)
    cfg = crud.update_app_config(db, payload)
    return _to_schema(cfg)
