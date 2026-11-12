# Embeddings gratuitos para CONCO

**¿Qué API de embeddings alojada gratuita (o de costo casi nulo) debería adoptar CONCO — MVP que guía a emprendedores de Buenos Aires en trámites comerciales, con búsqueda semántica sobre ~34 alias de actividad en español, desplegado en Render — en lugar del modelo in-process fastembed MiniLM-L12-v2?**

## Respuesta corta

Recomendación: **Cloudflare Workers AI `@cf/baai/bge-m3`** — 10.000 neuronas/día gratis (≈9,3M tokens/día), $0 sin tarjeta, subconjunto español MTEB ~#15 (Mean(Task) **64.76**), "zero data retention: Yes", modelo MIT, ruta OpenAI-compatible y elimina ~220 MB de RSS del free tier de Render. Runner-up: **gemini-embedding-001 free tier** (MTEB(Multilingual) Mean(Task) **68.37**, Retrieval **67.71**, ~#5), pero su free tier tiene cláusula de entrenamiento sobre inputs (válida en Argentina), EOL anunciado 2028-05-14 y dims >384 requieren migración o truncación con renormalización manual. Fallback pago casi nulo: **OpenAI text-embedding-3-small** ($0.02/1M, `dimensions=384`; el multilingüe más débil, sin free tier). MiniLM no escala: ~220 MB de RAM y español **46.32** (~18 puntos por debajo de bge-m3).

Por qué no los demás: **Cohere trial** prohíbe explícitamente producción (1.000 llamadas/mes); **Jina v4** es no-comercial (Qwen Research License); **Voyage** exige tarjeta para Tier 1 y el opt-out de entrenamiento requiere card + rol admin; **GitHub Models** retirado el 2026-07-30; **NVIDIA NIM** English-only; **HF** sin créditos free ($0).

## Comparativa

