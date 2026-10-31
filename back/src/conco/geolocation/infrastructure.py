from conco.config import settings
from conco.geolocation.domain import (
    Address,
    AddressContext,
    AddressContextError,
    AddressSearchError,
    Coordinates,
    Source,
)
from conco.integrations.georef.client import GeorefError, search_addresses
from conco.integrations.georef.models import GeorefAddress
from conco.integrations.usig.client import (
    UsigError,
    get_datos_utiles_by_address,
    get_datos_utiles_by_coordinates,
)
from conco.integrations.usig.models import UsigDatosUtiles


class GeorefAddressFinder:
    """Adaptador: busca direcciones en Georef y las traduce al modelo del dominio."""

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        try:
            response = await search_addresses(
                address, province=province, max_results=limit
            )
        except GeorefError as exc:
            raise AddressSearchError(str(exc)) from exc
        return [_to_domain(georef_address) for georef_address in response.addresses]


def _to_domain(georef_address: GeorefAddress) -> Address:
    """Copia solo los datos que la API necesita, con nombres propios del dominio."""
    location = georef_address.location
    return Address(
        full_address=georef_address.nomenclature,
        street=georef_address.street.name,
        number=georef_address.height.value,
        department=georef_address.department.name,
        locality=georef_address.census_locality.name,
        province=georef_address.province.name,
        coordinates=(
            Coordinates(latitude=location.lat, longitude=location.lon)
            if location is not None
            else None
        ),
    )


class UsigAddressContextProvider:
    """Adaptador: consulta los datos útiles de USIG y los traduce al modelo del dominio."""

    @property
    def source(self) -> Source:
        return Source(
            name="USIG - Datos útiles (Gobierno de la Ciudad de Buenos Aires)",
            url=settings.usig_docs_url,
            license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
        )

    async def by_address(self, street: str, number: int) -> AddressContext | None:
        try:
            result = await get_datos_utiles_by_address(street, number)
        except UsigError as exc:
            raise AddressContextError(str(exc)) from exc
        return _to_context(result) if result is not None else None

    async def by_coordinates(self, latitude: float, longitude: float) -> AddressContext | None:
        try:
            result = await get_datos_utiles_by_coordinates(
                longitude=longitude, latitude=latitude
            )
        except UsigError as exc:
            raise AddressContextError(str(exc)) from exc
        return _to_context(result) if result is not None else None


def _to_context(result: UsigDatosUtiles) -> AddressContext:
    """Copia barrio, comuna y códigos postales; un código vacío se informa como None."""
    return AddressContext(
        neighborhood=result.neighborhood.strip(),
        commune=result.commune.strip(),
        postal_code=(result.postal_code or "").strip() or None,
        argentine_postal_code=(result.argentine_postal_code or "").strip() or None,
    )
