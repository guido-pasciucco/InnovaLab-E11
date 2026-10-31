from pydantic import BaseModel, ConfigDict, Field


class EpokPlace(BaseModel):
    """Un lugar de `reverseGeocoderLugares`, solo con los campos que usa CONCO.

    EPOK informa la distancia en metros como texto (`"962.53"`); Pydantic la convierte a número.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str = Field(alias="nombre")
    distance_meters: float = Field(alias="distancia")


class EpokNearbyPlaces(BaseModel):
    """Respuesta de `reverseGeocoderLugares`. Sin resultados, `instancias` llega vacía."""

    model_config = ConfigDict(populate_by_name=True)

    places: list[EpokPlace] = Field(alias="instancias")


class EpokContentField(BaseModel):
    """Un dato del contenido de un lugar, identificado por `nombreId` (por ejemplo, `direccion`)."""

    model_config = ConfigDict(populate_by_name=True)

    field_id: str = Field(alias="nombreId")
    value: str = Field(alias="valor")


class EpokObjectContent(BaseModel):
    """Respuesta de `getObjectContent`, solo con los campos que usa CONCO.

    La respuesta trae además la ubicación (`ubicacion.centroide`) en coordenadas GKBA, no WGS84;
    no se usa.
    """

    model_config = ConfigDict(populate_by_name=True)

    fields: list[EpokContentField] = Field(alias="contenido")
    last_modified: str | None = Field(default=None, alias="fechaUltimaModificacion")
    normalized_address: str | None = Field(default=None, alias="direccionNormalizada")

    def value(self, field_id: str) -> str | None:
        """Devuelve el valor de un dato sin espacios sobrantes, o None si falta o está vacío."""
        for field in self.fields:
            if field.field_id == field_id:
                return field.value.strip() or None
        return None
