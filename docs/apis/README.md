# APIs externas de CONCO

Referencia de cada API externa que consume el backend de CONCO: qué es, para qué la usa CONCO, cómo se la llama, cómo se comporta en la práctica y dónde está el código que la integra. Todas son **oficiales, públicas y sin clave de acceso**.

> El backend es el único punto que consume APIs externas. El frontend solo habla con la API de CONCO.

## APIs integradas

| API | Proveedor | Para qué la usa CONCO | Endpoints de CONCO | Acceso | Licencia | Documento |
|---|---|---|---|---|---|---|
| Georef | Gobierno Nacional (datos.gob.ar) | Dirección → coordenadas aproximadas; verificar que un punto esté en CABA | `GET /geolocation/addresses`, `GET /geolocation/location-check` | Sin clave | CC BY 4.0 | [georef.md](georef.md) |
| Trámites CABA (JSON:API) | Gobierno de la Ciudad (buenosaires.gob.ar) | Buscar trámites oficiales y mostrar requisitos, pasos, organismo y enlace para iniciarlos | `GET /guidance/procedures`, `GET /guidance/procedures/{procedure_id}` | Sin clave | CC BY 2.5 AR | [tramites-caba.md](tramites-caba.md) |
| USIG datos útiles | USIG, Gobierno de la Ciudad | Barrio, comuna y código postal de una dirección o un punto de CABA | `GET /geolocation/address-context`, `GET /geolocation/address-context/by-coordinates` | Sin clave | CC BY 2.5 AR | [usig-datos-utiles.md](usig-datos-utiles.md) |
| USIG EPOK | USIG, Gobierno de la Ciudad | Sedes y subsedes comunales más cercanas a un punto | `GET /geolocation/nearby-offices` | Sin clave (requiere User-Agent propio) | Sin licencia explícita; se asume CC BY 2.5 AR | [usig-epok.md](usig-epok.md) |
| Boletín Oficial CABA | Boletín Oficial, Gobierno de la Ciudad | Mostrar una ley o un decreto de la Ciudad como respaldo de un trámite | `GET /guidance/regulations/{regulation_type}/{number}/{year}` | Sin clave | Sin licencia explícita; normas de acceso público | [boletin-oficial-caba.md](boletin-oficial-caba.md) |

## Cómo leer cada documento

Todos los documentos siguen la misma estructura, para poder comparar APIs sin releer todo:

| Sección | Qué responde |
|---|---|
| 1. Ficha | Quién la provee, URL base, documentación, acceso, licencia, latencia observada y riesgos |
| 2. Para qué la usa CONCO | Ítem del MVP y reglas de negocio (RN-xx) que cubre |
| 3. Endpoints que llama CONCO | Método, ruta, parámetros, `curl` listo para copiar y respuesta real abreviada |
| 4. Comportamiento observado | Caso → qué devuelve la API → cómo lo maneja CONCO |
| 5. Cómo se integra en CONCO | Módulo de integración, adaptador, endpoint de CONCO y códigos de respuesta |
| 6. Configuración | Variables de entorno y valores por defecto |
| 7. Tests y probe | Fixtures, tests y comando para explorar la API en forma aislada |
| 8. Pendientes | Decisiones abiertas |
| 9. Fuentes | URLs y fecha de verificación |

Convenciones comunes a todas las integraciones:

- Cada API tiene un único cliente en `back/src/conco/integrations/<api>/` y un único error (`<Api>Error`). Ninguna otra capa conoce URLs, parámetros ni la forma de la respuesta.
- Ante cualquier falla de la API (timeout, error HTTP, respuesta inesperada) el endpoint de CONCO responde `502`, nunca `500`.
- Toda respuesta de CONCO incluye `source` con nombre, URL y licencia de la fuente oficial ([RN-05](../REGLAS_DE_NEGOCIO.md)).
- Los comandos de `uv run` se ejecutan desde `back/`.

## Documentos relacionados

| Documento | Para qué |
|---|---|
| [`../GUIA_INTEGRACION_APIS.md`](../GUIA_INTEGRACION_APIS.md) | Flujo paso a paso para integrar una API nueva |
| [`../APIS_CON_REGISTRO.md`](../APIS_CON_REGISTRO.md) | APIs que requieren token o registro (candidatas a futuro) |
| [`../../back/README.md`](../../back/README.md) | Estructura del backend y uso de cada endpoint |
| [`../REGLAS_DE_NEGOCIO.md`](../REGLAS_DE_NEGOCIO.md) | Reglas RN-01 a RN-08 |
| [`../MVP_SCOPE.md`](../MVP_SCOPE.md) | Alcance incluido y excluido del MVP |

