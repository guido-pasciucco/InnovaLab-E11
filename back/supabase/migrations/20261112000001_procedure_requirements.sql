-- Requirement checklists per official procedure, exactly as published by the Ciudad
-- (plain text, already stripped of HTML). Rebuilt by the same tooling that loads the
-- catalog; `procedure_id` references the local copy of the official catalog.
create table public.procedure_requirements (
    procedure_id uuid not null references public.procedures(id) on delete cascade,
    position int not null,
    text text not null,
    primary key (procedure_id, position)
);

create index procedure_requirements_procedure_idx on public.procedure_requirements (procedure_id);
