# Feature: activity semantic search (guidance)

- **Branch:** `feature/04-caba-tramites-integration` (PR #65; the user asked for everything in this PR). Delivery: work-unit commits on this branch. Runner: `uv run pytest` (back), front runner per `front/package.json`.
- **Locator:** `odd/tasks/activity-semantic-search.md` · Engram topic `odd/activity-semantic-search/tasks`

## Specs

- **S1** — `GET /guidance/activities?query=<text>` suggests the curated activities closest in meaning to the free text (embedding similarity against every activity alias), ranked, dropping those under a minimum similarity. Each suggestion has slug, name, matched alias and similarity.
- **S2** — `GET /guidance/activities/{slug}/procedures` returns the activity and its curated procedures in order, each with its note ("when it applies"), title, summary, official URL and last update, plus the official `source` (RN-05). Unknown slug → `404`.
- **S3** — The embedding model runs inside the same FastAPI process, behind a domain port, so it can move to a separate service later by swapping the adapter. User question (L2): "no se si crea otra api para lo del modelo"; answer: no separate API.
- **S4** — Data lives in Postgres + pgvector (local Supabase in `back/supabase`, migrations versioned). A loader command rebuilds the procedure catalog (868 published procedures with `field_sector_economico`) and the curated activities with their embeddings. Database unavailable → `503`.
- **S5** — The curated activity → procedures relation is versioned in the repo and marked as a draft pending domain review: procedures that usually apply, not a legal determination (RN-04).
- **S6** — Frontend: a box where the person types the activity, sees suggested activities while typing, picks one and sees its procedures with notes and official links.
- **S7** — Tests (offline unit tests with fakes; database-backed checks marked so the default run stays offline) and docs (`back/README.md`, run instructions).

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S3, S4, S5 | inline | pending | |
| T2 | S1, S2, S7 | inline | pending | |
| T3 | S7 | inline | pending | |
| T4 | S6 | inline | pending | |
| T5 | S1–S6 | inline | pending | |

- T1: config, dependencies, domain port, embedding + Postgres adapters, curated data file, loader command.
- T2: activity endpoints and their tests.
- T3: README and run instructions.
- T4: frontend activity search.
- T5: end-to-end check in the browser.

Risk: item 5 (new runtime dependencies `fastembed`, `psycopg`, and a database the deploy now needs).

## Log

- **L1 (2026-11-05)** — "bueno quiero implementarlo apra este pr para que sea util la api y para el frontend"
- **L2 (2026-11-05)** — "todo dentro de este pr pero no se si crea otra api para lo del modelo"
- **L3** — Evidence from the prototype (`back/scripts/learning/procedures_lab.py`): searching procedures directly fails for one-word activities ("Habilitación de actividad económica" never ranks); matching against curated activity aliases works (barbería → Peluquería 0.85, cafetería 0.94, gimnasio 0.30 = no match). Short rare words score spuriously high (~0.7), so the UI lets the person pick among suggestions instead of auto-selecting.
