import pytest
from fastapi.testclient import TestClient

from conco.main import app

pytestmark = pytest.mark.integration

HABILITACION_ID = "338718b4-a2a0-44af-baa4-083f5d834b12"


def test_search_and_detail_endpoints_against_real_api() -> None:
    client = TestClient(app)

    search = client.get(
        "/guidance/procedures", params={"query": "habilitación de actividad económica"}
    )

    assert search.status_code == 200
    body = search.json()
    assert body["source"]["url"] == "https://buenosaires.gob.ar/gobierno/tramites"
    assert HABILITACION_ID in [procedure["id"] for procedure in body["procedures"]]

    detail = client.get(f"/guidance/procedures/{HABILITACION_ID}")

    assert detail.status_code == 200
    procedure = detail.json()["procedure"]
    assert procedure["official_url"].startswith("https://buenosaires.gob.ar/tramites/")
    assert procedure["requirements"]
    assert procedure["steps"]
    assert procedure["responsible_office"]


def test_unknown_procedure_endpoint_against_real_api_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/guidance/procedures/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_activity_procedures_endpoint_against_real_data_exposes_requirements() -> None:
    client = TestClient(app)

    response = client.get("/guidance/activities/cafeteria/procedures")

    assert response.status_code == 200
    body = response.json()
    assert body["requirements"]
    assert body["requirements_note"] == (
        "Fuente oficial: páginas de los trámites. Es una orientación general; "
        "verificá siempre con el organismo."
    )
