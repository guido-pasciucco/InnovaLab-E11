# Feature: Georef integration

- **Branch:** `feature/georef-integration` (stacked on `feature/backend-setup`, PR #50)
- **Locator:** `odd/tasks/georef-integration.md` · Engram topic `odd/georef-integration/tasks`

## Objective

Integrate the Georef `/direcciones` endpoint so the backend can turn a free-text address into a normalized address with approximate coordinates (MVP item 4: approximate map location).

## Problem / why

The MVP needs a map pin for the address the entrepreneur types. Georef (datos.gob.ar) is official, needs no API key, and was verified live on 2026-10-31. The user chose Georef after reviewing its context.

## Scope

- `src/conco/config.py`: Georef base URL and timeout settings.
- `src/conco/integrations/georef/client.py`: the only place that calls Georef over HTTP.
- `src/conco/integrations/georef/models.py`: Pydantic models of the observed Georef response.
- `scripts/probe_georef.py`: runs the client in isolation.
- Unit tests with mocked HTTP (respx) using real captured responses, plus an opt-in integration test against the live API.
- Docs: `docs/DEPENDENCIAS.md`, `back/README.md` checklist.

Out of scope: FastAPI endpoint, caching, retries (later PRs).

## Constraints

- Only files under `integrations/georef/` know Georef details (URLs, params, response shape).
- Models come from observed responses, never assumptions.
- No hardcoded URLs: everything variable comes from `config.py`.
- English identifiers, Spanish project docs.
- `back/.env.example` cannot be written by the agent (permission-denied): the user adds `GEOREF_*` variables.

## Observed Georef behavior (2026-10-31)

- `cantidad: 0` → `direcciones: []`.
- Street without number → `altura.valor: null`, still returns `ubicacion`.
- Without `provincia` the query is ambiguous across provinces.
- Missing `direccion` → HTTP 400 with `{"errores": [...]}`.
- Docs: `ubicacion` may be absent when data is insufficient; coordinates are approximate.

## Tasks

- [x] T1 · Config settings, client skeleton, probe script, httpx dependency (route: inline; small, already designed)
- [x] T2 · Models + typed client + `GeorefError` + unit/integration tests (route: delegated writer; trigger: 2+ non-trivial files)
- [x] T3 · Docs: DEPENDENCIAS dev deps + testing, README checklist (route: inline; mechanical)
- [ ] T4 · User adds `GEOREF_*` variables to `back/.env.example` and commits it (agent is permission-denied on `.env*`)

## Acceptance criteria

- `uv run pytest` passes offline (integration tests deselected by default).
- `uv run pytest -m integration` passes against live Georef.
- `uv run python scripts/probe_georef.py "Corrientes 2500"` prints a typed result.
- HTTP errors, timeouts and unexpected payloads surface as `GeorefError`.

## Checks

- `uv run pytest`
- `uv run pytest -m integration`
- `uv run python scripts/probe_georef.py "Corrientes 2500"`

## Progress / evidence

- 2026-10-31: T1 written and verified in a scratch copy (base_url path merge, normalization, probe, ConnectTimeout, HTTP 404). Real fixtures captured. Commit `f65dbf5`.
- 2026-10-31: T2 by delegated writer. RED: `ImportError: cannot import name 'GeorefError'`. GREEN: `9 passed, 1 deselected`. Parent re-ran: `uv run pytest -q` → 9 passed, 1 deselected; `uv run pytest -m integration -q` → 1 passed (live Georef); probe with `"  corrientes   2500 "` → typed result, Comuna 3. Writer deviation accepted: parse with `model_validate_json(response.content)` so non-JSON bodies become `GeorefError`.
- 2026-10-31: T3 docs updated (README checklist ticked + Tests section; DEPENDENCIAS dev dependencies).

## Next step

T4 (user), then open the Georef PR with base `feature/backend-setup` (retarget to `main` after PR #50 merges).
