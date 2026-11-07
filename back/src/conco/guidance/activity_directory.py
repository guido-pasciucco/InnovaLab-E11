import asyncio
from collections.abc import Sequence

import psycopg

from conco.config import settings
from conco.guidance.domain import (
    Activity,
    ActivityDirectoryError,
    ActivityProcedures,
    ActivitySuggestion,
    ApplicableProcedure,
    ContextAnswers,
    Procedure,
    TextEmbedder,
)

# Mejor alias de cada actividad, para que una actividad con muchos sinónimos no ocupe todo
# el ranking. `<=>` es la distancia coseno de pgvector: 1 - distancia = similitud.
_SUGGEST_SQL = """
    select a.slug, a.name, best.alias, best.similarity
    from public.activities a
    join lateral (
        select alias, 1 - (embedding <=> %(query)s::extensions.vector) as similarity
        from public.activity_aliases
        where activity_slug = a.slug and embedding_model = %(model)s
        order by embedding <=> %(query)s::extensions.vector
        limit 1
    ) best on true
    where best.similarity >= %(min_similarity)s
    order by best.similarity desc
    limit %(limit)s
"""

_ACTIVITY_SQL = "select slug, name from public.activities where slug = %s"

_PROCEDURES_SQL = """
    select p.id, p.title, p.url, p.summary, p.changed_at, ap.note, ap.applies_when
    from public.activity_procedures ap
    join public.procedures p on p.id = ap.procedure_id
    where ap.activity_slug = %s
    order by ap.position
"""


def to_pgvector(vector: Sequence[float]) -> str:
    """pgvector recibe un vector como el texto literal '[x1,x2,...]'."""
    return "[" + ",".join(f"{value:.6f}" for value in vector) + "]"


class PostgresActivityDirectory:
    """Adaptador: busca actividades por similitud en Postgres (pgvector) y lee sus trámites."""

    def __init__(
        self,
        embedder: TextEmbedder,
        database_url: str | None = None,
        min_similarity: float | None = None,
    ) -> None:
        self._embedder = embedder
        self._database_url = database_url or settings.database_url
        self._min_similarity = (
            settings.activity_min_similarity if min_similarity is None else min_similarity
        )

    async def suggest(self, query: str, limit: int) -> list[ActivitySuggestion]:
        # El modelo usa CPU: se corre en otro hilo para no bloquear las demás peticiones.
        try:
            [vector] = await asyncio.to_thread(self._embedder.embed, [query])
        except Exception as exc:
            # Por ejemplo, el modelo no se pudo descargar: la búsqueda no está disponible.
            raise ActivityDirectoryError(f"No se pudo vectorizar la consulta: {exc}") from exc
        params = {
            "query": to_pgvector(vector),
            "model": self._embedder.model_name,
            "min_similarity": self._min_similarity,
            "limit": limit,
        }
        rows = await self._fetch(_SUGGEST_SQL, params)
        return [
            ActivitySuggestion(slug=slug, name=name, matched_alias=alias, similarity=round(similarity, 4))
            for slug, name, alias, similarity in rows
        ]

    async def procedures_for(self, slug: str) -> ActivityProcedures | None:
        activity_rows = await self._fetch(_ACTIVITY_SQL, [slug])
        if not activity_rows:
            return None
        [(activity_slug, name)] = activity_rows
        procedure_rows = await self._fetch(_PROCEDURES_SQL, [slug])
        return ActivityProcedures(
            activity=Activity(slug=activity_slug, name=name),
            procedures=[
                ApplicableProcedure(
                    procedure=Procedure(
                        id=procedure_id,
                        title=title,
                        official_url=url,
                        summary=summary,
                        last_updated=changed_at,
                    ),
                    note=note,
                    applies_when=ContextAnswers.model_validate(applies_when),
                )
                for procedure_id, title, url, summary, changed_at, note, applies_when in procedure_rows
            ],
        )

    async def _fetch(self, sql: str, params: object) -> list[tuple]:
        try:
            async with await psycopg.AsyncConnection.connect(self._database_url) as conn:
                cursor = await conn.execute(sql, params)
                return await cursor.fetchall()
        except psycopg.Error as exc:
            raise ActivityDirectoryError(f"No se pudo consultar la base de actividades: {exc}") from exc
