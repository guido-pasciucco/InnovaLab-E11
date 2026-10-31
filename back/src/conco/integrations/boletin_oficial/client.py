from enum import StrEnum

import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.boletin_oficial.models import BoletinOficialNorm, BoletinOficialResults

RESULTS_PATH = "/obtenerResultado"


class BoletinOficialNormType(StrEnum):
    """Tipos de norma que se buscan por número y año, con el nombre que usa la API.

    Solo leyes y decretos: las resoluciones y disposiciones se numeran por organismo, así que
    un número y un año devuelven decenas de normas distintas (Resolución 100/2019 → 41).
    """

    LEY = "Ley"
    DECRETO = "Decreto"


# Ids de `tipoNorma` publicados por `/obtenerFiltrosDeBusqueda`.
NORM_TYPE_IDS: dict[BoletinOficialNormType, int] = {
    BoletinOficialNormType.LEY: 1,
    BoletinOficialNormType.DECRETO: 2,
}


class BoletinOficialError(Exception):
    """El Boletín Oficial no está disponible o devolvió una respuesta inesperada."""


def results_path(norm_type: BoletinOficialNormType, number: int, year: int) -> str:
    """Arma la ruta de búsqueda: los filtros van dentro de la ruta, no en la query string.

    Se envían siempre tipo, número y año (con cuatro dígitos): sin tipo se mezclan tipos de
    norma y sin año se mezclan años.
    """
    return f"{RESULTS_PATH}/tipoNorma={NORM_TYPE_IDS[norm_type]}&nNorma={number}&anio={year}"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.boletin_oficial_base_url,
        timeout=settings.boletin_oficial_timeout_seconds,
    )


async def find_norms(
    norm_type: BoletinOficialNormType, number: int, year: int
) -> list[BoletinOficialNorm]:
    """Busca una norma por tipo, número y año.

    Devuelve una lista vacía si no existe. Puede devolver más de una: por ejemplo, el Poder
    Ejecutivo y la Legislatura numeran sus decretos por separado.
    """
    try:
        async with _client() as client:
            response = await client.get(results_path(norm_type, number, year))
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise BoletinOficialError(f"No se pudo consultar el Boletín Oficial: {exc}") from exc
    try:
        # Un filtro inválido responde 200 con el texto "No hay criterio de búsqueda válido
        # seleccionado" en HTML: no es JSON y termina acá.
        results = BoletinOficialResults.model_validate_json(response.content)
    except ValidationError as exc:
        raise BoletinOficialError("El Boletín Oficial devolvió una respuesta inesperada.") from exc
    if results.norms == 0:
        return []
    return _matching(results.norms, norm_type, number, year)


def _matching(
    norms: list[BoletinOficialNorm], norm_type: BoletinOficialNormType, number: int, year: int
) -> list[BoletinOficialNorm]:
    """Se queda con las normas del tipo, número y año pedidos, sin repetir ninguna.

    La API ya filtra, pero se vuelve a comprobar por si ignora algún filtro.
    """
    seen: set[int] = set()
    matching: list[BoletinOficialNorm] = []
    for norm in norms:
        if (
            norm.type_name == norm_type.value
            and norm.number == number
            and norm.short_year in (year, year % 100)
            and norm.id not in seen
        ):
            seen.add(norm.id)
            matching.append(norm)
    return matching
