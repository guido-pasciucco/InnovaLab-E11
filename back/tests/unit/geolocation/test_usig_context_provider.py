from pathlib import Path

import pytest
import respx

from conco.config import settings
from conco.geolocation.domain import AddressContext, AddressContextError, Source
from conco.geolocation.infrastructure import UsigAddressContextProvider

pytestmark = pytest.mark.anyio

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "usig"
DATOS_UTILES_URL = f"{settings.usig_base_url}/datos_utiles"


def respond_with_fixture(name: str, content_type: str) -> respx.Route:
    """Simula USIG devolviendo una respuesta real guardada en tests/fixtures/usig/."""
    return respx.get(DATOS_UTILES_URL).respond(
        200,
        content=(FIXTURES_DIR / name).read_bytes(),
        headers={"Content-Type": content_type},
    )


def test_source_cites_usig_with_its_license() -> None:
    assert UsigAddressContextProvider().source == Source(
        name="USIG - Datos útiles (Gobierno de la Ciudad de Buenos Aires)",
        url="http://usig.buenosaires.gob.ar/apis/",
        license="Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)",
    )


@respx.mock
async def test_maps_an_address_to_its_context() -> None:
    route = respond_with_fixture(
        "datos_utiles_corrientes_2500.json", "text/javascript; charset=utf-8"
    )

    context = await UsigAddressContextProvider().by_address("Corrientes", 2500)

    assert context == AddressContext(
        neighborhood="Balvanera",
        commune="Comuna 3",
        postal_code="1046",
        argentine_postal_code="C1046AAP",
    )
    assert dict(route.calls.last.request.url.params) == {
        "calle": "Corrientes",
        "altura": "2500",
    }


@respx.mock
async def test_does_not_expose_cadastre_or_zoning_fields() -> None:
    respond_with_fixture("datos_utiles_corrientes_2500.json", "text/javascript; charset=utf-8")

    context = await UsigAddressContextProvider().by_address("Corrientes", 2500)

    assert context is not None
    assert set(context.model_dump()) == {
        "neighborhood",
        "commune",
        "postal_code",
        "argentine_postal_code",
    }


@respx.mock
async def test_maps_coordinates_to_a_context_without_postal_codes() -> None:
    route = respond_with_fixture(
        "datos_utiles_coordenadas_corrientes_2500.json", "application/json; charset=utf-8"
    )

    context = await UsigAddressContextProvider().by_coordinates(
        latitude=-34.604792, longitude=-58.401981
    )

    assert context == AddressContext(
        neighborhood="Balvanera",
        commune="Comuna 3",
        postal_code=None,
        argentine_postal_code=None,
    )
    assert dict(route.calls.last.request.url.params) == {
        "x": "-58.401981",
        "y": "-34.604792",
    }


@respx.mock
async def test_unknown_address_returns_none() -> None:
    respond_with_fixture("datos_utiles_calle_inexistente.txt", "text/plain; charset=utf-8")

    assert await UsigAddressContextProvider().by_address("Calle Inexistente Xyz", 1234) is None


@respx.mock
async def test_point_outside_caba_returns_none() -> None:
    respond_with_fixture(
        "datos_utiles_coordenadas_fuera_de_caba.json", "application/json; charset=utf-8"
    )

    context = await UsigAddressContextProvider().by_coordinates(
        latitude=-34.6423652, longitude=-58.7567541
    )

    assert context is None


@respx.mock
async def test_usig_failure_raises_address_context_error() -> None:
    respx.get(DATOS_UTILES_URL).respond(500, text="Internal Server Error")

    with pytest.raises(AddressContextError):
        await UsigAddressContextProvider().by_address("Corrientes", 2500)

    with pytest.raises(AddressContextError):
        await UsigAddressContextProvider().by_coordinates(latitude=-34.6, longitude=-58.4)
