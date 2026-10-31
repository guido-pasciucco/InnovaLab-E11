"""Ejecuta el cliente de EPOK (lugares de la Ciudad) e imprime la respuesta para observar su forma.

Uso:
    uv run python scripts/probes/epok.py -34.6047137 -58.4021372         # latitud longitud
    uv run python scripts/probes/epok.py -34.6047137 -58.4021372 1000    # radio en metros

Busca sedes comunales cercanas y muestra el contenido de la más cercana. EPOK corta la conexión
con el User-Agent por defecto de curl; para ver la respuesta completa con curl, enviá otro:
    curl -A "CONCO/0.1" "https://epok.buenosaires.gob.ar/reverseGeocoderLugares/?x=-58.4021372&y=-34.6047137&categorias=sedes_de_comunas&radio=3000"
"""

import asyncio
import sys

from conco.config import settings
from conco.integrations.epok.client import COMMUNE_OFFICES_CATEGORY, find_nearby, get_object


async def main() -> None:
    args = sys.argv[1:]
    latitude = float(args[0]) if len(args) >= 2 else -34.6047137
    longitude = float(args[1]) if len(args) >= 2 else -58.4021372
    radius = int(args[2]) if len(args) >= 3 else settings.epok_radius_meters
    places = await find_nearby(
        longitude=longitude,
        latitude=latitude,
        categories=[COMMUNE_OFFICES_CATEGORY],
        radius_meters=radius,
    )
    if not places:
        print("No hay sedes comunales en el radio indicado.")
        return
    for place in places:
        print(f"{place.distance_meters:>9.2f} m  {place.name}  ({place.id})")
    content = await get_object(places[0].id)
    print(content.model_dump_json(indent=2) if content else "Lugar sin contenido en EPOK.")


if __name__ == "__main__":
    asyncio.run(main())
