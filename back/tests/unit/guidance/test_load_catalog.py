import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from conco.guidance.activity_directory import PostgresActivityDirectory, to_pgvector
from conco.guidance.domain import ActivityDirectoryError
from conco.guidance.load_catalog import read_curated_catalog, referenced_procedures
from conco.integrations.caba_tramites.models import (
    CabaProcedure,
    CabaProcedureAttributes,
    CabaPath,
    CabaText,
)

HABILITACION_ID = "338718b4-a2a0-44af-baa4-083f5d834b12"


def _write_catalog(tmp_path: Path, activities: list[dict]) -> Path:
    path = tmp_path / "activities.json"
    path.write_text(json.dumps({"status": "Draft", "activities": activities}), encoding="utf-8")
    return path


def _activity(slug: str, procedure_ids: list[str]) -> dict:
    return {
        "slug": slug,
        "name": slug.title(),
        "synonyms": [],
        "procedures": [{"id": pid, "title": "Trámite", "note": "Siempre."} for pid in procedure_ids],
    }


def test_curated_file_in_repo_is_valid() -> None:
    catalog = read_curated_catalog()

    assert catalog.activities
    assert all(activity.procedures for activity in catalog.activities)
    assert all(procedure.note for a in catalog.activities for procedure in a.procedures)


def test_repo_catalog_has_the_nine_agreed_activities() -> None:
    catalog = read_curated_catalog()

    assert {activity.slug for activity in catalog.activities} == {
        "cafeteria",
        "restaurante",
        "kiosco",
        "peluqueria",
        "comercio-minorista",
        "foodtruck",
        "carniceria",
        "hotel",
        "optica",
    }


CAA_ID = "fc321f1e-badb-4439-be4e-5d4fbfc963ac"
HUMEDOS_ID = "1304fa97-1f5f-48d7-b867-d30ca2f78689"


def test_caa_is_tronco_comun_and_hummedos_lives_in_carniceria() -> None:
    catalog = read_curated_catalog()

    by_slug = {activity.slug: {procedure.id for procedure in activity.procedures} for activity in catalog.activities}

    assert all(UUID(CAA_ID) in ids for ids in by_slug.values()), "CAA debe ser tronco común en las 9 actividades"
    assert UUID(HUMEDOS_ID) in by_slug["carniceria"], "húmedos debe estar en carnicería"
    assert UUID(HUMEDOS_ID) not in by_slug["restaurante"], "húmedos debe salir de restaurante"


def test_aliases_are_name_plus_synonyms_without_duplicates(tmp_path: Path) -> None:
    activity = _activity("cafeteria", [HABILITACION_ID])
    activity.update(name="Cafetería", synonyms=["café", "Cafetería", "coffee shop"])

    catalog = read_curated_catalog(_write_catalog(tmp_path, [activity]))

    assert catalog.activities[0].aliases == ["Cafetería", "café", "coffee shop"]


def test_rejects_repeated_slugs(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path, [_activity("kiosco", [HABILITACION_ID]), _activity("kiosco", [HABILITACION_ID])]
    )

    with pytest.raises(ValidationError, match="mismo slug"):
        read_curated_catalog(path)


def test_rejects_repeated_procedure_in_one_activity(tmp_path: Path) -> None:
    path = _write_catalog(tmp_path, [_activity("kiosco", [HABILITACION_ID, HABILITACION_ID])])

    with pytest.raises(ValidationError, match="repite un trámite"):
        read_curated_catalog(path)


def _procedure(procedure_id: str) -> CabaProcedure:
    return CabaProcedure(
        id=UUID(procedure_id),
        attributes=CabaProcedureAttributes(
            title="Trámite",
            path=CabaPath(alias="/tramite"),
            changed=datetime(2026, 11, 1, tzinfo=timezone.utc),
            body=CabaText(value="Resumen", format="plain_text"),
        ),
    )


def test_referenced_procedures_keeps_only_what_the_curated_catalog_references(
    tmp_path: Path,
) -> None:
    keep = HABILITACION_ID
    drop = "00000000-0000-0000-0000-000000000000"
    activity = _activity("kiosco", [keep])
    catalog = read_curated_catalog(_write_catalog(tmp_path, [activity]))

    kept = referenced_procedures([_procedure(keep), _procedure(drop)], catalog)

    assert [str(procedure.id) for procedure in kept] == [keep]


def test_to_pgvector_formats_a_vector_literal() -> None:
    assert to_pgvector([0.1, -0.25, 1]) == "[0.100000,-0.250000,1.000000]"


class _FixedEmbedder:
    model_name = "test-model"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


@pytest.mark.anyio
async def test_directory_raises_domain_error_when_database_is_down() -> None:
    directory = PostgresActivityDirectory(
        _FixedEmbedder(), database_url="postgresql://postgres:postgres@127.0.0.1:1/postgres"
    )

    with pytest.raises(ActivityDirectoryError):
        await directory.suggest("barbería", limit=5)


class _BrokenEmbedder:
    model_name = "test-model"

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("model download failed")


@pytest.mark.anyio
async def test_directory_raises_domain_error_when_model_fails() -> None:
    directory = PostgresActivityDirectory(_BrokenEmbedder())

    with pytest.raises(ActivityDirectoryError):
        await directory.suggest("barbería", limit=5)


def test_reads_procedure_conditions(tmp_path: Path) -> None:
    activity = _activity("kiosco", [HABILITACION_ID])
    activity["procedures"][0]["applies_when"] = {"takes_over_existing": False}

    catalog = read_curated_catalog(_write_catalog(tmp_path, [activity]))

    assert catalog.activities[0].procedures[0].applies_when.answered() == {
        "takes_over_existing": False
    }


def test_rejects_unknown_condition(tmp_path: Path) -> None:
    activity = _activity("kiosco", [HABILITACION_ID])
    activity["procedures"][0]["applies_when"] = {"has_pets": True}

    with pytest.raises(ValidationError, match="has_pets"):
        read_curated_catalog(_write_catalog(tmp_path, [activity]))
