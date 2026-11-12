# Feature: activity semantic search (guidance)

- **Branch:** `feature/04-caba-tramites-integration` (PR #65; the user asked for everything in this PR). Delivery: work-unit commits on this branch. Runner: `uv run pytest` (back), front runner per `front/package.json`.
- **Locator:** `odd/tasks/activity-semantic-search.md` · Engram topic `odd/activity-semantic-search/tasks`

## Specs

- **S1** — `GET /guidance/activities?query=<text>` suggests the curated activities closest in meaning to the free text (embedding similarity against every activity alias), ranked, dropping those under a minimum similarity. Each suggestion has slug, name, matched alias and similarity.
- **S2** — `GET /guidance/activities/{slug}/procedures` returns the activity and its curated procedures in order, each with its note ("when it applies"), title, summary, official URL and last update, plus the official `source` (RN-05). Unknown slug → `404`.
- **S3** — The embedding model runs inside the same FastAPI process, behind a domain port, so it can move to a separate service later by swapping the adapter. User question (L2): "no se si crea otra api para lo del modelo"; answer: no separate API.
- **S4** — Data lives in Postgres + pgvector (local Supabase in `back/supabase`, migrations versioned). A loader command rebuilds the procedure catalog and the curated activities with their embeddings; the loader stores **only the procedures referenced by the curated catalog** (the app never reads the rest) and still validates that every curated id exists in the published list. Database unavailable → `503`.
- **S5** — The curated activity → procedures relation is versioned in the repo and marked as a draft pending domain review: procedures that usually apply, not a legal determination (RN-04).
- **S6** — Frontend: a box where the person types the activity, sees suggested activities while typing, picks one and sees its procedures with notes and official links.
- **S7** — Tests (offline unit tests with fakes; database-backed checks marked so the default run stays offline) and docs (`back/README.md`, run instructions).

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T1 | S3, S4, S5 | inline | done | f582840 |
| T2 | S1, S2, S7 | inline | done (RED import error → GREEN 18 tests) | f582840 |
| T3 | S7 | inline | done | f582840, 0d1a5fd |
| T4 | S6 | inline | done (typecheck + build; front has no test runner) | 0d1a5fd |
| T5 | S1–S6 | inline | done (browser check) | — |

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
- **L4** — Design: procedures are stored without embeddings (searching them failed in the prototype); only activity aliases are embedded. The curated file moved to `back/src/conco/guidance/data/activities.json`; the prototype script was removed. `_to_procedure` became the public `to_procedure`, reused by the loader. CABA models gained the optional `field_sector_economico` (`sector`); search requests do not ask for it, so their behavior is unchanged.
- **L5** — Evidence: `uv run pytest` → 95 passed, 10 deselected; `uv run pytest -m database` → 4 passed (barbería → peluqueria, gimnasio → none, cafetería procedures in curated order, unknown → None). Loader: 868 procedures, 6 activities, 34 aliases. Front: `npm run typecheck` and `npm run build` pass. Browser: "quiero poner una barbería" → suggestion «Peluquería · parecido a «barbería»» → step 3 lists 4 official procedures with note, link and the CABA source; "quiero abrir un gimnasio" → "No encontramos una actividad parecida"; no console errors.
- **L6** — Open: the curated relation is a draft (RN-04) and needs domain review; deploy needs Postgres + pgvector and ~600 MB RAM for the model.
- **L7 (2026-11-12)** — Loader now stores only the curated-referenced procedures (user: "no creo que haga falta que envie todos los trámites"). The app only reads referenced rows (join in `_PROCEDURES_SQL`); the other 852+ published rows were never read. `load()` keeps the existence validation against the published list (prints both counts: published vs referenced). RED → GREEN: `test_referenced_procedures_keeps_only_what_the_curated_catalog_references`; `uv run pytest` → 107 passed, `-m database` → 5 passed. Reload: published 870, referenced 16 stored; DB verified 16 rows in `procedures`, 54 in `activity_procedures`, all referenced. Trade-off recorded: a future semantic search over trámites (idea doc) would need the full catalog re-loaded with embeddings.
- **L8 (2026-11-12)** — Curated catalog expanded 6 → 9 activities (user: "encontra justamente los trámites para esas actividades"; approved set = keep the 6 user-facing entries + carnicería + hotel + óptica; dropping entries would break "No encontramos una actividad parecida" for exactly those rubros). Verified against the official API: **hotel** has two real trámites (Inscripción en el Registro de Prestadores Turísticos e459e8d6, sectors turistico; Rúbrica del libro de pasajeros b8a8c54e, citing Ley 4.631) plus the existing Exclusión Generadores Hoteleros 266d2abd; **óptica** has no applicable habilitación in the API (nearest match is a complaints channel — excluded per RN-04; the sanitaria habilitación, Ley 7.314, is handled in a note as an out-of-API step); **carnicería** has no dedicated trámites (tronco + Curso de Manipulación c5e44825; SENASA/cadena de frío live in notes, not as rows). Gimnasio discarded: its only match (Registro Único de Instituciones Deportivas b1bdbd59) is a dubious fit for commercial gyms (Ley 139). CAA/húmedos reassignment: see L9. RED → GREEN: `test_repo_catalog_has_the_nine_agreed_activities`; `uv run pytest` → 108 passed, `-m database` → 5 passed. Reload: 870 published, **18 referenced** (the two new hotel ids), 9 activities, 53 aliases; per-activity rows verified (cafeteria 11, carniceria 9, comercio-minorista 9, foodtruck 6, hotel 11, kiosco 8, optica 8, peluqueria 8, restaurante 12). Kiosco/peluquería notes reinforced from docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md.
- **L9 (2026-11-12)** — CAA (Impacto Ambiental: Certificado de Aptitud Ambiental, fc321f1e) added as tronco común to all 9 activities (user approved option (a) per docs/pendientes/HABILITACION_Y_CATALOGO.md task 3: the doc declares CAA mandatory categorization for every activity, Ley 123). *Inscripción en el Registro de Generadores Especiales de Residuos Sólidos Urbanos para Fracción Húmedos* (1304fa97) moved from Restaurante to Carnicería. Appended at the end of each activity's procedure list (review order); Restaurante keeps its original CAA position. RED → GREEN: `test_caa_is_tronco_comun_and_hummedos_lives_in_carniceria`; `uv run pytest` → 109 passed, `-m database` → 5 passed. Reload: 18 referenced, 9 activities, 53 aliases (ids already counted); per-activity rows verified (cafeteria 12, carniceria 11, comercio-minorista 10, foodtruck 7, hotel 12, kiosco 9, optica 9, peluqueria 9, restaurante 11).
- **L10 (2026-11-12)** — Migration `20261112000000_add_activity_aliases_vector_index` (HNSW index `activity_aliases_embedding_idx` on `activity_aliases.embedding`, vector_cosine_ops) was applied to the local stack with `npx supabase migration up` (not `db reset` — that would have wiped the DB for nothing). Benefit today is marginal: the `_SUGGEST_SQL` lateral query scans ~53 rows; the index matters if the corpus grows (more activities/aliases, or vectorizing trámites under RN-01) and the planner can pick it for the pattern. Index verified present; 53 alias rows intact; `-m database` → 5 passed.
