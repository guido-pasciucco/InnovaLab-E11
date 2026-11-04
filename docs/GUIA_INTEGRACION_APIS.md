# Guía para integrar una API externa

Flujo que se siguió para integrar **Georef**, la primera API externa de CONCO, escrito para repetirlo con cada API nueva (USIG, BA Data, etc.). Cada fase indica qué se hace, qué se obtiene y cómo quedó en Georef. La estructura de carpetas y las convenciones están definidas en [`back/README.md`](../back/README.md).

> **Regla de oro:** primero se **entiende** la API, después se **observa** su respuesta real y recién al final se **modela**. Nunca se escriben modelos ni tests a partir de suposiciones.

## Recorrido rápido

| Fase | Qué se hace | Resultado | En Georef |
|---|---|---|---|
| 0 · Entender | Investigar la API y decidir si se usa | Decisión informada | Contexto de datos.gob.ar |
| 1 · Rama | Crear una rama propia para la API | `feature/<api>-integration` | `feature/georef-integration` |
| 2 · Observar | Llamar a la API real y guardar respuestas | Fixtures en `tests/fixtures/<api>/` | 4 respuestas reales |
| 3 · Configurar | Declarar URL y timeout | `config.py` + `.env.example` | `GEOREF_BASE_URL`, `GEOREF_TIMEOUT_SECONDS` |
| 4 · Cliente | Escribir la llamada HTTP | `integrations/<api>/client.py` | `search_addresses()` |
| 5 · Probe | Script para explorar la API a mano | `scripts/probes/<api>.py` | `scripts/probes/georef.py` |
| 6 · Modelos | Tipar la respuesta observada | `integrations/<api>/models.py` | `GeorefAddressesResponse` |
| 7 · Errores | Un único error hacia afuera | `<Api>Error` | `GeorefError` |
| 8 · Tests | Unitarios (sin internet) + integración (API real) | `tests/unit/<api>/`, `tests/integration/<api>/` | 9 + 1 tests |
| 9 · Exponer | Endpoint para el front, aislado de la API | Carpeta por funcionalidad | `GET /geolocation/addresses` |
| 10 · Documentar | README y dependencias | Docs al día | README + `DEPENDENCIAS.md` |
| 11 · Entregar | Verificar, commitear y abrir PR | PR revisable | PR #51 |

---

## Fase 0 · Entender la API antes de tocar código

La decisión de qué API integrar es del equipo, no de quien implementa. Antes de decidir, se arma una ficha de contexto con fuentes oficiales.

| Pregunta | En Georef |
|---|---|
| ¿Quién la provee y la mantiene? | Equipo de Datos de la Nación (datos.gob.ar) |
| ¿Qué problema del caso de uso resuelve? | Dirección escrita → dirección normalizada + coordenadas (punto 4 del MVP: ubicación en el mapa) |
| ¿Qué endpoints sirven para CONCO? | `/direcciones` (principal); `/ubicacion` y `/calles` (posibles) |
| ¿Pide autenticación? | No para uso abierto |
| ¿Licencia? | CC BY 4.0 (uso libre citando la fuente) |
| ¿Límites de uso? | Estado "alpha", sin cuotas publicadas → usar timeout y, más adelante, caché |
| ¿Limitaciones de los datos? | Coordenadas aproximadas; `ubicacion` puede faltar |
| ¿Funciona hoy? | Se verificó con una llamada real |

- [ ] La ficha cita la documentación oficial.
- [ ] Se comprobó que la API responde.
- [ ] El equipo eligió la API después de ver la ficha.

## Fase 1 · Una rama y un PR por API

```bash
git switch -c feature/<api>-integration
```

- Si la rama depende de otro PR que todavía no se mergeó, se crea **desde esa rama** (PR apilado) y el PR se abre con esa rama como base. Cuando el PR anterior se mergea, se cambia la base a `main`.
- Si git configura la rama nueva para rastrear la rama base, quitarlo con `git branch --unset-upstream` y, al subirla por primera vez, usar `git push -u origin feature/<api>-integration`. Si no, un `git push` puede terminar en la rama de otro PR.

## Fase 2 · Observar la respuesta real

Llamar a la API con casos normales **y** casos límite, y mirar la forma exacta de la respuesta.

