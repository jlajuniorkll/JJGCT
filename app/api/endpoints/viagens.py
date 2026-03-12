from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

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

@router.post("/", response_model=schemas.Viagem)
def create_viagem(viagem: schemas.ViagemCreate, db: Session = Depends(get_db)):
    if not viagem.participantes_ids:
        raise HTTPException(status_code=400, detail="A viagem deve ter pelo menos um participante.")
    if viagem.meio_transporte in ["carro empresa", "carro próprio"]:
        if not viagem.transporte:
            raise HTTPException(status_code=400, detail="Informações de transporte são obrigatórias para este meio de transporte.")
        if not all([viagem.transporte.veiculo_id, viagem.transporte.motorista_id, viagem.transporte.km_saida]):
            raise HTTPException(status_code=400, detail="Veículo, motorista e km de saída são obrigatórios para este meio de transporte.")
    try:
        return crud.create_viagem(db=db, viagem=viagem)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.Viagem])
def read_viagens(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    viagens = crud.get_viagens(db, skip=skip, limit=limit)
    return viagens

@router.get("/{viagem_id}", response_model=schemas.Viagem)
def read_viagem(viagem_id: int, db: Session = Depends(get_db)):
    db_viagem = crud.get_viagem(db, viagem_id=viagem_id)
    if db_viagem is None:
        raise HTTPException(status_code=404, detail="Viagem not found")
    return db_viagem

@router.post("/{viagem_id}/cancelar", response_model=schemas.Viagem)
def cancelar_viagem(viagem_id: int, db: Session = Depends(get_db)):
    try:
        db_viagem = crud.cancelar_viagem(db, viagem_id=viagem_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db_viagem is None:
        raise HTTPException(status_code=404, detail="Viagem not found")
    return db_viagem


@router.post("/{viagem_id}/registrar-saida", response_model=schemas.Viagem)
def registrar_saida(viagem_id: int, db: Session = Depends(get_db)):
    db_viagem = crud.get_viagem(db, viagem_id=viagem_id)
    if db_viagem is None:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if db_viagem.status == "cancelada":
        raise HTTPException(status_code=400, detail="Viagem cancelada")
    if db_viagem.status != "planejada":
        raise HTTPException(status_code=400, detail="A saída só pode ser registrada para viagens planejadas")

    return crud.registrar_saida_real(db, viagem_id=viagem_id)

@router.post("/{viagem_id}/registrar-chegada", response_model=schemas.Viagem)
def registrar_chegada(viagem_id: int, km_chegada: float = None, db: Session = Depends(get_db)):
    db_viagem = crud.get_viagem(db, viagem_id=viagem_id)
    if db_viagem is None:
        raise HTTPException(status_code=404, detail="Viagem not found")
    if db_viagem.status == "cancelada":
        raise HTTPException(status_code=400, detail="Viagem cancelada")
    if db_viagem.status != "em_andamento":
        raise HTTPException(status_code=400, detail="A chegada só pode ser registrada para viagens em andamento")

    # Regra: Todas as atividades devem estar encerradas
    for atividade in db_viagem.atividades:
        if atividade.status != "finalizada":
            raise HTTPException(status_code=400, detail=f"A atividade '{atividade.descricao}' ainda não foi finalizada.")

    # Regra: KM final obrigatório se for carro empresa ou próprio
    if db_viagem.meio_transporte in ["carro empresa", "carro próprio"]:
        if km_chegada is None:
            raise HTTPException(status_code=400, detail="KM de chegada é obrigatório para este meio de transporte.")

    return crud.registrar_chegada_real(db, viagem_id=viagem_id, km_chegada=km_chegada)

@router.get("/{viagem_id}/relatorio", response_model=schemas.RelatorioViagem)
def relatorio_viagem(viagem_id: int, db: Session = Depends(get_db)):
    db_viagem = crud.get_viagem(db, viagem_id=viagem_id)
    if db_viagem is None:
        raise HTTPException(status_code=404, detail="Viagem not found")

    db_viagem.participantes
    if db_viagem.transporte:
        db_viagem.transporte.veiculo
        db_viagem.transporte.motorista

    distancia_percorrida = 0
    if db_viagem.transporte and db_viagem.transporte.km_chegada and db_viagem.transporte.km_saida:
        distancia_percorrida = db_viagem.transporte.km_chegada - db_viagem.transporte.km_saida

    total_horas_trabalhadas = timedelta(0)
    for atividade in db_viagem.atividades:
        if atividade.inicio and atividade.fim:
            total_horas_trabalhadas += atividade.fim - atividade.inicio
            for pausa in atividade.pausas:
                if pausa.inicio and pausa.fim:
                    total_horas_trabalhadas -= pausa.fim - pausa.inicio

    total_despesas = sum([d.valor for d in db_viagem.despesas])

    return {
        "viagem": db_viagem,
        "distancia_percorrida_km": distancia_percorrida,
        "total_horas_trabalhadas": str(total_horas_trabalhadas),
        "total_despesas": total_despesas
    }
