# ADR-001: Vectorizar actividades, no trámites

**Fecha:** 2026-11-12
**Estado:** Vigente
**Contexto relacionado:** [docs/ideas/busqueda-semantica-tramites.md](../ideas/busqueda-semantica-tramites.md), [RN-01](../REGLAS_DE_NEGOCIO.md), [MVP_SCOPE](../MVP_SCOPE.md)

## Contexto

La búsqueda de orientación del MVP resuelve dos problemas distintos:

1. **Qué actividad quiere hacer la persona.** El usuario escribe texto libre ("quiero poner una barbería") y hay que mapearlo a uno de los 9 rubros curados del catálogo (`activities`).
2. **Qué trámites le corresponden.** Una vez conocida la actividad, hay que recomendar los trámites oficiales de CABA que aplican.

La pregunta que originó esta decisión: ¿por qué el primer problema se resuelve con embeddings (pgvector) y el segundo no? ¿No sería más simple vectorizar también las descripciones de los trámites y comparar todo por similitud?

## Decisión

- **Actividades:** se vectorizan los *alias* (sinónimos) de cada actividad en `activity_aliases.embedding` (`vector(384)`, modelo `paraphrase-multilingual-MiniLM-L12-v2`). La consulta del usuario se vectoriza una vez y se compara por distancia coseno contra cada alias; por actividad gana solo el mejor alias.
- **Trámites:** NO se vectorizan. La relación actividad → trámites es una tabla curada a mano, `activity_procedures`, cargada desde `src/conco/guidance/data/activities.json` por `load_catalog`. Cada fila define `note` (explicación), `position` (orden) y `applies_when` (condiciones de contexto en jsonb).

## Por qué

### 1. Similitud semántica ≠ aplicabilidad legal

Que un trámite sea *parecido en significado* a la búsqueda no significa que *corresponda* al usuario. "Habilitación de foodtrucks" queda semánticamente cerca de "quiero abrir un local", pero no aplica a un restaurante. La aplicabilidad depende de condiciones que ningún embedding puede inferir: si el local toma una habilitación existente, si tiene empleados, si pone mesas en la vereda. Eso es exactamente lo que codifica `applies_when` — conocimiento curado, no estadístico.

Además hay evidencia empírica del prototipo (`odd/tasks/activity-semantic-search.md`, L3–L4): buscar trámites **directamente** por embedding falló — una actividad de una palabra ("cafetería") nunca rankeaba "Habilitación de actividad económica" entre los resultados. Matchar contra alias curados de actividad sí funcionó (barbería → Peluquería 0.85). Por eso los trámites se guardan **sin** embeddings y solo los alias los llevan.

### 2. La curación ES el valor del producto

`activity_procedures` no es un índice de búsqueda: es la capa de criterio que convierte "trámites parecidos" en "trámites que te tocan". Incluye la nota en lenguaje llano ("si continuás un local ya habilitado…") y el orden de presentación. Vectorizar trámites podría rankear candidatos, pero no produciría `note`, `position` ni `applies_when` sin curación manual igual — o sea, habría que mantener la tabla curada de todos modos.

### 3. La lista de actividades es cerrada y chica

Hay 9 actividades y ~54 relaciones curadas. Precomputar la respuesta cuesta casi nada y es determinística: misma entrada → mismos trámites, siempre. El costo de la búsqueda semántica se paga solo donde hace falta (texto libre → actividad), no en una relación que ya está resuelta.

### 4. Encaje con el alcance del MVP

- **RN-01** plantea "buscador, no IA": la recomendación de trámites debe ser verificable y predecible, no una caja negra de similitud.
- **MVP_SCOPE** exige orientación general con enlaces a fuentes oficiales (RN-04, RN-05): la tabla curada garantiza que solo se muestren trámites reales referenciados, con su `url` oficial.
- La idea de vectorizar trámites ya estaba evaluada en `docs/ideas/busqueda-semantica-tramites.md`, que concluye: *"Para el MVP alcanza con la alternativa precalculada"* — es decir, la relación ya resuelta. Esta ADR confirma esa alternativa como la implementación vigente.

### 5. Frescura sin costo extra

`procedures` se recarga completa desde la API oficial en cada `load_catalog` (`truncate` + insert), trayendo `changed_at` de la fuente. Si se vectorizaran trámites habría que re-embedir en esa misma corrida para no servir vectores viejos — complejidad adicional sin beneficio para el flujo actual, donde la búsqueda de trámites (`/guidance/procedures`) consulta la API en vivo por título.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Vectorizar trámites y recomendar por similitud | Similitud temática ≠ aplicabilidad; perdería `note`, `position`, `applies_when`. Ver sección 1-2. |
| Híbrido: vectores para candidatos + curación para filtrar | Válido como evolución (ver abajo), pero suma pipeline de ingesta + re-embedding sin necesidad para 18 trámites referenciados. |
| Texto libre → trámites directo (sin actividad) | El vocabulario del usuario ("mi emprendimiento") no coincide con el de la Ciudad ("Habilitación de actividad económica"); la actividad oficia de puente controlado. |

## Consecuencias

**Positivas:**

- Recomendaciones determinísticas, auditables y revisables a mano (`activities.json` es diff-able en git).
- Cero infraestructura extra: pgvector ya estaba para alias; la curación es una tabla más.
- La búsqueda semántica quedó acotada a su punto débil real: interpretar texto libre del usuario.

**Negativas / deuda aceptada:**

- Si el catálogo de actividades crece mucho o se quiere texto libre sin actividad, el modelo actual no escala solo — ver gatillos de revisión.
- La búsqueda `/guidance/procedures` sigue siendo literal por título (limitación conocida de la API de CABA: "caf" → 0 resultados).

## Qué revisaría esta decisión

- Sumar **búsqueda semántica de trámites** como feature de búsqueda libre (no de recomendación): vectores de `title + summary` como *complemento* para recall, manteniendo la curación para recomendación.
- Sumar **más fuentes** (normativa, Código Urbanístico, Boletín Oficial) donde la curación manual ya no alcance — el doc de ideas ya lo anticipa.
- Si RN-01 se redefine y se habilita IA generativa, re-evaluar embeddings en todo el pipeline.
- Si `activity_procedures` supera las ~100 relaciones curadas, evaluar tooling para mantenerla.

## Referencias de implementación

- Esquema: `back/supabase/migrations/20261105091512_create_activities.sql`, `20261105120000_add_activity_procedure_conditions.sql`
- Búsqueda: `back/src/conco/guidance/activity_directory.py` (`_SUGGEST_SQL`, `_PROCEDURES_SQL`)
- Carga: `back/src/conco/guidance/load_catalog.py`, datos en `back/src/conco/guidance/data/activities.json`
- Idea original: `docs/ideas/busqueda-semantica-tramites.md`
- Decisiones de implementación con evidencia: `odd/tasks/activity-semantic-search.md` (S3, S4, L3–L4, L7–L10)
