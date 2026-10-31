# Backend

API de "CONCO", Sistema Inteligente de Gestión, Consultas, Comerciales, Para Emprendedores.

El backend es el único punto que consume APIs externas. El frontend se comunica solamente con esta API.

> **Estado:** estructura planificada. Este documento describe cómo se organizará el backend para integrar la primera API externa (Georef). El código actual en `app/` será reemplazado por esta estructura.

## Responsabilidades

1. Recibir solicitudes de consulta.
2. Validar los datos de entrada.
3. Proporcionar orientación general sobre los procedimientos.
4. Ofrecer enlaces de referencia oficiales.
5. Geocodificar una dirección para mostrar una ubicación aproximada en el mapa.
6. Informar barrio, comuna y código postal de una dirección o un punto de CABA.
7. Mostrar leyes y decretos de la Ciudad publicados en el Boletín Oficial, como referencia de la normativa que respalda un trámite.
8. Indicar las sedes y subsedes comunales más cercanas a un punto de CABA, para la atención presencial.

## Tecnologías

| Herramienta | Uso |
|---|---|
| Python | Lenguaje del backend |
| FastAPI | Framework de la API |
| Pydantic | Validación y modelado de datos |
| uv | Gestión de dependencias y entorno virtual |
| httpx | Cliente HTTP para consumir APIs externas |

## Estructura planificada (mínima)

```
back/
├── pyproject.toml              # dependencias y configuración de herramientas
├── .env.example                # plantilla de variables de entorno, sin secretos
├── src/
│   └── conco/
│       ├── main.py             # crea la app de FastAPI y configura CORS
│       ├── config.py           # lee las variables de entorno con tipos
│       ├── geolocation/        # funcionalidad: buscar direcciones para el mapa, ubicarlas en CABA y encontrar oficinas cercanas
│       │   ├── domain.py       # Address, AddressContext, NearbyOffice, Source, los puertos AddressFinder, AddressContextProvider y NearbyOfficeFinder y sus errores
│       │   ├── infrastructure.py # adaptadores que usan Georef, USIG y EPOK y los traducen al dominio
│       │   └── api.py          # endpoints GET /geolocation/addresses, /geolocation/address-context y /geolocation/nearby-offices
│       ├── guidance/           # funcionalidad: orientación sobre trámites oficiales
│       │   ├── domain.py       # Procedure, ProcedureDetail, Regulation, Source, los puertos ProcedureCatalog y RegulationRegistry y sus errores
│       │   ├── infrastructure.py # adaptadores que usan la API de trámites y el Boletín Oficial de la Ciudad
│       │   └── api.py          # endpoints GET /guidance/procedures, /guidance/procedures/{procedure_id} y /guidance/regulations/...
│       └── integrations/       # un paquete por cada API externa
│           ├── georef/
│           │   ├── client.py   # única ubicación de las llamadas HTTP a Georef
│           │   └── models.py   # forma de la respuesta JSON de Georef
│           ├── caba_tramites/
│           │   ├── client.py   # única ubicación de las llamadas HTTP a la API de trámites de la Ciudad
│           │   └── models.py   # forma de la respuesta JSON:API de trámites
│           ├── usig/
│           │   ├── client.py   # única ubicación de las llamadas HTTP a USIG (datos útiles)
│           │   └── models.py   # forma de la respuesta de datos útiles (solo los campos usados)
│           ├── boletin_oficial/
│           │   ├── client.py   # única ubicación de las llamadas HTTP al Boletín Oficial de la Ciudad
│           │   └── models.py   # forma de la respuesta de búsqueda de normas
│           └── epok/
│               ├── client.py   # única ubicación de las llamadas HTTP a EPOK (lugares de la Ciudad)
│               └── models.py   # forma de las respuestas de lugares cercanos y de contenido de un lugar
├── scripts/
│   └── probes/                 # un script por API para explorarla en forma aislada
│       ├── georef.py           # ejecuta el cliente e imprime lo que devuelve
│       ├── caba_tramites.py
│       ├── usig.py
│       ├── boletin_oficial.py
│       └── epok.py
└── tests/
    ├── conftest.py             # configuración compartida de pytest
    ├── fixtures/               # respuestas reales guardadas, una carpeta por API
    │   ├── georef/
    │   ├── caba_tramites/
    │   ├── usig/
    │   ├── boletin_oficial/
    │   └── epok/
    ├── unit/                   # sin internet: las APIs externas se simulan
    │   ├── georef/
    │   │   └── test_client.py
    │   ├── caba_tramites/
    │   │   └── test_client.py
    │   ├── usig/
    │   │   └── test_client.py
    │   ├── boletin_oficial/
    │   │   └── test_client.py
    │   ├── epok/
    │   │   └── test_client.py
    │   ├── geolocation/
    │   │   ├── test_georef_finder.py
    │   │   ├── test_usig_context_provider.py
    │   │   ├── test_epok_nearby_office_finder.py
    │   │   ├── test_api.py
    │   │   ├── test_address_context_api.py
    │   │   └── test_nearby_offices_api.py
    │   └── guidance/
    │       ├── test_caba_catalog.py
    │       ├── test_boletin_oficial_registry.py
    │       ├── test_api.py
    │       └── test_regulations_api.py
    └── integration/            # con internet: llaman a las APIs reales
        ├── georef/
        │   └── test_client.py
        ├── caba_tramites/
        │   └── test_client.py
        ├── usig/
        │   └── test_client.py
        ├── boletin_oficial/
        │   └── test_client.py
        ├── epok/
        │   └── test_client.py
        ├── geolocation/
        │   ├── test_api.py
        │   ├── test_address_context_api.py
        │   └── test_nearby_offices_api.py
        └── guidance/
            ├── test_api.py
            └── test_regulations_api.py
```

