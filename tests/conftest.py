import os
from pathlib import Path

import pytest

DB_PATH = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"


def _import_engine():
    for mod in ("app.db.session", "app.db.database", "app.db.core", "app.db"):
        try:
            m = __import__(mod, fromlist=["engine"])
            if hasattr(m, "engine"):
                return m.engine
        except Exception:
            pass
    raise ImportError("Could not find SQLAlchemy 'engine' in app.db.*")


@pytest.fixture(scope="session", autouse=True)
def _init_db_for_tests():
    if DB_PATH.exists():
        DB_PATH.unlink()

    engine = _import_engine()

    from app.models import Base
    Base.metadata.create_all(bind=engine)

    yield

    if DB_PATH.exists():
        DB_PATH.unlink()

