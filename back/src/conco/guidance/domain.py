from datetime import date, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    """Fuente oficial de la que proviene la información (RN-05)."""

    model_config = ConfigDict(frozen=True)

    name: str
    url: str
    license: str


class Procedure(BaseModel):
    """Trámite oficial resumido, sin depender de qué servicio externo lo publica."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    title: str
    official_url: str
    summary: str
    last_updated: datetime


class ProcedureDetail(Procedure):
    """Trámite con requisitos y pasos en texto plano, en el orden de la página oficial."""

    requirements: list[str]
    steps: list[str]
    responsible_office: str | None
    start_url: str | None


class ProcedureSearchError(Exception):
    """El servicio de trámites no está disponible o respondió algo inesperado."""


class ProcedureCatalog(Protocol):
    """Puerto: cualquier catálogo oficial capaz de buscar trámites y mostrar su detalle."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def search(self, query: str, limit: int) -> list[Procedure]:
        """Devuelve los trámites que coinciden; lanza ProcedureSearchError si falla."""
        ...

    async def get(self, procedure_id: UUID) -> ProcedureDetail | None:
        """Devuelve el detalle, o None si no existe; lanza ProcedureSearchError si falla."""
        ...


class RegulationType(StrEnum):
    """Tipos de norma que se pueden consultar por número y año."""

    LEY = "ley"
    DECRETO = "decreto"


class Regulation(BaseModel):
    """Norma oficial publicada (ley o decreto) que respalda un trámite o requisito.

    Se cita como referencia de la fuente, no como una determinación legal (RN-04).
    """

    model_config = ConfigDict(frozen=True)

    type: RegulationType
    number: int
    year: int
    summary: str
    issuing_body: str | None
    publication_date: date
    bulletin_number: int
    document_url: str | None


class RegulationLookupError(Exception):
    """El registro de normas no está disponible o respondió algo inesperado."""


class RegulationRegistry(Protocol):
    """Puerto: cualquier registro oficial capaz de encontrar una norma por tipo, número y año."""

    @property
    def source(self) -> Source:
        """Fuente oficial que se cita en cada respuesta."""
        ...

    async def find(
        self, regulation_type: RegulationType, number: int, year: int
    ) -> list[Regulation]:
        """Devuelve las normas que coinciden (vacío si no existe; puede haber más de una,
        por ejemplo decretos del Poder Ejecutivo y de la Legislatura con el mismo número).

        Lanza RegulationLookupError si falla.
        """
        ...