Cada carpeta con código Python dentro de `src/` incluye un archivo `__init__.py`, que la convierte en un paquete importable. Las carpetas de `tests/` no lo necesitan.

> **No confundir:** `src/conco/integrations/` agrupa las **integraciones con APIs externas**, mientras que `tests/integration/` agrupa un **tipo de test** (el que usa internet). Los tests de una API se ubican en `tests/unit/<api>/` y `tests/integration/<api>/`.

## Qué hace cada parte

| Parte | Responsabilidad | No hace |
|---|---|---|
| `main.py` | Crea la app, registra el middleware de CORS y los routers | Consumir APIs externas |
| `<funcionalidad>/domain.py` | Define los conceptos propios del sistema y el puerto que necesita | Conocer APIs externas |
| `<funcionalidad>/infrastructure.py` | Implementa el puerto usando una integración y traduce sus datos al dominio | Exponer endpoints |
| `<funcionalidad>/api.py` | Valida la consulta HTTP y traduce errores a códigos HTTP | Conocer qué API externa se usa |
| `config.py` | Expone URLs y orígenes permitidos leídos del `.env` | Contener valores hardcodeados |
| `integrations/<api>/client.py` | Hace la llamada HTTP a una API externa | Conocer reglas de negocio |
| `integrations/<api>/models.py` | Describe la respuesta de esa API | Representar conceptos propios del sistema |
| `scripts/probes/<api>.py` | Permite explorar una API en forma aislada | Formar parte de la app en producción |
| `tests/unit/<api>/` | Prueba el cliente simulando la API con respuestas reales guardadas | Usar internet |
| `tests/integration/<api>/` | Comprueba que la API real siga respondiendo como se espera | Correrse por defecto (`uv run pytest -m integration`) |

**Regla principal:** solo los archivos dentro de `integrations/<api>/` conocen los detalles de esa API (URLs, parámetros y formato de respuesta).

## Primera API: Georef

