# Trámites de la Ciudad de Buenos Aires (Drupal JSON:API)

Catálogo oficial de trámites del Gobierno de la Ciudad, publicado por el JSON:API del sitio Drupal `buenosaires.gob.ar` (recurso `node/tramites_obelisco`). CONCO lo usa para buscar trámites por nombre y mostrar requisitos, pasos, organismo responsable y el enlace oficial para iniciarlos.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | Gobierno de la Ciudad de Buenos Aires (buenosaires.gob.ar) |
| URL base | `https://buenosaires.gob.ar/jsonapi` |
| Recurso | `node/tramites_obelisco` |
| Documentación oficial | No tiene. Es el JSON:API que Drupal expone por defecto (formato: <https://jsonapi.org/format/1.1/>) |
| Página del catálogo (se cita como fuente) | <https://buenosaires.gob.ar/gobierno/tramites> |
| Acceso | Sin clave de acceso |
| Licencia | Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), según el pie del sitio |
| Latencia observada | Búsqueda ~0,25 s; el detalle pesa alrededor de 35 KB |
| Volumen | 868 trámites publicados (960 sin filtrar por publicados) |
| Estabilidad y riesgos | **API no documentada**: su forma puede cambiar sin aviso. El test de integración es la alerta temprana y todo cambio de forma termina en `502`, nunca en `500` |

## 2. Para qué la usa CONCO

| Uso | MVP | Reglas |
|---|---|---|
| Buscar trámites oficiales por texto en el título | Ítem 2: orientación general sobre procedimientos | [RN-04](../REGLAS_DE_NEGOCIO.md) (orientación, no determinación legal), [RN-07](../REGLAS_DE_NEGOCIO.md) (verificar con el organismo) |
| Mostrar requisitos, pasos, organismo y enlace para iniciar | Ítems 2 y 3: enlaces a fuentes oficiales | [RN-05](../REGLAS_DE_NEGOCIO.md) (cada trámite lleva su `official_url`), [RN-06](../REGLAS_DE_NEGOCIO.md) (CONCO no inicia el trámite: solo enlaza) |

## 3. Endpoints que llama CONCO

### Búsqueda: `GET /node/tramites_obelisco`

| Parámetro | Valor que envía CONCO |
|---|---|
| `filter[status]` | `1` (solo publicados; siempre se envía) |
| `filter[title][operator]` | `CONTAINS` |
| `filter[title][value]` | Texto de la persona, sin espacios sobrantes |
| `sort` | `title` (orden estable; siempre se envía) |
| `page[limit]` | `10` por defecto (entre 1 y 20) |
| `fields[node--tramites_obelisco]` | `title,path,changed,body` |

```bash
curl -s -g 'https://buenosaires.gob.ar/jsonapi/node/tramites_obelisco?filter[status]=1&filter[title][operator]=CONTAINS&filter[title][value]=habilitaci&sort=title&page[limit]=10&fields[node--tramites_obelisco]=title,path,changed,body'
```

Respuesta real abreviada (`back/tests/fixtures/caba_tramites/busqueda_habilitaci.json`):

```json
{
  "data": [
    {
      "type": "node--tramites_obelisco",
      "id": "338718b4-a2a0-44af-baa4-083f5d834b12",
      "attributes": {
        "title": "Habilitación de actividad económica",
        "changed": "2026-08-07T18:57:01+00:00",
        "path": { "alias": "/tramites/habilitacion-de-actividad-economica" },
        "body": { "value": "Con este trámite podés solicitar la habilitación...", "format": "plain_text" }
      }
    }
  ],
  "meta": { "count": 11 }
}
```

### Detalle: `GET /node/tramites_obelisco/{uuid}`

El contenido de cada trámite está armado con párrafos anidados:

```text
field_contenido → field_seccion → field_columna_{central,izquierda,derecha} → field_componente
  ├── requisito_tramite      → field_item_requisito_tramite (field_texto, field_cuerpo)
  ├── pasos_del_tramite      → field_item_paso_del_tramite (field_titulo, field_parrafo)
  ├── organismo_responsable  (field_titulo)
  └── boton_iniciar_tramite  (field_link_iniciar_tramite)
```

CONCO pide con `include` solo esos componentes y usa *sparse fieldsets* (`fields[paragraph--...]`). Un valor vacío (por ejemplo `fields[paragraph--parrafo]=`) descarta todos los atributos de los párrafos que no se usan (costos, normativa, textos de ayuda). Los parámetros exactos están en `DETAIL_PARAMS` del cliente.

```bash
uv run python scripts/probes/caba_tramites.py --id 338718b4-a2a0-44af-baa4-083f5d834b12
```

Fragmentos reales (`back/tests/fixtures/caba_tramites/tramite_habilitacion_actividad_economica.json`, abreviados):

```json
{
  "type": "paragraph--organismo_responsable",
  "attributes": {
    "field_titulo": "Agencia Gubernamental de Control - Dirección General de Habilitaciones y Permisos "
  }
}
```

```json
{
  "type": "paragraph--boton_iniciar_tramite",
  "attributes": {
    "field_link_iniciar_tramite": {
      "uri": "https://login.buenosaires.gob.ar/auth/realms/miba/protocol/openid-connect/auth?client_id=tad&...",
      "title": "Iniciar Trámite"
    }
  }
}
```

## 4. Comportamiento observado

