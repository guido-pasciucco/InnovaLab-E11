"""Modelos de la API de consultas.

El frontend consume camelCase en este contrato (a diferencia del resto de la API,
que habla snake_case): los campos de estos modelos se publican con alias camelCase.
"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


def camel_model() -> ConfigDict:
    return ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GeoPoint(BaseModel):
    model_config = camel_model()

    lat: float
    lng: float


class ConsultationRequest(BaseModel):
    """Lo que envía el formulario de consulta."""

    model_config = camel_model()

    activity: str = Field(min_length=2, max_length=200)
    address: str = Field(min_length=3, max_length=200)
    # Coordinates picked from the address suggestions; null when unknown.
    point: GeoPoint | None = None
    # Curated activity picked from the suggestions; null when the person kept free text.
    activity_slug: str | None = Field(
        default=None,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )


class SourceReference(BaseModel):
    model_config = camel_model()

    id: str
    title: str
    publisher: str
    url: str
    note: str | None = None
    retrieved_at: str | None = None


class GuidanceStep(BaseModel):
    model_config = camel_model()

    id: str
    title: str
    description: str
    documents: list[str] = []
    source_ids: list[str]


class TerritorialFeature(BaseModel):
    model_config = camel_model()

    id: str
    label: str
    description: str
    geometry: dict


class ConsultationResponse(BaseModel):
    model_config = camel_model()

    consultation_id: str
    interpreted_activity: str
    normalized_address: str
    point: GeoPoint | None
    summary: str
    steps: list[GuidanceStep]
    territorial_features: list[TerritorialFeature]
    sources: list[SourceReference]
    limitations: list[str]


class FollowUpRequest(BaseModel):
    model_config = camel_model()

    question: str = Field(min_length=1, max_length=500)


class FollowUpResponse(BaseModel):
    model_config = camel_model()

    answer: str
    source_ids: list[str]
    limitations: list[str] | None = None
