import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_database_url

DATABASE_URL = get_database_url()

# Extract db path for directory creation and ensure it's absolute
if "sqlite" in DATABASE_URL:
    _db_path = DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(_db_path):
        _db_path = os.path.join(os.getenv("PROJECT_ROOT", str(Path(__file__).resolve().parents[1])), _db_path)
    Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

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
