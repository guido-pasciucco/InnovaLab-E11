# PR 02/09 — Integración de Georef (feature/02-georef-integration → feature/01-backend-setup)

**GitHub:** PR #63 — [chained 02/09] feat(back): integrate Georef address geocoding

**En una frase:** Conectó el backend con Georef (datos.gob.ar) para buscar direcciones, con un cliente propio, modelos tipados, un único tipo de error y pruebas con copias de respuestas reales.

## Qué se hace

1. Creó un cliente dedicado para hablar con el endpoint /direcciones de Georef.
2. Normaliza la dirección antes de enviarla y solicita solo una tanda chica de resultados.
3. Definió modelos Pydantic que traducen los campos de la API al idioma del proyecto (por ejemplo, calle → street).
4. Captura cualquier fallo de red o respuesta inesperada y lo devuelve como un único GeorefError.
5. Guardó copias de respuestas reales para probar sin consultar la API, dejó un script de consulta manual y documentó los datos del proveedor en .env.example.

## Secciones de código importantes

**Cliente de Georef** — `back/src/conco/integrations/georef/client.py` (líneas 1-14 y 17-27):

```python
import httpx
from pydantic import ValidationError

from conco.config import settings
from conco.integrations.georef.models import GeorefAddressesResponse


class GeorefError(Exception):
    """Georef no está disponible o devolvió una respuesta inesperada."""


def normalize_address(address: str) -> str:
    """Quita los espacios sobrantes de una dirección antes de enviarla a Georef."""
    return " ".join(address.split())
...
async def search_addresses(
    address: str,
    province: str = "caba",
    max_results: int = 5,
) -> GeorefAddressesResponse:
    """Consulta el endpoint /direcciones de Georef y devuelve la respuesta tipada."""
    params = {
        "direccion": normalize_address(address),
        "provincia": province,
        "max": max_results,
    }
```

Aquí se arma el pedido (dirección limpia, provincia, cantidad de resultados) y se declara el único tipo de error del cliente.

**Modelos de respuesta** — `back/src/conco/integrations/georef/models.py` (líneas 35-49):

```python
class GeorefAddress(BaseModel):
    """Una dirección normalizada devuelta por Georef."""

    model_config = ConfigDict(populate_by_name=True)

    nomenclature: str = Field(alias="nomenclatura")
    street: GeorefStreet = Field(alias="calle")
    height: GeorefHeight = Field(alias="altura")
    cross_street_1: GeorefStreet = Field(alias="calle_cruce_1")
    cross_street_2: GeorefStreet = Field(alias="calle_cruce_2")
    department: GeorefNamedEntity = Field(alias="departamento")
    census_locality: GeorefNamedEntity = Field(alias="localidad_censal")
    province: GeorefNamedEntity = Field(alias="provincia")
    floor: str | None = Field(default=None, alias="piso")
    location: GeorefCoordinates | None = Field(default=None, alias="ubicacion")
```

Adentro se usa street, la API dice calle: el modelo anota ambos nombres para traducir automáticamente.

**Manejo de errores** — `back/src/conco/integrations/georef/client.py` (líneas 36-39):

```python
    except httpx.HTTPError as exc:
        raise GeorefError(f"No se pudo consultar Georef: {exc}") from exc
    except ValidationError as exc:
        raise GeorefError("Georef devolvió una respuesta inesperada.") from exc
```

Cualquier fallo llega al resto del proyecto como el mismo GeorefError.

**Configuración del proveedor** — `back/.env.example` (líneas 7-9):

```ini
# Georef (Gobierno Nacional): normalización y geocodificación de direcciones.
GEOREF_BASE_URL=https://apis.datos.gob.ar/georef/api
GEOREF_TIMEOUT_SECONDS=10
```

La URL base y el tiempo de espera se configuran desde fuera del código.

**Pruebas con copia real** — `back/tests/unit/georef/test_client.py` (líneas 31-46):

```python
@respx.mock
async def test_search_addresses_parses_a_full_result() -> None:
    respx.get(ADDRESSES_URL).respond(
        200, json=load_fixture("direcciones_corrientes_2500.json")
    )

    result = await search_addresses("Corrientes 2500")

    assert result.count == 1
    address = result.addresses[0]
    assert address.nomenclature.startswith("AV CORRIENTES 2500")
    assert address.department.name == "Comuna 3"
    assert address.height.value == 2500
    assert address.location is not None
    assert address.location.lat == pytest.approx(-34.6047137500375)
    assert address.location.lon == pytest.approx(-58.402137170712)
```

La prueba valida el armado completo de una respuesta sin depender de que la API esté disponible.

## Por qué importa en la cadena

Con este PR suma el primer proveedor externo de direcciones, con reglas claras de error y espera. Deja el buscador listo para ser expuesto al público: el siguiente PR lo expone a través de una ventana pública.