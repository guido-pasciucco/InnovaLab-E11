# Georef (datos.gob.ar)

> **Estado:** integración y `GET /geolocation/addresses` mergeados a main (PRs #63 y #64). `GET /geolocation/location-check` (reverse geocoding para verificar CABA) está en el PR #69, abierto.

Servicio de normalización de datos geográficos del Gobierno Nacional. CONCO lo usa para dos cosas: convertir una dirección en coordenadas aproximadas (`/direcciones`) y saber si un punto está dentro de CABA (`/ubicacion`).

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | Gobierno Nacional (datos.gob.ar) |
| URL base | `https://apis.datos.gob.ar/georef/api` |
| Documentación oficial | <https://datosgobar.github.io/georef-ar-api/> |
| Acceso | Sin clave de acceso |
| Licencia | Creative Commons Atribución 4.0 Internacional (CC BY 4.0) |
| Latencia observada | `/direcciones` ~0,15 s; `/ubicacion` entre 0,02 y 0,12 s |
| Límites | La respuesta informa cabeceras `x-ratelimit-*` (observado: 200 por segundo, 6000 por minuto, 3.000.000 por día) |
| Estabilidad y riesgos | API documentada y estable. Las coordenadas son **aproximadas**. Una latitud fuera de rango responde `500` (CONCO lo evita validando antes) |

## 2. Para qué la usa CONCO

| Uso | MVP | Reglas |
|---|---|---|
| Dirección escrita libremente → dirección normalizada con coordenadas | Ítem 4: ubicación aproximada en el mapa | [RN-02](../../REGLAS_DE_NEGOCIO.md) (búsqueda restringida a CABA), [RN-03](../../REGLAS_DE_NEGOCIO.md) (ubicación aproximada; si no se encuentra, se informa) |
| Punto → ¿está en CABA? | Ítem 4 | [RN-02](../../REGLAS_DE_NEGOCIO.md) (solo CABA), [RN-05](../../REGLAS_DE_NEGOCIO.md) (cita la fuente) |

## 3. Endpoints que llama CONCO

### `GET /direcciones`

| Parámetro | Valor que envía CONCO |
|---|---|
| `direccion` | Texto de la persona, sin espacios sobrantes (`"  corrientes   2500 "` → `"corrientes 2500"`) |
| `provincia` | `caba` por defecto |
| `max` | `5` por defecto (entre 1 y 10) |

```bash
curl -s 'https://apis.datos.gob.ar/georef/api/direcciones?direccion=Corrientes%202500&provincia=caba&max=5'
```

Respuesta real abreviada (`back/tests/fixtures/georef/direcciones_corrientes_2500.json`):

```json
{
  "cantidad": 1,
  "direcciones": [
    {
      "altura": { "unidad": null, "valor": 2500 },
      "calle": { "categoria": "AV", "id": "0202101001185", "nombre": "AV CORRIENTES" },
      "departamento": { "id": "02021", "nombre": "Comuna 3" },
      "nomenclatura": "AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
      "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" },
      "ubicacion": { "lat": -34.6047137500375, "lon": -58.402137170712 }
    }
  ],
  "inicio": 0,
  "total": 1
}
```

### `GET /ubicacion`

| Parámetro | Valor que envía CONCO |
|---|---|
| `lat` | Latitud WGS84, ya validada entre -90 y 90 |
| `lon` | Longitud WGS84, ya validada entre -180 y 180 |

```bash
curl -s 'https://apis.datos.gob.ar/georef/api/ubicacion?lat=-34.6047137&lon=-58.4021372'
```

Respuesta real (`back/tests/fixtures/georef/ubicacion_caba_corrientes_2500.json`, abreviada):

```json
{
  "parametros": { "lat": -34.6047137, "lon": -58.4021372 },
  "ubicacion": {
    "departamento": { "id": "02021", "nombre": "Comuna 3" },
    "lat": -34.6047137,
    "lon": -58.4021372,
    "municipio": { "id": "022021", "nombre": "Comuna 3" },
    "provincia": { "id": "02", "nombre": "Ciudad Autónoma de Buenos Aires" }
  }
}
```

## 4. Comportamiento observado

| Caso | Qué devuelve Georef | Cómo lo maneja CONCO |
|---|---|---|
| Dirección inexistente | `200` con `"cantidad": 0` y `"direcciones": []` | `200` con `addresses: []` |
| Calle sin altura | `200` con `altura.valor: null`; igual trae `ubicacion` | Se devuelve la dirección; el modelo admite altura nula |
| Datos insuficientes para ubicar | `ubicacion` puede faltar (según la documentación) | `coordinates: null` en la respuesta de CONCO |
| Sin `provincia` | La búsqueda es ambigua entre provincias | CONCO envía siempre `provincia` (`caba` por defecto) |
| Falta `direccion` | `400` con `{"errores": [...]}` (`codigo_interno` 1003) | `GeorefError` → `502`; CONCO valida antes (`422`) |
| Punto en CABA | `provincia.id = "02"` y la comuna como departamento y municipio | `in_caba: true` |
| Punto en otra provincia (La Plata) | `provincia.id = "06"`, `"Buenos Aires"` | `in_caba: false` |
| Punto fuera de la Argentina (mar, Madrid) | `200` con `provincia`, `departamento` y `municipio` presentes pero `id` y `nombre` en `null` | `in_caba: false`, `province` y `department` en `null` |
| `lat=abc` o sin `lat` | `400` con `{"errores": [...]}` (`codigo_interno` 1001 o 1003) | CONCO valida antes y responde `422` |
| Latitud fuera de rango (`lat=-95`) | `500` con mensaje de error interno | CONCO valida antes y responde `422`; nunca envía la consulta |
| Timeout, error HTTP o cuerpo que no es JSON | — | `GeorefError` → `502` |

Error real (`back/tests/fixtures/georef/error_400_falta_direccion.json`):

```json
{
  "errores": [
    {
      "codigo_interno": 1003,
      "mensaje": "El parámetro 'direccion' es obligatorio.",
      "nombre_parametro": "direccion",
      "ubicacion": "querystring"
    }
  ]
}
```

## 5. Cómo se integra en CONCO

| Capa | Ubicación | Qué hace |
|---|---|---|
| Cliente | [`back/src/conco/integrations/georef/client.py`](../../../back/src/conco/integrations/georef/client.py) | `search_addresses(address, province, max_results)` y `locate(latitude, longitude)`; comparten `_get` |
| Modelos | [`back/src/conco/integrations/georef/models.py`](../../../back/src/conco/integrations/georef/models.py) | `GeorefAddressesResponse`, `GeorefLocationResponse` |
| Error | `GeorefError` | Timeout, error HTTP, cuerpo no JSON o JSON inesperado |
| Adaptadores | [`back/src/conco/geolocation/infrastructure.py`](../../../back/src/conco/geolocation/infrastructure.py) | `GeorefAddressFinder` y `GeorefLocationChecker` (CABA = `CABA_PROVINCE_ID = "02"`, se compara el id y no el nombre) |
| Errores de dominio | [`back/src/conco/geolocation/domain.py`](../../../back/src/conco/geolocation/domain.py) | `AddressSearchError`, `LocationCheckError` |

### Flujo de una consulta

```
caller
  └─ search_addresses(address, provincia="caba", max_results=5)
       ├─ normalize_address()        # colapsa espacios
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

### Modelos (models.py)

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

La API devuelve claves en español (`nomenclatura`, `calle`, `altura`); el código usa inglés. Cada `Field(alias="...")` define el nombre externo, y `ConfigDict(populate_by_name=True)` permite instanciar los modelos tanto por alias como por nombre de atributo — útil en tests y al serializar.

Los campos observados como `null` en respuestas reales están tipados como `| None` con default `None`: `id`, `name`, `category`, `unit`, `value`, `floor`, `location`, y **todos** los campos de `GeorefStreet` (las calles de cruce suelen venir completamente en null). `nomenclature`, `street`, `height`, `department`, `province` son requeridos.

### Cómo extender

- **Georef `/ubicacion`** (coords → comuna): ya integrado; mismo patrón para cualquier endpoint nuevo — función en `client.py`, modelos nuevos en `models.py`, fixtures propios, tests en ambas capas.
- **Nueva API**: replicar la estructura `integrations/<api>/` completa. Ver [back/README.md](../../../back/README.md) §Cómo incorporar una API nueva.

### `GET /geolocation/addresses`

| Parámetro | Obligatorio | Por defecto | Validación |
|---|---|---|---|
| `address` | Sí | — | Entre 3 y 200 caracteres, no solo espacios |
| `province` | No | `caba` | Nombre o id de provincia de Georef |
| `limit` | No | `5` | Entre 1 y 10 |

### `GET /geolocation/location-check`

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `latitude` | Sí | Entre -90 y 90 |
| `longitude` | Sí | Entre -180 y 180 |

| Código | `/geolocation/addresses` | `/geolocation/location-check` |
|---|---|---|
| `200` | `{"addresses": [...]}`; la lista puede venir vacía | `{"location": {"in_caba", "province", "department"}, "source": {...}}`, también fuera de CABA |
| `404` | No se usa | No se usa |
| `422` | Parámetros inválidos | Parámetros inválidos |
| `502` | Georef no respondió o devolvió algo inesperado | Ídem |

## 6. Configuración

| Variable | Por defecto |
|---|---|
| `GEOREF_BASE_URL` | `https://apis.datos.gob.ar/georef/api` |
| `GEOREF_TIMEOUT_SECONDS` | `10.0` |

Definidas en [`back/src/conco/config.py`](../../../back/src/conco/config.py). `/ubicacion` reutiliza la misma configuración.

## 7. Tests y probe

| Tipo | Ruta |
|---|---|
| Fixtures | `back/tests/fixtures/georef/`: `direcciones_corrientes_2500.json`, `direcciones_sin_altura.json`, `direcciones_sin_resultados.json`, `error_400_falta_direccion.json`, `error_400_lat_invalida.json`, `ubicacion_caba_corrientes_2500.json`, `ubicacion_la_plata.json`, `ubicacion_fuera_de_argentina.json` |
| Unitarios (cliente) | `back/tests/unit/georef/test_client.py`, `back/tests/unit/georef/test_locate.py` |
| Unitarios (adaptadores y API) | `back/tests/unit/geolocation/test_georef_finder.py`, `test_georef_location_checker.py`, `test_api.py`, `test_location_check_api.py` |
| Integración (API real) | `back/tests/integration/georef/test_client.py`, `back/tests/integration/geolocation/test_api.py`, `back/tests/integration/geolocation/test_location_check_api.py` |

```bash
uv run python scripts/probes/georef.py "Corrientes 2500"
uv run python scripts/probes/georef.py --locate -34.6047137 -58.4021372   # latitud longitud
```

## 8. Pendientes y decisiones abiertas

- Agregar `GEOREF_*` a `back/.env.example` (tarea T4 del usuario en [georef-integration](../../../odd/tasks/georef-integration.md)).
- Aplicar la verificación de CABA dentro de `/geolocation/address-context/by-coordinates` y `/geolocation/nearby-offices`, y decidir la respuesta para puntos fuera de CABA, o encadenarla en el frontend ([georef-caba-check](../../../odd/tasks/georef-caba-check.md)). Requiere decisión de producto.

## 9. Fuentes

- Documentación oficial: <https://datosgobar.github.io/georef-ar-api/>
- `/direcciones`: <https://apis.datos.gob.ar/georef/api/direcciones>
- `/ubicacion`: <https://apis.datos.gob.ar/georef/api/ubicacion>
- Seguimiento: [georef-integration](../../../odd/tasks/georef-integration.md), [geolocation-endpoint](../../../odd/tasks/geolocation-endpoint.md), [georef-caba-check](../../../odd/tasks/georef-caba-check.md)

Fecha de verificación: 2026-10-31.
