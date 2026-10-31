import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration


def test_regulation_endpoint_against_real_boletin_oficial() -> None:
    client = TestClient(app)

    response = client.get("/guidance/regulations/ley/6101/2018")

    assert response.status_code == 200
    body = response.json()
    assert body["source"]["url"] == "https://boletinoficial.buenosaires.gob.ar"
    [regulation] = body["regulations"]
    assert regulation["type"] == "ley"
    assert regulation["publication_date"] == "2018-12-27"
    assert regulation["document_url"].startswith("https://")


def test_unknown_regulation_endpoint_against_real_boletin_oficial_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/guidance/regulations/ley/6101/2019")

    assert response.status_code == 404
