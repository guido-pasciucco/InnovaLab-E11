import pytest

from conco.guidance.activity_directory import PostgresActivityDirectory
from conco.guidance.embeddings import FastEmbedTextEmbedder

pytestmark = [pytest.mark.database, pytest.mark.anyio]

HABILITACION_ID = "338718b4-a2a0-44af-baa4-083f5d834b12"


@pytest.fixture(scope="module")
def directory() -> PostgresActivityDirectory:
    return PostgresActivityDirectory(FastEmbedTextEmbedder())


async def test_synonym_suggests_its_activity_first(directory: PostgresActivityDirectory) -> None:
    suggestions = await directory.suggest("quiero poner una barbería", limit=5)

    assert suggestions[0].slug == "peluqueria"
    assert suggestions[0].matched_alias == "barbería"


async def test_unrelated_text_suggests_nothing(directory: PostgresActivityDirectory) -> None:
    assert await directory.suggest("quiero abrir un gimnasio", limit=5) == []


async def test_procedures_come_in_curated_order(directory: PostgresActivityDirectory) -> None:
    result = await directory.procedures_for("cafeteria")

    assert result is not None
    assert result.activity.name == "Cafetería"
    assert str(result.procedures[0].procedure.id) == HABILITACION_ID
    assert result.procedures[0].procedure.official_url.startswith("https://buenosaires.gob.ar/")


async def test_unknown_activity_returns_none(directory: PostgresActivityDirectory) -> None:
    assert await directory.procedures_for("gimnasio") is None
