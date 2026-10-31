# Feature: Georef CABA location check (RN-02 guard)

- **Branch:** `feature/georef-caba-check` (stacked on `feature/epok-integration`)
- **Locator:** `odd/tasks/georef-caba-check.md` · Engram topic `odd/georef-caba-check/tasks`

## Objective

Given a point (latitude/longitude), tell the frontend whether it is inside the Ciudad Autónoma de Buenos Aires, with the province and department names, always citing the official source. This is the deterministic check behind RN-02 ("only CABA locations are accepted").

## Problem / why

RN-02 restricts CONCO to CABA, but until now nothing verified it for a point: `/geolocation/addresses` only filters the search by `provincia=caba`, and the coordinate-based endpoints (`address-context/by-coordinates`, `nearby-offices`) accept any point. Georef `/ubicacion` returns the province id of a point, and `"02"` is CABA, so the check is exact and does not depend on name spelling.

API choice: third API of round 2. It reuses Georef (datos.gob.ar, CC BY 4.0, no key, same base URL and timeout) because no new official no-key API with clear MVP value was found. Discarded: CABA JSON:API `node/sedes` (placeholder opening hours), `node/turnos` (empty), Series de Tiempo IPC and BCRA (no MVP value), ArgentinaDatos feriados (unofficial), InfoLEG (bulk download only), AFIP padrón (needs a certificate).

## Scope

- `src/conco/integrations/georef/`: `locate(latitude, longitude)` in the client (shared private `_get` with `search_addresses`), models `GeorefLocation`, `GeorefLocationResponse`; reuses `GeorefError` and `GeorefNamedEntity`.
- `scripts/probes/georef.py`: new `--locate LAT LON` mode; the address usage is unchanged.
- `src/conco/geolocation/`: domain (`LocationCheck`, `LocationChecker`, `LocationCheckError`, reuses `Source`), adapter `GeorefLocationChecker` with `CABA_PROVINCE_ID = "02"`, endpoint `GET /geolocation/location-check`.
- Real fixtures, unit tests (client, adapter, API) and integration tests (client, API).
- Docs: `back/README.md`.

Out of scope: applying the guard inside the existing endpoints (`/geolocation/addresses`, `/geolocation/address-context*`, `/geolocation/nearby-offices`, `/guidance/*`), caching, persistence, frontend.

## Constraints

- Only `integrations/georef/` knows the Georef URL, parameters and response shape.
- Existing endpoints keep their behavior; existing Georef tests pass unchanged.
- Every response cites the official source (RN-05).
- No new runtime dependencies, no database, no new configuration.
- English identifiers, Spanish docs and messages. No AI attribution in commits.

## Observed API behavior (2026-10-31)

- `GET /ubicacion?lat=-34.6047137&lon=-58.4021372` → 200 in 0.02–0.07 s: `provincia {"id":"02","nombre":"Ciudad Autónoma de Buenos Aires"}`, `departamento` and `municipio` "Comuna 3", plus `lat`/`lon` and `parametros`.
- `lat=-34.9214&lon=-57.9545` (La Plata) → 200, `provincia {"id":"06","nombre":"Buenos Aires"}`, `departamento` "La Plata".
- `lat=-40&lon=-30` (South Atlantic) and `lat=40.4168&lon=-3.7038` (Madrid) → 200 with `provincia`, `departamento` and `municipio` present but `id` and `nombre` null.
- `lat=abc` → 400 `{"errores":[{"codigo_interno":1001,"mensaje":"El parámetro no es un número real.",...}]}`; missing `lat` → 400 `codigo_interno` 1003.
- `lat=-95` → 500 `{"errores":[{"mensaje":"Ocurrió un error interno de servidor..."}]}`. The CONCO endpoint validates ranges first (422), so it never sends such a request.
- Fixtures captured with the client's own parameters (`lat`, `lon`): `ubicacion_caba_corrientes_2500.json`, `ubicacion_la_plata.json`, `ubicacion_fuera_de_argentina.json`, `error_400_lat_invalida.json`.

## Tasks

- [x] T1 · Integration: client `locate`, models, probe mode, fixtures, client unit tests, client integration test (route: delegated writer, 2+ non-trivial files)
- [x] T2 · Geolocation: domain, adapter, endpoint, unit and integration tests (route: delegated writer, same)
- [x] T3 · Docs: `back/README.md` and this document (route: delegated writer, same unit of work)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /geolocation/location-check?latitude=-34.6047137&longitude=-58.4021372` → 200 with `in_caba: true` and the `source` block.
- Other province or outside Argentina → 200 with `in_caba: false` (not 404). Georef down or unexpected payload → 502. Invalid params → 422.
- Existing endpoints unchanged.

## Checks

- `uv run pytest -q`
- `uv run pytest -q -m integration`
- `uv run python scripts/probes/georef.py "Corrientes 2500"` and `uv run python scripts/probes/georef.py --locate -34.6047137 -58.4021372`

## Progress / evidence

- 2026-10-31 · T1 RED: `uv run pytest -q tests/unit/georef` → `ImportError: cannot import name 'locate' from 'conco.integrations.georef.client'` (1 error during collection).
- 2026-10-31 · T1 GREEN: `tests/unit/georef` 17 passed (9 existing unchanged + 8 new). Live client integration: 2 passed. Full unit suite: 192 passed.
- 2026-10-31 · T1 commit `562a2de` feat(back): add Georef reverse geocoding client.
- 2026-10-31 · T2 RED: `uv run pytest -q tests/unit/geolocation` → `ImportError: cannot import name 'LocationCheck' from 'conco.geolocation.domain'` and `ImportError: cannot import name 'get_location_checker' from 'conco.geolocation.api'` (2 errors during collection).
- 2026-10-31 · T2 GREEN: full unit suite 211 passed. Live endpoint integration: 1 passed.
- 2026-10-31 · T2 commit `76bd1d4` feat(back): expose CABA location check endpoint.
- 2026-10-31 · Checks: `uv run pytest -q` → 211 passed, 18 deselected. `uv run pytest -q -m integration` → 18 passed. Probe `"Corrientes 2500"` → 1 address (unchanged). Probe `--locate -34.6047137 -58.4021372` → province id `02`; `--locate -40 -30` → all entities null.
- 2026-10-31 · T3: README (structure, Georef `/ubicacion` card, endpoint section with the follow-up note) and this document, committed together as `docs(back): document CABA location check and feature progress`.
- Decisions:
  - CABA is decided by `provincia.id == "02"` (`CABA_PROVINCE_ID`), not by name.
  - Outside CABA or outside Argentina is a valid answer (200, `in_caba: false`), not 404: the endpoint answers a yes/no question.
  - `province` and `department` are `str | None` because Georef returns null entities outside Argentina. `municipio` is modeled in the client but not exposed (in CABA it repeats the commune).
  - `search_addresses` and `locate` share a private `_get` helper so both map HTTP errors, timeouts, non-JSON and unexpected JSON to `GeorefError` the same way.
  - Source URL is `settings.georef_base_url` (like EPOK), so no new configuration was needed.
- Note: `StarletteDeprecationWarning` (httpx with `starlette.testclient`) comes from the installed FastAPI/Starlette, not from this change.

## Next step

- User decision: push the branch and open the PR with base `feature/epok-integration`.
- Follow-up (needs a product decision): apply the guard inside `/geolocation/address-context/by-coordinates` and `/geolocation/nearby-offices` (and decide the response for points outside CABA), or chain it in the frontend flow.