| Caso | Qué devuelve la API | Cómo lo maneja CONCO |
|---|---|---|
| `CONTAINS` sobre el título | No distingue mayúsculas ni acentos (`habilitacion`, `HABILITACIÓN` y `habilitaci` devuelven los mismos 11) | Solo búsqueda por título; no hay búsqueda por actividad ni por relevancia |
| Texto sin coincidencias (`caf`) | `200` con `"data": []` y `"meta": {"count": 0}` | `200` con `procedures: []` |
| Sin `filter[status]=1` | `meta.count` 960 y páginas incompletas (los no publicados se omiten con un bloque `omitted`) | Se envía siempre `filter[status]=1` (868 resultados, páginas completas) |
| Corchetes en la query string | httpx los codifica (`%5B`/`%5D`) y la API los acepta | Sin acción |
| Campo de filtro inexistente | `400` JSON:API con `errors[].detail` | `CabaTramitesError` → `502` |
| UUID inexistente, no publicado o mal formado | **`301`** a una página HTML bajo `/gcaba_historico/` (no `404`) | El cliente devuelve `None` → `404` |
| Trámite sin botón para iniciar | No viene `boton_iniciar_tramite` (7 de 90 en un muestreo) | `start_url: null` |
| Paso sin explicación | `field_parrafo: null` (5 de 90) | El paso se muestra solo con el título |
| `body` | Siempre `plain_text` en los 868 publicados | Se quita HTML solo si el formato no es `plain_text` |
| Cambio de forma, timeout o error HTTP | — | `CabaTramitesError` → `502` |

Error real (`back/tests/fixtures/caba_tramites/error_400_filtro_invalido.json`, abreviado):

```json
{
  "errors": [
    {
      "title": "Bad Request",
      "status": "400",
      "detail": "Invalid nested filtering. The field `campo_inexistente`, given in the path `campo_inexistente`, does not exist."
    }
  ]
}
```

## 5. Cómo se integra en CONCO

| Capa | Ubicación | Qué hace |
|---|---|---|
| Cliente | [`back/src/conco/integrations/caba_tramites/client.py`](../../back/src/conco/integrations/caba_tramites/client.py) | `search_procedures(query, limit)` y `get_procedure(procedure_id)`; resuelve el grafo de párrafos |
| Modelos | [`back/src/conco/integrations/caba_tramites/models.py`](../../back/src/conco/integrations/caba_tramites/models.py) | Un modelo por tipo de párrafo usado |
| Error | `CabaTramitesError` | Error HTTP, timeout o respuesta inesperada |
| Adaptador | [`back/src/conco/guidance/infrastructure.py`](../../back/src/conco/guidance/infrastructure.py) | `CabaProcedureCatalog`: HTML → texto plano; URL oficial = `https://buenosaires.gob.ar` + `path.alias` |
| Error de dominio | [`back/src/conco/guidance/domain.py`](../../back/src/conco/guidance/domain.py) | `ProcedureSearchError` |

### `GET /guidance/procedures`

| Parámetro | Obligatorio | Por defecto | Validación |
|---|---|---|---|
| `query` | Sí | — | Entre 3 y 100 caracteres, no solo espacios |
| `limit` | No | `10` | Entre 1 y 20 |

### `GET /guidance/procedures/{procedure_id}`

| Parámetro | Validación |
|---|---|
| `procedure_id` | UUID devuelto por la búsqueda |

| Código | Cuándo |
|---|---|
| `200` | Búsqueda: `{"procedures": [...], "source": {...}}` (puede venir vacía). Detalle: `{"procedure": {...}, "source": {...}}` con `requirements`, `steps`, `responsible_office` y `start_url` (los dos últimos pueden ser `null`) |
| `404` | Solo el detalle: el trámite no existe o no está publicado |
| `422` | Parámetros inválidos (en el detalle, si el id no es un UUID) |
| `502` | La API de la Ciudad no respondió o devolvió algo inesperado |

## 6. Configuración

| Variable | Por defecto |
|---|---|
| `CABA_TRAMITES_BASE_URL` | `https://buenosaires.gob.ar/jsonapi` |
| `CABA_TRAMITES_SITE_URL` | `https://buenosaires.gob.ar` |
| `CABA_TRAMITES_TIMEOUT_SECONDS` | `10.0` |

Definidas en [`back/src/conco/config.py`](../../back/src/conco/config.py).

## 7. Tests y probe

| Tipo | Ruta |
|---|---|
| Fixtures | `back/tests/fixtures/caba_tramites/`: `busqueda_habilitaci.json`, `busqueda_sin_resultados.json`, `error_400_filtro_invalido.json`, `tramite_habilitacion_actividad_economica.json`, `tramite_sin_boton_iniciar.json`, `tramite_inexistente_301.html` |
| Unitarios | `back/tests/unit/caba_tramites/test_client.py`, `back/tests/unit/guidance/test_caba_catalog.py`, `back/tests/unit/guidance/test_api.py` |
| Integración (API real) | `back/tests/integration/caba_tramites/test_client.py`, `back/tests/integration/guidance/test_api.py` |

```bash
uv run python scripts/probes/caba_tramites.py habilitaci
uv run python scripts/probes/caba_tramites.py --id 338718b4-a2a0-44af-baa4-083f5d834b12
```

## 8. Pendientes y decisiones abiertas

- Agregar `CABA_TRAMITES_*` a `back/.env.example` (tarea del usuario).
- Relacionar una actividad (por ejemplo, "cafetería") con los trámites que le corresponden: la búsqueda por título no alcanza (`caf` devuelve 0). Requiere decisión de producto.
- Costos y documentos descargables de cada trámite quedaron fuera de alcance.

## 9. Fuentes

- Catálogo: <https://buenosaires.gob.ar/gobierno/tramites>
- JSON:API: <https://buenosaires.gob.ar/jsonapi/node/tramites_obelisco>
- Especificación JSON:API 1.1: <https://jsonapi.org/format/1.1/>
- Seguimiento: [caba-tramites-integration](../../odd/tasks/caba-tramites-integration.md)

Fecha de verificación: 2026-10-31.
