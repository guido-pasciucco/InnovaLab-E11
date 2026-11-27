"""Caché TTL/LRU en memoria para las respuestas GET exitosas de USIG.

La clave es `(path, params ordenados)`, así dos consultas equivalentes con distinto
orden de parámetros comparten entrada. Los errores nunca se guardan: el loader se
ejecuta fuera del lock y sólo se almacena su valor si termina sin lanzar.
"""

import asyncio
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from conco.config import settings

T = TypeVar("T")

CacheKey = tuple[str, tuple[tuple[str, object], ...]]


class UsigCache:
    """Caché acotada con expiración temporal y desalojo least-recently-used."""

    def __init__(self) -> None:
        self._entries: OrderedDict[CacheKey, tuple[float, Any]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_or_set(self, key: CacheKey, loader: Callable[[], Awaitable[T]]) -> T:
        """Devuelve el valor cacheado si está fresco; si no, carga y guarda."""
        now = time.monotonic()
        async with self._lock:
            entry = self._entries.get(key)
            if entry is not None:
                if now - entry[0] < settings.usig_cache_ttl_seconds:
                    self._entries.move_to_end(key)
                    return cast(T, entry[1])
                del self._entries[key]

        # Fuera del lock: no serializa las consultas concurrentes ni guarda errores.
        value = await loader()

        async with self._lock:
            self._entries[key] = (time.monotonic(), value)
            self._entries.move_to_end(key)
            while len(self._entries) > settings.usig_cache_max_entries:
                self._entries.popitem(last=False)
        return value

    def clear(self) -> None:
        """Descarta todas las entradas; lo usan los tests para aislarse."""
        self._entries.clear()
