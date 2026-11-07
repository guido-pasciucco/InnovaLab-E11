"""Ejecuta el cliente de trámites de la Ciudad e imprime la respuesta para observar su forma.

Uso:
    uv run python scripts/probes/caba_tramites.py habilitaci
    uv run python scripts/probes/caba_tramites.py --id 338718b4-a2a0-44af-baa4-083f5d834b12
"""

import asyncio
import sys
from uuid import UUID

from conco.integrations.caba_tramites.client import get_procedure, search_procedures


async def main() -> None:
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--id":
        detail = await get_procedure(UUID(args[1]))
        print(detail.model_dump_json(indent=2) if detail else "Trámite no encontrado.")
        return
    query = args[0] if args else "habilitaci"
    result = await search_procedures(query)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
