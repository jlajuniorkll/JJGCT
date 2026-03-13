from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import timezone

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

@router.post("/", response_model=schemas.Atividade)
def create_atividade_for_viagem(viagem_id: int, atividade: schemas.AtividadeCreate, db: Session = Depends(get_db)):
    return _normalize_atividade(crud.create_atividade(db=db, atividade=atividade, viagem_id=viagem_id))

@router.post("/{atividade_id}/iniciar", response_model=schemas.Atividade)
def iniciar_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = crud.iniciar_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    return _normalize_atividade(db_atividade)

@router.post("/{atividade_id}/finalizar", response_model=schemas.Atividade)
def finalizar_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = crud.finalizar_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    return _normalize_atividade(db_atividade)

@router.post("/{atividade_id}/pausar", response_model=schemas.Pausa)
def pausar_atividade(atividade_id: int, pausa: schemas.PausaCreate, db: Session = Depends(get_db)):
    return _normalize_pausa(crud.create_pausa(db=db, pausa=pausa, atividade_id=atividade_id))

@router.post("/pausas/{pausa_id}/finalizar", response_model=schemas.Pausa)
def finalizar_pausa(pausa_id: int, db: Session = Depends(get_db)):
    db_pausa = crud.finalizar_pausa(db, pausa_id=pausa_id)
    if db_pausa is None:
        raise HTTPException(status_code=404, detail="Pausa not found")
    return _normalize_pausa(db_pausa)
