from typing import Any

import httpx

from conco.config import settings


def normalize_address(address: str) -> str:
    """Quita los espacios sobrantes de una dirección antes de enviarla a Georef."""
    return " ".join(address.split())


async def search_addresses(
    address: str,
    province: str = "caba",
    max_results: int = 5,
) -> dict[str, Any]:
    """Consulta el endpoint /direcciones de Georef y devuelve el JSON tal como llega."""
    params = {
        "direccion": normalize_address(address),
        "provincia": province,
        "max": max_results,
    }
    async with httpx.AsyncClient(
        base_url=settings.georef_base_url,
        timeout=settings.georef_timeout_seconds,
    ) as client:
        response = await client.get("/direcciones", params=params)
        response.raise_for_status()
        return response.json()