| Dato | Valor |
|---|---|
| Proveedor | Gobierno Nacional (datos.gob.ar) |
| Endpoint | `GET https://apis.datos.gob.ar/georef/api/direcciones` |
| Uso en CONCO | Convertir una dirección en coordenadas para el mapa |
| Parámetros principales | `direccion`, `provincia=caba`, `max` |

Ejemplo de respuesta (abreviado), obtenido con `direccion=Corrientes 2500`:

```json
{
  "cantidad": 1,
  "direcciones": [
    {
      "nomenclatura": "AV CORRIENTES 2500, Comuna 3, Ciudad Autónoma de Buenos Aires",
      "calle": { "nombre": "AV CORRIENTES", "categoria": "AV" },
      "altura": { "valor": 2500 },
      "departamento": { "nombre": "Comuna 3" },
      "ubicacion": { "lat": -34.6047, "lon": -58.4021 }
    }
  ],
  "total": 1
}
```

## Endpoint de geolocalización

`GET /geolocation/addresses` convierte una dirección escrita libremente en direcciones normalizadas con coordenadas aproximadas.

| Parámetro | Obligatorio | Valor por defecto | Validación |
|---|---|---|---|
| `address` | Sí | — | Entre 3 y 200 caracteres, no solo espacios |
| `province` | No | `caba` | Nombre o id de provincia de Georef |
| `limit` | No | `5` | Entre 1 y 10 |

| Respuesta | Cuándo |
|---|---|
| `200` con `{"addresses": [...]}` | La búsqueda funcionó; la lista puede venir vacía |
| `422` | Los parámetros no cumplen la validación |
| `502` | Georef no respondió o devolvió algo inesperado |

`coordinates` puede venir en `null` cuando Georef no tiene datos suficientes para ubicar la dirección.

Para probarlo a mano, levantar la API y abrir `http://127.0.0.1:8000/docs`:

```bash
uv run uvicorn conco.main:app --reload
```

## Segunda API: trámites de la Ciudad de Buenos Aires

| Dato | Valor |
|---|---|
| Proveedor | Gobierno de la Ciudad de Buenos Aires (buenosaires.gob.ar) |
| Endpoint | `GET https://buenosaires.gob.ar/jsonapi/node/tramites_obelisco` (búsqueda) y `.../tramites_obelisco/{uuid}` (detalle) |
| Formato | JSON:API de Drupal, sin clave de acceso |
| Licencia | Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR) |
| Uso en CONCO | Buscar trámites oficiales y mostrar requisitos, pasos, organismo y enlace para iniciarlos |
| Parámetros principales | `filter[status]=1`, `filter[title][operator]=CONTAINS`, `filter[title][value]`, `sort=title`, `page[limit]`, `include` y `fields[...]` |

**Limitaciones:**

- La API no tiene documentación pública: es el JSON:API que Drupal expone por defecto. Su forma puede cambiar sin aviso; el test de integración es la alerta temprana.
- La búsqueda es solo por texto en el título (no distingue mayúsculas ni acentos). No hay búsqueda por actividad ni por relevancia.
- El contenido de cada trámite está armado con párrafos anidados (requisitos, pasos, organismo, botón para iniciar). El cliente pide solo esos párrafos y descarta el resto (costos, normativa, textos de ayuda).
- Un id inexistente o no publicado no devuelve 404: redirige (301) a una página HTML. El cliente lo informa como "no encontrado".
- Sin `filter[status]=1`, las páginas vienen incompletas porque la API omite los trámites no publicados.

Ejemplo de respuesta de la búsqueda (abreviado), obtenido con `filter[title][value]=habilitaci`:

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

## Endpoints de orientación sobre trámites

Toda respuesta incluye `source` (nombre, URL y licencia de la fuente oficial) y cada trámite incluye `official_url`, el enlace a su página oficial (RN-05). La información es orientación general: la persona debe verificarla con el organismo responsable (RN-04, RN-07).

