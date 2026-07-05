import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.utils.rate_limiter import rate_limiter
from src.utils.storage import store


@pytest.fixture(autouse=True)
def clear_store():
    """Reset in-memory storage and rate-limit counters before every test."""
    store.clear()
    rate_limiter.reset()
    yield
    store.clear()
    rate_limiter.reset()


@pytest.fixture
def client():
    return TestClient(app)
