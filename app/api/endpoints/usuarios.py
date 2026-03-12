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

@router.post("/", response_model=schemas.Usuario)
def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario_by_email(db, email=usuario.email)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_usuario(db=db, usuario=usuario)

@router.get("/", response_model=List[schemas.Usuario])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    usuarios = crud.get_usuarios(db, skip=skip, limit=limit)
    return usuarios

@router.get("/{usuario_id}", response_model=schemas.Usuario)
def read_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario


@router.put("/{usuario_id}", response_model=schemas.Usuario)
def update_usuario(usuario_id: int, usuario: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    try:
        db_usuario = crud.update_usuario(db, usuario_id=usuario_id, usuario=usuario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario


@router.delete("/{usuario_id}", response_model=schemas.Usuario)
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    try:
        db_usuario = crud.delete_usuario(db, usuario_id=usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario not found")
    return db_usuario
