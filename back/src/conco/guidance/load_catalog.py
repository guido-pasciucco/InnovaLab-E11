"""Carga en Postgres el catálogo de trámites de la Ciudad y las actividades curadas.

Uso (desde back/, con la base levantada):
    uv run python -m conco.guidance.load_catalog
"""

import asyncio
import json
import time
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, model_validator

from conco.config import settings
from conco.guidance.activity_directory import to_pgvector
from conco.guidance.domain import ContextAnswers
from conco.guidance.embeddings import FastEmbedTextEmbedder
from conco.guidance.infrastructure import to_procedure
from conco.integrations.caba_tramites.client import list_procedures
from conco.integrations.caba_tramites.models import CabaProcedure

ACTIVITIES_FILE = Path(__file__).parent / "data" / "activities.json"


class CuratedProcedure(BaseModel):
    """Trámite de una actividad en el archivo curado; el título es solo para leerlo a mano."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    title: str
    note: str
    # Preguntas de contexto que deciden si aplica; un nombre desconocido es un error.
    applies_when: ContextAnswers = ContextAnswers()


class CuratedActivity(BaseModel):
    model_config = ConfigDict(frozen=True)

    slug: str
    name: str
    synonyms: list[str]
    procedures: list[CuratedProcedure]

    @property
    def aliases(self) -> list[str]:
        """El nombre y los sinónimos, sin repetidos y en orden."""
        return list(dict.fromkeys([self.name, *self.synonyms]))

    @model_validator(mode="after")
    def _procedures_are_unique(self) -> "CuratedActivity":
        ids = [procedure.id for procedure in self.procedures]
        if len(ids) != len(set(ids)):
            raise ValueError(f"La actividad {self.slug!r} repite un trámite.")
        return self


class CuratedCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    activities: list[CuratedActivity]

    @model_validator(mode="after")
    def _slugs_are_unique(self) -> "CuratedCatalog":
        slugs = [activity.slug for activity in self.activities]
        if len(slugs) != len(set(slugs)):
            raise ValueError("Hay actividades con el mismo slug.")
        return self

    def procedure_ids(self) -> set[UUID]:
        return {p.id for activity in self.activities for p in activity.procedures}


def referenced_procedures(
    caba_procedures: list[CabaProcedure], catalog: CuratedCatalog
) -> list[CabaProcedure]:
    """Deja solo los trámites publicados que el catálogo curado referencia.

    La Ciudad publica cientos; la app solo muestra los del curado.
    """
    wanted = catalog.procedure_ids()
    return [procedure for procedure in caba_procedures if procedure.id in wanted]


def read_curated_catalog(path: Path = ACTIVITIES_FILE) -> CuratedCatalog:
    """Lee y valida el archivo curado de actividades."""
    return CuratedCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load(database_url: str) -> None:
    started = time.perf_counter()
    published = asyncio.run(list_procedures())
    print(f"Trámites publicados: {len(published)} ({time.perf_counter() - started:.1f}s)")

    catalog = read_curated_catalog()
    missing = catalog.procedure_ids() - {procedure.id for procedure in published}
    if missing:
        raise SystemExit(
            "El archivo curado menciona trámites que la Ciudad ya no publica: "
            f"{sorted(str(procedure_id) for procedure_id in missing)}"
        )
    caba_procedures = referenced_procedures(published, catalog)
    print(f"Trámites referenciados por el curado: {len(caba_procedures)}")

    started = time.perf_counter()
    embedder = FastEmbedTextEmbedder()
    aliases = [(activity.slug, alias) for activity in catalog.activities for alias in activity.aliases]
    vectors = embedder.embed([alias for _, alias in aliases])
    print(f"Alias vectorizados: {len(aliases)} ({time.perf_counter() - started:.1f}s)")

    procedure_rows = []
    for caba_procedure in caba_procedures:
        procedure = to_procedure(caba_procedure)
        procedure_rows.append((
            procedure.id, procedure.title, procedure.summary, procedure.official_url,
            caba_procedure.attributes.sector, procedure.last_updated,
        ))

    # Una sola transacción: si algo falla, la base queda como estaba.
    with psycopg.connect(database_url) as conn, conn.cursor() as cursor:
        cursor.execute("truncate public.procedures")
        cursor.execute("delete from public.activities")
        cursor.executemany(
            """
            insert into public.procedures (id, title, summary, url, sector, changed_at)
            values (%s, %s, %s, %s, %s, %s)
            """,
            procedure_rows,
        )
        cursor.executemany(
            "insert into public.activities (slug, name) values (%s, %s)",
            [(activity.slug, activity.name) for activity in catalog.activities],
        )
        cursor.executemany(
            """
            insert into public.activity_aliases (activity_slug, alias, embedding_model, embedding)
            values (%s, %s, %s, %s::extensions.vector)
            """,
            [
                (slug, alias, embedder.model_name, to_pgvector(vector))
                for (slug, alias), vector in zip(aliases, vectors, strict=True)
            ],
        )
        cursor.executemany(
            """
            insert into public.activity_procedures
                (activity_slug, procedure_id, note, position, applies_when)
            values (%s, %s, %s, %s, %s)
            """,
            [
                (activity.slug, procedure.id, procedure.note, position,
                 Jsonb(procedure.applies_when.answered()))
                for activity in catalog.activities
                for position, procedure in enumerate(activity.procedures)
            ],
        )
    print(
        f"Cargados {len(procedure_rows)} trámites referenciados y {len(catalog.activities)} actividades "
        f"con {len(aliases)} alias (de {len(published)} publicados)."
    )


if __name__ == "__main__":
    load(settings.database_url)
