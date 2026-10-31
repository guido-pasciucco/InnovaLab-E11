from conco.geolocation.domain import Address, AddressSearchError, Coordinates
from conco.integrations.georef.client import GeorefError, search_addresses
from conco.integrations.georef.models import GeorefAddress


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
