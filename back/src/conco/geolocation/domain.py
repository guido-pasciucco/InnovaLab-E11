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
