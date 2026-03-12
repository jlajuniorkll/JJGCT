from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ... import crud, models, schemas
from ...database import SessionLocal

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Atividade)
def create_atividade_for_viagem(viagem_id: int, atividade: schemas.AtividadeCreate, db: Session = Depends(get_db)):
    return crud.create_atividade(db=db, atividade=atividade, viagem_id=viagem_id)

@router.post("/{atividade_id}/iniciar", response_model=schemas.Atividade)
def iniciar_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = crud.iniciar_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    return db_atividade

@router.post("/{atividade_id}/finalizar", response_model=schemas.Atividade)
def finalizar_atividade(atividade_id: int, db: Session = Depends(get_db)):
    db_atividade = crud.finalizar_atividade(db, atividade_id=atividade_id)
    if db_atividade is None:
        raise HTTPException(status_code=404, detail="Atividade not found")
    return db_atividade

@router.post("/{atividade_id}/pausar", response_model=schemas.Pausa)
def pausar_atividade(atividade_id: int, pausa: schemas.PausaCreate, db: Session = Depends(get_db)):
    return crud.create_pausa(db=db, pausa=pausa, atividade_id=atividade_id)

@router.post("/pausas/{pausa_id}/finalizar", response_model=schemas.Pausa)
def finalizar_pausa(pausa_id: int, db: Session = Depends(get_db)):
    db_pausa = crud.finalizar_pausa(db, pausa_id=pausa_id)
    if db_pausa is None:
        raise HTTPException(status_code=404, detail="Pausa not found")
    return db_pausa