### `GET /guidance/procedures`

Busca trámites oficiales por su nombre.

| Parámetro | Obligatorio | Valor por defecto | Validación |
|---|---|---|---|
| `query` | Sí | — | Entre 3 y 100 caracteres, no solo espacios |
| `limit` | No | `10` | Entre 1 y 20 |

Respuesta (`200`): `{"procedures": [...], "source": {...}}`. Cada trámite tiene `id`, `title`, `official_url`, `summary` (texto plano) y `last_updated`. La lista puede venir vacía.

### `GET /guidance/procedures/{procedure_id}`

Devuelve el detalle de un trámite a partir del `id` que entrega la búsqueda.

Respuesta (`200`): `{"procedure": {...}, "source": {...}}`. Además de los datos del resumen, el trámite incluye `requirements` y `steps` (listas de textos planos, en el orden de la página oficial), `responsible_office` y `start_url` (enlace oficial para iniciar el trámite). Estos dos últimos pueden venir en `null`.

| Respuesta | Cuándo |
|---|---|
| `200` | La consulta funcionó |
| `404` | El trámite no existe o no está publicado (solo el detalle) |
| `422` | Los parámetros no cumplen la validación (en el detalle, si el id no es un UUID) |
| `502` | La API de la Ciudad no respondió o devolvió algo inesperado |

Para explorar la API en forma aislada:

```bash
uv run python scripts/probes/caba_tramites.py habilitaci
uv run python scripts/probes/caba_tramites.py --id 338718b4-a2a0-44af-baa4-083f5d834b12
```

## Tercera API: USIG (datos útiles)

| Dato | Valor |
|---|---|
| Proveedor | Unidad de Sistemas de Información Geográfica (USIG), Gobierno de la Ciudad de Buenos Aires |
| Endpoint | `GET https://ws.usig.buenosaires.gob.ar/datos_utiles` |
| Documentación | `http://usig.buenosaires.gob.ar/apis/` (por `https` el certificado del sitio de documentación no valida; la API sí funciona por `https`) |
| Acceso | Sin clave de acceso |
| Licencia | Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR) |
| Uso en CONCO | Informar barrio, comuna y código postal de una dirección o de un punto de CABA |
| Parámetros | `calle` y `altura`, o bien `x` (longitud) e `y` (latitud) en WGS84 |

**Limitaciones:**

- Todas las respuestas llegan con estado `200`, incluso los errores: si no encuentra la dirección devuelve el texto plano `ERROR: No se pudo normalizar o geocodificar la dirección.`; si faltan parámetros o no son números, devuelve una página de ayuda en HTML; si el punto está fuera de la Ciudad, devuelve JSON con `comuna` y `barrio` vacíos. El cliente informa la dirección no encontrada y el punto fuera de la Ciudad como "no encontrado" (`404` en los endpoints) y la página de ayuda como error (`502`).
- El `Content-Type` no es confiable: por calle y altura declara `text/javascript` aunque el cuerpo es JSON. El cliente interpreta el cuerpo sin mirarlo.
- Por coordenadas no se informan códigos postales.
- La normalización de calles es estricta: por ejemplo, `Avenida de Mayo 500` no se encuentra.
- La respuesta también trae `seccion_catastral` y `codigo_de_planeamiento_urbano`. CONCO **no** los usa ni los expone: no informa catastro ni zonificación (RN-04).
- El servidor es antiguo; el cliente usa un tiempo máximo de espera (`USIG_TIMEOUT_SECONDS`) y ante cualquier falla responde con un error controlado.

Ejemplo de respuesta (abreviado), obtenido con `calle=Corrientes&altura=2500`:

```json
{
  "comuna": "Comuna 3",
  "barrio": "Balvanera",
  "codigo_postal": "1046",
  "codigo_postal_argentino": "C1046AAP"
}
```

## Endpoints de contexto de una dirección en CABA

