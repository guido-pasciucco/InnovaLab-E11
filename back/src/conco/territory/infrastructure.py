"""Adaptador de Territory: traduce USIG a los modelos del dominio."""

import asyncio

from conco.integrations.usig import client as usig
from conco.territory.domain import (
    NO_PARCELA_LIMITATION,
    REFERENCE_LIMITATIONS,
    SOURCE,
    Category,
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
                    limitations=[NO_PARCELA_LIMITATION, *REFERENCE_LIMITATIONS],
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
            limitations=list(REFERENCE_LIMITATIONS),
        )

    async def resolve_references(
        self, smp: str, categoria: int, mixtura: int, rubro: int
    ) -> RubroReferences:
        """Condiciones del rubro; `smp` se acepta para el cliente pero USIG no lo usa."""
        try:
            referencias = await usig.get_referencias(categoria, mixtura, rubro)
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
            limitations=list(REFERENCE_LIMITATIONS),
        )
