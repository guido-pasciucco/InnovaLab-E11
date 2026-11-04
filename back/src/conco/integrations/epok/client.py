import json
from collections.abc import Sequence

import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.epok.models import EpokNearbyPlaces, EpokObjectContent, EpokPlace

NEARBY_PATH = "/reverseGeocoderLugares/"
OBJECT_CONTENT_PATH = "/getObjectContent/"

# Categoría de EPOK con las sedes y subsedes comunales (atención presencial del Gobierno de la
# Ciudad). EPOK publica 182 categorías; para sumar otras (por ejemplo `oficinas_de_empleo`) se
# agrega su id acá y se pasa en `categories`.
COMMUNE_OFFICES_CATEGORY = "sedes_de_comunas"


class EpokError(Exception):
    """EPOK no está disponible o devolvió una respuesta inesperada."""


def _client() -> httpx.AsyncClient:
    # Un filtro de EPOK corta la conexión con algunos User-Agent (por ejemplo, el de curl),
    # así que se envía siempre uno propio en vez de depender del que trae la librería.
    return httpx.AsyncClient(
        base_url=settings.epok_base_url,
        timeout=settings.epok_timeout_seconds,
        headers={"User-Agent": settings.epok_user_agent},
    )


async def find_nearby(
    longitude: float, latitude: float, categories: Sequence[str], radius_meters: int
) -> list[EpokPlace]:
    """Busca lugares de las categorías dadas dentro de un radio alrededor de un punto (WGS84).

    Devuelve la lista ordenada por distancia (EPOK no la ordena), o vacía si no hay lugares en
    el radio. EPOK también responde vacío ante una categoría desconocida.
    """
    params: dict[str, str | int | float] = {
        "x": longitude,
        "y": latitude,
        "categorias": ",".join(categories),
        "radio": radius_meters,
    }
    body = await _get(NEARBY_PATH, params)
    try:
        result = EpokNearbyPlaces.model_validate_json(body)
    except ValidationError as exc:
        raise EpokError("EPOK devolvió una respuesta inesperada.") from exc
    return sorted(result.places, key=lambda place: place.distance_meters)


async def get_object(object_id: str) -> EpokObjectContent | None:
    """Devuelve el contenido (nombre, dirección, teléfonos, etc.) de un lugar de EPOK.

    Devuelve None si el id no existe: EPOK responde `{}`.
    """
    body = await _get(OBJECT_CONTENT_PATH, {"id": object_id})
    try:
        parsed = json.loads(body)
        if parsed == {}:
            return None
        return EpokObjectContent.model_validate(parsed)
    except (ValueError, ValidationError) as exc:
        raise EpokError("EPOK devolvió una respuesta inesperada.") from exc


async def _get(path: str, params: dict[str, str | int | float]) -> bytes:
    """Hace la consulta y devuelve el cuerpo sin mirar el Content-Type.

    EPOK declara su JSON como `text/javascript`.
    """
    try:
        async with _client() as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EpokError(f"No se pudo consultar EPOK: {exc}") from exc
    return response.content