Informan barrio, comuna y códigos postales de una ubicación dentro de la Ciudad (RN-02). Toda respuesta incluye `source` con nombre, URL y licencia de la fuente oficial (RN-05). No informan catastro ni zonificación (RN-04).

### `GET /geolocation/address-context`

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `street` | Sí | Entre 2 y 100 caracteres, no solo espacios |
| `number` | Sí | Entero entre 1 y 99999 |

### `GET /geolocation/address-context/by-coordinates`

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `latitude` | Sí | Entre -90 y 90 |
| `longitude` | Sí | Entre -180 y 180 |

Se validan solo los rangos generales de latitud y longitud: un punto fuera de CABA responde `404`, porque USIG no lo ubica en la Ciudad.

Respuesta (`200`) de ambos endpoints:

```json
{
  "context": {
    "neighborhood": "Balvanera",
    "commune": "Comuna 3",
    "postal_code": "1046",
    "argentine_postal_code": "C1046AAP"
  },
  "source": {
    "name": "USIG - Datos útiles (Gobierno de la Ciudad de Buenos Aires)",
    "url": "http://usig.buenosaires.gob.ar/apis/",
    "license": "Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR)"
  }
}
```

`postal_code` y `argentine_postal_code` pueden venir en `null` (por coordenadas siempre vienen en `null`).

| Respuesta | Cuándo |
|---|---|
| `200` | La ubicación está en CABA |
| `404` | USIG no encuentra la dirección o la ubicación está fuera de CABA |
| `422` | Los parámetros no cumplen la validación |
| `502` | USIG no respondió o devolvió algo inesperado |

Para explorar la API en forma aislada:

```bash
uv run python scripts/probes/usig.py Corrientes 2500
uv run python scripts/probes/usig.py --coords -34.604792 -58.401981   # latitud longitud
```

## Cuarta API: Boletín Oficial de la Ciudad de Buenos Aires

| Dato | Valor |
|---|---|
| Proveedor | Boletín Oficial de la Ciudad de Buenos Aires, Gobierno de la Ciudad de Buenos Aires |
| Endpoint | `GET https://api-restboletinoficial.buenosaires.gob.ar/obtenerResultado/tipoNorma=<id>&nNorma=<número>&anio=<año>` |
| Documentación | `https://api-restboletinoficial.buenosaires.gob.ar/api/doc/` |
| Sitio que se cita | `https://boletinoficial.buenosaires.gob.ar` |
| Acceso | Sin clave de acceso |
| Licencia | Sin licencia explícita. Las normas son actos oficiales de publicación obligatoria y acceso público; se cita la fuente |
| Uso en CONCO | Mostrar una ley o un decreto de la Ciudad (resumen, organismo, fecha, edición del Boletín y PDF) como respaldo de un trámite |
| Tipos de norma | `tipoNorma=1` (Ley) y `tipoNorma=2` (Decreto), según `GET /obtenerFiltrosDeBusqueda` |

**Limitaciones:**

- Los filtros van **dentro de la ruta**, separados por `&`, no en la query string. httpx los envía tal cual.
- El año del filtro debe tener cuatro dígitos (`anio=18` no encuentra nada), pero la respuesta lo devuelve con dos (`"anio_norma": 18`).
- Se envían siempre tipo, número y año: sin tipo se mezclan tipos de norma y sin año se mezclan años (el Decreto 40 sin año devuelve 17 normas). El cliente vuelve a filtrar la respuesta por tipo, número y año, y descarta normas repetidas (el Decreto 40/2025 llega dos veces).
- Un mismo tipo, número y año puede corresponder a **más de una norma**: el Poder Ejecutivo y la Legislatura numeran sus decretos por separado (Decreto 40/2022 devuelve dos). Por eso el endpoint devuelve una lista.
- Solo se admiten leyes y decretos. Las resoluciones y disposiciones se numeran por organismo: la Resolución 100/2019 devuelve 41 normas de organismos distintos.
- Sin resultados, la API responde `200` con `"normas": 0` (un número, no una lista). Con un filtro inválido responde `200` con el texto HTML `No hay criterio de búsqueda válido seleccionado`; el cliente lo trata como error (`502`).
- Los enlaces de descarga llegan como `http://.../download/<id>` y redirigen a `https://`; el cliente los expone con `https://`. En normas antiguas el enlace al documento llega vacío y el organismo (`nombre_reparticion`) en `null`.
- La búsqueda por palabras (`palabras`) busca la frase exacta y da resultados pobres: no se usa.
- `GET /getUrlDocument/...` responde con un cuerpo vacío: no se usa.

