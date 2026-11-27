"""Consultas a la API de USIG (GeoEPOK).

Todas las rutas llevan barra final y la cabecera User-Agent configurada: sin ella
el servidor corta la conexión. Los payloads vienen en español y se validan con los
modelos de `conco.integrations.usig.models`.
"""

import json
from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError

from conco.config import settings
from conco.integrations.usig.cache import CacheKey, UsigCache
from conco.integrations.usig.models import (
    UsigCategoria,
    UsigDireccionNormalizada,
    UsigGeometriaResponse,
    UsigMixtura,
    UsigNormalizarResponse,
    UsigParcela,
    UsigReferencias,
    UsigRubro,
    UsigRubrosResponse,
)

PARCELA_PATH = "/catastro/parcela/"
MIXTURA_PATH = "/cur3d/mixtura_usos/"
CATEGORIAS_PATH = "/cur3d/categorias/"
RUBROS_PATH = "/cur3d/cuadrosdeuso/rubros/"
REFERENCIAS_PATH = "/cur3d/cuadrosdeuso/referencias/"
GEOMETRIA_PATH = "/catastro/geometria/"
# S14: otra host, misma ruta; el host entra en la clave de caché para no mezclarlos.
NORMALIZAR_PATH = "/normalizar/"
CATASTRO_API_PARCELA_PATH = "/catastro/parcela/"


class UsigError(Exception):
    """USIG no está disponible o devolvió una respuesta inesperada."""


_PARCELA = TypeAdapter(UsigParcela)
_MIXTURA = TypeAdapter(UsigMixtura)
_CATEGORIAS = TypeAdapter(list[UsigCategoria])
_RUBROS = TypeAdapter(UsigRubrosResponse)
_REFERENCIAS = TypeAdapter(UsigReferencias)
_GEOMETRIA = TypeAdapter(UsigGeometriaResponse)
_NORMALIZAR = TypeAdapter(UsigNormalizarResponse)

# S8: una sola caché por proceso, compartida por todos los clientes USIG.
_CACHE = UsigCache()


def clear_usig_cache() -> None:
    """Vacía la caché USIG (tests y reinicios de configuración)."""
    _CACHE.clear()


def _client(base_url: str | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url or settings.usig_base_url,
        timeout=settings.usig_timeout_seconds,
        headers={"User-Agent": settings.usig_user_agent},
    )


def _parse[T](content: bytes, adapter: TypeAdapter[T]) -> T:
    try:
        payload = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UsigError("USIG devolvió una respuesta que no es JSON.") from exc
    # Un SMP inválido puede responderse con HTTP 200 y un cuerpo {"error": ...}.
    if isinstance(payload, dict) and payload.get("error"):
        raise UsigError(f"USIG devolvió un error: {payload['error']}")
    try:
        return adapter.validate_python(payload)
    except ValidationError as exc:
        raise UsigError("USIG devolvió una respuesta inesperada.") from exc


async def _request[T](
    path: str,
    params: dict[str, object],
    adapter: TypeAdapter[T],
    base_url: str | None = None,
) -> T:
    host = base_url or settings.usig_base_url
    key: CacheKey = (f"{host}{path}", tuple(sorted(params.items())))

    async def loader() -> T:
        try:
            async with _client(host) as client:
                response = await client.get(path, params=params)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise UsigError(f"No se pudo consultar USIG: {exc}") from exc
        return _parse(response.content, adapter)

    return await _CACHE.get_or_set(key, loader)


async def get_parcela(lat: float, lng: float) -> UsigParcela:
    """Resuelve la parcela de un punto; sin SMP significa que cayó fuera de CABA."""
    return await _request(PARCELA_PATH, {"lng": lng, "lat": lat}, _PARCELA)


async def normalize_address(address: str) -> list[UsigDireccionNormalizada]:
    """Normaliza una dirección; sin calle conocida USIG responde una lista vacía.

    La nomenclatura de Georef incluye ", Comuna N, Ciudad Autónoma…" y USIG la
    rechaza como calle inexistente; se envía sólo calle y altura.
    """
    query = " ".join(address.split(",", 1)[0].split())
    data = await _request(
        NORMALIZAR_PATH,
        {"direccion": query, "geocodificar": "true", "srid": 4326},
        _NORMALIZAR,
        base_url=settings.usig_normalize_base_url,
    )
    if data.error_message:
        return []
    return data.direcciones


async def get_parcela_by_address(cod_calle: int, altura: int) -> UsigParcela | None:
    """Resuelve la parcela con el código de calle y la altura que devolvió USIG."""
    parcela = await _request(
        CATASTRO_API_PARCELA_PATH,
        {
            "codigo_calle": cod_calle,
            "altura": altura,
            "geocodificar": "true",
            "srid": 4326,
        },
        _PARCELA,
        base_url=settings.usig_catastro_api_base_url,
    )
    return parcela if parcela.smp else None


async def get_mix_area(smp: str) -> int:
    """Devuelve el área de mixtura de usos (primer valor de `usos`)."""
    data = await _request(MIXTURA_PATH, {"smp": smp}, _MIXTURA)
    if not data.uses:
        raise UsigError("USIG no devolvió el área de mixtura para el SMP indicado.")
    return data.uses[0]


async def list_categorias() -> list[UsigCategoria]:
    """Devuelve las 10 categorías del cuadro de usos."""
    return await _request(CATEGORIAS_PATH, {}, _CATEGORIAS)


async def list_rubros(categoria: int, mixtura: int) -> list[UsigRubro]:
    """Devuelve los rubros de una categoría para el área de mixtura indicada."""
    data = await _request(
        RUBROS_PATH, {"categoria": categoria, "mixtura": mixtura}, _RUBROS
    )
    return data.rubros


async def get_referencias(
    categoria: int, mixtura: int, rubro: int
) -> UsigReferencias:
    """Devuelve las condiciones del rubro; no hay endpoint bulk para las 401 referencias."""
    return await _request(
        REFERENCIAS_PATH,
        {"categoria": categoria, "mixtura": mixtura, "rubro": rubro},
        _REFERENCIAS,
    )


async def get_geometria(smp: str) -> dict[str, Any] | None:
    """Devuelve la geometría del primer feature, o None si no hay features."""
    data = await _request(GEOMETRIA_PATH, {"smp": smp}, _GEOMETRIA)
    if not data.features:
        return None
    return data.features[0].geometry
