# Testing

Cómo está organizado `tests/` y cómo funcionan los fixtures.

## Estrategia: dos capas

| Capa | Carpeta | Red | Cuándo corre |
|---|---|---|---|
| Unitarios | `tests/unit/<api>/` | No. HTTP mockeado con `respx` + fixtures | `uv run pytest` (default) |
| Integración | `tests/integration/<api>/` | Sí. Llama a la API real | `uv run pytest -m integration` (opt-in) |

La separación está en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib -m 'not integration'"
markers = ["integration: calls real external APIs (needs internet)"]
```

- Por defecto pytest **excluye** los tests marcados `integration`.
- Los tests async usan `anyio`/`asyncio`; `tests/conftest.py` fija `anyio_backend = "asyncio"`.

## tests/fixtures

`tests/fixtures/` **no son tests**: son datos. Contienen respuestas HTTP reales grabadas de las APIs externas, organizadas por proveedor:

```
tests/fixtures/georef/
├── direcciones_corrientes_2500.json   # respuesta exitosa con 1 resultado
├── direcciones_sin_altura.json        # dirección sin número → height.valor = null
├── direcciones_sin_resultados.json    # cantidad = 0
└── error_400_falta_direccion.json     # error 400 de la API
```

**Por qué existen:** los tests unitarios no pueden depender de internet ni de que la API externa esté disponible. Con `respx` se simula la respuesta HTTP, y el fixture garantiza que el mock devuelve **exactamente** lo que la API real devuelve — mismos campos, mismos `null`, mismas rarezas.

**Qué señal dan:** si la API externa cambia su formato, los tests unitarios siguen pasando (usan datos viejos) pero los de integración fallan, señalando que hay que actualizar fixtures y modelos.

## Cómo se usan los fixtures

En `tests/unit/georef/test_client.py`:

```python
FIXTURES_DIR = Path(__file__).parents[2] / "fixtures" / "georef"

def load_fixture(name: str):
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))

@respx.mock
async def test_...():
    respx.get(ADDRESSES_URL).respond(200, json=load_fixture("direcciones_corrientes_2500.json"))
    result = await search_addresses("Corrientes 2500")
    ...
```

`respx.mock` intercepta el `httpx.AsyncClient` dentro de `search_addresses` y responde con el fixture, como si fuera la red. El cliente nunca sabe que fue mockeado.

## Qué cubre cada test de Georef

| Test unitario | Escenario |
|---|---|
| `test_normalize_address_removes_extra_spaces` | Normalización de espacios en la query |
| `test_search_addresses_parses_a_full_result` | Parsing completo del fixture real (campos, coords con `pytest.approx`) |
| `test_search_addresses_sends_normalized_query_params` | Params enviados: `direccion` normalizada, `provincia=caba`, `max=5` |
| `test_search_addresses_without_results_returns_empty_list` | `cantidad=0` → `addresses == []` |
| `test_search_addresses_street_without_number_has_no_height` | Dirección sin número → `height.value is None` |
| `test_search_addresses_http_error_raises_georef_error` | HTTP 400 → `GeorefError` |
| `test_search_addresses_timeout_raises_georef_error` | Timeout → `GeorefError` |
| `test_search_addresses_unexpected_payload_raises_georef_error` | JSON con shape inesperado → `GeorefError` |
| `test_search_addresses_non_json_body_raises_georef_error` | Body HTML → `GeorefError` |

| Test de integración | Qué verifica |
|---|---|
| `test_search_addresses_against_real_georef` | Respuesta real: `count >= 1`, comuna "Comuna 3", coords dentro de rangos esperados |

## Cómo agregar tests para una API nueva

1. Guardar respuestas reales en `tests/fixtures/<api>/` (obtenidas con el probe o curl).
2. Escribir tests unitarios en `tests/unit/<api>/test_client.py` con `respx` + fixtures.
3. Escribir un test de integración en `tests/integration/<api>/test_client.py` marcado con `pytest.mark.integration`.
4. Verificar: `uv run pytest` corre los unitarios; `uv run pytest -m integration` corre los de integración.
