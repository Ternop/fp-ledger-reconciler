from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

def get_sqlalchemy_url() -> str:
    return settings.database_url

_engine = None
_SessionLocal = None

def _init():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(get_sqlalchemy_url(), future=True, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

@contextmanager
def db_session() -> Session:
    _init()
    assert _SessionLocal is not None
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
