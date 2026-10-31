from typing import Protocol

from pydantic import BaseModel, ConfigDict


class Coordinates(BaseModel):
    """Coordenadas aproximadas de una dirección."""

    model_config = ConfigDict(frozen=True)

    latitude: float
    longitude: float


class Address(BaseModel):
    """Dirección normalizada, sin depender de qué servicio externo la encontró."""

    model_config = ConfigDict(frozen=True)

    full_address: str
    street: str | None
    number: int | None
    department: str | None
    locality: str | None
    province: str | None
    coordinates: Coordinates | None


class AddressSearchError(Exception):
    """El servicio de direcciones no está disponible o respondió algo inesperado."""


class AddressFinder(Protocol):
    """Puerto: cualquier servicio capaz de buscar direcciones a partir de un texto."""

    async def search(self, address: str, province: str, limit: int) -> list[Address]:
        """Devuelve las direcciones que coinciden; lanza AddressSearchError si falla."""
        ...


class Source(BaseModel):
    """Fuente oficial de la que proviene la información (RN-05)."""

    model_config = ConfigDict(frozen=True)

    name: str
    url: str
    license: str


class AddressContext(BaseModel):
    """Barrio, comuna y códigos postales de una ubicación de CABA.

    No incluye datos de catastro ni de zonificación: CONCO no los informa (RN-04).
    Los códigos postales pueden faltar, por ejemplo cuando se consulta por coordenadas.
    """

    model_config = ConfigDict(frozen=True)

    neighborhood: str
    commune: str
    postal_code: str | None
    argentine_postal_code: str | None


class AddressContextError(Exception):
    """El servicio de datos de la Ciudad no está disponible o respondió algo inesperado."""


class AddressContextProvider(Protocol):
    """Puerto: cualquier servicio oficial capaz de ubicar una dirección o un punto en CABA."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def by_address(self, street: str, number: int) -> AddressContext | None:
        """Devuelve el contexto, o None si no está en CABA; lanza AddressContextError si falla."""
        ...

    async def by_coordinates(self, latitude: float, longitude: float) -> AddressContext | None:
        """Devuelve el contexto, o None si no está en CABA; lanza AddressContextError si falla."""
        ...


class NearbyOffice(BaseModel):
    """Oficina de atención presencial de la Ciudad cercana a un punto (sede o subsede comunal).

    Los textos se informan como los publica la fuente oficial (por ejemplo, el barrio en
    mayúsculas). `info_url` es la página oficial de trámites y servicios de la comuna y
    `last_updated` es la fecha de la última modificación del dato en la fuente.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    address: str
    phone: str | None
    neighborhood: str | None
    commune: str | None
    distance_meters: float
    info_url: str | None
    last_updated: str | None


class NearbyOfficeError(Exception):
    """El servicio de lugares de la Ciudad no está disponible o respondió algo inesperado."""


class NearbyOfficeFinder(Protocol):
    """Puerto: cualquier servicio oficial capaz de listar oficinas cercanas a un punto de CABA."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def find_nearby(
        self, latitude: float, longitude: float, limit: int
    ) -> list[NearbyOffice]:
        """Devuelve hasta `limit` oficinas ordenadas por distancia, o una lista vacía si no hay
        ninguna en el radio de búsqueda; lanza NearbyOfficeError si falla."""
        ...


class LocationCheck(BaseModel):
    """Resultado de verificar si un punto está dentro de la Ciudad de Buenos Aires (RN-02).

    `province` y `department` se informan como los publica la fuente; fuera de la Argentina
    (por ejemplo, en el mar) vienen en None.
    """

    model_config = ConfigDict(frozen=True)

    in_caba: bool
    province: str | None
    department: str | None


class LocationCheckError(Exception):
    """El servicio de ubicación no está disponible o respondió algo inesperado."""


class LocationChecker(Protocol):
    """Puerto: cualquier servicio oficial capaz de decir en qué provincia está un punto."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def check(self, latitude: float, longitude: float) -> LocationCheck:
        """Indica si el punto está en CABA; lanza LocationCheckError si falla."""
        ...
