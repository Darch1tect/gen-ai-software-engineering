from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures"

CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "xml": "application/xml",
}


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def file_client(tmp_path):
    """Client backed by a file-based SQLite DB with a real connection pool.

    The default `client` fixture shares a single in-memory connection
    (StaticPool), which cannot serve truly concurrent requests. This one
    gives every request its own connection, so it is safe for
    multi-threaded tests.
    """
    engine = create_engine(
        f"sqlite:///{tmp_path / 'concurrent.db'}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def upload(client):
    """Upload raw content to POST /tickets/import as a multipart file."""

    def _upload(filename, content, content_type=None, **params):
        if content_type is None:
            content_type = CONTENT_TYPES.get(filename.rsplit(".", 1)[-1], "text/plain")
        return client.post(
            "/tickets/import",
            params=params,
            files={"file": (filename, content, content_type)},
        )

    return _upload


@pytest.fixture()
def upload_fixture(upload):
    """Upload one of the files in tests/fixtures/ by name."""

    def _upload_fixture(name, **params):
        return upload(name, (FIXTURES_DIR / name).read_bytes(), **params)

    return _upload_fixture


@pytest.fixture()
def ticket_payload():
    return {
        "customer_id": "CUST-001",
        "customer_email": "jane.doe@example.com",
        "customer_name": "Jane Doe",
        "subject": "Cannot log into my account",
        "description": "I keep getting an 'invalid password' error even after resetting it.",
        "category": "account_access",
        "priority": "high",
        "tags": ["login", "password"],
        "metadata": {"source": "web_form", "browser": "Chrome 126", "device_type": "desktop"},
    }
