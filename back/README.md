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
│       ├── geolocation/        # funcionalidad: buscar direcciones para el mapa
│       │   ├── domain.py       # Address, el puerto AddressFinder y AddressSearchError
│       │   ├── infrastructure.py # adaptador que usa Georef y lo traduce al dominio
│       │   └── api.py          # endpoint GET /geolocation/addresses
│       ├── guidance/           # funcionalidad: orientación sobre trámites oficiales
│       │   ├── domain.py       # trámites, actividades y los puertos ProcedureCatalog, ActivityDirectory y TextEmbedder
│       │   ├── infrastructure.py # adaptador que usa la API de trámites de la Ciudad y pasa el HTML a texto
│       │   ├── embeddings.py   # adaptador que corre el modelo de embeddings dentro de la API
│       │   ├── activity_directory.py # adaptador que busca actividades en Postgres con pgvector
│       │   ├── load_catalog.py # comando que carga trámites y actividades en la base
│       │   ├── data/activities.json # relación curada actividad → trámites (borrador)
│       │   └── api.py          # endpoints GET /guidance/procedures y /guidance/activities
│       └── integrations/       # un paquete por cada API externa
│           ├── georef/
│           │   ├── client.py   # única ubicación de las llamadas HTTP a Georef
│           │   └── models.py   # forma de la respuesta JSON de Georef
│           └── caba_tramites/
│               ├── client.py   # única ubicación de las llamadas HTTP a la API de trámites de la Ciudad
│               └── models.py   # forma de la respuesta JSON:API de trámites
├── scripts/
│   └── probes/                 # un script por API para explorarla en forma aislada
│       ├── georef.py           # ejecuta el cliente e imprime lo que devuelve
│       └── caba_tramites.py
└── tests/
    ├── conftest.py             # configuración compartida de pytest
    ├── fixtures/               # respuestas reales guardadas, una carpeta por API
    │   ├── georef/
    │   └── caba_tramites/
    ├── unit/                   # sin internet: las APIs externas se simulan
    │   ├── georef/
    │   │   └── test_client.py
    │   ├── caba_tramites/
    │   │   └── test_client.py
    │   ├── geolocation/
    │   │   ├── test_georef_finder.py
    │   │   └── test_api.py
    │   └── guidance/
    │       ├── test_caba_catalog.py
    │       └── test_api.py
    └── integration/            # con internet: llaman a las APIs reales
        ├── georef/
        │   └── test_client.py
        ├── caba_tramites/
        │   └── test_client.py
        ├── geolocation/
        │   └── test_api.py
        └── guidance/
            └── test_api.py
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

## Búsqueda de actividades

La API de trámites solo busca por texto en el título y ningún trámite menciona actividades: «cafetería» no encuentra «Habilitación de actividad económica». Por eso la relación entre actividades y trámites es **curada**: `src/conco/guidance/data/activities.json` dice, para cada actividad, qué trámites suelen aplicar y en qué caso. Es un **borrador** que tiene que revisar alguien que conozca el tema (RN-04).

Para entender lo que escribe la persona se usan **embeddings**: un modelo multilingüe convierte cada nombre y sinónimo de actividad en un vector de 384 números, y la consulta se compara por similitud coseno. Así, «quiero poner una barbería» sugiere «Peluquería» aunque no compartan palabras.

- El modelo (`paraphrase-multilingual-MiniLM-L12-v2`, ONNX con `fastembed`) corre **dentro de la API**, detrás del puerto `TextEmbedder`. Se carga en segundo plano al arrancar y ocupa unos 600 MB de RAM. La primera vez se descarga (~220 MB).
- Los datos viven en Postgres con la extensión pgvector. En desarrollo se usa el Supabase local de `back/supabase/` (solo la base de datos, puerto `55322`).
- Por debajo de `ACTIVITY_MIN_SIMILARITY` (0.5) no se sugiere nada. Con palabras cortas o poco comunes el modelo puede dar similitudes altas sin sentido, por eso el frontend muestra las sugerencias para que la persona elija, en vez de elegir solo.

### Levantar la base y cargar los datos

Desde la carpeta `back/` (necesita Docker):

```bash
npx supabase start -x gotrue,realtime,storage-api,imgproxy,kong,mailpit,postgrest,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
uv run python -m conco.guidance.load_catalog
```

`supabase start` aplica las migraciones de `supabase/migrations/`. `load_catalog` trae los 868 trámites publicados, valida el archivo curado y vectoriza los alias; se vuelve a correr cada vez que cambia `activities.json` o para actualizar los trámites. `npx supabase db reset` borra la base y vuelve a aplicar las migraciones (después hay que volver a cargar los datos).

| Variable | Valor por defecto |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@127.0.0.1:55322/postgres` |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (si cambia, hay que volver a cargar los datos) |
| `ACTIVITY_MIN_SIMILARITY` | `0.5` |

### `GET /guidance/activities`

Sugiere actividades parecidas por significado al texto.

| Parámetro | Obligatorio | Valor por defecto | Validación |
|---|---|---|---|
| `query` | Sí | — | Entre 2 y 100 caracteres, no solo espacios |
| `limit` | No | `5` | Entre 1 y 10 |

Respuesta (`200`): `{"activities": [{"slug": "peluqueria", "name": "Peluquería", "matched_alias": "barbería", "similarity": 0.8512}]}`, de la más a la menos parecida. La lista puede venir vacía.

### `GET /guidance/activities/{slug}/procedures`

Devuelve los trámites que suelen aplicar a la actividad, en el orden en que conviene revisarlos. Las respuestas de contexto son opcionales (`true` o `false`) y descartan los trámites que no corresponden:

| Parámetro | Pregunta |
|---|---|
| `has_employees` | ¿Vas a contratar personal? |
| `under_200_m2` | ¿El local tiene menos de 200 m²? |
| `sidewalk_tables` | ¿Vas a poner mesas y sillas en la vereda? |
| `signage` | ¿Vas a poner un cartel, una marquesina o un toldo? |
| `protected_building` | ¿El inmueble está en un área de protección histórica (APH) o está catalogado? |
| `takes_over_existing` | ¿Vas a continuar un local que ya está habilitado? |

Respuesta (`200`): `{"activity": {"slug", "name"}, "questions": [{"id": "has_employees", "text": "¿Vas a contratar personal?", "answer": null}], "procedures": [{"procedure": {...}, "note": "Si vas a contratar personal.", "status": "may_apply"}], "excluded_count": 0, "source": {...}}`.

- `questions` trae solo las preguntas que usa esa actividad, con la respuesta recibida (`null` si no se respondió).
- Cada `procedure` tiene los mismos campos que en la búsqueda de trámites; `note` dice en qué caso aplica.
- `status` es `applies` si el trámite no tiene condiciones o todas se cumplen, y `may_apply` si falta responder alguna.
- `excluded_count` cuenta los trámites descartados por las respuestas.

Las condiciones de cada trámite están en `applies_when` dentro de `src/conco/guidance/data/activities.json`. Al cambiarlas, hay que volver a correr la carga.

| Respuesta | Cuándo |
|---|---|
| `200` | La consulta funcionó |
| `404` | La actividad no existe (solo los trámites) |
| `422` | Los parámetros no cumplen la validación (el `slug` va en minúsculas, con números y guiones; las respuestas, `true` o `false`; no se aceptan preguntas desconocidas) |
| `503` | La base de datos no está disponible |

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
| `uv run pytest -m database` | Tests contra la base local. Necesitan la base levantada y los datos cargados con `load_catalog`. |
