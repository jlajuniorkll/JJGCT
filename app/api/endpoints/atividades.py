from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from datetime import timezone
import json

from ... import crud, models, schemas
from ...database import SessionLocal

router = APIRouter()


def _ensure_utc(dt):
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_atividade(db_atividade):
    if db_atividade is None:
        return None

    db_atividade.inicio = _ensure_utc(getattr(db_atividade, "inicio", None))
    db_atividade.fim = _ensure_utc(getattr(db_atividade, "fim", None))
    for pausa in getattr(db_atividade, "pausas", []) or []:
        pausa.inicio = _ensure_utc(getattr(pausa, "inicio", None))
        pausa.fim = _ensure_utc(getattr(pausa, "fim", None))

    return db_atividade


def _normalize_pausa(db_pausa):
    if db_pausa is None:
        return None

    db_pausa.inicio = _ensure_utc(getattr(db_pausa, "inicio", None))
    db_pausa.fim = _ensure_utc(getattr(db_pausa, "fim", None))
    return db_pausa

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _parse_json_list(value: str | None):
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []

@router.post("/", response_model=schemas.Atividade)
def create_atividade_for_viagem(
    viagem_id: int,
    atividade: schemas.AtividadeCreate,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem registrar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    return _normalize_atividade(crud.create_atividade(db=db, atividade=atividade, viagem_id=viagem_id))


@router.post("/reordenar", response_model=List[schemas.Atividade])
def reordenar_atividades(
    viagem_id: int,
    payload: schemas.AtividadeReorder,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    atividades = crud.reorder_atividades(db=db, viagem_id=viagem_id, atividade_ids=payload.atividade_ids)
    return [_normalize_atividade(a) for a in atividades]

@router.put("/{atividade_id}", response_model=schemas.Atividade)
def atualizar_atividade(
    atividade_id: int,
    payload: schemas.AtividadeUpdate,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_atividade = crud.get_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_trip_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_trip_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    allowed_activity_statuses = _parse_json_list(getattr(cfg, "activity_edit_delete_allowed_statuses", None))
    if db_atividade.status not in allowed_activity_statuses:
        raise HTTPException(status_code=400, detail="Edição/Exclusão não permitida para este status de atividade")
    updated = crud.update_atividade(db, atividade_id=atividade_id, payload=payload)
    return _normalize_atividade(updated)

@router.delete("/{atividade_id}", response_model=schemas.Atividade)
def excluir_atividade(
    atividade_id: int,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_atividade = crud.get_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_trip_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_trip_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    allowed_activity_statuses = _parse_json_list(getattr(cfg, "activity_edit_delete_allowed_statuses", None))
    if db_atividade.status not in allowed_activity_statuses:
        raise HTTPException(status_code=400, detail="Edição/Exclusão não permitida para este status de atividade")
    deleted = crud.delete_atividade(db, atividade_id=atividade_id)
    return _normalize_atividade(deleted)

@router.post("/{atividade_id}/iniciar", response_model=schemas.Atividade)
def iniciar_atividade(atividade_id: int, x_user_id: int = Header(default=None), db: Session = Depends(get_db)):
    db_atividade = crud.get_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    return _normalize_atividade(crud.iniciar_atividade(db, atividade_id=atividade_id))

@router.post("/{atividade_id}/finalizar", response_model=schemas.Atividade)
def finalizar_atividade(atividade_id: int, x_user_id: int = Header(default=None), db: Session = Depends(get_db)):
    db_atividade = crud.get_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    return _normalize_atividade(crud.finalizar_atividade(db, atividade_id=atividade_id))

@router.post("/{atividade_id}/pausar", response_model=schemas.Pausa)
def pausar_atividade(
    atividade_id: int,
    pausa: schemas.PausaCreate,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_atividade = crud.get_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    return _normalize_pausa(crud.create_pausa(db=db, pausa=pausa, atividade_id=atividade_id))

@router.post("/pausas/{pausa_id}/finalizar", response_model=schemas.Pausa)
def finalizar_pausa(pausa_id: int, x_user_id: int = Header(default=None), db: Session = Depends(get_db)):
    db_pausa = db.query(models.Pausa).filter(models.Pausa.id == pausa_id).first()
    if db_pausa is None:
        raise HTTPException(status_code=404, detail="Pausa not found")
    db_atividade = crud.get_atividade(db, atividade_id=db_pausa.atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    db_viagem = crud.get_viagem(db, db_atividade.viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem alterar atividades")
    cfg = crud.get_app_config(db)
    allowed_statuses = _parse_json_list(cfg.trip_activity_expense_allowed_statuses)
    if db_viagem.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Atividades não permitidas para este status de viagem")
    return _normalize_pausa(crud.finalizar_pausa(db, pausa_id=pausa_id))