Ejemplo de respuesta (abreviado), obtenido con `tipoNorma=1&nNorma=6101&anio=2018`:

```json
{
  "normas": [
    {
      "id": 435567,
      "nombre_tipo": "Ley",
      "numero_norma": 6101,
      "anio_norma": 18,
      "sumario": "Ley Marco de Regulación de actividades económicas de la Ciudad Autónoma de Buenos Aires",
      "nombre_reparticion": "Legislatura de la Ciudad de Buenos Aires",
      "boletines": [["5526", "27/12/2018", "http://api-restboletinoficial.buenosaires.gob.ar/download/1255814"]],
      "link_documento_normas": [["27/12/2018", "http://api-restboletinoficial.buenosaires.gob.ar/download/1255476"]]
    }
  ]
}
```

## Endpoint de normas de la Ciudad

### `GET /guidance/regulations/{regulation_type}/{number}/{year}`

Busca una ley o un decreto de la Ciudad en el Boletín Oficial. La norma se muestra como **referencia de la fuente oficial**: CONCO no interpreta su alcance ni determina si se aplica a un caso concreto (RN-04). La respuesta incluye `source` con nombre, URL y licencia de la fuente (RN-05).

| Parámetro | Validación |
|---|---|
| `regulation_type` | `ley` o `decreto` |
| `number` | Entero mayor o igual a 1 |
| `year` | Año con cuatro dígitos, entre 1900 y 2100 |

Respuesta (`200`) de `GET /guidance/regulations/ley/6101/2018`:

```json
{
  "regulations": [
    {
      "type": "ley",
      "number": 6101,
      "year": 2018,
      "summary": "Ley Marco de Regulación de actividades económicas de la Ciudad Autónoma de Buenos Aires",
      "issuing_body": "Legislatura de la Ciudad de Buenos Aires",
      "publication_date": "2018-12-27",
      "bulletin_number": 5526,
      "document_url": "https://api-restboletinoficial.buenosaires.gob.ar/download/1255476"
    }
  ],
  "source": {
    "name": "Boletín Oficial de la Ciudad de Buenos Aires",
    "url": "https://boletinoficial.buenosaires.gob.ar",
    "license": "Sin licencia explícita: normas oficiales de publicación obligatoria y acceso público"
  }
}
```

`regulations` puede tener más de un elemento (por ejemplo, `decreto/40/2022`). `issuing_body` y `document_url` pueden venir en `null` en normas antiguas.

| Respuesta | Cuándo |
|---|---|
| `200` | Se encontró al menos una norma |
| `404` | No hay normas con ese tipo, número y año |
| `422` | Los parámetros no cumplen la validación |
| `502` | El Boletín Oficial no respondió o devolvió algo inesperado |

Para explorar la API en forma aislada:

```bash
uv run python scripts/probes/boletin_oficial.py ley 6101 2018
uv run python scripts/probes/boletin_oficial.py decreto 40 2019
```

## Quinta API: USIG EPOK (lugares de la Ciudad)

