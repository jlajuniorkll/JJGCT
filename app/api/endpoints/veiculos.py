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

@router.post("/", response_model=schemas.Veiculo)
def create_veiculo(veiculo: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    db_veiculo = crud.get_veiculo_by_placa(db, placa=veiculo.placa)
    if db_veiculo:
        raise HTTPException(status_code=400, detail="Placa already registered")
    return crud.create_veiculo(db=db, veiculo=veiculo)

@router.get("/", response_model=List[schemas.Veiculo])
def read_veiculos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    veiculos = crud.get_veiculos(db, skip=skip, limit=limit)
    return veiculos

@router.get("/{veiculo_id}", response_model=schemas.Veiculo)
def read_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    db_veiculo = crud.get_veiculo(db, veiculo_id=veiculo_id)
    if db_veiculo is None:
        raise HTTPException(status_code=404, detail="Veiculo not found")
    return db_veiculo


@router.put("/{veiculo_id}", response_model=schemas.Veiculo)
def update_veiculo(veiculo_id: int, veiculo: schemas.VeiculoUpdate, db: Session = Depends(get_db)):
    try:
        db_veiculo = crud.update_veiculo(db, veiculo_id=veiculo_id, veiculo=veiculo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db_veiculo is None:
        raise HTTPException(status_code=404, detail="Veiculo not found")
    return db_veiculo


@router.delete("/{veiculo_id}", response_model=schemas.Veiculo)
def delete_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    try:
        db_veiculo = crud.delete_veiculo(db, veiculo_id=veiculo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db_veiculo is None:
        raise HTTPException(status_code=404, detail="Veiculo not found")
    return db_veiculo
