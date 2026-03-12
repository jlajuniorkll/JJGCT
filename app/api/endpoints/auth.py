from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/login", response_model=schemas.Usuario)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_usuario_by_email(db, email=payload.email)
    if not user or user.senha != payload.senha:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return user

