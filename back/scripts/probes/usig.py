"""Ejecuta el cliente de USIG (datos útiles) e imprime la respuesta para observar su forma.

Uso:
    uv run python scripts/probes/usig.py Corrientes 2500
    uv run python scripts/probes/usig.py --coords -34.604792 -58.401981   # latitud longitud

El cliente solo modela los campos que usa CONCO. Para ver la respuesta completa:
    curl "https://ws.usig.buenosaires.gob.ar/datos_utiles?calle=Corrientes&altura=2500"
"""

import asyncio
import sys

from conco.integrations.usig.client import (
    get_datos_utiles_by_address,
    get_datos_utiles_by_coordinates,
)


async def main() -> None:
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "--coords":
        result = await get_datos_utiles_by_coordinates(
            longitude=float(args[2]), latitude=float(args[1])
        )
    else:
        street = " ".join(args[:-1]) if len(args) >= 2 else "Corrientes"
        number = int(args[-1]) if len(args) >= 2 else 2500
        result = await get_datos_utiles_by_address(street, number)
    print(result.model_dump_json(indent=2) if result else "Dirección no encontrada en CABA.")


if __name__ == "__main__":
    asyncio.run(main())
