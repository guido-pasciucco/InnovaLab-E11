# USIG EPOK (lugares de la Ciudad)

EPOK es el servicio de lugares de USIG (Gobierno de la Ciudad). CONCO lo usa para indicar las sedes y subsedes comunales más cercanas a un punto, donde la persona puede hacer atención presencial.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | USIG - EPOK, Gobierno de la Ciudad de Buenos Aires |
| URL base | `https://epok.buenosaires.gob.ar` |
| Endpoints | `GET /reverseGeocoderLugares/` y `GET /getObjectContent/` |
| Documentación oficial | El proyecto no registra una documentación propia de EPOK; se cita `https://epok.buenosaires.gob.ar` |
| Acceso | Sin clave de acceso; CORS `*`. **Requiere un User-Agent distinto al de curl** |
| Licencia | Sin licencia explícita. Se asume Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), como el resto de los datos de la Ciudad, y se cita la fuente |
| Latencia observada | `reverseGeocoderLugares` ~0,05–0,08 s; `getObjectContent` entre 0,1 y 0,2 s |
| Categorías | 182 publicadas; CONCO usa `sedes_de_comunas` |
| Estabilidad y riesgos | Un filtro BigIP corta la conexión según el User-Agent. Todo responde `200` con `Content-Type: text/javascript`. La categoría `centros_comerciales` está desactualizada (2008) |

## 2. Para qué la usa CONCO

| Uso | MVP | Reglas |
|---|---|---|
| Sedes y subsedes comunales más cercanas a un punto, con dirección, teléfono y enlace oficial | Ítems 3 y 4: enlaces a fuentes oficiales y ubicación | [RN-05](../REGLAS_DE_NEGOCIO.md) (cita la fuente y el enlace de la comuna), [RN-06](../REGLAS_DE_NEGOCIO.md) (CONCO indica dónde ir; no gestiona el trámite) |

## 3. Endpoints que llama CONCO

La búsqueda es en dos pasos: primero los lugares cercanos (id, nombre, distancia) y después el contenido de cada uno.

### `GET /reverseGeocoderLugares/`

| Parámetro | Valor que envía CONCO |
|---|---|
| `x` | Longitud (WGS84) |
| `y` | Latitud (WGS84) |
| `categorias` | `sedes_de_comunas` (constante `COMMUNE_OFFICES_CATEGORY`) |
| `radio` | Metros; `EPOK_RADIUS_METERS` (3000 por defecto). Es obligatorio: sin él no hay resultados |

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/reverseGeocoderLugares/?x=-58.4021372&y=-34.6047137&categorias=sedes_de_comunas&radio=3000'
```

Respuesta real abreviada (`back/tests/fixtures/epok/lugares_cercanos_sedes_de_comunas.json`):

```json
{
  "totalFull": 7,
  "instancias": [
    { "nombre": "Subsede Comunal 3", "id": "sedes_de_comunas|3", "distancia": "962.53" },
    { "nombre": "Sede Comunal 2", "id": "sedes_de_comunas|2", "distancia": "940.95" }
  ],
  "total": 7
}
```

### `GET /getObjectContent/`

| Parámetro | Valor que envía CONCO |
|---|---|
| `id` | Id devuelto por `reverseGeocoderLugares` (por ejemplo `sedes_de_comunas|2`) |

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/getObjectContent/?id=sedes_de_comunas%7C2'
```

Respuesta real abreviada (`back/tests/fixtures/epok/contenido_sedes_de_comunas_2.json`):

```json
{
  "contenido": [
    { "nombreId": "nombre", "valor": "Sede Comunal 2" },
    { "nombreId": "direccion", "valor": "URIBURU JOSE E., Pres. 1022 " },
    { "nombreId": "telefonos", "valor": "4370-9702" },
    { "nombreId": "barrio", "valor": "RECOLETA" },
    { "nombreId": "comuna", "valor": "Comuna 2" },
    { "nombreId": "tramites_y_servicios", "valor": "<a href=\"https://buenosaires.gob.ar/jefaturadegabinete/atencion-ciudadana-y-gestion-comunal/gestion-comunal/comuna-2\" target=\"_blank\">Página web</a>" }
  ],
  "fechaUltimaModificacion": "2024-04-11",
  "id": "sedes_de_comunas|2",
  "direccionNormalizada": "URIBURU JOSE E., Pres. 1022",
  "ubicacion": { "centroide": "POINT (105904.5067999991 103616.1745999991)", "tipo": "Punto" }
}
```

## 4. Comportamiento observado

