import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.usig.models import UsigDatosUtiles

DATOS_UTILES_PATH = "/datos_utiles"

# Cuando no puede ubicar la dirección, USIG responde 200 con este texto plano en vez de JSON.
NOT_FOUND_PREFIX = b"ERROR:"


class UsigError(Exception):
    """USIG no está disponible o devolvió una respuesta inesperada."""


def normalize_street(street: str) -> str:
    """Quita los espacios sobrantes del nombre de la calle antes de enviarlo."""
    return " ".join(street.split())


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.usig_base_url,
        timeout=settings.usig_timeout_seconds,
    )


async def get_datos_utiles_by_address(street: str, number: int) -> UsigDatosUtiles | None:
    """Devuelve comuna, barrio y códigos postales de una dirección de CABA.

    Devuelve None si USIG no encuentra la dirección o si está fuera de la Ciudad.
    """
    return await _get_datos_utiles({"calle": normalize_street(street), "altura": number})


async def get_datos_utiles_by_coordinates(
    longitude: float, latitude: float
) -> UsigDatosUtiles | None:
    """Devuelve comuna y barrio de un punto (WGS84). Por coordenadas no hay códigos postales.

    Devuelve None si el punto está fuera de la Ciudad.
    """
    return await _get_datos_utiles({"x": longitude, "y": latitude})


async def _get_datos_utiles(params: dict[str, str | int | float]) -> UsigDatosUtiles | None:
    try:
        async with _client() as client:
            response = await client.get(DATOS_UTILES_PATH, params=params)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise UsigError(f"No se pudo consultar USIG: {exc}") from exc
    return _parse(response.content)


def _parse(body: bytes) -> UsigDatosUtiles | None:
    """Interpreta el cuerpo sin mirar el Content-Type: USIG declara JSON como text/javascript.

    Todos los casos llegan con estado 200: un texto `ERROR: ...` si no encuentra la dirección,
    la página de ayuda en HTML si faltan parámetros, y JSON con comuna y barrio vacíos si el
    lugar está fuera de la Ciudad.
    """
    if body.lstrip().startswith(NOT_FOUND_PREFIX):
        return None
    try:
        result = UsigDatosUtiles.model_validate_json(body)
    except ValidationError as exc:
        raise UsigError("USIG devolvió una respuesta inesperada.") from exc
    if not result.commune.strip() or not result.neighborhood.strip():
        return None
    return result