> Al momento de escribir este documento, `GUIA_INTEGRACION_APIS.md` y `APIS_CON_REGISTRO.md` existen en la copia local pero todavía no están versionados en el repositorio.

## Candidatas en evaluación

APIs probadas que todavía no están integradas: [`candidatas/`](candidatas/README.md) (USIG Catastro, Ciudad 3D, habilitaciones aprobadas de la AGC, diccionario CLAE de CEP XXI, OpenStreetMap y Mapa de Oportunidades Comerciales).

## Candidatas descartadas

Se evaluaron con llamadas reales el 2026-10-31 (PR #53 y PR #57 de `guido-pasciucco/InnovaLab-E11`).

| Candidata | Motivo del descarte |
|---|---|
| BA Data (CKAN de `data.buenosaires.gob.ar`) | Bloquea las consultas del servidor con un desafío anti-bots y sus datos son descargas masivas (requieren base de datos). **Corrección del 2026-11-05:** `package_show` y `package_list` sí responden JSON y los archivos se descargan desde `cdn.buenosaires.gob.ar`; solo `package_search` sigue bloqueado. Ver [habilitaciones aprobadas](candidatas/habilitaciones-aprobadas.md) |
| datos.gob.ar (CKAN de Nación) | Sin resultados útiles para trámites de CABA |
| CLAE / nomenclador de actividades | No es consultable en vivo y es una clasificación fiscal nacional. Como descarga sí sirve: ver [CEP XXI](candidatas/cep-xxi-clae.md) |
| Guía de trámites de argentina.gob.ar | No expone una API pública |
| USIG `normalizar` | Georef ya cubre la normalización y las coordenadas |
| JSON:API de la Ciudad, `node/sedes` | Los horarios son de relleno (`00:00 a 00:00`) |
| JSON:API de la Ciudad, `node/turnos` | Responde vacío |
| Series de Tiempo (IPC) | Sin valor claro para el MVP |
| BCRA | Sin valor claro para el MVP |
| Feriados de ArgentinaDatos | No es una fuente oficial |
| InfoLEG | Solo ofrece descarga masiva |
| Padrón de AFIP | Requiere certificado |

Fecha de verificación: 2026-10-31.

### Relevamiento del 2026-11-05

Búsqueda de fuentes para relacionar la actividad con su rubro y sus trámites. Estas no tienen API utilizable o aportan poco:

| Candidata | Motivo del descarte |
|---|---|
| ARCA `soa.afip.gob.ar/sr-padron/v2` y `sr-parametros/v1/actividades` | Responden `404`: ya no existen |
| argentina.gob.ar `/jsonapi` y `/api/node/tramite` | Responden `404` |
| JSON:API de buenosaires.gob.ar para rubros | No hay tipos de contenido de rubros; `taxonomy_term/tematicas` está vacío y `search_page` pide autorización |
| Nomenclador NAES de AGIP y tabla NAES ↔ CLAE (Comisión Arbitral) | Solo PDF o Excel publicados por resolución (RG 19/2025), sin buscador |
| Rubros de la AGC por Ley 6101 y cuadro de asimilación (Decreto 87/19) | Solo PDF y normativa, sin buscador público |
| MOC en vivo | Plataforma discontinuada; quedan los [CSV históricos](candidatas/mapa-oportunidades-comerciales.md) |
| `cdn.buenosaires.gob.ar` como directorio | `403` al listar; los archivos sueltos sí se descargan |
| `hub.tumidata.org` (copia de habilitaciones) | No respondió |
| datos.jus.gob.ar (IGJ, Registro Nacional de Sociedades) | Permite consultas, pero solo hay una muestra de sociedades sin columna de actividad |
| ESCO (Comisión Europea) | Ocupaciones, no actividades comerciales; solo serviría para sinónimos |
| Wikidata (código CIIU, P1796) | Cobertura muy baja: 436 ítems y ninguno para «peluquería» |
| ANMAT, INAES, Mi Argentina | No se encontró API pública (sin verificar con llamadas) |
