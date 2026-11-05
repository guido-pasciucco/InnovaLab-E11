from datetime import datetime
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


class Activity(BaseModel):
    """Actividad comercial curada, por ejemplo «Cafetería»."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str


class ActivitySuggestion(Activity):
    """Actividad parecida al texto que escribió la persona, con qué tan parecida es."""

    matched_alias: str
    similarity: float


class ApplicableProcedure(BaseModel):
    """Trámite que suele aplicar a una actividad y en qué caso aplica."""

    model_config = ConfigDict(frozen=True)

    procedure: Procedure
    note: str


class ActivityProcedures(BaseModel):
    """Trámites curados de una actividad, en el orden en que conviene revisarlos."""

    model_config = ConfigDict(frozen=True)

    activity: Activity
    procedures: list[ApplicableProcedure]


class ActivityDirectoryError(Exception):
    """La base de actividades no está disponible."""


class ActivityDirectory(Protocol):
    """Puerto: relaciona lo que la persona quiere hacer con actividades y sus trámites."""

    async def suggest(self, query: str, limit: int) -> list[ActivitySuggestion]:
        """Actividades más parecidas al texto; lanza ActivityDirectoryError si falla."""
        ...

    async def procedures_for(self, slug: str) -> ActivityProcedures | None:
        """Trámites curados de la actividad, o None si no existe; lanza ActivityDirectoryError si falla."""
        ...


class TextEmbedder(Protocol):
    """Puerto: convierte textos en vectores que se pueden comparar por significado."""

    @property
    def model_name(self) -> str:
        """Modelo que generó los vectores; solo se comparan vectores del mismo modelo."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Un vector por texto, en el mismo orden."""
        ...
