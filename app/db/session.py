from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

DATABASE_URL = settings.database_url  # tests set env DATABASE_URL before importing

_connect_args: dict = {}
try:
    if make_url(DATABASE_URL).get_backend_name() == "sqlite":
        _connect_args = {"check_same_thread": False}
except Exception:
    pass

engine = create_engine(DATABASE_URL, future=True, connect_args=_connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