| Caso | Qué se observó en Georef |
|---|---|
| Normal | `Corrientes 2500` → 1 resultado con coordenadas |
| Sin resultados | `cantidad: 0`, `direcciones: []` |
| Dato incompleto | Calle sin número → `altura.valor: null` |
| Ambiguo | Sin provincia, `San Martin 100` devuelve resultados de varias provincias |
| Error | Falta un parámetro obligatorio → HTTP 400 con `{"errores": [...]}` |

Cada respuesta se guarda tal cual en `back/tests/fixtures/<api>/<caso>.json`. Esos archivos son la base de los modelos y de los tests unitarios.

## Fase 3 · Configuración

Ninguna URL ni valor variable se escribe en el código: se declara en `src/conco/config.py` con un valor por defecto y se documenta en `back/.env.example`.

```python
# src/conco/config.py
georef_base_url: str = "https://apis.datos.gob.ar/georef/api"
georef_timeout_seconds: float = 10.0
```

```bash
# back/.env.example
GEOREF_BASE_URL=https://apis.datos.gob.ar/georef/api
GEOREF_TIMEOUT_SECONDS=10
```

## Fase 4 · Cliente HTTP

`src/conco/integrations/<api>/client.py` es **el único archivo** que conoce la URL, los parámetros y el formato de esa API.

```bash
uv add "httpx>=0.28,<1.0"   # solo la primera vez
```

| Decisión | Por qué |
|---|---|
| `httpx.AsyncClient` dentro de `async with` | No bloquea el servidor mientras espera, y cierra la conexión aunque algo falle |
| `base_url` y `timeout` desde `settings` | Cambiar de entorno no requiere tocar código; sin timeout, una API caída cuelga el servidor |
| `params={...}` | httpx codifica espacios y acentos; nunca concatenar la URL a mano |
| `raise_for_status()` | Un 4xx/5xx se convierte en excepción en lugar de pasar como dato válido |
| Normalizar la entrada antes de enviarla | `"  corrientes   2500 "` → `"corrientes 2500"` |

## Fase 5 · Script de exploración (probe)

`scripts/probes/<api>.py` ejecuta el cliente en forma aislada e imprime el resultado:

```bash
uv run python scripts/probes/georef.py "Corrientes 2500"
```

- Es la **linterna**: sirve para investigar un caso puntual (por ejemplo, una dirección que un usuario reporta mal).
- No reemplaza a los tests ni forma parte de la app en producción.
- Una vez que el cliente devuelve modelos tipados, el probe ya no muestra los campos que el modelo no conoce. Para ver campos nuevos de la API, consultar la respuesta cruda con `curl`.

## Fase 6 · Modelos de la respuesta

`src/conco/integrations/<api>/models.py` describe **la respuesta de esa API**, no los conceptos de CONCO.

```python
class GeorefAddress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    nomenclature: str = Field(alias="nomenclatura")
    location: GeorefCoordinates | None = Field(default=None, alias="ubicacion")
```

- Atributos en inglés y `alias` con la clave original de la API: la traducción ocurre en un solo lugar.
- Un campo es opcional (`| None`) **solo** si se observó vacío o la documentación dice que puede faltar.
- El cliente valida con `Model.model_validate_json(response.content)`: así, un cuerpo que no es JSON (por ejemplo, una página HTML de mantenimiento) también termina en un error controlado.

## Fase 7 · Un único error hacia afuera

Dentro del cliente pueden fallar muchas cosas; hacia afuera se expone **un solo tipo de error**, para que el resto del sistema no dependa de httpx ni de Pydantic.

```python
class GeorefError(Exception):
    """Georef no está disponible o devolvió una respuesta inesperada."""

try:
    ...
except httpx.HTTPError as exc:      # timeouts, conexión, 4xx/5xx
    raise GeorefError(...) from exc
except ValidationError as exc:      # respuesta con otra forma o que no es JSON
    raise GeorefError(...) from exc
```

## Fase 8 · Tests

| Tipo | Carpeta | Usa internet | Cómo se corre |
|---|---|---|---|
| Unitario | `tests/unit/<api>/` | No: `respx` simula la API con las fixtures | `uv run pytest` (por defecto) |
| Integración | `tests/integration/<api>/` | Sí: llama a la API real | `uv run pytest -m integration` |

**Casos mínimos del test unitario del cliente** (en Georef, 9 tests):

- [ ] Respuesta completa → se lee bien (un campo de cada nivel).
- [ ] Los parámetros enviados son los esperados (entrada normalizada incluida).
- [ ] Sin resultados → lista vacía.
- [ ] Dato incompleto → el campo opcional queda en `None`.
- [ ] HTTP 4xx/5xx → `<Api>Error`.
- [ ] Timeout → `<Api>Error`.
- [ ] Respuesta con otra forma → `<Api>Error`.
- [ ] Cuerpo que no es JSON → `<Api>Error`.

