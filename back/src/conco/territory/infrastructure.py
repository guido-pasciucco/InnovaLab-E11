"""Adaptador de Territory: traduce USIG a los modelos del dominio."""

import asyncio

from conco.integrations.usig import client as usig
from conco.integrations.usig.models import UsigParcela
from conco.territory.domain import (
    ADDRESS_RESOLVED_LIMITATION,
    APPROXIMATE_LOCATION_LIMITATION,
    NO_PARCELA_BY_ADDRESS_LIMITATION,
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

    async def resolve_use_table(
        self, lat: float, lng: float, address: str | None = None
    ) -> UseTable:
        """Punto primero; sólo sin SMP y con dirección se intenta el fallback (S14)."""
        resolved_from_address = False
        try:
            parcela = await usig.get_parcela(lat, lng)
            if not parcela.smp and address:
                parcela = await self._parcela_from_address(address)
                resolved_from_address = parcela is not None and parcela.smp is not None
            if not parcela or not parcela.smp:
                limitations = [APPROXIMATE_LOCATION_LIMITATION, NO_PARCELA_LIMITATION]
                if address:
                    limitations.append(NO_PARCELA_BY_ADDRESS_LIMITATION)
                limitations.extend(REFERENCE_LIMITATIONS)
                return UseTable(
                    smp=None,
                    official_address=None,
                    mix_area=None,
                    categories=[],
                    source=SOURCE,
                    limitations=limitations,
                )
            mix_area = await usig.get_mix_area(parcela.smp)
            categorias = await usig.list_categorias()
            rubros_por_categoria = await asyncio.gather(
                *(usig.list_rubros(categoria.id, mix_area) for categoria in categorias)
            )
        except usig.UsigError as exc:
            raise TerritoryLookupError(str(exc)) from exc

        limitations = [APPROXIMATE_LOCATION_LIMITATION]
        if resolved_from_address:
            limitations.append(ADDRESS_RESOLVED_LIMITATION)
        limitations.extend(REFERENCE_LIMITATIONS)
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
            limitations=limitations,
        )

    async def _parcela_from_address(self, address: str) -> UsigParcela | None:
        """Normaliza y toma la primera dirección de CABA; sin ella devuelve None."""
        normalized = await usig.normalize_address(address)
        for item in normalized:
            if (
                (item.partido or "").lower() == "caba"
                and item.street_code is not None
                and item.number is not None
            ):
                return await usig.get_parcela_by_address(item.street_code, item.number)
        return None

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

    async def resolve(
        self, lat: float, lng: float, address: str | None = None
    ) -> UseTable:
        return await self._service.resolve_use_table(lat, lng, address)


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
