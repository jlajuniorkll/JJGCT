from . import config_env
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from . import models, crud, schemas
from .database import engine, SessionLocal
from .api.endpoints import usuarios, veiculos, viagens, despesas, atividades, auth, config, ia

models.Base.metadata.create_all(bind=engine)
crud.ensure_app_config_schema(engine)

app = FastAPI(    
    title="Sistema de Viagens",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)
app.mount("/api/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router, prefix="/api/usuarios", tags=["usuarios"])
app.include_router(veiculos.router, prefix="/api/veiculos", tags=["veiculos"])
app.include_router(viagens.router, prefix="/api/viagens", tags=["viagens"])
app.include_router(despesas.router, prefix="/api/despesas", tags=["despesas"])
app.include_router(atividades.router, prefix="/api/atividades", tags=["atividades"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(ia.router, prefix="/api/ia", tags=["ia"])


@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        if not crud.get_usuarios(db, limit=1):
            crud.create_usuario(
                db=db,
                usuario=schemas.UsuarioCreate(
                    nome="Administrador",
                    email="admin@empresa.com",
                    senha="admin123",
                    tipousuario="admin",
                    tem_cnh=False,
                ),
            )
        crud.get_app_config(db)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API de Viagens Corporativas!"}
