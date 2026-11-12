# ADR-003: Entrada por buscador, no por IA (RN-01)

**Fecha:** 2026-11-12
**Estado:** Pendiente de validar (regla RN-01 aún no es firme)
**Contexto relacionado:** [RN-01](../REGLAS_DE_NEGOCIO.md), [RN-04](../REGLAS_DE_NEGOCIO.md), [RN-05](../REGLAS_DE_NEGOCIO.md), [PROPUESTA_TECBA.md](../PROPUESTA_TECBA.md), [APIS_CON_REGISTRO.md](../APIS_CON_REGISTRO.md)

## Contexto

La planificación original ([PROPUESTA_TECBA.md](../PROPUESTA_TECBA.md)) planteaba una consulta en lenguaje natural interpretada por IA — ej.: *"Quiero abrir una cafetería en Av. Corrientes 2500"* — como punto de entrada. En la práctica el equipo trabaja con una regla distinta: la entrada es un **buscador** con dos campos (actividad + dirección), y el rol de la IA quedó pendiente de definir.

## Decisión (en trabajo)

- La entrada es un formulario/buscador: la persona escribe la actividad y la dirección por separado.
- **No** se usa IA para interpretar la consulta inicial.
- La interpretación de la actividad la hace la búsqueda semántica de aliases (pgvector), no un LLM — es determinística, barata y auditable.
- El rol de la IA, si existe, queda acotado a preguntas de seguimiento (`submitFollowUp`) y a redacción de orientación sobre fuentes — nunca a decidir qué trámites aplican.

## Por qué

### 1. Trazabilidad y fuentes oficiales (RN-04, RN-05)

CONCO se compromete a que toda orientación esté respaldada por una fuente oficial con enlace. Un LLM interpretando la consulta inicial introduce una capa no verificable entre lo que la persona quiere y lo que el sistema entiende. El buscador + aliases mantiene el mapeo actividad → trámites en terreno curado y revisable.

### 2. Costo y operación

Un LLM en el camino crítico de cada consulta exige API key paga (Claude API está en `APIS_CON_REGISTRO.md` como candidata que requiere credenciales), latencia extra y gestión de prompts. La búsqueda por embeddings corre local con `fastembed` (int8, ~300-400 MB), sin costo por consulta.

### 3. El caso piloto no lo necesita

RN-08 acota el MVP a un caso: actividad + dirección. Dos campos estructurados cubren ese caso sin interpretación libre. El texto libre ya se resuelve en el paso "sugerencias de actividad" (embeddings), que es más simple y predecible que un LLM.

### 4. Honestidad del prototipo

RN-07 exige mostrar limitaciones. Un sistema que "adivina" con IA contradice el tono de orientación general del MVP; un buscador que dice «No encontramos una actividad parecida» es más honesto y depurable.

## Alternativas consideradas

| Alternativa | Por qué se descartó / está pendiente |
|---|---|
| Lenguaje natural interpretado por LLM (propuesta TECBA) | Costo, latencia, no determinismo, tensión con RN-04/RN-05. Queda como posible evolución si RN-01 se reabre. |
| Solo buscador textual sin embeddings | La API de trámites busca por título y falla con vocabulario coloquial ("caf" → 0 resultados). Los embeddings resuelven el puente sin IA generativa. |

## Consecuencias

**Positivas:** determinismo, costo cero por consulta, alineación con RN-04/05/07, modelo de embeddings ya resuelve el texto libre sin LLM.

**Negativas / pendiente:**

- **RN-01 sigue pendiente de validar**: falta confirmar que el buscador cumple los requisitos de *consulta inicial* e *interpretación* del MVP, y definir si la IA tiene algún rol.
- Si se aprueba IA para interpretación, el flujo `QueryForm → InterpretationConsulta` tendría que rediseñarse.
- La búsqueda semántica de **trámites** (idea en `docs/ideas/busqueda-semantica-tramites.md`) también depende de esta decisión.

## Qué revisaría esta decisión

- Validación formal de RN-01 contra los requisitos del MVP.
- Si el usuario pide interacciones más conversacionales (el front ya tiene `submitFollowUp`, hoy mock).
- Cambios en `APIS_CON_REGISTRO.md`: si Claude API se aprueba, re-evaluar este ADR.

## Referencias

- Regla: `docs/REGLAS_DE_NEGOCIO.md` RN-01 (estado: pendiente de validar)
- Plan original: `docs/PROPUESTA_TECBA.md`
- APIs con credenciales evaluadas: `docs/APIS_CON_REGISTRO.md`
- Implementación actual: `front/` (`QueryForm`, `InterpretacionConsulta`), `back/src/conco/guidance/`
