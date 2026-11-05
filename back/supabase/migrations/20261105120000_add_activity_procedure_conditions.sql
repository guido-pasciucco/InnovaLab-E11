-- Answers the context must have for a procedure to apply to an activity, keyed by the
-- context question (for example {"has_employees": true}). Empty means it always applies.
alter table public.activity_procedures
    add column applies_when jsonb not null default '{}'::jsonb;
