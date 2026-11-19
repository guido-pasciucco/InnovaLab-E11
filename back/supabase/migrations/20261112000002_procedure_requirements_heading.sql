-- Keep the requirement heading (field_texto) as its own column instead of folding it
-- into the body text. Nullable: most requirement items have no heading.
alter table public.procedure_requirements
    add column heading text;
