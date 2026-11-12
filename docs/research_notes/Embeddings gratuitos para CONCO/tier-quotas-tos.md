# Free / near-zero-cost hosted text embedding APIs — state as of November 2026

Scope: MVP "CONCO" (Buenos Aires, Argentina); embeddings of short Spanish texts; a catalog of ~34 activity aliases; deployed on Render free tier. Facts per provider; numbers marked **[UNVERIFIED]** could not be confirmed on primary pages fetched 2026-11-12.

## 1) Google Gemini API (AI Studio) — gemini-embedding-001 / gemini-embedding-2 (text-embedding-004 superseded and retired 2026-01-14)

### The only major genuinely-free embedding tier, but with a hard data-training clause on free quota.

- Free tier: "Free of charge" for input tokens on `gemini-embedding-001` (paid: $0.15/1M tokens standard, $0.075/1M batch) and `gemini-embedding-2` (paid: $0.20/1M text) — [Pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-embedding). Per-model free RPM/TPM/RPD are no longer published; rate limits are viewed in AI Studio and vary by tier — [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits). Old hard free numbers **[UNVERIFIED]**.
- Free tier Additional Terms (effective March 23, 2026, "Unpaid Services"): "Google uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies…" plus human reviewers may read/annotate inputs — "**Do not submit sensitive, confidential, or personal information to the Unpaid Services.**" EEA/Switzerland/UK exception: paid-tier data handling applies there even on free quota; Argentina does NOT get that exception — [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms#data-use-unpaid); pricing page corroborates: free tier "Used to improve our products: Yes".
- Commercial use: allowed on free tier for professional/business purposes outside EEA/UK/CH ("You may use only Paid Services when making API Clients available to users in the EEA, Switzerland, or the United Kingdom") — [Terms](https://ai.google.dev/gemini-api/terms).
- Age 18+; available regions explicitly include **Argentina** — [Available regions](https://ai.google.dev/gemini-api/docs/available-regions).
- 429 behavior: spend-based limits return `429 RESOURCE_EXHAUSTED`; RPM/RPD resets midnight PT. Exact free per-model limits **[UNVERIFIED]** (AI Studio dashboard only).
- Output dims: gemini-embedding-001, ≤2048 tokens, default 3072 dims, `output_dimensionality` 128–3072 (recommended 768/1536/3072); non-3072 dims must be manually L2-normalized. gemini-embedding-2: 8,192 ctx, auto-renormalizes truncated dims — [Embeddings doc](https://ai.google.dev/gemini-api/docs/embeddings).
- MTEB sanity anchors: 1536d ≈ 68.17, 768d ≈ 67.99, 512d ≈ 67.55, 256d ≈ 66.19.
- gemini-embedding-001 has dated shutdown 2028-05-14; gemini-embedding-2 (April 2026, multimodal) has an incompatible vector space — [Deprecations](https://ai.google.dev/gemini-api/docs/deprecations).
- Free tier batch NOT available for gemini-embedding-001.
- Stability: free-tier terms/quota can change at Google's discretion; no SLA.

## 2) Cloudflare Workers AI (@cf/baai/bge-m3 et al.)

### Genuinely free 10,000 neurons/day on every account, multilingual bge-m3, "zero data retention: Yes".

- Free allocation: **10,000 Neurons per day at no charge**, included in Workers Free AND Workers Paid; resets 00:00 UTC; "If you exceed any one of the above limits, further operations will fail with an error." Beyond 10k/day requires Workers Paid — [Workers AI Pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/) (updated Oct 20, 2026).
- Embedding prices: `@cf/baai/bge-m3` $0.012 / 1075 neurons per M tokens; `@cf/qwen/qwen3-embedding-0.6b` $0.012 / 1075; `@cf/baai/bge-small-en-v1.5` $0.020 / 1841 — so 10k free neurons/day ≈ **~9.3M bge-m3 tokens/day**.
- Rate limits (GA): Text Embeddings task: **3,000 requests/minute**; bge-large = 1,500 RPM — [Limits](https://developers.cloudflare.com/workers-ai/platform/limits/) (Sep 17, 2026).
- bge-m3 model page: "Context Window 60,000 tokens" (contradicts BAAI upstream card's 8,192 — unresolved), "Zero data retention: **Yes**", "Unit Pricing $0.0118 per M input tokens" — [bge-m3 model page](https://developers.cloudflare.com/workers-ai/models/bge-m3/).
- bge-m3 output dims: **1024** (100+ languages) [published BAAI card value; CF page does not restate — UNVERIFIED on CF page].
- Account: free Cloudflare account, no card for Workers Free (standard; page-unverified); Argentina signup unrestricted.
- Commercial use: no non-commercial clause found for Workers AI free allocation; Workers AI is GA, priced as infrastructure — treat as allowed, no "not for production" language.
- Stability: Cloudflare re-priced to granular units in 2026; free allocation could change; no SLA.
- Quota exceeded: requests "fail with an error" (HTTP shape unverified; typical CF envelope `{"success":false,"errors":[...]}` with 429).

## 3) Jina AI — jina-embeddings-v3 / v4 (v5 family now recommended line)

### Free API key gets free tokens (pool size not published); hard 100 RPM / 100K TPM cap on free keys; data NOT used for training; v4 is free because its weights are non-commercial — unsuitable for production.

- Free key limits: **Free API key: 100 RPM & 100,000 TPM**; Paid: 500 RPM / 2M TPM; Premium: 5,000 RPM / 50M TPM; limits per key over a 60s window; "a request over the limit returns HTTP 429 and should be retried with exponential backoff" — [jina.ai/embeddings](https://jina.ai/embeddings/).
- Free allowance: "New users get an auto-generated API key with free tokens" — amount **not published** (commonly cited 10M tokens — **[UNVERIFIED]**); buy more via Stripe if consumed.
- Commercial use: hosted API use needs no separate license (service terms cover it); professional use only.
- Jina v4 special case: built on Qwen2.5-VL, released under **Qwen Research License — non-commercial use only**; provided free via API; "It is not suitable for production workloads… For production use, take the jina-embeddings-v5 family." — same page.
- Dimensions: v3 dims 1024 (MRL 32→1024), task adapters `retrieval.query`/`retrieval.passage`, 8K ctx; v5-omni-small 1024d; v5-omni-nano 768d; v3 license CC-BY-NC-4.0 (weights non-commercial; API use OK).
- Data handling (verbatim FAQ): "**No.** We never use your API requests… to train our models." — same page.
- Account: email signup + API key; no card for free tokens; no country restrictions found (works from Argentina).
- Stability: repriced May 6, 2025; Elastic acquired Jina; no SLA; free pool can change.

## 4) Cohere — embed-multilingual-v3.0 / embed-v4.0 (current flagship: embed-v5.0-pro)

### Trial keys are free but explicitly NOT permitted for production/commercial purposes; 1,000 calls/month trial cap.

- "API calls made from a Trial API key are free. However, trial keys are rate limited and are **not permitted to be used for production or commercial purposes**." Every account starts with a Trial key — [cohere.com/pricing](https://cohere.com/pricing).
- Rate limits (official): **Trial keys limited to 1,000 API calls a month** (all endpoints); Embed trial: **2,000 inputs/minute**; images 5/min trial; rerank 10/min — [docs.cohere.com/docs/rate-limits](https://docs.cohere.com/docs/rate-limits).
- Production embed pricing not published on fetched page; historical Embed v3 = $0.10/M tokens [**UNVERIFIED**].
- Dims: `embed-v5.0-pro` Matryoshka [256..2048] (Oct 2026 flagship) — [docs.cohere.com/docs/embeddings](https://docs.cohere.com/docs/embeddings); `embed-multilingual-v3.0`: 1024 dims, ~100 langs, ~8K ctx [UNVERIFIED on current docs]; `embed-v4.0`: [256,512,1024,1536], 128k ctx. v3 requires `input_type=search_query/search_document`. Fixed 1024 for v3 → pgvector migration needed.
- 429: `429 Too Many Requests` documented.
- Account: signup, no card for trial; Argentina unrestricted.
- Stability: trial cap stable for years but changeable anytime; enterprise pivot; not production-usable on free.

## 5) Hugging Face Inference (hf-inference) & Inference Providers

### As of Nov 2026, no free inference credits for free accounts; PRO ($9/mo) includes $2/mo credits; effectively "near-zero", not free.

- Free users: **$0 monthly credits**; PRO: **$2.00/month**; Team/Enterprise: $2/seat — [HF Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing).
- Since July 2025 hf-inference focuses on CPU inference (embeddings OK); billed by compute time — costs ~zero for tiny batches but never free.
- hf-inference supports Feature Extraction (embeddings) — [Inference Providers docs](https://huggingface.co/docs/inference-providers). Dedicated Inference Endpoints start at $0.033/hour — not free.
- Model licenses apply per model (e.g., intfloat/multilingual-e5-small = MIT).
- Stability: HF has repeatedly shifted/killed free tiers (legacy serverless → pay-as-you-go July 2024+) — unreliable as a free path.

## 6) Voyage AI

### Largest free token pool among embedding APIs (200M tokens current models per account) — but Tier-1 requires a payment method, and by default data may be used for future model training unless an org admin opts out.

- Free tokens (one-time, per account, current models): voyage-4-large, voyage-4, voyage-4-lite, voyage-context-4, voyage-code-3/4: **200M tokens**; **voyage-multilingual-2**, voyage-finance-2, voyage-law-2, voyage-code-2: **50M tokens**; voyage-multimodal-3.x: 200M text + 150B pixels — free tokens do NOT apply to Batch API; not replenished — [docs.voyageai.com/docs/pricing](https://docs.voyageai.com/docs/pricing) (2026-09-29).
- After free pool: voyage-4-lite $0.02/M, voyage-4 $0.06/M, voyage-4-large $0.12/M. Older models: no free tokens.
- Rate limits (Tier 1 = "Payment method added"; Tier 2/3 higher): voyage-4-large/context-4/code: 3M TPM / 2000 RPM; voyage-4 / 3.5: 8M TPM; voyage-4-lite / 3.5-lite: 16M TPM — [Rate limits](https://docs.voyageai.com/docs/rate-limits). Exceeding → HTTP 429.
- Data policy (verbatim FAQ): opt-out of Voyage storing/using data for future model training (zero-day retention) requires **a payment method on file and org Admin role**; default is data may be used — [docs.voyageai.com/docs/faq](https://docs.voyageai.com/docs/faq).
- Commercial use: not restricted for hosted API; standard paid after free pool.
- Region: no published country restrictions (Argentina presumably OK; unverified).

## 7) Mistral (mistral-embed-2312 / codestral-embed-2505)

### No dedicated free embedding allowance; Free mode default for new accounts gets a small shared monthly included usage; mistral-embed $0.10/M tokens beyond it. Near-zero, not zero.

- "Free mode is the default state for new accounts." Usage shared across Studio/API/Vibe; exact Free-mode allowance not published — [subscriptions](https://docs.mistral.ai/admin/billing-usage/subscriptions.md); [mistral.ai/pricing](https://mistral.ai/pricing).
- `mistral-embed-2312` $0.10/M tokens paid; `codestral-embed-2505` $0.15/M — [API pricing](https://docs.mistral.ai/inference/pricing.md).
- mistral-embed: 1024 dims, unit-norm, ~8K ctx [partially UNVERIFIED]; text_embeddings docs verified — no input asymmetry param.
- Account: free signup; pay-as-you-go needs prepaid credits; no card until pay-as-you-go.
- Data-use policy on free/paid API not documented verbatim — gap.

## 8) NVIDIA build.nvidia.com NIM embeddings

### Free NVIDIA-hosted inference "for prototyping"; English-only embedding models — non-viable for CONCO.

- Free inference with leading models; "1,000 free credits per developer account" commonly cited **[UNVERIFIED]** — [build.nvidia.com](https://build.nvidia.com/).
- nv-embedqa-e5-v5: 1024 dims, max context **512 tokens, English-only** — [model card](https://build.nvidia.com/nvidia/nv-embedqa-e5-v5). English-only QA models: non-viable for Spanish.
- Commercial use allowed via NVIDIA AI Foundation Models Community License; hosted endpoints = prototyping; no production SLA.

## 9) GitHub Models — RETIRED

### Dead as of July 30, 2026. Any plan using "GitHub Models free text-embedding-3-small" is invalid.

- "As of July 30, 2026, GitHub Models has been fully retired." — [docs.github.com/en/github-models/prototyping-with-ai-models](https://docs.github.com/en/github-models/prototyping-with-ai-models). Successor path: Azure AI Foundry (free tier unverified this session).

## 10) OpenAI text-embedding-3-small — paid reference point

### Cheapest paid reference ($0.02/1M tokens); no free tier; card required.

- `text-embedding-3-small` **$0.02/1M tokens**; 3-large $0.13/M — [platform.openai.com/docs/pricing](https://platform.openai.com/docs/pricing). No free tier (only omni-moderation-latest is free).
- Dims 1536 default, `dimensions` param accepts any value ≤1536; context 8,191/8,192 tokens [exact current doc not re-fetched — UNVERIFIED]; card required; 429 rate_limit_exceeded standard behavior.
- Commercial use: yes (paid).

## 11) Other options found (mostly UNVERIFIED)

- Together AI — historically $1 free signup credits; embeddings via HF Inference Providers — [UNVERIFIED].
- Scaleway (via HF Inference Providers) — French cloud, historical free Serverless Inference allocation — [UNVERIFIED].
- Azure AI Foundry — designated GitHub Models successor; $200/30d trial credits classic — [UNVERIFIED].
- Groq/Cerebras — no embeddings.
- Self-hosted bge-m3 / multilingual-e5 / nomic-embed (Ollama) — not a hosted API; out of scope of the hosted constraint.

## Cross-provider synthesis (facts only)

- $0/mo, no card: Gemini free quota (**data-training clause applies to free inputs in Argentina**), Cloudflare 10k neurons/day (zero retention, bge-m3 1024d), Jina free tokens (429 at 100 RPM/100K TPM; no-training wording; v4 non-commercial), Mistral Free-mode monthly usage (unspecified). Cohere trial (1,000 calls/mo, **no production/commercial use**). HF: nothing free. OpenAI: nothing free. GitHub Models: retired.
- Card-required-but-free-in-effect: Voyage (200M one-time, 50M for multilingual-2; default training opt-in, opt-out needs card+org admin).
- Only Cloudflare bge-m3 page carries a verbatim zero-data-retention badge.
- 429 confirmed: Jina, Voyage, Google (RESOURCE_EXHAUSTED). Cohere 429 documented. Cloudflare/Mistral shapes unverified.
- Every free tier fetched is explicitly change-prone (Google revises terms periodically; Cloudflare re-priced in 2026; Jina repriced 2025; Mistral repackaged 2026; HF killed anonymous serverless free tier). **None carries an SLA.**
- Argentina: Gemini lists Argentina available; Cohere/Jina/Cloudflare/Voyage/Mistral/NVIDIA/OpenAI publish no country blocks; EEA/UK/CH is the only special-cased region (Google forces Paid Services there for API Clients serving users).

## Could not verify this session

1. Exact current free-tier RPM/RPD/TPM for Gemini embeddings (AI Studio dashboard only now).
2. Jina free token pool size (login-gated; 10M cited but UNVERIFIED).
3. Cohere Embed-specific trial cap details and current embed-v4/v5 pricing.
4. Mistral Free-mode monthly included usage allowance.
5. NVIDIA credit count and per-model RPM.
6. OpenAI default-data-use clause re-verification this session.
7. Cloudflare exact HTTP error body when 10k neurons exhausted; whether Workers Free strictly needs a card.
8. hf-inference rate limits / any hidden free embedding allowance.
9. Azure AI Foundry free tier details.
10. Voyage default opt-in nuance beyond the FAQ wording.
11. bge-m3 dimension restatement on Cloudflare's own page (1024 from BAAI card).
12. text-embedding-004 deprecation date specifics on Gemini API (absent from pricing).
13. Mistral/NVIDIA/OpenAI ToS verbatim — owner should do a legal pass before shipping.
