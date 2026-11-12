# Spanish-quality embedding models for CONCO — comparative notes (Nov 2026)

Context: pgvector `vector(384)` in the CONCO MVP; ~34 activity aliases; short Spanish queries. License- and cost-sensitive. Facts per model; uncertain items marked.

## 0. Cross-cutting context (Nov 2026)

- **text-embedding-004 is retired** on Gemini API (2026-01-14; Vertex AI 2027-04-01); for multilingual Google offers gemini-embedding-001 / gemini-embedding-2. ([ai.google.dev deprecations](https://ai.google.dev/gemini-api/docs/deprecations))
- **gemini-embedding-001** shutdown announced 2028-05-14; replaced by gemini-embedding-2 (Apr 2026, multimodal, incompatible space).
- **MTEB leaderboards moved to MTEB(Multilingual, v2)**; leaderboard.mteb.org is current.
- **pgvector implication**: only `multilingual-e5-small` (384d) and MiniLM-L12-v2 (384d) fit `vector(384)` natively. Everything else requires a column type change or Matryoshka truncation. Gemini/OpenAI/Voyage/Cohere/Jina support truncation or configurable dims; truncating to exactly 384 for Gemini is in-range but not a recommended size (768/1536/3072 recommended).

## 1. Facts per model

### Google gemini-embedding-001 (Gemini API / Vertex AI)
- Dims: default 3072; MRL-truncatable via `output_dimensionality`, range 128–3072; Google recommends 768/1536/3072. 384 in-range but not recommended — uncertain quality. ([model card](https://ai.google.dev/gemini-api/docs/models/gemini-embedding-001), [Vertex embeddings docs](https://cloud.google.com/gemini-enterprise-agent-platform/models/embeddings/get-text-embeddings))
- Max tokens: **2048**; 100+ languages incl. Spanish.
- Task types: `RETRIEVAL_QUERY`, `RETRIEVAL_DOCUMENT`, `SEMANTIC_SIMILARITY`, … — optional but strongly recommended for asymmetric retrieval.
- Normalization: 3072-dim output is normalized; **non-3072 must be L2-normalized manually** (gemini-embedding-2 auto-normalizes).
- MTEB(Multilingual, v2): Mean(Task) **68.37**, Retrieval **67.71**, ~#5; Google reports by dims: 68.17@1536, 67.99@768, 67.55@512, 66.19@256. ([leaderboard](https://leaderboard.mteb.org/benchmark/MTEB(Multilingual%2C%20v2)))
- Spanish subset: third-party blog reports ≈63.5 — **uncertain**.
- License: proprietary.
- Free: **free tier in Gemini API / AI Studio** (rate-limited; free-tier inputs may be used to improve Google products).
- Weaknesses: taskType must be set per side; single input per request in embed_content; free-tier data-use caveat; dims >384 for the current column.
- RTEB (Octen, third-party, uncertain): public mean 0.7218 (#7 public).

### text-embedding-004
- **Retired 2026-01-14** on Gemini API; 768 dims max; designed for English. Do not use for new work.

### Cloudflare Workers AI `@cf/baai/bge-m3`
- It IS BAAI/bge-m3 served by Cloudflare: **1024 dims, 8192-token context, MIT license, 100+ languages, sparse+dense+multi-vector** (CF page says "60,000 tokens" — contradicts BAAI's card; treat 8192 as the model's true capacity). ([CF bge-m3 page](https://developers.cloudflare.com/workers-ai/models/bge-m3), [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3))
- Free: **10,000 Neurons/day**; bge-m3 costs ~1,075 neurons per M tokens ($0.012/M) → ≈9.3M tokens/day free.
- MTEB(Multilingual, v2): ~#52 Mean(TaskType) ≈ 60.35 (partial). **Spanish subset: Mean(Task) 64.76, Mean(TaskType) 66.33, ranked #15/225** — strong Spanish showing. ([leaderboard bge-m3](https://leaderboard.mteb.org/models/BAAI/bge-m3))
- No query instruction prefixes needed. Cosine similarity; L2-normalize for cosine.
- Open weights (568M, 2.1GB), MIT → fully self-hostable. Best-documented open artifact for CONCO's constraints. Cloudflare serving adds "zero data retention" badge.
- Caveat: dense-only via CF API; 1024 dims ≠ 384 column.

### intfloat multilingual-e5-small / e5-large
- **multilingual-e5-small: 384 dims natively — only permissively-licensed candidate fitting vector(384) today.** 118M params, 512-token context. (License: MIT per intfloat repos; not re-verified this session.)
- **multilingual-e5-large: 1024 dims, 560M params**, 512-token context; instruct variant uses `Instruct: ...\nQuery: ...` on queries.
- **Prefixes are MANDATORY**: `"query: "` / `"passage: "` even for non-English; omitting degrades recall substantially.
- Normalize (`normalize_embeddings=True`) + cosine.
- Benchmarks: e5-small Spanish **Mean(Task) 61.35 / Mean(TaskType) 62.90, #26/228**; e5-large-instruct MMTEB v2: Mean(Task) 63.22, Retrieval 57.12. ([leaderboard e5-small](https://leaderboard.mteb.org/models/intfloat/multilingual-e5-small))
- 100 languages; Mr. TyDi training included — relevant for Spanish retrieval.
- Weakness: the prefix footgun (mixing prefixed queries with unprefixed aliases silently kills recall).

### paraphrase-multilingual-MiniLM-L12-v2 (incumbent)
- 384 dims, 50+ languages, Apache-2.0, mean pooling; 128-token max_seq_length (config wins over card's 512).
- MTEB(Multilingual, v2): English 52.68 (#162); **Spanish Mean(Task) 46.32 / Mean(TaskType) 47.70 (#24/222)** — clearly outclassed (bge-m3 ≈ +18 points on Spanish).

### Cohere embed-multilingual-v3.0
- 1024 dims fixed; **512 max tokens** (irrelevant for aliases); 100+ langs incl. Spanish; proprietary.
- **Requires `input_type`**: `search_query` vs `search_document` (asymmetric); wrong/missing degrades results.
- Normalized; cosine/dot equivalent.
- Trial: 1,000 calls/month, ~2,000 inputs/min; MTEB eng 64.0 (secondary source).
- Fixed 1024 → migration mandatory.

### Cohere embed-v4.0 / embed-v5.0-pro
- v4.0: text/image/PDF; dims [256, 512, 1024, 1536] Matryoshka (default 1536); 128k ctx; input_type required; RTEB ≈ 0.6534 (third-party, uncertain).
- **Embed 5 (v5.0-pro / v5.0-fast) is now Cohere's flagship** (Oct 2026): 256–2048 dims (2048 default).
- Main downside: proprietary + trial-key limits.

### OpenAI text-embedding-3-small
- 1536 dims default; **`dimensions` API param accepts any value ≤1536** (truncation handled server-side; pass 384 to keep the column — normalization automatic for MRL truncations via the API).
- 8,191/8,192 token ctx; proprietary; $0.02/1M tokens; no free tier; 8191-token context; card required.
- MTEB 62.3 (vendor-reported); MIRACL multilingual 44.0 (vendor-reported) — **weakest multilingual of this set**; no Spanish-specific verified figure.
- No task prefixes; cosine standard.

### Mistral mistral-embed
- **1024 dims**, unit-norm outputs (cosine ≡ dot ≡ euclidean), ~8K ctx; $0.10/1M tokens; no asymmetry param; multilingual **not officially stated** for this model — Spanish support unverified; MTEB retrieval 55.26 (stale, Dec-2023). New 2025 variants mistral-embed-dim256/dim128-2510 exist.

### Voyage (voyage-3/3-large/3.5/3.5-lite/4 family / voyage-multilingual-2)
- Context: **32K tokens**; dims: voyage-3 fixed 1024; voyage-3-large/3.5/3.5-lite/4 family → 1024 default, optional 256/512/2048 (Matryoshka + quantization-aware training); voyage-3-lite fixed 512; **voyage-multilingual-2: 1024 fixed, Spanish-specialized** (62 datasets, 26 languages incl. Spanish).
- Recommended: `input_type=query` / `document` for asymmetric retrieval.
- Free: 200M one-time tokens for voyage-4 family; **50M for voyage-multilingual-2**; none for 3.x — [pricing](https://docs.voyageai.com/docs/pricing). RTEB (third-party): voyage-3-large 0.7434 (#4–5).
- Proprietary (MongoDB-owned).

### Jina v3 / v4 (and v5-text-small)
- **v3: 570M, 8192 ctx, 1024 dims (MRL 32→1024), task adapters `retrieval.query`/`retrieval.passage`, MTEB 65.52 avg, multilingual MTEB 64.44, 30-language focused set incl. Spanish, CC-BY-NC-4.0** (API use OK; weights non-commercial). v4: 3.8B, 32k ctx, 2048 dims, Qwen Research License — **non-commercial**. Current line: v5-text-small/nano (596M/32k/1024d, also CC-BY-NC-4.0).
- Hosted API use does NOT require separate commercial license; data not used for training (verbatim FAQ).

## 2. Direct answers

### MTEB overall + Spanish
- Retrieval (Multilingual v2): gemini-embedding-001 **67.71**; Qwen3-Embedding-8B 70.88; e5-large-instruct 57.12; MiniLM n/a.
- Spanish subset (Mean Task / TaskType / rank): **bge-m3 64.76 / 66.33 / #15**; **e5-small 61.35 / 62.90 / #26**; **MiniLM-L12-v2 46.32 / 47.70 / #24**; gemini-001 ≈ 63.5 (uncertain).

### Officially multilingual
gemini (100+), bge-m3 (100+), e5 (100), Jina v3 (100+ trained 30), Cohere v3/v4 (100+), Voyage (26+), MiniLM (50+), Mistral (unspecified), OpenAI 3-small (multilingual-capable but not advertised; weakest scores).

### Dimensions
| Model | Default | Configurable | Exactly 384 |
|---|---|---|---|
| gemini-embedding-001 | 3072 | 128–3072 (rec. 768/1536/3072) | yes (in-range, not recommended) |
| CF @cf/baai/bge-m3 | 1024 | no | no |
| multilingual-e5-small | **384** | no | **yes (native)** |
| multilingual-e5-large | 1024 | no | no |
| MiniLM-L12-v2 | 384 | no | yes (native) |
| Cohere embed-multilingual-v3.0 | 1024 | no | no |
| Cohere embed-v4.0 / v5 | 1536/2048 | [256,512,1024,1536] / [256..2048] | no |
| OpenAI 3-small | 1536 | any ≤1536 | **yes (API param)** |
| mistral-embed | 1024 | no | no |
| Voyage 4 family | 1024 | 256/512/1024/2048 | no |
| voyage-multilingual-2 | 1024 | no | no |
| jina-embeddings-v3 | 1024 | 32..1024 | no |

### Licenses
MIT: bge-m3, e5. Apache-2.0: MiniLM. CC-BY-NC-4.0: Jina v3/v5 (weights). Qwen Research License (non-commercial): Jina v4. Proprietary: Gemini, OpenAI, Cohere, Voyage, Mistral. For a commercial MVP: open-weight MIT (bge-m3 / e5-small) is clean; Jina weights are NOT; proprietary API consumption follows each provider's ToS (Gemini free tier: training clause).

### Short-query vs short-document weaknesses
- e5: prefixes `query:`/`passage:` mandatory or recall silently collapses.
- Jina v3: `task=retrieval.query/passage` mandatory for best quality.
- Cohere: `input_type=search_query/search_document` required.
- Gemini: `taskType=RETRIEVAL_QUERY/DOCUMENT` recommended.
- Voyage: `input_type=query/document` recommended.
- bge-m3 / MiniLM / mistral-embed / OpenAI: no prefixes.
- General: long-doc-retrieval models dilate on 3–8 token aliases; prefer retrieval-tuned models with asymmetric adapters; fine-tuning on the 34 aliases is the highest-leverage quality fix regardless of model.

### Distance metric
Cosine similarity everywhere. pgvector: `vector_cosine_ops` / `<=>`, normalized vectors. e5/ST/FlagEmbedding/Gemini(<3072)/OpenAI(truncated)/Jina/Cohere/etc. — normalize explicitly or rely on model's normalization as documented.

### Free summary
bge-m3 via Cloudflare: ~9.3M tokens/day free (best true-free fit). Gemini: free tier (training clause). Voyage: 50M (multilingual-2) / 200M (voyage-4) one-time + card. Jina: free token pool (100 RPM), v4 non-commercial. Cohere: trial only (no production). OpenAI: none. MiniLM: incumbent, weakest Spanish.

## 3. Gaps / uncertainties

- Mr. TyDi Spanish per-model nDCG — not retrievable from public leaderboard static pages.
- Spanish-specific numbers for gemini-001, mistral, OpenAI 3-small, voyage-multilingual-2 — absent or third-party-only.
- e5 MIT license — reported, not re-verified.
- Gemini free-tier embedding rate limits — AI Studio dashboard only.
- Exact-384 truncation quality for Gemini/OpenAI — untested.
- bge-m3 "60,000" vs 8,192 context contradiction — unresolved.
- MTEB(Multilingual v2) vs RTEB rankings disagree materially; both noisy.
- gemini-embedding-001 EOL 2028-05-14 → budget a future re-embedding migration.
