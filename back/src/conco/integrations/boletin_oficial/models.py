from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# El Boletín escribe las fechas como día/mes/año.
_DATE_FORMAT = "%d/%m/%Y"


def to_https(url: str) -> str:
    """Los enlaces de descarga llegan como http:// y redirigen a https://: se usa https."""
    if url.startswith("http://"):
        return "https://" + url.removeprefix("http://")
    return url


def _parse_date(value: Any) -> Any:
    if isinstance(value, str):
        return datetime.strptime(value, _DATE_FORMAT).date()
    return value


class BoletinOficialBulletin(BaseModel):
    """Edición del Boletín en la que se publicó la norma.

    La API la envía como arreglo: `["5526", "27/12/2018", "http://.../download/1255814"]`.
    """

    bulletin_number: int
    publication_date: date
    url: str

    @model_validator(mode="before")
    @classmethod
    def _from_array(cls, value: Any) -> Any:
        if isinstance(value, list | tuple) and len(value) == 3:
            number, published, url = value
            return {"bulletin_number": number, "publication_date": published, "url": url}
        return value

    @field_validator("publication_date", mode="before")
    @classmethod
    def _date(cls, value: Any) -> Any:
        return _parse_date(value)

    @field_validator("url")
    @classmethod
    def _https(cls, value: str) -> str:
        return to_https(value)


class BoletinOficialDocument(BaseModel):
    """Documento (PDF) de la norma: `["27/12/2018", "http://.../download/1255476"]`.

    En normas antiguas el enlace llega vacío (`""`): queda en None.
    """

    publication_date: date
    url: str | None

    @model_validator(mode="before")
    @classmethod
    def _from_array(cls, value: Any) -> Any:
        if isinstance(value, list | tuple) and len(value) == 2:
            published, url = value
            return {"publication_date": published, "url": url}
        return value

    @field_validator("publication_date", mode="before")
    @classmethod
    def _date(cls, value: Any) -> Any:
        return _parse_date(value)

    @field_validator("url")
    @classmethod
    def _https(cls, value: str | None) -> str | None:
        return to_https(value) if value else None


class BoletinOficialNorm(BaseModel):
    """Una norma publicada, tal como la devuelve `/obtenerResultado`."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    type_name: str = Field(alias="nombre_tipo")
    number: int = Field(alias="numero_norma")
    # Año con dos dígitos (2018 → 18), aunque el filtro de búsqueda exige cuatro.
    short_year: int = Field(alias="anio_norma")
    summary: str = Field(alias="sumario")
    issuing_body: str | None = Field(alias="nombre_reparticion")
    bulletins: list[BoletinOficialBulletin] = Field(alias="boletines", min_length=1)
    documents: list[BoletinOficialDocument] = Field(alias="link_documento_normas", min_length=1)


class BoletinOficialResults(BaseModel):
    """Respuesta de `/obtenerResultado`. Sin resultados, `normas` es el número 0."""

    norms: list[BoletinOficialNorm] | Literal[0] = Field(alias="normas")
