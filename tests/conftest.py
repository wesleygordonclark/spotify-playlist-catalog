# tests/conftest.py
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.api.deps import get_db

TEST_DB_PATH = Path("test_db.sqlite3")
TEST_DATABASE_URL = f"sqlite+pysqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def test_engine():
    # Remove any existing test DB file
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    # Create all tables once for the test DB
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        engine.dispose()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def TestingSessionLocal(test_engine):
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )


@pytest.fixture(scope="function")
def db_session(TestingSessionLocal) -> Generator:
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_engine, db_session, monkeypatch):
    """
    FastAPI TestClient with DB dependency and engine overridden
    to use the file-based SQLite test database.
    """
    from app import main as app_main
    from app.db import session as db_session_module

    # Make app and db.session use the SQLite test engine
    monkeypatch.setattr(db_session_module, "engine", test_engine)
    monkeypatch.setattr(app_main, "engine", test_engine)

    # Override get_db to use the test session
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app_main.app.dependency_overrides[get_db] = _get_test_db

    with TestClient(app_main.app) as c:
        yield c

    app_main.app.dependency_overrides.clear()



