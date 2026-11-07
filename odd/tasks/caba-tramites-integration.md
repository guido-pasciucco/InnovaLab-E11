# Feature: CABA trámites integration (guidance)

- **Branch:** `feature/caba-tramites-integration` (stacked on `feature/geolocation-endpoint`)
- **Locator:** `odd/tasks/caba-tramites-integration.md` · Engram topic `odd/caba-tramites-integration/tasks`

## Objective

Let the frontend search the official City of Buenos Aires procedure catalog and show, for one procedure, its summary, requirements, steps, responsible office and the official link to start it, always citing the official source.

## Problem / why

The MVP promises general guidance on procedures with official reference links (README responsibilities 3 and 4; RN-04, RN-05, RN-07). Until now CONCO only geocodes addresses; it has no procedure content. The README already plans a `guidance/` feature folder for "orientación por actividad".

API choice: delegated by the user on 2026-10-31. Source: Drupal JSON:API of buenosaires.gob.ar, resource `node/tramites_obelisco`, no key, content license Creative Commons Reconocimiento 2.5 Argentina. The JSON:API is not publicly documented (it is Drupal's default JSON:API left open), so its shape may change without notice; the integration test is the early warning.

## Scope

- `src/conco/config.py`: `caba_tramites_base_url`, `caba_tramites_site_url`, `caba_tramites_timeout_seconds`.
- `src/conco/integrations/caba_tramites/`: client (`search_procedures`, `get_procedure`), models, single `CabaTramitesError`.
- `scripts/probes/caba_tramites.py`.
- `src/conco/guidance/`: domain (`Procedure`, `ProcedureDetail`, `Source`, `ProcedureCatalog`, `ProcedureSearchError`), adapter (`CabaProcedureCatalog`, HTML → plain text), router (`GET /guidance/procedures`, `GET /guidance/procedures/{procedure_id}`), included in `main.py`.
- Real fixtures, unit tests (client, adapter, API) and integration tests (client, API).
- Docs: `back/README.md`.

Out of scope: caching, persistence, matching an activity to procedures (needs a product decision), costs and documents of each procedure, frontend.

## Constraints

- Only `integrations/caba_tramites/` knows URLs, JSON:API parameters and Drupal paragraph types; domain and router never import them.
- Every response cites the official source (name, URL, license) and each procedure carries its official page URL (RN-05).
- No new runtime dependencies (stdlib `html.parser` for HTML → text). No database.
- `back/.env*` is not editable by the implementer: defaults in `config.py` make everything work.
- English identifiers, Spanish docs and messages. No AI attribution in commits.

## Observed API behavior (2026-10-31)

- Search: `GET /jsonapi/node/tramites_obelisco?filter[status]=1&filter[title][operator]=CONTAINS&filter[title][value]=<q>&sort=title&page[limit]=<n>&fields[node--tramites_obelisco]=title,path,changed,body`. httpx percent-encodes the brackets (`%5B`/`%5D`) and the API accepts it.
- `CONTAINS` on the title is case- and accent-insensitive (`habilitacion`, `HABILITACIÓN` and `habilitaci` return the same 11 results). `caf` returns 0.
- Without `filter[status]=1`, `meta.count` is 960 and pages come short (unpublished items are omitted with an `omitted` block); with it, `meta.count` is 868 and pages are full.
- Over the 868 published procedures: `body` and `path.alias` are never null and `body.format` is always `plain_text`.
- Detail: `GET /jsonapi/node/tramites_obelisco/<uuid>?include=...&fields[...]=...`. Content is nested paragraphs: `field_contenido` → `field_seccion` → `field_columna_{central,izquierda,derecha}` → `field_componente` → `requisito_tramite` / `pasos_del_tramite` (with `field_item_requisito_tramite` / `field_item_paso_del_tramite`), `organismo_responsable`, `boton_iniciar_tramite`. Sampling 25 procedures: always one `organismo_responsable`; one had no `boton_iniciar_tramite`.
- Sparse fieldsets apply to included types too; an empty value (`fields[paragraph--parrafo]=`) drops all attributes, which keeps the detail around 35 KB.
- Unknown filter field → 400 JSON:API `errors[].detail`. Unknown, unpublished or malformed UUID → 301 redirect to an HTML page under `/gcaba_historico/` (treated as not found).
- Official procedure page = `https://buenosaires.gob.ar` + `path.alias`. Catalog page: `https://buenosaires.gob.ar/gobierno/tramites`. Site footer: "Creative Commons Reconocimiento 2.5 Argentina".

## Tasks

- [x] T1 · Integration: config, client, models, probe, fixtures, client unit tests, client integration test (route: delegated writer, 2+ non-trivial files)
- [x] T2 · Guidance feature: domain, adapter, router, `main.py`, unit and integration tests (route: delegated writer, same)
- [x] T3 · Docs: `back/README.md` and this document (route: delegated writer, same unit of work)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /guidance/procedures?query=habilitaci` returns procedures with official URL and the `source` block.
- `GET /guidance/procedures/338718b4-a2a0-44af-baa4-083f5d834b12` returns requirements, steps, responsible office and start URL.
- Unknown procedure → 404. Source down or malformed → 502. Invalid params → 422.

## Checks

- `uv run pytest -q`
- `uv run pytest -q -m integration`
- `uv run python scripts/probes/caba_tramites.py habilitaci`

## Progress / evidence

- 2026-10-31 · T1 RED: `uv run pytest -q tests/unit/caba_tramites` → `ModuleNotFoundError: No module named 'conco.integrations.caba_tramites'` (1 error during collection).
- 2026-10-31 · T1 GREEN: 16 passed. Fixtures recaptured with the client's own `search_params` / `DETAIL_PARAMS`: all five responses identical to the stored files. Live survey of 90 published procedures with `get_procedure`: 90 ok, 0 errors; 5 steps without explanation (`field_parrafo: null`, hence optional), 7 procedures without start button, office and button link never null.
- 2026-10-31 · T1 commit `8ec579f` feat(back): add CABA trámites JSON:API client.
- 2026-10-31 · T2 RED: `uv run pytest -q tests/unit/guidance` → `ModuleNotFoundError: No module named 'conco.guidance'` (2 errors during collection).
- 2026-10-31 · T2 GREEN: 27 passed. Live smoke through `TestClient`: detail of `338718b4-...` → 200 with 11 requirements and 5 steps; `/openapi.json` lists `/guidance/procedures` and `/guidance/procedures/{procedure_id}`.
- 2026-10-31 · T2 commit `7fe1fd3` feat(back): expose official procedure guidance endpoints.
- 2026-10-31 · Checks: `uv run pytest -q` → 68 passed, 6 deselected. `uv run pytest -q -m integration` → 6 passed (Georef + CABA, live). `uv run python scripts/probes/caba_tramites.py habilitaci` → 10 procedures printed.
- 2026-10-31 · T3: README (structure, API card with limitations, endpoint section) and this document, committed together as `docs(back): document CABA procedures guidance and feature progress`.
- Decisions:
  - Not found is `None` in both layers (client `get_procedure` and port `ProcedureCatalog.get`), mapped to 404 by the router; no extra exception type.
  - `filter[status]=1` and `sort=title` are always sent: full pages and a stable order.
  - The client resolves the paragraph graph (following relationship order) and validates each used paragraph with its own model inside the `try`, so any shape change surfaces as `CabaTramitesError` → 502.
  - Each requirement text becomes one entry, prefixed with the item heading when present (`Importante: ...`). Each step is `title: explanation`, or only the title.
  - `body` is stripped of HTML only when its format is not `plain_text` (all 868 published procedures use `plain_text`).
  - `ProcedureCatalog.source` is a property of the port, so the router cites the source without knowing which API is behind it.
- Note: `StarletteDeprecationWarning` (httpx with `starlette.testclient`) comes from the installed FastAPI/Starlette, not from this change.

## Environment variables pending for `back/.env.example`

The implementer cannot edit `back/.env*`. Add:

```bash
# Trámites de la Ciudad de Buenos Aires (JSON:API de buenosaires.gob.ar)
CABA_TRAMITES_BASE_URL=https://buenosaires.gob.ar/jsonapi
CABA_TRAMITES_SITE_URL=https://buenosaires.gob.ar
CABA_TRAMITES_TIMEOUT_SECONDS=10
```

## Next step

- User: add the three variables above to `back/.env.example`.
- User decision: push the branch and open the PR with base `feature/geolocation-endpoint`.
- Later (needs a product decision): map an activity (for example "cafetería") to the relevant procedures; title search alone does not do it (`caf` returns 0).