**Test de integración:** un caso conocido y estable contra la API real, marcado con `pytestmark = pytest.mark.integration`. Si falla, puede ser el código **o** la API caída: por eso no se corre por defecto.

Se recomienda escribir primero el test, verlo fallar y después implementar hasta que pase.

## Fase 9 · Exponer la funcionalidad (endpoint)

Cuando el front necesita usar la API, se crea una **carpeta por funcionalidad** (no por API) dentro de `src/conco/`, con tres capas. Así, el front y el endpoint no saben qué API externa hay detrás, y se puede reemplazar sin tocarlos.

| Archivo | Rol | En geolocalización |
|---|---|---|
| `<funcionalidad>/domain.py` | Modelos propios de CONCO, el **puerto** (`Protocol`) y el error de dominio | `Address`, `AddressFinder`, `AddressSearchError` |
| `<funcionalidad>/infrastructure.py` | **Adaptador**: usa el cliente de la API y traduce al dominio | `GeorefAddressFinder` (traduce `GeorefError` → `AddressSearchError`) |
| `<funcionalidad>/api.py` | Router de FastAPI: valida parámetros y maneja errores HTTP | `GET /geolocation/addresses` (422 si la entrada es inválida, 502 si la API falla) |

- El adaptador se inyecta con `Depends(get_<x>)`. En los tests se reemplaza por uno falso con `app.dependency_overrides`.
- El router se registra en `main.py` con `app.include_router(...)`.
- Tests: `tests/unit/<funcionalidad>/` (adaptador con respx + endpoint con el adaptador falso) y `tests/integration/<funcionalidad>/` (endpoint contra la API real).

## Fase 10 · Documentar

- [ ] `back/README.md`: sección de la API (proveedor, endpoint, ejemplo de respuesta) y, si hay endpoint, sus parámetros y respuestas.
- [ ] `docs/DEPENDENCIAS.md`: cada dependencia nueva con su rango y para qué sirve.
- [ ] `back/.env.example`: variables nuevas con un comentario.

## Fase 11 · Verificar y entregar

Desde `back/`:

```bash
uv run pytest
uv run pytest -m integration
uv run python scripts/probes/<api>.py "<caso conocido>"
```

- Commits por unidad de trabajo, con Conventional Commits (por ejemplo `feat(back): add <api> client`).
- Antes de commitear, confirmar que `.env` **no** está incluido: `git check-ignore -q back/.env`.
- El PR incluye contexto, cambios, comandos para validar y qué quedó fuera del alcance. El repositorio no tiene CI: quien revisa corre los tests a mano.

---

## Plantilla de archivos para una API nueva

```
back/
├── src/conco/
│   ├── config.py                     # + <api>_base_url, <api>_timeout_seconds
│   ├── integrations/<api>/
│   │   ├── __init__.py
│   │   ├── client.py                 # llamada HTTP + <Api>Error
│   │   └── models.py                 # forma de la respuesta observada
│   └── <funcionalidad>/              # solo si se expone un endpoint (fase 9)
│       ├── __init__.py
│       ├── domain.py
│       ├── infrastructure.py
│       └── api.py
├── scripts/probes/<api>.py
└── tests/
    ├── fixtures/<api>/*.json
    ├── unit/<api>/test_client.py
    └── integration/<api>/test_client.py
```

## Errores que ya cometimos (y cómo evitarlos)

| Error | Cómo evitarlo |
|---|---|
| Elegir la API sin entender su contexto | Hacer siempre la fase 0 y decidir en equipo |
| Correr comandos en otra pestaña de la terminal, parada en otra carpeta | Revisar que el prompt termine en `InnovaLab-E11/back$` |
| `uv add <paquete>` sin rango deja la versión sin tope | Usar `uv add "<paquete>>=X.Y,<Z.0"` |
| Confundir `src/conco/integrations/` (APIs externas) con `tests/integration/` (tipo de test) | Los tests van en `tests/unit/<api>/` o `tests/integration/<api>/` |
| `response.json()` deja escapar un error cuando la API devuelve HTML | Validar con `model_validate_json(response.content)` |
| La rama nueva rastrea la rama base y el push va a otro PR | `git branch --unset-upstream` + `git push -u origin <rama>` |