| Dato | Valor |
|---|---|
| Proveedor | USIG - EPOK, Gobierno de la Ciudad de Buenos Aires |
| Endpoints | `GET https://epok.buenosaires.gob.ar/reverseGeocoderLugares/?x=<longitud>&y=<latitud>&categorias=<ids>&radio=<metros>` y `GET https://epok.buenosaires.gob.ar/getObjectContent/?id=<id>` |
| Sitio que se cita | `https://epok.buenosaires.gob.ar` |
| Acceso | Sin clave de acceso |
| Licencia | Sin licencia explícita; se asume Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), como el resto de los datos de la Ciudad, y se cita la fuente |
| Uso en CONCO | Indicar las sedes y subsedes comunales más cercanas a un punto, para la atención presencial |
| Categoría usada | `sedes_de_comunas` (constante `COMMUNE_OFFICES_CATEGORY` en `integrations/epok/client.py`) |

**Limitaciones:**

- **User-Agent:** un filtro del servidor corta la conexión, sin respuesta, cuando la consulta llega con el User-Agent por defecto de curl. El cliente envía siempre su propio User-Agent (`EPOK_USER_AGENT`, por defecto `CONCO/0.1`) para no depender del que trae la librería. Con curl hay que pasar otro, por ejemplo `curl -A "CONCO/0.1" ...`.
- La búsqueda es en dos pasos: `reverseGeocoderLugares` devuelve id, nombre y distancia de cada lugar, y `getObjectContent` devuelve su dirección, teléfonos, barrio, comuna y la página de trámites. El adaptador pide el contenido de las oficinas elegidas en paralelo (cada consulta tarda entre 0,05 y 0,2 s).
- Los lugares **no** llegan ordenados por distancia, y la distancia (en metros) llega como texto: el cliente la convierte a número y ordena.
- `radio` es obligatorio (sin él no hay resultados). El radio se configura con `EPOK_RADIUS_METERS` (por defecto 3000 m).
- Sin resultados, con una categoría desconocida o sin coordenadas, responde `200` con `"instancias": []`: CONCO lo informa como lista vacía, no como error. Un id inexistente en `getObjectContent` responde `{}`: esa oficina se omite.
- Todas las respuestas declaran `Content-Type: text/javascript` aunque el cuerpo es JSON. El cliente interpreta el cuerpo sin mirarlo; un cuerpo vacío o que no es JSON es un error (`502`).
- La página de trámites llega como HTML (`<a href="...">Página web</a>`): se expone solo el enlace `http`/`https`.
- Los textos se informan como los publica EPOK (por ejemplo, el barrio en mayúsculas y la dirección como `URIBURU JOSE E., Pres. 1022`). La ubicación viene en coordenadas GKBA, no WGS84: no se usa.
- EPOK publica 182 categorías. Otras posiblemente útiles (`oficinas_de_empleo`, `centros_integracion_laboral`, `comunas_sstrabajo`) se pueden sumar agregando su id; `centros_comerciales` está desactualizada (2008).

Ejemplo de respuesta (abreviado) de `reverseGeocoderLugares` con `x=-58.4021372&y=-34.6047137&categorias=sedes_de_comunas&radio=3000`:

```json
{
  "totalFull": 7,
  "instancias": [
    {"nombre": "Subsede Comunal 3", "id": "sedes_de_comunas|3", "distancia": "962.53"},
    {"nombre": "Sede Comunal 2", "id": "sedes_de_comunas|2", "distancia": "940.95"}
  ],
  "total": 7
}
```

## Endpoint de oficinas cercanas

### `GET /geolocation/nearby-offices`

Lista las sedes y subsedes comunales más cercanas a un punto, ordenadas por distancia. Toda respuesta incluye `source` con nombre, URL y licencia de la fuente oficial (RN-05).

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `latitude` | Sí | Entre -90 y 90 |
| `longitude` | Sí | Entre -180 y 180 |
| `limit` | No (por defecto 3) | Entero entre 1 y 5 |

Respuesta (`200`) de `GET /geolocation/nearby-offices?latitude=-34.6047137&longitude=-58.4021372&limit=1`:

