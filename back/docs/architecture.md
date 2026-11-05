# Backend — Arquitectura

Cómo está organizado `back/` y qué hace cada sección. Pensado para quien entra al código sin contexto previo.

## Stack

| Pieza | Rol |
|---|---|
| FastAPI | Framework HTTP. La app se crea en `src/conco/main.py`. |
| Pydantic v2 | Validación de datos de entrada/salida y modelado de respuestas externas. |
| pydantic-settings | Lee variables de entorno / `.env` con tipos (`config.py`). |
| httpx | Cliente HTTP async para consumir APIs externas. |
| uv | Package manager y entorno virtual (`uv.lock`, `.venv`). |
| pytest + respx | Tests unitarios que mockean HTTP sin internet. |

## Estructura

```
back/
├── pyproject.toml            # dependencias, toolchain uv, config de pytest
├── README.md                 # guía general del backend
├── scripts/
│   └── probes/
│       └── georef.py         # script manual para probar la integración real
├── src/
│   └── conco/                # paquete principal (src layout)
│       ├── __init__.py
│       ├── main.py           # instancia FastAPI, CORS, endpoints /health y /
│       ├── config.py         # Settings: cors_origins, georef_base_url, timeout
│       └── integrations/     # un subpaquete por API externa
│           ├── __init__.py
│           └── georef/
│               ├── __init__.py
│               ├── client.py # httpx + lógica de llamada + errores de dominio
│               └── models.py # modelos Pydantic del JSON de Georef
└── tests/
    ├── conftest.py           # fixtures globales de pytest
    ├── fixtures/             # respuestas HTTP reales guardadas (JSON)
    │   └── georef/
    ├── unit/                 # tests sin internet (HTTP mockeado)
    │   └── georef/
    │       └── test_client.py
    └── integration/          # tests que llaman a la API real
        └── georef/
            └── test_client.py
```

## Qué hace cada parte

| Parte | Responsabilidad | Detalle clave |
|---|---|---|
| `src/conco/main.py` | Crear la app FastAPI y registrar middleware | CORS configurable vía `CORS_ORIGINS`; hoy solo expone `/` y `/health`. |
| `src/conco/config.py` | Centralizar configuración | `Settings(BaseSettings)` lee `.env`; valores default para desarrollo. Instancia singleton `settings`. |
| `src/conco/integrations/<api>/client.py` | Único lugar que conoce la API externa | Construye request, `raise_for_status()`, `model_validate_json()`, traduce errores a `GeorefError`. |
| `src/conco/integrations/<api>/models.py` | Contrato del JSON externo | Aliases ES→EN (`nomenclatura`→`nomenclature`), `populate_by_name=True`. |
| `scripts/probes/<api>.py` | Explorar la API real a mano | No es parte de la app; se corre con `uv run python scripts/probes/georef.py "direccion"`. |
| `tests/unit/<api>/` | Verificar el cliente sin red | `respx` intercepta httpx y devuelve fixtures. Corren por defecto con `uv run pytest`. |
| `tests/integration/<api>/` | Verificar que la API real siga igual | Marcados con `pytest.mark.integration`; excluidos por defecto, corren con `uv run pytest -m integration`. |
| `tests/fixtures/<api>/` | Respuestas reales capturadas | JSON tal cual lo devuelve la API. Sirven de input para los tests unitarios. |
| `tests/conftest.py` | Config global de pytest | Hoy solo fija `anyio_backend = "asyncio"` para tests async. |

## Tests y fixtures

Los tests están separados en dos capas — unitarios sin internet (`tests/unit/`, con `respx` + fixtures) e integración con internet (`tests/integration/`, opt-in vía `pytest -m integration`). El detalle completo está en [testing.md](testing.md).

## Reglas de diseño

1. **Solo `integrations/<api>/` conoce la API externa.** URLs, parámetros, formato de respuesta y errores viven ahí. El resto del sistema consume objetos Python tipados.
2. **Una API = un subpaquete.** Nueva integración → nueva carpeta `integrations/<api>/` + `tests/{unit,integration}/<api>/` + `fixtures/<api>/` + `scripts/probes/<api>.py`.
3. **Config por variables de entorno.** Nada hardcodeado fuera de defaults en `config.py`.
4. **Errores de dominio propios.** Fallas de red o de validación se traducen a `GeorefError`; el caller no ve `httpx` ni `ValidationError`.
5. **Tests separados por costo.** Unitarios sin red (default), integración con red (opt-in vía marker).

## Estado actual

- FastAPI con `/` y `/health` — el endpoint de geolocalización está documentado en `docs/prs/pr-03-geolocation-endpoint.md` pero aún no está implementado en `main.py`.
- Única integración implementada: Georef (`/direcciones`).
- Estructura pensada para crecer a capas de dominio/aplicación/infraestructura cuando las APIs se conecten a endpoints reales (ver `back/README.md` §Crecimiento previsto).
