# ADR-002: Catálogo curado de 9 actividades, no los 868 trámites completos

**Fecha:** 2026-11-12
**Estado:** Vigente
**Contexto relacionado:** [ADR-001](001-tramites-curados-no-vectorizados.md), [RN-04](../REGLAS_DE_NEGOCIO.md), [RN-08](../REGLAS_DE_NEGOCIO.md), [pendientes/HABILITACION_Y_CATALOGO.md](../pendientes/HABILITACION_Y_CATALOGO.md)

## Contexto

La API de trámites de CABA publica ~870 trámites. El MVP tiene un caso piloto acotado (RN-08): abrir una actividad comercial, con cafetería en Av. Corrientes 2500 como referencia. La pregunta era si convenía volcar todo el catálogo o curar un set chico de actividades con sus trámites.

## Decisión

- **Catálogo curado**: 9 actividades (cafetería, carnicería, comercio minorista, foodtruck, hotel, kiosco, óptica, peluquería, restaurante) definidas a mano en `activities.json`, con sus aliases y sus trámites asignados.
- **El set se amplía, nunca se reduce**: sacar una actividad hace que quien abre exactamente ese rubro reciba «No encontramos una actividad parecida» — una respuesta peor que una lista imperfecta.
- **El loader guarda solo los trámites referenciados** (~18 de 870), validando que cada id curado exista en la lista publicada. La limpieza es del loader, no quitando filas a mano.
- **Lo que no es trámite de la Ciudad va como nota**: requisitos sectoriales inexistentes en la API (SENASA, cadena de frío, habilitación sanitaria de óptica — Ley 7.314) se documentan en `note`, no como filas.
- **CAA como tronco común**: el Certificado de Aptitud Ambiental aplica a las 9 actividades (Ley 123: toda actividad se categoriza).

## Por qué

### 1. El caso piloto no necesita 868 trámites

RN-08 acota el MVP a "abrir una actividad comercial". Mostrar los 868 trámites de la Ciudad sería ruido: la persona busca orientación, no un directorio. La curación convierte el catálogo oficial en una respuesta accionable.

### 2. La curación es donde vive el criterio (RN-04)

Asignar trámites a rubros requiere juicio de dominio: qué aplica, en qué orden, bajo qué condición (`applies_when`), y qué explicarle a la persona. La API de CABA no expone rubros ni relaciones — solo títulos. Esa relación solo puede salir de relevamiento humano (ver `docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md`).

### 3. La base queda chica, rápida y auditable

18 trámites + 9 actividades + ~53 aliases caben en memoria, la búsqueda semántica es instantánea, y `activities.json` es revisable en git. Escalar el catálogo completo (con o sin embeddings) es trabajo de ingesta que hoy no se paga.

### 4. Ampliar es barato, reducir rompe la UX

Agregar una actividad = entrada en `activities.json` + aliases + recargar. Sacar una = usuarios de ese rubro sin respuesta. Por eso la decisión registrada es mantener/ampliar.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Volcar los 868 trámites con embeddings y buscar por similitud | Ver [ADR-001](001-tramites-curados-no-vectorizados.md): el prototipo demostró que la similitud no encuentra la habilitación correcta y no codifica aplicabilidad. Además contradice RN-04/RN-08. |
| Habilitar todos los rubros de la Ciudad como actividades | No hay fuente consultable de rubros (relevamiento 2026-11-05: NAES solo PDF, AGC sin buscador, Wikidata cobertura nula). La curación manual es la única vía. |
| Reducir el set por solapamiento de trámites | Rompe el caso "quiero X exacto" → sin sugerencia. Descartado explícitamente. |

## Consecuencias

**Positivas:** respuestas curadas y verificables; base mínima; tests de dominio (`test_repo_catalog_has_the_nine_agreed_activities`) que fijan el set acordado.

**Negativas / deuda aceptada:**

- `activities.json` es **borrador pendiente de revisión de dominio** (RN-04): cada asignación puede requerir corrección legal.
- Cobertura limitada a 9 rubros: una actividad fuera del set no tiene resultados (trade-off aceptado).
- Si RN-01 habilita búsqueda semántica sobre trámites, el loader vuelve a traer el catálogo completo — revertir parcialmente esta limpieza (costo conocido, no pérdida de datos).

## Qué revisaría esta decisión

- Ampliación del set de actividades (candidatas ya evaluadas: gimnasio quedó descartado por encuadre dudoso; hotel y óptica ya sumadas).
- Si se suman fuentes nuevas (Código Urbanístico, Boletín Oficial) que cambien el universo de "trámites aplicables".
- Si la revisión de dominio (RN-04) fuerza re-asignaciones masivas.

## Referencias

- Datos: `back/src/conco/guidance/data/activities.json`
- Loader: `back/src/conco/guidance/load_catalog.py`
- Log de decisiones: `odd/tasks/activity-semantic-search.md` (L7–L9)
- Relevamiento de dominio: `docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md`
