# Feature: Geolocation endpoint

- **Branch:** `feature/geolocation-endpoint` (stacked on `feature/georef-integration`, PR #51)
- **Locator:** `odd/tasks/geolocation-endpoint.md` · Engram topic `odd/geolocation-endpoint/tasks`

## Objective

Expose `GET /geolocation/addresses` so the frontend can turn a free-text address into normalized addresses with approximate coordinates, and so the user can try it from FastAPI `/docs`.

## Problem / why

The Georef client exists but nothing in the API uses it. The MVP needs a map pin for the address the entrepreneur types (README responsibility 5). The README plans one folder per feature (`geolocation/`) with layers.

## Scope

- `src/conco/geolocation/domain.py`: `Address`, `Coordinates`, `AddressFinder` port, `AddressSearchError`.
- `src/conco/geolocation/infrastructure.py`: `GeorefAddressFinder` adapter (maps Georef models to the domain).
- `src/conco/geolocation/api.py`: router, dependency, error translation (502).
- `src/conco/main.py`: include the router.
- Unit tests: adapter (respx + real fixtures) and API (TestClient + `dependency_overrides`).
- Docs: `back/README.md` structure and endpoint usage.

Out of scope: caching, retries, an application/use-case layer (no logic to hold yet).

## Constraints

- Only `integrations/georef/` and the adapter know Georef shapes; domain and API never import Georef models.
- Georef failures surface as HTTP 502, never as an unhandled 500.
- English identifiers, Spanish project docs. No AI attribution in commits.

## Tasks

- [x] T1 · Domain + Georef adapter + adapter tests (route: inline; learn-by-example session, user wants each file explained)
- [x] T2 · API router + dependency + API tests + include in `main.py` (route: inline; same reason)
- [x] T3 · README: structure and endpoint usage (route: inline; mechanical)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /geolocation/addresses?address=Corrientes 2500` returns normalized addresses with coordinates.
- Georef down or malformed → 502 with a clear message. Invalid query params → 422.
- The endpoint appears in `/docs` and "Try it out" works against live Georef.

## Checks

- `uv run pytest`
- `uv run pytest -m integration`
- Manual: `uv run uvicorn conco.main:app --reload` → `/docs`

## Progress / evidence

- 2026-10-31: RED observed: `ModuleNotFoundError: No module named 'conco.geolocation'` for both new unit test modules.
- 2026-10-31: GREEN: `uv run pytest -q` → 25 passed, 1 deselected. `uv run pytest -q -m integration` → 2 passed (live Georef, client and endpoint). `/openapi.json` lists `/geolocation/addresses` with params `address`, `province`, `limit`; `/docs` → 200.
- Decision: `pattern=r"\S"` on `address` rejects whitespace-only input with 422 instead of forwarding an empty query to Georef (which would surface as a misleading 502). Verified by the parametrized 422 test.
- Note: Starlette emits `StarletteDeprecationWarning` (httpx with `starlette.testclient`); comes from the installed FastAPI/Starlette, not from this change.

## Next step

Push the branch and open the PR with base `feature/georef-integration` (user decision).
