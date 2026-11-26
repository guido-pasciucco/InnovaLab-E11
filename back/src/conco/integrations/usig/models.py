"""Payloads crudos de USIG, con los nombres originales en español como alias."""

from pydantic import BaseModel, ConfigDict, Field


class UsigParcela(BaseModel):
    """Respuesta de /catastro/parcela/. Vacía si el punto cae fuera de CABA."""

    model_config = ConfigDict(populate_by_name=True)

    smp: str | None = None
    address: str | None = Field(default=None, alias="direccion")


class UsigMixtura(BaseModel):
    """Respuesta de /cur3d/mixtura_usos/: el primer valor es el área de mixtura."""

    model_config = ConfigDict(populate_by_name=True)

    uses: list[int] | None = Field(default=None, alias="usos")


class UsigCategoria(BaseModel):
    """Categoría del cuadro de usos."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str = Field(alias="nombre")


class UsigRubro(BaseModel):
    """Rubro dentro de una categoría del cuadro de usos."""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(alias="rubro_id")
    name: str = Field(alias="rubro")


class UsigRubrosResponse(BaseModel):
    """Los rubros vienen dentro de un objeto con totales, no como lista directa."""

    model_config = ConfigDict(populate_by_name=True)

    rubros: list[UsigRubro] = Field(default_factory=list)


class UsigDetalle(BaseModel):
    """Cada condición de una referencia viene como {"detalle": "..."}."""

    model_config = ConfigDict(populate_by_name=True)

    detail: str = Field(alias="detalle")


class UsigReferencias(BaseModel):
    """Respuesta de /cur3d/cuadrosdeuso/referencias/ para un rubro."""

    model_config = ConfigDict(populate_by_name=True)

    permitido_mixtura_de_usos: list[UsigDetalle] = Field(default_factory=list)
    bicicletas: list[UsigDetalle] = Field(default_factory=list)
    estacionamientos: list[UsigDetalle] = Field(default_factory=list)
    cargaydescarga: list[UsigDetalle] = Field(default_factory=list)
    observaciones: str | None = None
