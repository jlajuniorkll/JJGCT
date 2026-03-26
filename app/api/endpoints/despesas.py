from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from uuid import uuid4
import shutil

from ... import crud, models, schemas
from ...database import SessionLocal

router = APIRouter()

UPLOADS_DIR = Path("uploads")


def _save_upload(file: UploadFile) -> str:
    UPLOADS_DIR.mkdir(exist_ok=True)

    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if not suffix:
        suffix = ".bin"

    filename = f"{uuid4().hex}{suffix}"
    path = UPLOADS_DIR / filename

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return f"uploads/{filename}"


def _safe_remove_upload(stored_path: str) -> None:
    if not stored_path:
        return

    normalized = str(stored_path).replace("\\", "/")
    if not normalized.startswith("uploads/"):
        return

    base = (Path.cwd() / "uploads").resolve()
    candidate = (Path.cwd() / normalized).resolve()

    if base in candidate.parents and candidate.is_file():
        try:
            candidate.unlink()
        except OSError:
            pass


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.Despesa)
def create_despesa_for_viagem(
    viagem_id: int,
    valor: float,
    forma_pagamento: str,
    descricao: str,
    file: UploadFile = File(None),
    pago_por_id: int = None,
    tipo_pagamento: str = None,
    registrado_para_id: int = None,
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db)
):
    db_viagem = crud.get_viagem(db, viagem_id)
    if not db_viagem:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if db_viagem.status != "em_andamento":
        raise HTTPException(status_code=400, detail="Despesas só podem ser lançadas em viagens em andamento")
    if x_user_id and x_user_id not in [u.id for u in db_viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem registrar despesas")

    cfg = crud.get_app_config(db)
    if cfg.expense_photo_required and file is None:
        raise HTTPException(status_code=400, detail="Comprovante é obrigatório")

    file_path = _save_upload(file) if file is not None else ""
    if pago_por_id is None and x_user_id:
        pago_por_id = x_user_id
    if registrado_para_id is None and x_user_id:
        registrado_para_id = x_user_id
    despesa = schemas.DespesaCreate(
        valor=valor,
        forma_pagamento=forma_pagamento,
        descricao=descricao,
        pago_por_id=pago_por_id,
        tipo_pagamento=tipo_pagamento or "INDIVIDUAL",
        registrado_para_id=registrado_para_id,
    )
    return crud.create_despesa(db=db, despesa=despesa, viagem_id=viagem_id, comprovante_url=file_path)


@router.get("/{despesa_id}", response_model=schemas.Despesa)
def read_despesa(despesa_id: int, db: Session = Depends(get_db)):
    db_despesa = crud.get_despesa(db, despesa_id)
    if db_despesa is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    return db_despesa


@router.put("/{despesa_id}", response_model=schemas.Despesa)
def update_despesa(
    despesa_id: int,
    valor: float,
    forma_pagamento: str,
    descricao: str,
    file: UploadFile = File(None),
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_despesa = crud.get_despesa(db, despesa_id)
    if db_despesa is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    if db_despesa.viagem and db_despesa.viagem.status in ["finalizada", "cancelada"]:
        raise HTTPException(status_code=400, detail="Não é permitido alterar despesas de uma viagem finalizada/cancelada")
    if x_user_id and x_user_id not in [u.id for u in db_despesa.viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem editar despesas")

    cfg = crud.get_app_config(db)
    if cfg.expense_photo_required and file is None and not db_despesa.comprovante_url:
        raise HTTPException(status_code=400, detail="Comprovante é obrigatório")

    old_path = db_despesa.comprovante_url
    new_path = old_path

    created_path = None
    if file is not None:
        created_path = _save_upload(file)
        new_path = created_path

    try:
        updated = crud.update_despesa(
            db,
            despesa_id,
            schemas.DespesaUpdate(
                valor=valor,
                forma_pagamento=forma_pagamento,
                descricao=descricao,
                comprovante_url=new_path,
            ),
        )
    except Exception:
        if created_path:
            _safe_remove_upload(created_path)
        raise

    if updated is None:
        if created_path:
            _safe_remove_upload(created_path)
        raise HTTPException(status_code=404, detail="Despesa not found")

    if created_path and old_path and old_path != created_path:
        _safe_remove_upload(old_path)

    return updated


@router.delete("/{despesa_id}", response_model=schemas.Despesa)
def delete_despesa(despesa_id: int, x_user_id: int = Header(default=None), db: Session = Depends(get_db)):
    db_despesa = crud.get_despesa(db, despesa_id)
    if db_despesa is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    if db_despesa.viagem and db_despesa.viagem.status in ["finalizada", "cancelada"]:
        raise HTTPException(status_code=400, detail="Não é permitido excluir despesas de uma viagem finalizada/cancelada")
    if x_user_id and x_user_id not in [u.id for u in db_despesa.viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem excluir despesas")

    old_path = db_despesa.comprovante_url
    deleted = crud.delete_despesa(db, despesa_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Despesa not found")

    _safe_remove_upload(old_path)
    return deleted


@router.get("/{despesa_id}/rateio", response_model=List[schemas.DespesaRateio])
def read_despesa_rateio(despesa_id: int, x_user_id: int = Header(default=None), db: Session = Depends(get_db)):
    db_despesa = crud.get_despesa(db, despesa_id)
    if db_despesa is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    if x_user_id and x_user_id not in [u.id for u in db_despesa.viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem acessar rateio")
    return crud.get_despesa_rateios(db, despesa_id)


@router.put("/{despesa_id}/rateio", response_model=List[schemas.DespesaRateio])
def replace_despesa_rateio(
    despesa_id: int,
    payload: List[schemas.DespesaRateioBase],
    x_user_id: int = Header(default=None),
    db: Session = Depends(get_db),
):
    db_despesa = crud.get_despesa(db, despesa_id)
    if db_despesa is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    if x_user_id and x_user_id not in [u.id for u in db_despesa.viagem.participantes]:
        raise HTTPException(status_code=403, detail="Apenas participantes podem editar rateio")

    try:
        result = crud.replace_despesa_rateios(db, despesa_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if result is None:
        raise HTTPException(status_code=404, detail="Despesa not found")
    return result
