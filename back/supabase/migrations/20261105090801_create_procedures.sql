-- Local copy of the CABA official procedures catalog, rebuilt by
-- `uv run python -m conco.guidance.load_catalog`.
create table public.procedures (
    id uuid primary key,
    title text not null,
    summary text not null,
    url text not null,
    -- field_sector_economico from the CABA API; null for non-business procedures.
    sector text,
    changed_at timestamptz not null,
    loaded_at timestamptz not null default now()
);

create index procedures_sector_idx on public.procedures (sector);
