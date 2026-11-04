"""Ejecuta el cliente del Boletín Oficial de la Ciudad e imprime las normas encontradas.

Uso:
    uv run python scripts/probes/boletin_oficial.py ley 6101 2018
    uv run python scripts/probes/boletin_oficial.py decreto 40 2019
"""

import asyncio
import sys

from conco.integrations.boletin_oficial.client import BoletinOficialNormType, find_norms

NORM_TYPES = {norm_type.name.lower(): norm_type for norm_type in BoletinOficialNormType}


async def main() -> None:
    args = sys.argv[1:] or ["ley", "6101", "2018"]
    if len(args) != 3 or args[0].lower() not in NORM_TYPES:
        sys.exit(f"Uso: boletin_oficial.py {{{'|'.join(NORM_TYPES)}}} <número> <año>")
    norms = await find_norms(NORM_TYPES[args[0].lower()], int(args[1]), int(args[2]))
    if not norms:
        print("Norma no encontrada.")
        return
    for norm in norms:
        print(norm.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
