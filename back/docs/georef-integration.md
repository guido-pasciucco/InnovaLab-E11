# Integración Georef — guía técnica

Documentación interna para el equipo de backend sobre cómo funciona la integración con la API de Georef (geocodificación de direcciones argentinas).

Archivos involucrados:

- `back/src/conco/integrations/georef/client.py` — transporte HTTP + errores
- `back/src/conco/integrations/georef/models.py` — contrato Pydantic del JSON
- `back/src/conco/config.py` — `georef_base_url`, `georef_timeout_seconds`
- `back/tests/unit/georef/test_client.py` + `tests/fixtures/georef/` — tests sin red
- `back/tests/integration/georef/test_client.py` — test contra la API real
- `back/scripts/probes/georef.py` — exploración manual

## API externa

| Dato | Valor |
|---|---|
| Proveedor | datos.gob.ar (Gobierno Nacional) |
| Endpoint | `GET https://apis.datos.gob.ar/georef/api/direcciones` |
| Auth | Ninguna |
| Params | `direccion` (string), `provincia` (default `caba`), `max` (default 5) |

## Flujo de una consulta

```
caller
  └─ search_addresses(address, provincia="caba", max_results=5)
       ├─ normalize_address()        # colapsa espacios: "  Corrientes   2500 " → "Corrientes 2500"
       ├─ httpx.AsyncClient          # base_url + timeout desde settings
       │    GET /direcciones?direccion=...&provincia=caba&max=5
       ├─ response.raise_for_status() # 4xx/5xx → httpx.HTTPStatusError
       └─ GeorefAddressesResponse.model_validate_json(response.content)
            └─ GeorefAddress[]        # objetos tipados, aliases ES→EN resueltos
```

### Manejo de errores

`client.py` captura dos familias y las unifica en `GeorefError`:

| Excepción original | Causa | Resultado |
|---|---|---|
| `httpx.HTTPError` | timeout, DNS, conexión rechazada, HTTP 4xx/5xx | `GeorefError("No se pudo consultar Georef: ...")` |
| `pydantic.ValidationError` | JSON válido pero no cumple el contrato (campos faltantes, tipos incorrectos) | `GeorefError("Georef devolvió una respuesta inesperada.")` |

El caller solo maneja `GeorefError` — no conoce httpx ni Pydantic.

## Modelos (models.py)

Jerarquía Pydantic v2:

```
GeorefAddressesResponse        # envoltorio: cantidad, total, inicio, direcciones[]
└── GeorefAddress              # una dirección normalizada
    ├── nomenclature: str                    (alias: nomenclatura)
    ├── street: GeorefStreet                 (alias: calle)
    │     ├── id, name                       (alias: nombre)
    │     └── category                       (alias: categoria)
    ├── height: GeorefHeight                 (alias: altura)
    │     ├── unit                           (alias: unidad)
    │     └── value: int                     (alias: valor, null si no hay número)
    ├── cross_street_1 / cross_street_2: GeorefStreet   (alias: calle_cruce_1/2)
    ├── department: GeorefNamedEntity        (alias: departamento)
    ├── census_locality: GeorefNamedEntity   (alias: localidad_censal)
    ├── province: GeorefNamedEntity          (alias: provincia)
    ├── floor: str | None                    (alias: piso)
    └── location: GeorefCoordinates | None   (alias: ubicacion)
          ├── lat: float
          └── lon: float
```

`GeorefNamedEntity` = `{ id, name }` reutilizado para departamento/provincia/localidad.

### Alias y populate_by_name

La API devuelve claves en español (`nomenclatura`, `calle`, `altura`); el código usa inglés. Cada `Field(alias="...")` define el nombre externo, y `ConfigDict(populate_by_name=True)` permite instanciar los modelos tanto por alias como por nombre de atributo — útil en tests y al serializar.

### Nullabilidad

Los campos observados como `null` en respuestas reales están tipados como `| None` con default `None`: `id`, `name`, `category`, `unit`, `value`, `floor`, `location`, y **todos** los campos de `GeorefStreet` (las calles de cruce suelen venir completamente en null). `nomenclature`, `street`, `height`, `department`, `province` son requeridos.

## Ejemplo real

Request: `GET /direcciones?direccion=Corrientes%202500&provincia=caba&max=5`

Respuesta (recortada, de `tests/fixtures/georef/direcciones_corrientes_2500.json`):

```json
{
  "cantidad": 1,
  "total": 1,
  "inicio": 1,
  "direcciones": [{
    "nomenclatura": "AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
    "calle": { "id": "0202101001185", "nombre": "AV CORRIENTES", "categoria": "AV" },
    "altura": { "unidad": null, "valor": 2500 },
    "calle_cruce_1": { "categoria": null, "id": null, "nombre": null },
    "departamento": { "id": "02021", "nombre": "Comuna 3" },
    "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" },
    "ubicacion": { "lat": -34.6047137500375, "lon": -58.402137170712 }
  }]
}
```

Uso del resultado:

```python
result = await search_addresses("Corrientes 2500")
addr = result.addresses[0]
addr.nomenclature        # "AV CORRIENTES 2500, Comuna 3, ..."
addr.department.name     # "Comuna 3"   ← clave para cruzar con IDECABA/BA Data
addr.location.lat        # -34.6047137500375
```

## Testing

| Capa | Archivo | Qué cubre |
|---|---|---|
| Unit | `tests/unit/georef/test_client.py` | Parsing de fixtures reales, params normalizados, `count=0`, `height` null, errores HTTP/timeout/payload inválido → `GeorefError`. Usa `respx` + `tests/fixtures/georef/*.json`. |
| Integration | `tests/integration/georef/test_client.py` | Una llamada real a Georef verificando rangos de lat/lon y comuna. Requiere internet. |

Comandos (desde `back/`):

```bash
uv run pytest                    # unitarios (sin internet)
uv run pytest -m integration     # integración (con internet)
uv run python scripts/probes/georef.py "Av. Corrientes 2500"   # probe manual
```

## Cómo extender

- **Georef `/ubicacion`** (coords → comuna): mismo patrón — agregar función en `client.py` (o `client_ubicacion.py`), modelos nuevos en `models.py`, fixtures propios, tests en ambas capas.
- **Nueva API**: replicar la estructura `integrations/<api>/` completa. Ver `architecture.md` §Reglas de diseño.
