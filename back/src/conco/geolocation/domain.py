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
