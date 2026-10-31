"""Ejecuta el cliente de Georef e imprime la respuesta para observar su forma.

Uso: uv run python scripts/probe_georef.py "Corrientes 2500"
"""

import asyncio
import sys

from conco.integrations.georef.client import search_addresses


async def main() -> None:
    address = sys.argv[1] if len(sys.argv) > 1 else "Corrientes 2500"
    result = await search_addresses(address)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
