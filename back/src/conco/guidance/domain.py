from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

REQUIREMENTS_NOTE = (
    "Fuente oficial: páginas de los trámites. Es una orientación general; "
    "verificá siempre con el organismo."
)


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


class RequirementOrigin(BaseModel):
    """Official procedure a consolidated requirement comes from (RN-05)."""

    model_config = ConfigDict(frozen=True)

    procedure_id: UUID
    procedure_title: str
    official_url: str


class Requirement(BaseModel):
    """Official requirement consolidated across the procedures that publish it."""

    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    heading: str | None
    origins: list[RequirementOrigin]


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


class ContextAnswers(BaseModel):
    """Lo que la persona contó de su comercio; None significa que no respondió.

    Cada campo es una pregunta de contexto y su descripción es el texto que se le muestra.
    Las condiciones del archivo curado usan los mismos campos.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    has_employees: bool | None = Field(default=None, description="¿Vas a contratar personal?")
    under_200_m2: bool | None = Field(
        default=None, description="¿El local tiene menos de 200 m²?"
    )
    sidewalk_tables: bool | None = Field(
        default=None, description="¿Vas a poner mesas y sillas en la vereda?"
    )
    signage: bool | None = Field(
        default=None, description="¿Vas a poner un cartel, una marquesina o un toldo?"
    )
    protected_building: bool | None = Field(
        default=None,
        description="¿El inmueble está en un área de protección histórica (APH) o está catalogado?",
    )
    takes_over_existing: bool | None = Field(
        default=None, description="¿Vas a continuar un local que ya está habilitado?"
    )

    def answered(self) -> dict[str, bool]:
        return self.model_dump(exclude_none=True)


class ApplicableProcedure(BaseModel):
    """Trámite que suele aplicar a una actividad, en qué caso aplica y con qué condiciones."""

    model_config = ConfigDict(frozen=True)

    procedure: Procedure
    note: str
    # Respuestas que tiene que tener el contexto para que el trámite aplique; vacío = siempre.
    applies_when: ContextAnswers = ContextAnswers()


class ActivityProcedures(BaseModel):
    """Trámites curados de una actividad, en el orden en que conviene revisarlos."""

    model_config = ConfigDict(frozen=True)

    activity: Activity
    procedures: list[ApplicableProcedure]
    requirements: list[Requirement] = Field(default_factory=list)
    requirements_note: str = REQUIREMENTS_NOTE


class ContextQuestion(BaseModel):
    """Pregunta de contexto que afina los trámites de una actividad, con la respuesta dada."""

    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    answer: bool | None


class ContextualProcedure(BaseModel):
    """Trámite que sigue en pie según el contexto.

    `applies`: no tiene condiciones o todas se cumplen. `may_apply`: falta responder alguna.
    """

    model_config = ConfigDict(frozen=True)

    procedure: Procedure
    note: str
    status: Literal["applies", "may_apply"]


class ExcludedProcedure(BaseModel):
    """Trámite descartado porque sus condiciones contradicen las respuestas de contexto."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    title: str
    # Context questions whose answer contradicts the procedure, in question order.
    because: list[str] = Field(default_factory=list)


class ContextualProcedures(BaseModel):
    """Trámites de una actividad afinados con el contexto que dio la persona."""

    model_config = ConfigDict(frozen=True)

    activity: Activity
    questions: list[ContextQuestion]
    procedures: list[ContextualProcedure]
    excluded_count: int
    # Trámites descartados, en el orden del catálogo, para poder nombrarlos en pantalla.
    excluded: list[ExcludedProcedure] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    requirements_note: str = REQUIREMENTS_NOTE


def apply_context(result: ActivityProcedures, answers: ContextAnswers) -> ContextualProcedures:
    """Descarta los trámites cuyas condiciones contradicen las respuestas.

    Solo se preguntan las condiciones que usa esta actividad, en el orden de ContextAnswers.
    """
    given = answers.answered()
    procedures: list[ContextualProcedure] = []
    excluded: list[ExcludedProcedure] = []
    for applicable in result.procedures:
        conditions = applicable.applies_when.answered()
        because = [
            key
            for key in ContextAnswers.model_fields
            if key in conditions and key in given and given[key] != conditions[key]
        ]
        if because:
            excluded.append(
                ExcludedProcedure(
                    id=applicable.procedure.id, title=applicable.procedure.title, because=because
                )
            )
            continue
        status = "applies" if conditions.keys() <= given.keys() else "may_apply"
        procedures.append(
            ContextualProcedure(
                procedure=applicable.procedure, note=applicable.note, status=status
            )
        )
    used = {key for applicable in result.procedures for key in applicable.applies_when.answered()}
    questions = [
        ContextQuestion(id=key, text=field.description or key, answer=getattr(answers, key))
        for key, field in ContextAnswers.model_fields.items()
        if key in used
    ]
    return ContextualProcedures(
        activity=result.activity,
        questions=questions,
        procedures=procedures,
        excluded_count=len(excluded),
        excluded=excluded,
        requirements=result.requirements,
        requirements_note=result.requirements_note,
    )


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

    async def catalog_ready(self) -> bool:
        """Indica si el catálogo de actividades ya está cargado; lanza ActivityDirectoryError
        si la base no responde."""
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
