from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from conco.config import settings
from conco.integrations.georef.models import (
    GeorefAddressesResponse,
    GeorefLocationResponse,
)

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class GeorefError(Exception):
    """Georef no está disponible o devolvió una respuesta inesperada."""


def normalize_address(address: str) -> str:
    """Quita los espacios sobrantes de una dirección antes de enviarla a Georef."""
    return " ".join(address.split())


async def search_addresses(
    address: str,
    province: str = "caba",
    max_results: int = 5,
) -> GeorefAddressesResponse:
    """Consulta el endpoint /direcciones de Georef y devuelve la respuesta tipada."""
    params = {
        "direccion": normalize_address(address),
        "provincia": province,
        "max": max_results,
    }
    return await _get("/direcciones", params, GeorefAddressesResponse)


async def locate(latitude: float, longitude: float) -> GeorefLocationResponse:
    """Consulta el endpoint /ubicacion de Georef (geocodificación inversa de un punto).

    Fuera de la Argentina Georef responde 200 con provincia, departamento y municipio en null.
    """
    params = {"lat": latitude, "lon": longitude}
    return await _get("/ubicacion", params, GeorefLocationResponse)


async def _get(
    path: str, params: dict[str, str | int | float], model: type[ResponseModel]
) -> ResponseModel:
    """Hace un GET a Georef y valida la respuesta; cualquier falla se informa como GeorefError."""
    try:
        async with httpx.AsyncClient(
            base_url=settings.georef_base_url,
            timeout=settings.georef_timeout_seconds,
        ) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return model.model_validate_json(response.content)
    except httpx.HTTPError as exc:
        raise GeorefError(f"No se pudo consultar Georef: {exc}") from exc
    except ValidationError as exc:
        raise GeorefError("Georef devolvió una respuesta inesperada.") from exc
