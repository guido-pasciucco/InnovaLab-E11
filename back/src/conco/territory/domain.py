"""Modelos del dominio y puertos del cuadro de usos, sin depender de USIG."""

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class Rubro(BaseModel):
    """Rubro del cuadro de usos."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str


class Category(BaseModel):
    """Categoría con sus rubros."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    rubros: list[Rubro]


class TerritorySource(BaseModel):
    """Fuente oficial que se cita en la respuesta."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    publisher: str
    url: str


class ParcelGeometry(BaseModel):
    """Geometría oficial de la parcela para dibujar en el mapa."""

    model_config = ConfigDict(frozen=True)

    geometry: dict[str, Any] | None
    source: TerritorySource
    limitations: list[str]


class UseTable(BaseModel):
    """Cuadro de usos completo para la parcela de un punto."""

    model_config = ConfigDict(frozen=True)

    smp: str | None
    official_address: str | None
    mix_area: int | None
    categories: list[Category]
    source: TerritorySource
    limitations: list[str]


class RubroReferences(BaseModel):
    """Condiciones de un rubro, ya aplanadas a texto para la interfaz."""

    model_config = ConfigDict(frozen=True)

    permitido_mixtura_de_usos: list[str]
    bicicletas: list[str]
    estacionamientos: list[str]
    cargaydescarga: list[str]
    observaciones: str | None
    source: TerritorySource
    limitations: list[str]


SOURCE = TerritorySource(
    id="usig-ciudad-3d",
    title="Ciudad 3D — Cuadro de usos",
    publisher="USIG, Gobierno de la Ciudad de Buenos Aires",
    url="https://ciudad3d.buenosaires.gob.ar",
)

# RN-03: el punto se resuelve con Georef, así que la parcela es estimada.
APPROXIMATE_LOCATION_LIMITATION = (
    "La ubicación de la parcela proviene de Georef y es aproximada: el SMP puede "
    "corresponder a la parcela vecina o a la calle."
)
# RN-04: el cuadro es orientación general, no una determinación legal ni una
# confirmación catastral de lo que se puede hacer en el lote.
REFERENCE_LIMITATIONS = [
    "Información de referencia del cuadro de usos oficial: no acredita la zonificación del lote ni confirma que una actividad esté permitida."
]
NO_PARCELA_LIMITATION = "No se encontró la parcela para el punto consultado dentro de la Ciudad Autónoma de Buenos Aires."


class TerritoryLookupError(Exception):
    """La consulta a USIG falló o devolvió algo inesperado."""


class ParcelGeometryResolver(Protocol):
    """Puerto: devuelve la geometría oficial de una parcela por SMP."""

    async def resolve(self, smp: str) -> ParcelGeometry:
        """Devuelve la geometría; lanza TerritoryLookupError si USIG falla."""
        ...


class UseTableResolver(Protocol):
    """Puerto: resuelve el cuadro de usos a partir de un punto."""

    async def resolve(self, lat: float, lng: float) -> UseTable:
        """Devuelve el cuadro; lanza TerritoryLookupError si USIG falla."""
        ...


class RubroReferencesResolver(Protocol):
    """Puerto: devuelve las condiciones de un rubro del cuadro."""

    async def resolve(
        self, smp: str, categoria: int, mixtura: int, rubro: int
    ) -> RubroReferences:
        """Devuelve las referencias; lanza TerritoryLookupError si USIG falla."""
        ...
