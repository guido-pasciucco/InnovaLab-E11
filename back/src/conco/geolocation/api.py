from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from conco.geolocation.domain import (
    Address,
    AddressContext,
    AddressContextError,
    AddressContextProvider,
    AddressFinder,
    AddressSearchError,
    NearbyOffice,
    NearbyOfficeError,
    NearbyOfficeFinder,
    Source,
)
from conco.geolocation.infrastructure import (
    EpokNearbyOfficeFinder,
    GeorefAddressFinder,
    UsigAddressContextProvider,
)

router = APIRouter(prefix="/geolocation", tags=["Geolocalización"])

CONTEXT_NOT_FOUND_DETAIL = "No se encontró la ubicación dentro de la Ciudad de Buenos Aires."
CONTEXT_UNAVAILABLE_DETAIL = (
    "El servicio de datos de la Ciudad no está disponible. Intentá de nuevo más tarde."
)
OFFICES_UNAVAILABLE_DETAIL = (
    "El servicio de lugares de la Ciudad no está disponible. Intentá de nuevo más tarde."
)


class AddressSearchResponse(BaseModel):
    """Respuesta del endpoint de búsqueda de direcciones."""

    addresses: list[Address]


class AddressContextResponse(BaseModel):
    """Barrio, comuna y códigos postales de una ubicación, con la fuente oficial que los informa."""

    context: AddressContext
    source: Source


class NearbyOfficesResponse(BaseModel):
    """Oficinas de atención cercanas, ordenadas por distancia, con la fuente oficial."""

    offices: list[NearbyOffice]
    source: Source


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


def get_address_context_provider() -> AddressContextProvider:
    """Elige qué servicio informa barrio y comuna; los tests lo reemplazan por uno falso."""
    return UsigAddressContextProvider()


def _context_response(
    context: AddressContext | None, provider: AddressContextProvider
) -> AddressContextResponse:
    """Traduce "no encontrado" a 404 y arma la respuesta citando la fuente (RN-05)."""
    if context is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CONTEXT_NOT_FOUND_DETAIL
        )
    return AddressContextResponse(context=context, source=provider.source)


@router.get("/address-context", response_model=AddressContextResponse)
async def get_address_context(
    provider: Annotated[AddressContextProvider, Depends(get_address_context_provider)],
    street: Annotated[
        str,
        Query(
            min_length=2,
            max_length=100,
            pattern=r"\S",
            description="Nombre de la calle, por ejemplo: Corrientes.",
        ),
    ],
    number: Annotated[
        int,
        Query(ge=1, le=99999, description="Altura de la calle, por ejemplo: 2500."),
    ],
) -> AddressContextResponse:
    """Informa barrio, comuna y códigos postales de una dirección de la Ciudad de Buenos Aires."""
    try:
        context = await provider.by_address(street, number)
    except AddressContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=CONTEXT_UNAVAILABLE_DETAIL
        ) from exc
    return _context_response(context, provider)


@router.get("/address-context/by-coordinates", response_model=AddressContextResponse)
async def get_address_context_by_coordinates(
    provider: Annotated[AddressContextProvider, Depends(get_address_context_provider)],
    latitude: Annotated[
        float,
        Query(ge=-90, le=90, description="Latitud en grados (WGS84), por ejemplo: -34.604792."),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=-180, le=180, description="Longitud en grados (WGS84), por ejemplo: -58.401981."
        ),
    ],
) -> AddressContextResponse:
    """Informa barrio y comuna de un punto de la Ciudad de Buenos Aires.

    Por coordenadas, USIG no informa códigos postales: vienen en null.
    """
    try:
        context = await provider.by_coordinates(latitude=latitude, longitude=longitude)
    except AddressContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=CONTEXT_UNAVAILABLE_DETAIL
        ) from exc
    return _context_response(context, provider)


def get_nearby_office_finder() -> NearbyOfficeFinder:
    """Elige qué servicio informa las oficinas cercanas; los tests lo reemplazan por uno falso."""
    return EpokNearbyOfficeFinder()


@router.get("/nearby-offices", response_model=NearbyOfficesResponse)
async def get_nearby_offices(
    finder: Annotated[NearbyOfficeFinder, Depends(get_nearby_office_finder)],
    latitude: Annotated[
        float,
        Query(ge=-90, le=90, description="Latitud en grados (WGS84), por ejemplo: -34.6047137."),
    ],
    longitude: Annotated[
        float,
        Query(
            ge=-180, le=180, description="Longitud en grados (WGS84), por ejemplo: -58.4021372."
        ),
    ],
    limit: Annotated[
        int,
        Query(ge=1, le=5, description="Cantidad máxima de oficinas."),
    ] = 3,
) -> NearbyOfficesResponse:
    """Lista las sedes y subsedes comunales más cercanas a un punto de la Ciudad de Buenos Aires.

    Si no hay ninguna en el radio de búsqueda, devuelve una lista vacía.
    """
    try:
        offices = await finder.find_nearby(latitude=latitude, longitude=longitude, limit=limit)
    except NearbyOfficeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=OFFICES_UNAVAILABLE_DETAIL
        ) from exc
    return NearbyOfficesResponse(offices=offices, source=finder.source)
