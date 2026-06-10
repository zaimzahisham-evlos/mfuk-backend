import pytest
from app.storage import dependencies
from tests.fakes.storage import FakeStorageClient

@pytest.fixture
def fake_storage(monkeypatch):
    """
    Replace get_storage_client for this test module.

    lru_cache must be cleared so each test gets a fresh fake
    and does not reuse a real boto3 client from a previous test.
    """
    real_client = dependencies.get_storage_client
    real_client.cache_clear()

    client = FakeStorageClient()

    def _fake_client():
        return client

    monkeypatch.setattr(dependencies, "get_storage_client", _fake_client)
    monkeypatch.setattr("app.production.services.get_storage_client", _fake_client)
    monkeypatch.setattr("app.core.routes.get_storage_client", _fake_client)
    yield client

    real_client.cache_clear()