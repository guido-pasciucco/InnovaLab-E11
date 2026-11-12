# Handoff: Hosted Embedding APIs vs. fastembed + pgvector migration (InnovaLab-E11)

Repo ground facts verified by reading:
- `back/src/conco/guidance/embeddings.py` — `FastEmbedTextEmbedder`, lazy `@cache` `TextEmbedding`, `embed(texts)`, `warm_up()` (~220 MB model).
- `back/src/conco/guidance/activity_directory.py` — query path: `asyncio.to_thread(self._embedder.embed, [query])` → `_SUGGEST_SQL` computes `1 - (embedding <=> query::vector)`, filters `embedding_model = %(model)s` and `best.similarity >= %(min_similarity)s`.
- `back/src/conco/guidance/load_catalog.py` — single `embed()` call re-embeds **all aliases** (~34), then ONE psycopg transaction: truncate `procedures`, delete `activities` (cascade → aliases), insert with `embedder.model_name` + `to_pgvector()`.
- `back/supabase/migrations/20261105091512_create_activities.sql` — `embedding extensions.vector(384)`, `embedding_model text not null`.
- `20261112000000_add_activity_aliases_vector_index.sql` — HNSW `vector_cosine_ops`.
- `config.py` — `embedding_model` default MiniLM-L12-v2, `activity_min_similarity = 0.5`, pydantic-settings `.env`.
- `domain.py` — `TextEmbedder` Protocol (`model_name`, `warm_up`, `embed`).

## 0. Per-candidate effort row

Common work for ALL: new `TextEmbedder` impl (~40-80 lines w/ httpx/SDK), new `EMBEDDING_*_API_KEY` env + Render env var, drop fastembed/onnx deps, new Supabase migration (drop/recreate `embedding` column at new dim + recreate HNSW **after** bulk load), re-run `load_catalog` (34 aliases, one batch), recalibrate `activity_min_similarity`, update `.env.example`/README, keep `embedding_model` naming consistent. **API integration is hours; migration + eval-set recalibration is the bulk.**

| Candidate | Dims (default) | SDK? | Auth | Asymmetry | Batch | Effort |
|---|---|---|---|---|---|---|
| Google gemini-embedding-001 | 3072 (MRL 128–3072; **can request 384**) | `google-genai` | `x-goog-api-key` | `task_type=RETRIEVAL_QUERY/DOCUMENT` | batchEmbedContents / contents list | **Low** (keep 384 → no migration; manual L2-normalize <3072) |
| OpenAI text-embedding-3-small | 1536 (`dimensions` param; **can request 384**) | `openai` | `Authorization: Bearer` | none (symmetric) | array input | **Low** (keep 384 → no migration) |
| Jina jina-embeddings-v3 | 1024 (`dimensions` MRL) | REST-first | Bearer | `task=retrieval.query/.passage` | async `/v1/batch/embeddings` ≤10k | **Low–Med** (1024 → migration) |
| Cohere embed-multilingual-v3.0 | 1024 fixed (v4+ has output_dimension) | `cohere` ClientV2 | Bearer | `input_type=search_query/document` | **96 texts/call** (verified) | **Low–Med** (1024 → migration) |
| Voyage voyage-multilingual-2 / voyage-4-lite | 1024 (4-lite: 256/512/1024/2048) | `voyageai` | Bearer | `input_type=query/document` | ≤1000 texts/call | **Low–Med** (migration; no 384) |
| Cloudflare Workers AI bge-m3 | 1024 [CF page does not print dims UNVERIFIED; BAAI card 1024] | none dedicated; REST or OpenAI-SDK at CF `/ai/v1` | CF API token Bearer (Workers AI **Read + Edit**) + Account ID | none documented | `{"text": [...]}` array | **Med** (REST shape + token setup) |
| Mistral mistral-embed | 1024, unit-norm (verified) | `mistralai` | Bearer | none (symmetric) | `inputs` array | **Low–Med** (1024 → migration) |

**Unverified everywhere:** published p50 latency (short texts ≈ 1 RTT + tens–hundreds ms, treat as estimate); exact 429 body schemas; per-model free-tier RPMs (check dashboards: AI Studio rate-limit, CF/Jina/Cohere/Voyage/Mistral consoles).

## 1. Provider API facts (Nov 2026)

