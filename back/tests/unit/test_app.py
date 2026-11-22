import logging
import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from conco.config import settings
from conco.guidance.api import get_activity_directory
from conco.guidance.domain import ActivityDirectoryError, ActivitySuggestion
from conco.main import app

HEX_ID = re.compile(r"^[0-9a-f]{32}$")


class FakeDirectory:
    """Directorio falso para probar el estado de la app y los errores inesperados."""

    def __init__(self) -> None:
        self.catalog_loaded = True
        self.catalog_error: Exception | None = None
        self.suggest_error: Exception | None = None

    async def suggest(self, query: str, limit: int) -> list[ActivitySuggestion]:
        if self.suggest_error is not None:
            raise self.suggest_error
        return []

    async def procedures_for(self, slug: str) -> None:
        return None

    async def catalog_ready(self) -> bool:
        if self.catalog_error is not None:
            raise self.catalog_error
        return self.catalog_loaded


@pytest.fixture
def directory() -> FakeDirectory:
    return FakeDirectory()


@pytest.fixture
def client(directory: FakeDirectory) -> Iterator[TestClient]:
    app.dependency_overrides[get_activity_directory] = lambda: directory
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_stays_unchanged(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_every_response_carries_a_generated_request_id(client: TestClient) -> None:
    response = client.get("/health")

    assert HEX_ID.match(response.headers["x-request-id"])


def test_valid_incoming_request_id_is_reused(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "qa-run-42"})

    assert response.headers["x-request-id"] == "qa-run-42"


@pytest.mark.parametrize("incoming", ["no valido!", "x" * 65, ""])
def test_invalid_incoming_request_id_is_replaced(client: TestClient, incoming: str) -> None:
    response = client.get("/health", headers={"X-Request-ID": incoming})

    assert HEX_ID.match(response.headers["x-request-id"])


def test_request_is_logged_with_its_request_id(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="conco.request_id"):
        client.get("/health", headers={"X-Request-ID": "trace-1"})

    [record] = [r for r in caplog.records if r.name == "conco.request_id"]
    message = record.getMessage()
    assert record.levelno == logging.INFO
    assert "GET /health" in message
    assert "200" in message
    assert "ms" in message
    assert "trace-1" in message


def test_cors_exposes_the_request_id_header(client: TestClient) -> None:
    origin = settings.cors_origins[0]

    response = client.get("/health", headers={"Origin": origin})

    assert response.headers["access-control-allow-origin"] == origin
    assert "X-Request-ID" in response.headers["access-control-expose-headers"]
    assert response.headers["x-request-id"]


def test_validation_error_keeps_fastapi_default_shape(client: TestClient) -> None:
    response = client.get("/guidance/activities", params={"query": "a"})

    assert response.status_code == 422
    body = response.json()
    assert list(body) == ["detail"]
    assert isinstance(body["detail"], list)
    assert body["detail"][0]["loc"] == ["query", "query"]
    assert body["detail"][0]["type"] == "string_too_short"
    assert response.headers["x-request-id"]


def test_unexpected_error_returns_generic_500_and_logs_the_traceback(
    directory: FakeDirectory, caplog: pytest.LogCaptureFixture
) -> None:
    directory.suggest_error = RuntimeError("secreto técnico")
    app.dependency_overrides[get_activity_directory] = lambda: directory
    try:
        client = TestClient(app, raise_server_exceptions=False)
        with caplog.at_level(logging.ERROR):
            response = client.get(
                "/guidance/activities",
                params={"query": "barbería"},
                headers={"X-Request-ID": "boom-1"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "request_id": "boom-1",
        "detail": "Ocurrió un error inesperado. Intentá de nuevo más tarde.",
    }
    assert response.headers["x-request-id"] == "boom-1"
    assert "secreto técnico" not in response.text
    [record] = [r for r in caplog.records if r.levelno == logging.ERROR and r.exc_info]
    assert "boom-1" in record.getMessage()
    assert "secreto técnico" in str(record.exc_info[1])


def test_ready_when_database_and_catalog_are_ok(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "catalog": "ok"},
    }


def test_ready_reports_an_empty_catalog(client: TestClient, directory: FakeDirectory) -> None:
    directory.catalog_loaded = False

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "ok", "catalog": "empty"},
    }


def test_ready_reports_a_database_error(client: TestClient, directory: FakeDirectory) -> None:
    directory.catalog_error = ActivityDirectoryError("connection refused")

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "error", "catalog": "error"},
    }
