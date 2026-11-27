import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.georef.models import GeorefAddressesResponse


class GeorefError(Exception):
    """Georef no está disponible o devolvió una respuesta inesperada."""


def normalize_address(address: str) -> str:
    """Quita los espacios sobrantes de una dirección antes de enviarla a Georef."""
    return " ".join(address.split())


def lookup_query(address: str) -> str:
    """Georef no entiende la nomenclatura completa: descarta Comuna/provincia.

    La nomenclatura que devuelve la API termina en ", Comuna N, Ciudad Autónoma…";
    si se envía tal cual, Georef toma "3" como altura y no encuentra la dirección.
    """
    return normalize_address(address.split(",", 1)[0])


async def search_addresses(
    address: str,
    province: str = "caba",
    max_results: int = 5,
) -> GeorefAddressesResponse:
    """Consulta el endpoint /direcciones de Georef y devuelve la respuesta tipada."""
    params = {
        "direccion": lookup_query(address),
        "provincia": province,
        "max": max_results,
    }
    try:
        async with httpx.AsyncClient(
            base_url=settings.georef_base_url,
            timeout=settings.georef_timeout_seconds,
        ) as client:
            response = await client.get("/direcciones", params=params)
            response.raise_for_status()
            return GeorefAddressesResponse.model_validate_json(response.content)
    except httpx.HTTPError as exc:
        raise GeorefError(f"No se pudo consultar Georef: {exc}") from exc
    except ValidationError as exc:
        raise GeorefError("Georef devolvió una respuesta inesperada.") from exc
