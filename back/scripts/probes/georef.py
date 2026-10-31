"""Ejecuta el cliente de Georef e imprime la respuesta para observar su forma.

Uso:
    uv run python scripts/probes/georef.py "Corrientes 2500"
    uv run python scripts/probes/georef.py --locate -34.6047137 -58.4021372
"""

import asyncio
import sys

from conco.integrations.georef.client import locate, search_addresses


async def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--locate":
        location = await locate(latitude=float(sys.argv[2]), longitude=float(sys.argv[3]))
        print(location.model_dump_json(indent=2))
        return
    address = sys.argv[1] if len(sys.argv) > 1 else "Corrientes 2500"
    result = await search_addresses(address)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
