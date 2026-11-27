"""Aislamiento: la caché USIG es global al proceso, se limpia antes de cada test."""

import pytest

from conco.integrations.usig.client import clear_usig_cache


@pytest.fixture(autouse=True)
def isolated_usig_cache() -> None:
    """Evita que una respuesta cacheada en un test filtre al siguiente."""
    clear_usig_cache()
