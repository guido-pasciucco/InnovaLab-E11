-- Curated relation between business activities (what the person wants to do) and the
-- official procedures that usually apply. Loaded from src/conco/guidance/data/activities.json.
create table public.activities (
    slug text primary key,
    name text not null
);

-- Every way of naming an activity (its name plus synonyms), each with its own embedding,
-- so a free-text query is matched against the closest alias instead of an averaged vector.
create table public.activity_aliases (
    activity_slug text not null references public.activities (slug) on delete cascade,
    alias text not null,
    embedding_model text not null,
    embedding extensions.vector(384) not null,
    primary key (activity_slug, alias)
);

-- No foreign key to public.procedures: the loader rebuilds that table on every run and
-- checks that every referenced procedure exists instead.
create table public.activity_procedures (
    activity_slug text not null references public.activities (slug) on delete cascade,
    procedure_id uuid not null,
    -- When or why the procedure applies to this activity.
    note text not null,
    position integer not null,
    primary key (activity_slug, procedure_id)
);
