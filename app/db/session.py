"""Database engine and session management."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

if os.getenv("VERCEL"):
    DB_PATH = Path(os.getenv("DB_DIR", "/tmp")) / "fraud_pipeline.db"
else:
    DB_PATH = Path(os.getenv("DB_DIR", Path(__file__).parent.parent.parent)) / "fraud_pipeline.db"
DEFAULT_DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# SQLite concurrency configuration
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