**Google Gemini embeddings** — https://ai.google.dev/gemini-api/docs/embeddings
- `pip install google-genai`; `client = genai.Client()` (reads GEMINI_API_KEY/GOOGLE_API_KEY). REST: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent`, header `x-goog-api-key`.
- `text-embedding-004` **retired 2026-01-14**. gemini-embedding-001: text-only, ≤2048 tokens, **128–3072 dims** via `output_dimensionality` (recommended 768/1536/3072; default 3072). Non-3072 output must be **manually L2-normalized**. EOL 2028-05-14. gemini-embedding-2 exists; incompatible space.
- Batch: contents list or `:batchEmbedContents`. 429 = `RESOURCE_EXHAUSTED`; per-model free limits **[UNVERIFIED]** (AI Studio dashboard).
- 1536d ≈ 68.17, 768d ≈ 67.99 MTEB anchors.

**OpenAI text-embedding-3-small** — https://platform.openai.com/docs/guides/embeddings
- `pip install openai`; `client.embeddings.create(input=[...], model="text-embedding-3-small", dimensions=...)`. REST `POST /v1/embeddings`, Bearer.
- 1536 default; `dimensions` truncates server-side (MRL) — can pass **384** to keep column. 8192 ctx. ~$0.02/M tokens [UNVERIFIED exact]. No free tier.

**Cohere** — https://docs.cohere.com/docs/embeddings ; https://docs.cohere.com/reference/embed
- `pip install cohere`; `cohere.ClientV2(api_key=...)`; `co.embed(texts=[...], model="embed-multilingual-v3.0", input_type="search_document"|"search_query", embedding_types=["float"])`. REST `POST https://api.cohere.com/v2/embed`.
- **`input_type` required**; **max 96 texts/call** (34 aliases = one call). Response `{id, embeddings: {float: [[...]]}, meta:{...}}`. 1024 fixed for v3. 429 `{message, id}` documented. Trial = 1,000 calls/mo, not for production.

**Voyage** — https://docs.voyageai.com/docs/embeddings
- `pip install voyageai`; `voyageai.Client()` (VOYAGE_API_KEY). REST `POST https://api.voyageai.com/v1/embeddings`.
- voyage-multilingual-2: 32K ctx, **1024 fixed**, multilingual retrieval; 50M free tokens. voyage-4-lite: 1024 default, **256/512/2048 selectable**; 200M free tokens. 200M NOT for Batch API. Tier 1 needs payment method; data may be used for training by default (opt-out needs card + org admin). Batch ≤1000 texts.

**Jina** — https://docs.jina.ai/embeddings/types-and-task/
- REST-first: `POST https://api.jina.ai/v1/embeddings`, Bearer; async batch `/v1/batch/embeddings` (≤10k inline, poll `/v1/batch/{id}`).
- Body: `{model, input:[str], task:"retrieval.query"|"retrieval.passage"|..., dimensions:int, normalized:bool}`; v3 570M, 1024 dims, 8192 ctx, 100+ langs, CC-BY-NC-4.0.
- Rate limits: **free key 100 RPM / 100K TPM**; paid 500/2M; premium 5000/50M; 429 + exponential backoff. 34 aliases sync re-embed OK.

**Mistral mistral-embed** — https://docs.mistral.ai/inference/embeddings/text_embeddings/
- `pip install mistralai`; `client.embeddings.create(model="mistral-embed", inputs=[...])`. REST `/v1/embeddings`.
- **1024 dims, unit-norm → cosine ≡ dot ≡ euclidean**; no asymmetry param; $0.10/M tokens; Free mode monthly included usage (unspecified) — no true free tier.

**Cloudflare Workers AI (@cf/baai/bge-m3)** — https://developers.cloudflare.com/workers-ai/models/bge-m3/
- From Render (non-Workers) = **REST**: `POST https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/baai/bge-m3`, Bearer CF API token needing **Workers AI — Read + Edit**. Request: `{"text": [...]}`. Envelope `{"result":..., "success":bool, "errors":[...], "messages":[...]}`; embeddings result shape **[UNVERIFIED]** — smoke-test, or use the **OpenAI-compatible route** `POST .../ai/v1/embeddings` with the standard openai SDK (baseURL=…/ai/v1) — response = OpenAI `data[i].embedding` shape.
- No `pooling` param documented; ignore mislabeled Synchronous/Async/schema sections. Free allocation **10,000 neurons/day ≈ 9.3M bge-m3 tokens/day**; 3,000 RPM text-embeddings GA; "zero data retention: Yes"; "60,000 tokens" page claim contradicts BAAI card 8,192.
- Commercial use: no non-production clause for Workers AI free allocation found.