| Provider | Free tier | card? | Comercial | Entrena con datos (free) | MTEB español* | Dims (¿384?) | Integración | ¿Migración? |
|---|---|---|---|---|---|---|---|---|
| **Cloudflare `bge-m3`** | 10.000 neur/día ≈ 9,3M tok/día; 3.000 RPM GA | No | Sí (GA, sin cláusula no-productiva hallada) | No ("zero data retention: Yes") | **64.76** / 66.33 (#15/225) | 1024 fijo (BAAI card; CF no lo restate — UNVERIFIED) | Media (REST u OpenAI-compatible) | Sí (→1024) |
| **Gemini gemini-embedding-001** | Sí ("Free of charge"; RPM/RPD solo en dashboard) | No | Sí fuera de EEA/UK/CH; Argentina OK | **Sí** ("Unpaid Services": revisores humanos pueden leer inputs) | ≈63.5 (terceros — uncertain) | 128–3072 (rec. 768/1536/3072); 384 en rango, no recomendado | Baja (`google-genai`, batch) | Parcial (truncar a 384 o migrar; 3072 excede el techo 2.000 de `vector`) |
| **OpenAI text-embedding-3-small** | No | Sí | Sí | Sí (pago) | Sin figura española verificada (MTEB 62.3 vendor-reported) | 1536 default; `dimensions` ≤1536; 384 OK server-side | Baja (`openai` SDK) | No (con `dimensions=384`) |
| **Jina v3** (v5 actual) | Tokens free no publicados (¿10M? UNVERIFIED); 100 RPM / 100K TPM | No | Sí hosted (pesos v3/v5 CC-BY-NC; v4 prohibido en producción) | No ("never use your API requests… to train") | Sin figura española; MMTEB v3: 64.44 | 1024 (MRL 32→1024); no 384 | Media-baja (REST, async batch) | Sí (→1024) |
| **Cohere embed-multilingual-v3.0** | Trial: 1.000 calls/mes; 2.000 inputs/min | No | **No** (trial no permite producción) | n/a | Sin figura española (MTEB eng 64.0 2.ª fuente) | 1024 fijo; v4/v5 Matryoshka [256..2048]; no 384 | Media-baja (ClientV2, `input_type` requerido, 96 texts/call) | Sí (→1024) |
| **Voyage voyage-multilingual-2** | 50M tokens una vez (voyage-4: 200M) | **Sí** | Sí tras pago | **Sí por defecto** (opt-out = card + org admin) | Sin figura española | 1024 fijo (4-lite: 256/512/1024/2048); no 384 | Media-baja (`voyageai`, ≤1000 texts/call) | Sí (→1024) |
| **Mistral mistral-embed** | Free mode con uso mensual incluido no publicado | No hasta PAYG | Sí | n/a (política no documentada) | Español no verificado (retrieval MTEB 55.26 stale) | 1024, unit-norm; no 384 | Media-baja (`mistralai`) | Sí (→1024) |
| **MiniLM-L12-v2** (incumbente) | n/a (local) | No | Sí (Apache-2.0) | No | **46.32** / 47.70 (#24/222) | 384 nativo | Ninguna | No |
| **HF hf-inference** | **$0** (PRO $2/mes) | — | — | — | — | — | — | Descartado |
| **NVIDIA NIM** | "Prototyping" (1.000 créditos UNVERIFIED) | No | Prototipo | — | — | 1024, English-only | — | Descartado |
| **GitHub Models** | **Retirado 2026-07-30** | — | — | — | — | — | — | Descartado |

\* Spanish subset MTEB(Multilingual, v2): Mean(Task) / Mean(TaskType) / rank. bge-m3 y MiniLM verificados en leaderboard; español de gemini y Mistral es incierto.

## Plan de migración propuesto

1. **Nuevo `TextEmbedder`** (protocolo en `domain.py`: `model_name`, `warm_up()`, `embed()`): `CloudflareTextEmbedder` vía ruta OpenAI-compatible `POST …/accounts/{ACCOUNT_ID}/ai/v1/embeddings` (SDK `openai`, baseURL `…/ai/v1`, respuesta `data[i].embedding`), o REST directo `POST …/ai/run/@cf/baai/bge-m3` con `{"text": [...]}`. Auth: Bearer API token CF (Workers AI **Read + Edit**) + Account ID. ~40–80 líneas.
2. **Env vars**: `EMBEDDING_API_KEY` (+ `CLOUDFLARE_ACCOUNT_ID`) en pydantic-settings y Render; actualizar `.env.example`. `warm_up()`: eliminar o reemplazar por preflight de 1 token con try/except (mantener `_log_warmup_failure`).
3. **Migración SQL** (nueva `.sql` con timestamp): `drop index if exists activity_aliases_embedding_idx;` → `alter table … drop column embedding;` (borra vectores MiniLM — deseable) → `add column embedding extensions.vector(1024) not null;` → **re-run `load_catalog`** (re-encodea ~34 alias en una transacción; 1024 ≤ techo HNSW/`vector` de 2.000 dims) → **crear HNSW DESPUÉS de la carga**: `create index … using hnsw (embedding extensions.vector_cosine_ops);`. Nota: `ALTER COLUMN ... TYPE vector(1024)` **no funciona in-place** (typmod exacto); drop/recreate es el patrón.
4. **Recalibrar `activity_min_similarity`**: el 0.5 actual es MiniLM-específico. Construir eval set de ~20–40 queries (semilla: logs + sinónimos de `activities.json`), medir con el modelo nuevo, elegir el umbral más bajo con precision@1 aceptable + 1–2 queries negativas por debajo; actualizar `config.py`.
5. **Smoke-test**: consulta real → `activity_directory.py` (filtro `embedding_model = %(model)s` + `similarity >= %(min_similarity)s`) → alias correcto; nunca swap sin re-correr `load_catalog` (devuelve cero sugerencias en silencio con HTTP 200).
6. **Rollback**: conservar fastembed y el commit previo como red de seguridad hasta verificar. **Tradeoff**: `load_catalog` trunca `procedures` y borra `activities` en cascada → los vectores MiniLM se pierden; el rollback exige re-aplicar la migración `vector(384)` + re-instalar fastembed + re-correr `load_catalog`, no basta un `git revert`.
7. **Higiene**: `httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)`; reintentos con backoff + jitter (máx 3, solo 429/5xx/red, respetar `Retry-After`); `load_catalog` debe pedir TODAS las embeddings ANTES de abrir la transacción; 1 reintento máx en query-time; loguear top-1 similarity en 0 resultados.

## Riesgos y detalles a verificar

Lo marcado [UNVERIFIED] en las notas no está resuelto:

- **Cloudflare**: forma exacta del body HTTP al exceder las 10.000 neuronas/día (probablemente envelope `{"success":false,"errors":[...]}` con 429, no confirmado); si Workers Free exige tarjeta (estándar: no, página sin verificar); **1024 dims de bge-m3 no restated en página CF** (viene de la card BAAI); contradicción "60,000 tokens" (CF) vs 8,192 (BAAI) — tratar 8.192 como real; shape del `result` embedding vía REST sin verificar (por eso se prefiere `/ai/v1`).
- **Gemini**: free RPM/RPD por modelo **solo en dashboard de AI Studio**; cláusula de entrenamiento aplica en Argentina (sin excepción EEA/UK/CH); EOL **2028-05-14** → presupuestar re-embedding; 3072 excede el techo HNSW/`vector` 2.000 → truncar a ≤1536 o `halfvec`; batch no disponible en free; español ≈63.5 (solo terceros).
- **Cohere**: trial (1.000 calls/mes, sin producción) inviable; precios embed actuales [UNVERIFIED]. **Jina**: pool free no publicado (10M citados, UNVERIFIED). **Voyage**: Tier 1 exige tarjeta; opt-out requiere card + rol admin; 200M/50M una vez por cuenta, no renovables, no aplican a Batch API.
- **Ningún free tier tiene SLA y todos son cambiantes** (Google revisa términos; Cloudflare re-priceó en 2026; Jina en 2025; Mistral en 2026; HF mató el serverless anónimo). **Presupuestar migración a pago como plan B** (p. ej. OpenAI 3-small o post-free de Voyage/Mistral) y monitorear neuronas/429s/similitud.
- **Calidad**: MTEB(Multilingual v2) y RTEB discrepan; benchmarks ruidosos; Mr. TyDi español por modelo no disponible en leaderboard estático; fine-tuning sobre los 34 alias es la mayor mejora de calidad sin importar el modelo.
- ToS de Mistral/NVIDIA/OpenAI no verificados verbatim; pase legal del owner recomendable antes de producción.

## Veredicto final y timeline sugerido

**Adoptar Cloudflare Workers AI `@cf/baai/bge-m3`.** Único candidato que combina free tier real sin tarjeta ni cláusula de entrenamiento ("zero data retention: Yes"), uso comercial sin restricción conocida, español fuerte (64.76), ~9,3M tokens/día — órdenes de magnitud sobre las necesidades de un MVP de 34 alias — y salida MIT self-hostable, eliminando ~220 MB de RAM del free tier de Render. El esfuerzo se concentra en la migración pgvector 384→1024 y la recalibración del umbral, no en la integración. **Runner-up: gemini-embedding-001 free tier** si se tolera la cláusula de entrenamiento (datos no sensibles), el EOL 2028-05-14 y dims ≤1536 para HNSW. **Respaldo pago casi nulo: OpenAI 3-small con `dimensions=384`** — paga con menor calidad multilingüe por cero migración de esquema.

Timeline: (1) **research** — hecho; (2) **validación local** — `CloudflareTextEmbedder`, `load_catalog` en dev DB, medir retrieval sobre el eval set, recalibrar `activity_min_similarity`; (3) **deploy en Render** — env vars, migración (drop/recreate + HNSW post-carga), smoke-test, fastembed disponible para rollback hasta verificar; (4) **en curso** — monitorear neuronas/día, 429 y top-1; re-chequear EOL de gemini-001 si se usa runner-up; revisar ToS/cuotas en cada deploy.

## Fuentes

**Tiers, cuotas y términos (Nov 2026):**
[Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-embedding) · [Gemini Additional Terms (Unpaid)](https://ai.google.dev/gemini-api/terms#data-use-unpaid) · [Available regions](https://ai.google.dev/gemini-api/docs/available-regions) · [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations) · [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) · [CF Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) · [CF limits](https://developers.cloudflare.com/workers-ai/platform/limits/) · [CF bge-m3 page](https://developers.cloudflare.com/workers-ai/models/bge-m3/) · [Jina embeddings](https://jina.ai/embeddings/) · [Cohere pricing](https://cohere.com/pricing) · [Cohere rate limits](https://docs.cohere.com/docs/rate-limits) · [Cohere embeddings](https://docs.cohere.com/docs/embeddings) · [HF Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing) · [Voyage pricing](https://docs.voyageai.com/docs/pricing) · [Voyage rate limits](https://docs.voyageai.com/docs/rate-limits) · [Voyage FAQ](https://docs.voyageai.com/docs/faq) · [Mistral subscriptions](https://docs.mistral.ai/admin/billing-usage/subscriptions.md) · [Mistral API pricing](https://docs.mistral.ai/inference/pricing.md) · [NVIDIA build](https://build.nvidia.com/) · [GitHub Models retirado](https://docs.github.com/en/github-models/prototyping-with-ai-models) · [OpenAI pricing](https://platform.openai.com/docs/pricing)

**Calidad español:**
[MTEB(Multilingual, v2)](https://leaderboard.mteb.org/benchmark/MTEB(Multilingual%2C%20v2)) · [bge-m3](https://leaderboard.mteb.org/models/BAAI/bge-m3) · [multilingual-e5-small](https://leaderboard.mteb.org/models/intfloat/multilingual-e5-small) · [BAAI/bge-m3 card](https://huggingface.co/BAAI/bge-m3) · [gemini-embedding-001](https://ai.google.dev/gemini-api/docs/models/gemini-embedding-001)

**Integración/migración:**
[Gemini embeddings](https://ai.google.dev/gemini-api/docs/embeddings) · [OpenAI embeddings guide](https://platform.openai.com/docs/guides/embeddings) · [Cohere /embed](https://docs.cohere.com/reference/embed) · [Voyage embeddings](https://docs.voyageai.com/docs/embeddings) · [Jina types & task](https://docs.jina.ai/embeddings/types-and-task/) · [Mistral text_embeddings](https://docs.mistral.ai/inference/embeddings/text_embeddings/) · [Render free](https://render.com/docs/free) · [pgvector](https://github.com/pgvector/pgvector)
