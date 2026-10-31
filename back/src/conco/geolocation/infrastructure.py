import asyncio
from html.parser import HTMLParser

from conco.config import settings
from conco.geolocation.domain import (
    Address,
    AddressContext,
    AddressContextError,
    AddressSearchError,
    Coordinates,
    NearbyOffice,
    NearbyOfficeError,
    Source,
)
from conco.integrations.epok.client import (
    COMMUNE_OFFICES_CATEGORY,
    EpokError,
    get_object,
)
from conco.integrations.epok.client import find_nearby as find_nearby_places
from conco.integrations.epok.models import EpokObjectContent, EpokPlace
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


class EpokNearbyOfficeFinder:
    """Adaptador: busca sedes comunales cercanas en EPOK y las traduce al modelo del dominio.

    EPOK resuelve la búsqueda en dos pasos: primero los lugares en un radio (con distancia) y
    después el contenido de cada uno (dirección, teléfono, etc.). El contenido de las oficinas
    elegidas se pide en paralelo.
    """

    @property
    def source(self) -> Source:
        return Source(
            name="USIG - EPOK (Gobierno de la Ciudad de Buenos Aires)",
            url=settings.epok_base_url,
            license=(
                "Sin licencia explícita; se asume Creative Commons Reconocimiento 2.5 "
                "Argentina (CC BY 2.5 AR), como el resto de los datos de la Ciudad"
            ),
        )

    async def find_nearby(
        self, latitude: float, longitude: float, limit: int
    ) -> list[NearbyOffice]:
        try:
            places = await find_nearby_places(
                longitude=longitude,
                latitude=latitude,
                categories=[COMMUNE_OFFICES_CATEGORY],
                radius_meters=settings.epok_radius_meters,
            )
            closest = places[:limit]
            contents = await asyncio.gather(*(get_object(place.id) for place in closest))
        except EpokError as exc:
            raise NearbyOfficeError(str(exc)) from exc
        offices = (
            _to_office(place, content)
            for place, content in zip(closest, contents, strict=True)
            if content is not None
        )
        return [office for office in offices if office is not None]


def _to_office(place: EpokPlace, content: EpokObjectContent) -> NearbyOffice | None:
    """Copia los datos de la oficina; sin dirección no sirve para ir, así que se descarta."""
    address = content.value("direccion") or (content.normalized_address or "").strip()
    if not address:
        return None
    return NearbyOffice(
        name=content.value("nombre") or place.name,
        address=address,
        phone=content.value("telefonos"),
        neighborhood=content.value("barrio"),
        commune=content.value("comuna"),
        distance_meters=place.distance_meters,
        info_url=extract_link(content.value("tramites_y_servicios")),
        last_updated=(content.last_modified or "").strip() or None,
    )


class _FirstLinkParser(HTMLParser):
    """Guarda el `href` del primer enlace web (`http` o `https`) de un fragmento HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.link: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.link is not None or tag != "a":
            return
        href = (dict(attrs).get("href") or "").strip()
        if href.startswith(("https://", "http://")):
            self.link = href


def extract_link(html: str | None) -> str | None:
    """Extrae el enlace de un dato que EPOK publica como HTML (`<a href="...">Página web</a>`).

    Devuelve None si no hay un enlace web: así no se expone HTML ni enlaces de otro tipo.
    """
    if not html:
        return None
    parser = _FirstLinkParser()
    parser.feed(html)
    parser.close()
    return parser.link