| Caso | Qué devuelve EPOK | Cómo lo maneja CONCO |
|---|---|---|
| User-Agent por defecto de curl (`curl/8.5.0`) | Corta la conexión sin respuesta (httpx: `RemoteProtocolError`) | El cliente envía siempre `User-Agent: CONCO/0.1` (`EPOK_USER_AGENT`); con curl usar `-A` |
| Lugares en el radio | `200`; **no** vienen ordenados y `distancia` es texto en metros | El cliente la convierte a número y ordena |
| Nada en el radio, categoría desconocida, sin `radio` o sin `x`/`y` | `200` con `{"totalFull": 0, "instancias": [], "total": 0}` | `200` con `offices: []` (no es un error) |
| Id inexistente en `getObjectContent` | `200` con `{}` | El cliente devuelve `None`; esa oficina se omite |
| Oficina sin dirección (`direccion` ni `direccionNormalizada`) | — | Se omite; la lista puede tener menos elementos que `limit` |
| `Content-Type` | Siempre `text/javascript`, aunque el cuerpo es JSON | Se interpreta el cuerpo sin mirarlo |
| Enlace de la comuna | HTML dentro de `tramites_y_servicios` | Se extrae el primer `href` `http`/`https` con `html.parser`; cualquier otra cosa → `null` |
| Textos | Barrio en mayúsculas, dirección como `URIBURU JOSE E., Pres. 1022` (con espacios al final) | Se informan como los publica EPOK; el formato es tarea del frontend |
| Ubicación | `ubicacion.centroide` en coordenadas GKBA, no WGS84 | No se usa |
| Cuerpo vacío o no JSON, error HTTP, timeout o conexión cortada | — | `EpokError` → `502`. Si falla el contenido de cualquiera de las oficinas, la llamada entera responde `502` (no una lista parcial) |

## 5. Cómo se integra en CONCO

| Capa | Ubicación | Qué hace |
|---|---|---|
| Cliente | [`back/src/conco/integrations/epok/client.py`](../../back/src/conco/integrations/epok/client.py) | `find_nearby(longitude, latitude, categories, radius_meters)` y `get_object(object_id)` |
| Modelos | [`back/src/conco/integrations/epok/models.py`](../../back/src/conco/integrations/epok/models.py) | `EpokNearbyPlaces`, `EpokPlace`, `EpokObjectContent` |
| Error | `EpokError` | Ver la última fila de la tabla anterior |
| Adaptador | [`back/src/conco/geolocation/infrastructure.py`](../../back/src/conco/geolocation/infrastructure.py) | `EpokNearbyOfficeFinder`: pide el contenido solo de las `limit` más cercanas, en paralelo (`asyncio.gather`) |
| Error de dominio | [`back/src/conco/geolocation/domain.py`](../../back/src/conco/geolocation/domain.py) | `NearbyOfficeError` |

### `GET /geolocation/nearby-offices`

| Parámetro | Obligatorio | Por defecto | Validación |
|---|---|---|---|
| `latitude` | Sí | — | Entre -90 y 90 |
| `longitude` | Sí | — | Entre -180 y 180 |
| `limit` | No | `3` | Entre 1 y 5 |

| Código | Cuándo |
|---|---|
| `200` | Siempre que EPOK responda. `{"offices": [...], "source": {...}}`, ordenadas por distancia; vacía si no hay oficinas en el radio (por ejemplo, un punto en Moreno) |
| `404` | No se usa |
| `422` | Parámetros inválidos (incluido `limit` fuera de 1..5) |
| `502` | EPOK no respondió o devolvió algo inesperado |

Cada oficina trae `name`, `address`, `phone`, `neighborhood`, `commune`, `distance_meters`, `info_url` y `last_updated`. Todos salvo `name`, `address` y `distance_meters` pueden venir en `null`.

## 6. Configuración

| Variable | Por defecto |
|---|---|
| `EPOK_BASE_URL` | `https://epok.buenosaires.gob.ar` |
| `EPOK_USER_AGENT` | `CONCO/0.1` |
| `EPOK_TIMEOUT_SECONDS` | `10.0` |
| `EPOK_RADIUS_METERS` | `3000` |

Definidas en [`back/src/conco/config.py`](../../back/src/conco/config.py).

## 7. Tests y probe

| Tipo | Ruta |
|---|---|
| Fixtures | `back/tests/fixtures/epok/`: `lugares_cercanos_sedes_de_comunas.json`, `lugares_cercanos_sin_resultados.json`, `contenido_sedes_de_comunas_2.json`, `contenido_sedes_de_comunas_3.json`, `contenido_sedes_de_comunas_5.json`, `contenido_sedes_de_comunas_19.json`, `contenido_inexistente.json` |
| Unitarios | `back/tests/unit/epok/test_client.py`, `back/tests/unit/geolocation/test_epok_nearby_office_finder.py`, `back/tests/unit/geolocation/test_nearby_offices_api.py` |
| Integración (API real) | `back/tests/integration/epok/test_client.py`, `back/tests/integration/geolocation/test_nearby_offices_api.py` |

```bash
uv run python scripts/probes/epok.py -34.6047137 -58.4021372         # latitud longitud
uv run python scripts/probes/epok.py -34.6047137 -58.4021372 1000    # radio en metros
```

## 8. Pendientes y decisiones abiertas

- Agregar `EPOK_*` a `back/.env.example` (tarea del usuario).
- Encadenar dirección → coordenadas (Georef o USIG) → oficinas cercanas en el flujo del frontend. Requiere decisión de producto.
- Sumar otras categorías (`oficinas_de_empleo`, `centros_integracion_laboral`, `comunas_sstrabajo`) agregando su id.
- Convertir el centroide GKBA a WGS84 quedó fuera de alcance.

## 9. Fuentes

- Servicio: <https://epok.buenosaires.gob.ar>
- Seguimiento: [epok-integration](../../odd/tasks/epok-integration.md)

Fecha de verificación: 2026-10-31.
