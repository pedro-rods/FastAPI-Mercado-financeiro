# app/db.py
import os
import pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# --------- Flags de modo ---------
APP_MODE = os.getenv("APP_MODE", "").lower()
IS_DEV = APP_MODE == "dev"

# --------- URLs de banco ---------
# Produção/normal: usa DATABASE_URL (Postgres etc.)
DATABASE_URL = os.getenv("DATABASE_URL")

if IS_DEV:
    dev_path = os.getenv("DEV_DB_PATH", "./dev.db")
    dev_path = str(pathlib.Path(dev_path).resolve())
    DATABASE_URL = f"sqlite:///{dev_path}"

# --------- Base ORM ---------
class Base(DeclarativeBase):
    pass

# --------- Engine / Session ---------
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # necessário para uso do SQLite com FastAPI (threads)
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------- Utilitário: inicialização DEV ----------
def init_dev_db():
    """
    Se APP_MODE=dev:
      - opcionalmente apaga o arquivo (DEV_DB_RECREATE=1)
      - cria as tabelas via Base.metadata.create_all()
    """
    if not IS_DEV:
        return

    from app import models  # importa modelos para popular o metadata

    # apaga arquivo se pedir recriação
    recreate = os.getenv("DEV_DB_RECREATE", "0") == "1"
    if recreate:
        if DATABASE_URL.startswith("sqlite:///"):
            db_file = DATABASE_URL.replace("sqlite:///", "", 1)
            try:
                pathlib.Path(db_file).unlink(missing_ok=True)
            except Exception:
                pass

    # cria tudo do zero
    Base.metadata.create_all(bind=engine)