```json
{
  "offices": [
    {
      "name": "Sede Comunal 2",
      "address": "URIBURU JOSE E., Pres. 1022",
      "phone": "4370-9702",
      "neighborhood": "RECOLETA",
      "commune": "Comuna 2",
      "distance_meters": 940.95,
      "info_url": "https://buenosaires.gob.ar/jefaturadegabinete/atencion-ciudadana-y-gestion-comunal/gestion-comunal/comuna-2",
      "last_updated": "2024-04-11"
    }
  ],
  "source": {
    "name": "USIG - EPOK (Gobierno de la Ciudad de Buenos Aires)",
    "url": "https://epok.buenosaires.gob.ar",
    "license": "Sin licencia explícita; se asume Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), como el resto de los datos de la Ciudad"
  }
}
```

`phone`, `neighborhood`, `commune`, `info_url` y `last_updated` pueden venir en `null`. `last_updated` es la fecha de la última modificación del dato en EPOK. Una oficina sin contenido o sin dirección en EPOK se omite, por lo que la lista puede tener menos elementos que `limit`.

| Respuesta | Cuándo |
|---|---|
| `200` | Siempre que EPOK responda; `offices` vacía si no hay oficinas en el radio (por ejemplo, un punto alejado de la Ciudad) |
| `422` | Los parámetros no cumplen la validación |
| `502` | EPOK no respondió o devolvió algo inesperado |

Para explorar la API en forma aislada:

```bash
uv run python scripts/probes/epok.py -34.6047137 -58.4021372         # latitud longitud
uv run python scripts/probes/epok.py -34.6047137 -58.4021372 1000    # radio en metros
```

## Cómo incorporar una API nueva

Cada API se integra y se prueba por separado, en este orden:

1. Crear `src/conco/integrations/<api>/client.py` con la llamada HTTP.
2. Crear `scripts/probes/<api>.py` y ejecutarlo para observar la respuesta real.
3. Con esa respuesta, definir `src/conco/integrations/<api>/models.py`.
4. Agregar la URL base de la API a `.env.example` y a `config.py`.
5. Guardar respuestas reales en `tests/fixtures/<api>/` y escribir los tests en `tests/unit/<api>/` y `tests/integration/<api>/`.

Primero se observa la respuesta y después se modela. No se escriben modelos a partir de suposiciones.

## Convenciones

| Tema | Convención |
|---|---|
| Nombres de archivos y funciones | `snake_case` |
| Nombres de clases | `PascalCase` |
| Tipos | Type hints en todas las funciones |
| Configuración | Toda URL o valor variable se lee desde `config.py`, nunca se hardcodea |
| Idioma del código | Inglés para identificadores; español para documentación del proyecto |

## Crecimiento previsto

Cada funcionalidad que expone un endpoint tiene su carpeta (`geolocation/` y `guidance/` ya existen), con capas de dominio, infraestructura y API. La capa de aplicación (casos de uso) se agregará cuando haya lógica que coordinar, por ejemplo caché o combinar varias APIs; mientras tanto, el endpoint usa el puerto directamente.

## Checklist de la primera integración

- [x] `pyproject.toml` creado con FastAPI, Pydantic y httpx
- [x] `src/conco/main.py` y `config.py` creados
- [x] `integrations/georef/client.py` realiza la consulta de direcciones
- [x] `scripts/probes/georef.py` imprime la respuesta de Georef
- [x] `integrations/georef/models.py` refleja la respuesta observada

## Tests

Desde la carpeta `back/`:

| Comando | Qué ejecuta |
|---|---|
| `uv run pytest` | Tests unitarios. No usan internet: simulan las APIs externas con `respx` y respuestas reales guardadas en `tests/fixtures/`. |
| `uv run pytest -m integration` | Tests de integración. Llaman a las APIs reales, por lo que necesitan internet y que el servicio esté disponible. |
