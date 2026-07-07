import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


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
