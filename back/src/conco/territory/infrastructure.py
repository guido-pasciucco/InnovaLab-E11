"""Adaptador de Territory: traduce USIG a los modelos del dominio."""

import asyncio

from conco.integrations.usig import client as usig
from conco.territory.domain import (
    APPROXIMATE_LOCATION_LIMITATION,
    NO_PARCELA_LIMITATION,
    REFERENCE_LIMITATIONS,
    SOURCE,
    Category,
    ParcelGeometry,
    Rubro,
    RubroReferences,
    TerritoryLookupError,
    UseTable,
)


class UsigTerritoryService:
    """Resuelve el cuadro de usos con Catastro y Ciudad 3D."""

    async def resolve_use_table(self, lat: float, lng: float) -> UseTable:
        """Una consulta de Catastro, una de mixtura, una de categorías y 10 de rubros."""
        try:
            parcela = await usig.get_parcela(lat, lng)
            if not parcela.smp:
                return UseTable(
                    smp=None,
                    official_address=None,
                    mix_area=None,
                    categories=[],
                    source=SOURCE,
                    limitations=[
                        APPROXIMATE_LOCATION_LIMITATION,
                        NO_PARCELA_LIMITATION,
                        *REFERENCE_LIMITATIONS,
                    ],
                )
            mix_area = await usig.get_mix_area(parcela.smp)
            categorias = await usig.list_categorias()
            rubros_por_categoria = await asyncio.gather(
                *(usig.list_rubros(categoria.id, mix_area) for categoria in categorias)
            )
        except usig.UsigError as exc:
            raise TerritoryLookupError(str(exc)) from exc

        return UseTable(
            smp=parcela.smp,
            official_address=parcela.address,
            mix_area=mix_area,
            categories=[
                Category(
                    id=categoria.id,
                    name=categoria.name,
                    rubros=[Rubro(id=rubro.id, name=rubro.name) for rubro in rubros],
                )
                for categoria, rubros in zip(categorias, rubros_por_categoria)
            ],
            source=SOURCE,
            limitations=[APPROXIMATE_LOCATION_LIMITATION, *REFERENCE_LIMITATIONS],
        )

    async def resolve_references(
        self, smp: str, categoria: int, mixtura: int, rubro: int
    ) -> RubroReferences:
        """Condiciones del rubro; la mixtura se deriva del SMP, no del query param.

        `mixtura` se mantiene en la firma por compatibilidad de contrato (S11).
        """
        try:
            derived_mixtura = await usig.get_mix_area(smp)
            referencias = await usig.get_referencias(categoria, derived_mixtura, rubro)
        except usig.UsigError as exc:
            raise TerritoryLookupError(str(exc)) from exc
        return RubroReferences(
            permitido_mixtura_de_usos=[
                item.detail for item in referencias.permitido_mixtura_de_usos
            ],
            bicicletas=[item.detail for item in referencias.bicicletas],
            estacionamientos=[item.detail for item in referencias.estacionamientos],
            cargaydescarga=[item.detail for item in referencias.cargaydescarga],
            observaciones=referencias.observaciones or None,
            source=SOURCE,
            limitations=[APPROXIMATE_LOCATION_LIMITATION, *REFERENCE_LIMITATIONS],
        )

    async def resolve_parcel_geometry(self, smp: str) -> ParcelGeometry:
        """Geometría de la parcela; `None` cuando USIG no devuelve features."""
        try:
            geometry = await usig.get_geometria(smp)
        except usig.UsigError as exc:
            raise TerritoryLookupError(str(exc)) from exc
        return ParcelGeometry(
            geometry=geometry,
            source=SOURCE,
            limitations=[APPROXIMATE_LOCATION_LIMITATION, *REFERENCE_LIMITATIONS],
        )


class UsigUseTableResolver:
    """Puerto `resolve()` para el cuadro: delega en el adaptador compartido."""

    def __init__(self, service: UsigTerritoryService | None = None) -> None:
        self._service = service or UsigTerritoryService()

    async def resolve(self, lat: float, lng: float) -> UseTable:
        return await self._service.resolve_use_table(lat, lng)


class UsigRubroReferencesResolver:
    """Puerto `resolve()` para las condiciones: delega en el adaptador compartido."""

    def __init__(self, service: UsigTerritoryService | None = None) -> None:
        self._service = service or UsigTerritoryService()

    async def resolve(
        self, smp: str, categoria: int, mixtura: int, rubro: int
    ) -> RubroReferences:
        return await self._service.resolve_references(smp, categoria, mixtura, rubro)


class UsigParcelGeometryResolver:
    """Puerto `resolve()` para la geometría: delega en el adaptador compartido."""

    def __init__(self, service: UsigTerritoryService | None = None) -> None:
        self._service = service or UsigTerritoryService()

    async def resolve(self, smp: str) -> ParcelGeometry:
        return await self._service.resolve_parcel_geometry(smp)
