-- Approximate nearest-neighbor index for the semantic activity search.
-- Without it, every suggestion scans and sorts all alias embeddings.
create index activity_aliases_embedding_idx on public.activity_aliases
using hnsw (embedding extensions.vector_cosine_ops);
