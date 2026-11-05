from pydantic import BaseModel, ConfigDict, Field


class UsigDatosUtiles(BaseModel):
    """Respuesta de `datos_utiles` de USIG, solo con los campos que usa CONCO.

    La respuesta trae además comisaría, área hospitalaria, distrito escolar y datos de
    catastro y planeamiento (`seccion_catastral`, `codigo_de_planeamiento_urbano`).
    Estos últimos quedan fuera a propósito: CONCO no informa zonificación ni catastro (RN-04).
    Los códigos postales solo vienen cuando la consulta es por calle y altura.
    """

    model_config = ConfigDict(populate_by_name=True)

    commune: str = Field(alias="comuna")
    neighborhood: str = Field(alias="barrio")
    postal_code: str | None = Field(default=None, alias="codigo_postal")
    argentine_postal_code: str | None = Field(default=None, alias="codigo_postal_argentino")