## 2. pgvector dimension migration mechanics

- Supabase migrations = plain SQL in lexical order (`supabase migration up`); new timestamped `.sql`.
- **`ALTER COLUMN ... TYPE vector(1024)` on an existing `vector(384)` column does NOT work in-place** (typmod is exact dims; no documented cast path). Pattern: drop & recreate the column, or parallel `embedding_new` + swap (unnecessary at 34 rows).
- Recommended single migration:
  1. `drop index if exists activity_aliases_embedding_idx;`
  2. `alter table public.activity_aliases drop column embedding;` (wipes stale MiniLM vectors — desirable)
  3. `alter table public.activity_aliases add column embedding extensions.vector(<new dim>) not null;`
  4. Re-run `load_catalog`; **create HNSW AFTER the bulk load**:
  5. `create index activity_aliases_embedding_idx on public.activity_aliases using hnsw (embedding extensions.vector_cosine_ops);`
- **HNSW ceiling**: `vector` supports ≤2,000 dims (halfvec ≤4,000). 1024/1536 fine; **3072 (Gemini default) exceeds 2,000 → requires Matryoshka truncation ≤1536** or `halfvec`.
- `load_catalog` is atomic (single transaction) and re-embeds all aliases in one call → migration + one command fully refreshes vectors.
- **`embedding_model` filter**: suggest SQL has `embedding_model = %(model)s` — stale rows never match. Swap embedder WITHOUT re-running load_catalog ⇒ **search silently returns zero suggestions, HTTP 200**, no error. Always re-run loader.

## 3. Recalibration — `activity_min_similarity = 0.5` is MiniLM-specific

- Cosine distributions are model-dependent. Silent failure modes: too-high threshold ⇒ empty suggestions list, UI shows nothing, no error logged; too-low ⇒ always-same top-1 irrelevant suggestion; wrong asymmetry param (e.g., aliases embedded with `search_query`) ⇒ compressed similarities.
- Recipe: build a ~20–40 query eval set (seed from logs/activities.json synonyms); compute similarities for the NEW model; pick the lowest threshold keeping acceptable precision@1; keep a couple of negative/gibberish queries below it; update `config.py`.
- No vendor publishes calibration guidance. **Any model switch invalidates 0.5; budget for the eval pass.**

## 4. Render free/cheap tier mechanics

- Free web service: 0.1 CPU / 512 MB RAM; spins down after 15 min idle; ~1 min spin-up; ephemeral FS; may be suspended for unusual service-initiated outbound traffic (external API calls count); 750 free instance-hours/mo; HTTPS outbound unrestricted (ports 25/465/587 blocked) — [Render free docs](https://render.com/docs/free). Static site frontend free tier fine.
- Swapping to hosted embeddings **eliminates the ~220 MB model download + ONNX RSS** — meaningful headroom on 512 MB.
- `warm_up()` becomes trivial: delete the step, or replace with a 1-token preflight embed guarded by try/except (keep the log-and-continue pattern from `_log_warmup_failure`).
- Render env vars for the API key — pydantic-settings already reads env; add e.g. `EMBEDDING_API_KEY`; `.env.example` gains the key (secret stays out of repo).
- Outbound HTTPS to all seven providers is fine at this call volume (35-call re-embed + 1 call/query).

## 5. Failure-mode design

- httpx timeouts: `httpx.Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0)`; distinguishes ConnectTimeout/ReadTimeout.
- API down ⇒ `ActivityDirectoryError` → handler maps to 5xx/503 (verify `guidance/api.py` exact status in implementation); never hang 30s.
- **load_catalog must stay atomic**: fetch ALL embeddings BEFORE opening the transaction; any failure (429 after retries, 5xx, network) aborts before touching DB.
- Retries: exponential backoff + jitter, max 3, retry only 429/5xx/network, honor `Retry-After`; never retry 4xx other than 429; embedding POSTs are read-only → safe to retry; query-time: 1 retry max; catalog-time: 3–5.
- Degradation options: fail closed 503 (current shape) vs lexical fallback (out of scope). Log top-1 similarity on empty results for monitoring.

## 6. Suggested read order for implementer

repo: embeddings.py → domain.py → activity_directory.py → load_catalog.py → config.py → migrations → main.py.
external: provider embedding docs (URLs above), pgvector README (https://github.com/pgvector/pgvector), Render free docs (https://render.com/docs/free).
