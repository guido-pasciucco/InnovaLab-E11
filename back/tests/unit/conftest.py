import pytest

from conco.integrations.caba_tramites import client as caba_client


@pytest.fixture(autouse=True)
def no_retry_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Los reintentos a la API de la Ciudad no esperan en los tests unitarios."""
    monkeypatch.setattr(caba_client, "RETRY_BACKOFF_SECONDS", 0)
