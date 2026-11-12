# ADR-005: Embeddings vía Cloudflare Workers AI (bge-m3), no modelo local

**Fecha:** 2026-11-12
**Estado:** Vigente
**Contexto relacionado:** [ADR-001](001-tramites-curados-no-vectorizados.md), [ADR-003](003-entrada-buscador-no-ia.md), [ADR-004](004-solo-apis-publicas-sin-credenciales.md), [REGLAS_DE_NEGOCIO.md](../REGLAS_DE_NEGOCIO.md)

## Contexto

La búsqueda semántica de actividades usaba `paraphrase-multilingual-MiniLM-L12-v2` (384 dims, Apache-2.0) con `fastembed` corrriendo dentro del proceso de la API: ~220 MB de descarga la primera vez, ~600 MB de RAM en runtime. Dos fricciones la estaban tensando:

1. **Calidad en español.** En MTEB(Multilingual, v2) la submuestra española da Mean(Task) **46.32** para MiniLM(L12-v2), contra **64.76** para `bge-m3` (BAAI, MIT, 1024 dims) — rankeado ~#15/225, con cobertura ~87%.
2. **Deploy.** El objetivo de despliegue (Render, free tier de 512 MB RAM) deja poco margen con un modelo ONNX in-process; Cloudflare Workers AI ofrece 10.000 neurons/día gratis (~9,3M tokens de bge-m3/día, órdenes de magnitud sobre un catálogo de ~53 alias), sin tarjeta y con "zero data retention" declarado en la página del modelo.

Investigación completa: búsqueda profunda comparando Gemini (free tier con cláusula de entrenamiento en inputs no-EEA/UK/CH + EOL anunciado 2028-05-14), OpenAI (sin free tier), Cohere (trial prohibido para producción), Jina (pesos v3/v5 CC-BY-NC; v4 no-comercial), Voyage (tarjeta + opt-out de entrenamiento) y Cloudflare (free 10k neurons/día, read+edit acotado). Conclusión: `bge-m3` vía Workers AI era la única opción con simultáneamente free tier real, español verificado, uso comercial no restringido y licencia MIT del modelo (self-hostable como plan B).

## Decisión

- Los alias de actividad se vectorizan con **`@cf/baai/bge-m3`** servido por **Cloudflare Workers AI**, por HTTP a la ruta OpenAI-compatible `…/ai/v1/embeddings` (httpx directo, sin dependencias nuevas).
- **Actualización (2026-11-13):** `fastembed` se eliminó del árbol principal (dependencia, código, tests y docs) por decisión del equipo — la búsqueda usa únicamente Cloudflare Workers AI. No hay ruta dual soportada; el rollback documentado es revertir el commit + aplicar la migración `vector(384)` + re-correr `load_catalog`.
- Migración `20261113000000_activity_aliases_vector_1024.sql`: drop del índice HNSW, drop/recreate de la columna `vector(384)` → `vector(1024)`, `truncate` de `activity_aliases` (datos derivados) y recreación del índice. `vector(n)` de pgvector exige typmod exacto; no se puede alterar in-place.
- `load_catalog` reconstruye los alias vía el proveedor elegido (transacción atómica igual que antes).
- `ACTIVITY_MIN_SIMILARITY`: **0.5 → 0.55**. El 0.5 estaba calibrado para MiniLM; con bge-m3, los matches correctos más débiles del eval set rozan 0.56 y los negativos se quedan en ≤0.53. Calibrado con ~26 queries + 3 negativas (2026-11-12); es un piso frágil: recalibrar con más datos en producción.
- Los vectores siguen comparándose con distancia coseno (índice HNSW `vector_cosine_ops`). No hay LLM en el camino crítico (ADR-003 se mantiene).

### Tensión explícita con ADR-004

ADR-004 ("Solo APIs públicas sin clave; credenciales para después") queda **reinterpretada, no derogada**: este ADR introduce la primera credencial por diseño, de forma acotada:

- El token es de scope mínimo (Workers AI Read+Edit sobre la cuenta del proyecto; no hay acceso a datos de usuarios ni a otros recursos de Cloudflare).
- Georef y la API de trámites de CABA siguen siendo públicas y sin clave.
- No se adopta ningún proveedor que exija credenciales para *ingesta* de trámites ni para otra función aparte de embeddings.

Si el equipo prefiere mantener ADR-004 estricto, la alternativa es self-hostear `bge-m3` (MIT, 568M parámetros) dentro de un proceso — mismo modelo, sin credencial, pero vuelve el costo de RAM/latencia en frío que se intentaba eliminar.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Mantener fastembed + MiniLM | Español claramente peor (46.32 vs 64.76); ~220 MB de descarga y ~600 MB de RAM en un deploy de 512 MB. |
| Gemini free tier (gemini-embedding-001) | Free tier con cláusula de entrenamiento sobre inputs (aplica a Argentina; revisores humanos). EOL anunciado 2028-05-14. Dims >1536 exceden el techo HNSW de `vector` (2000); español ≈63.5 solo en fuentes de terceros. |
| OpenAI text-embedding-3-small (`dimensions=384`) | Sin free tier ($0.02/1M — barato, pero costo); MIRACL 44.0 vendor-reported; mantiene el esquema de 384 sin migración, pero no gana en español. Queda como plan B barato (respaldo pago). |
| multilingual-e5-small (384d nativo, MIT) | Español 61.35, mejor que MiniLM pero ~3 puntos debajo de bge-m3; exige prefijos `query:`/`passage:` obligatorios (footgun silencioso en producción si se olvida). |
| Jina v3/v4 (API) | Pesos v3/v4 CC-BY-NC / Qwen Research License (no-comercial). API gratis sí cubre, pero v4 gratis por no-comercial es inadecuado para un MVP comercial. |
| Cohere trial | 1.000 calls/mes y cláusula explícita: trial keys no permitidas para producción/comercial. |
| Voyage | Tier 1 exige tarjeta; opt-out de entrenamiento exige tarjeta + rol admin; free pool 200M (multilingüe-2: 50M) no se renueva. |
| GitHub Models | Retirado el 2026-07-30. |

## Consecuencias

**Positivas:** ~220–600 MB de RAM liberados en la API; sin descarga de pesos al arrancar; español mucho más fuerte; costo $0 con el volumen actual; modelo MIT (salida self-hostable como plan B sin cambiar de modelo); búsqueda sigue siendo determinística (distancia coseno, sin LLM).

**Negativas / costos:**

- Dependencia externa con token rotatorio (riesgo operativo: rotación/renovación manual).
- Latencia de red por consulta (el warm-up in-process pasa a ser un preflight de 1 token; la primera consulta real añade ~decenas-cientos de ms, no segundos).
- **Ningún free tier tiene SLA y todos son cambiantes** (Cloudflare re-priceó en 2026; Google, Jina, Mistral y HF cambiaron términos/cuotas en 2025–2026). Plan B presupuestado: OpenAI 3-small (pago, `dimensions=384`) o self-host de bge-m3.
- El umbral 0.55 es frágil: calibrado sobre 29 queries; queries ambiguas ("vendo cigarrillos…", "comedor") siguen matcheando alias con el verbo "venta/local" por encima del umbral — límite del modelo, no del corte. Recalibrar con datos reales.
- La migración trunca `activity_aliases`: cualquier entorno con datos locales debe correr `load_catalog` después (documentado en README/GUIA_LEVANTAR). Los vectores MiniLM se pierden; rollback = revert del commit + migración `vector(384)` + re-embed.
- ADR-003/001 quedan con matices: los embeddings ya no corren "local con fastembed"; la migración hizo que los alias dejen de ser 384 dims.
