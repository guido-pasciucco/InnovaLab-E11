# Decisiones

Decisiones de diseño tomadas en CONCO: qué se eligió, por qué, y qué haría falta para revisarla. Cada decisión tiene su propio archivo con formato de ADR simplificado (contexto, decisión, alternativas, consecuencias).

Las reglas de negocio RN-01 a RN-08 viven en [`../REGLAS_DE_NEGOCIO.md`](../REGLAS_DE_NEGOCIO.md); estas ADRs documentan las decisiones de implementación que las sustentan o las extienden.

| # | Decisión | Estado | Fuente original |
|---|---|---|---|
| [001](001-tramites-curados-no-vectorizados.md) | Vectorizar actividades (aliases), no trámites | Vigente | `odd/tasks/activity-semantic-search.md` L3–L4 |
| [002](002-catalogo-curado-actividades.md) | Catálogo curado de 9 actividades, no los ~870 trámites | Vigente | `docs/pendientes/HABILITACION_Y_CATALOGO.md` |
| [003](003-entrada-buscador-no-ia.md) | Entrada por buscador, no por IA (RN-01) | Pendiente de validar | `docs/REGLAS_DE_NEGOCIO.md` RN-01 |
| [004](004-solo-apis-publicas-sin-credenciales.md) | Solo APIs públicas sin clave; credenciales para después | Reinterpretada por [005](005-embeddings-cloudflare-bge-m3.md) (token acotado para embeddings) | `docs/APIS_CON_REGISTRO.md` |
| [005](005-embeddings-cloudflare-bge-m3.md) | Embeddings vía Cloudflare Workers AI (`@cf/baai/bge-m3`), no modelo local | Vigente | PRs de `feature/cloudflare-embeddings` |
