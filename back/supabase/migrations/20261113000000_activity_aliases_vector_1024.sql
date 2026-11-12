-- Switch the activity search embeddings from MiniLM (384 dims, local fastembed)
-- to bge-m3 served by Cloudflare Workers AI (1024 dims).
-- pgvector's vector(n) type is exact, so vector(384) cannot be altered in place:
-- drop the derived column and rebuild it. The alias rows are derived data;
-- `python -m conco.guidance.load_catalog` re-embeds and re-inserts them.
-- The HNSW index is created here because the table is empty at this point;
-- with this catalog size (a few dozen rows) it makes no practical difference.
drop index if exists public.activity_aliases_embedding_idx;
alter table public.activity_aliases drop column embedding;
truncate table public.activity_aliases;
alter table public.activity_aliases add column embedding extensions.vector(1024) not null;
create index activity_aliases_embedding_idx on public.activity_aliases
using hnsw (embedding extensions.vector_cosine_ops);
