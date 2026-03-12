import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/viagens",
)

if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1,
    )

engine_kwargs = {"pool_pre_ping": True}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["connect_args"] = {"connect_timeout": 5}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
