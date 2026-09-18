import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

_BASE_DIR = Path(__file__).resolve().parents[2]
_DB_PATH = _BASE_DIR / "data" / "product.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models
    Base.metadata.create_all(bind=engine)
