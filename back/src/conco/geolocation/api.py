from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from conco.geolocation.domain import Address, AddressFinder, AddressSearchError
from conco.geolocation.infrastructure import GeorefAddressFinder

router = APIRouter(prefix="/geolocation", tags=["Geolocalización"])


class AddressSearchResponse(BaseModel):
    """Respuesta del endpoint de búsqueda de direcciones."""

    addresses: list[Address]


def get_address_finder() -> AddressFinder:
    """Elige qué servicio busca direcciones; los tests lo reemplazan por uno falso."""
    return GeorefAddressFinder()


@router.get("/addresses", response_model=AddressSearchResponse)
async def search_addresses(
    finder: Annotated[AddressFinder, Depends(get_address_finder)],
    address: Annotated[
        str,
        Query(
            min_length=3,
            max_length=200,
            pattern=r"\S",
            description="Dirección escrita libremente, por ejemplo: Corrientes 2500.",
        ),
    ],
    province: Annotated[
        str,
        Query(
            min_length=2,
            max_length=60,
            description="Provincia donde buscar (nombre o id de Georef).",
        ),
    ] = "caba",
    limit: Annotated[
        int,
        Query(ge=1, le=10, description="Cantidad máxima de resultados."),
    ] = 5,
) -> AddressSearchResponse:
    """Convierte una dirección escrita libremente en direcciones normalizadas con coordenadas aproximadas."""
    try:
        addresses = await finder.search(address, province=province, limit=limit)
    except AddressSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio de direcciones no está disponible. Intentá de nuevo más tarde.",
        ) from exc
    return AddressSearchResponse(addresses=addresses)
