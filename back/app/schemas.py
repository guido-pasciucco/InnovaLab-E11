from pydantic import BaseModel, Field


class ActivityQuery(BaseModel):
    """Datos generales de una consulta por actividad."""

    activity: str = Field(
        min_length=2,
        max_length=120,
        description="Actividad económica que se quiere consultar.",
        examples=["cafetería"],
    )
    locality: str | None = Field(
        default=None,
        max_length=120,
        description="Localidad o jurisdicción general, si se conoce.",
    )
    has_existing_premises: bool | None = Field(
        default=None,
        description="Indica si el usuario ya dispone de un local.",
    )


class GuidanceItem(BaseModel):
    """Elemento informativo general; no es una decisión oficial."""

    title: str
    description: str
    official_source_url: str | None = None
