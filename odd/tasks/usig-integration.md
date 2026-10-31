# Feature: USIG integration (address context in CABA)

- **Branch:** `feature/usig-integration` (stacked on `feature/caba-tramites-integration`)
- **Locator:** `odd/tasks/usig-integration.md` · Engram topic `odd/usig-integration/tasks`

## Objective

Given a CABA address (street + number) or a point (latitude/longitude), tell the frontend its neighborhood (barrio), commune (comuna) and postal codes, always citing the official source.

## Problem / why

CONCO geocodes addresses with Georef, but Georef only returns the commune as "departamento" and nothing about the neighborhood or postal code. Neighborhood and commune are the context an entrepreneur recognizes and the one many City procedures ask for. RN-02 limits CONCO to CABA, and USIG is the City's own geographic service, so it also confirms whether a location is inside CABA.

API choice: delegated by the user on 2026-10-31. Source: USIG (Unidad de Sistemas de Información Geográfica, Gobierno de la Ciudad de Buenos Aires), service `datos_utiles`, no key, CORS `*`, content license Creative Commons Reconocimiento 2.5 Argentina (stated in the footer of `http://usig.buenosaires.gob.ar/apis/`).

## Scope

- `src/conco/config.py`: `usig_base_url`, `usig_docs_url`, `usig_timeout_seconds`.
- `src/conco/integrations/usig/`: client (`get_datos_utiles_by_address`, `get_datos_utiles_by_coordinates`), model `UsigDatosUtiles`, single `UsigError`.
- `scripts/probes/usig.py`.
- `src/conco/geolocation/`: domain (`AddressContext`, `Source`, `AddressContextProvider`, `AddressContextError`), adapter `UsigAddressContextProvider`, endpoints `GET /geolocation/address-context` and `GET /geolocation/address-context/by-coordinates`.
- Real fixtures, unit tests (client, adapter, API) and integration tests (client, API).
- Docs: `back/README.md`.

Out of scope: cadastre and zoning (`seccion_catastral`, `codigo_de_planeamiento_urbano`, RN-04), the other `datos_utiles` fields (police station, hospital area, school district), the USIG address normalizer, caching, persistence, frontend.

## Constraints

- Only `integrations/usig/` knows the USIG URL, parameters and response quirks.
- `GET /geolocation/addresses` and the `guidance/` feature keep their behavior.
- Every response cites the official source (RN-05). No cadastre or zoning data is modeled or exposed (RN-04).
- No new runtime dependencies, no database.
- `back/.env*` is not editable by the implementer: defaults in `config.py` make everything work.
- English identifiers, Spanish docs and messages. No AI attribution in commits.

## Observed API behavior (2026-10-31)

- `GET https://ws.usig.buenosaires.gob.ar/datos_utiles?calle=Corrientes&altura=2500` → 200 in ~0.5 s, `Content-Type: text/javascript; charset=utf-8`, JSON body with `comuna`, `barrio`, `comisaria`, `area_hospitalaria`, `region_sanitaria`, `distrito_escolar`, `comisaria_vecinal`, `seccion_catastral`, `distrito_economico`, `codigo_de_planeamiento_urbano`, `partido_amba`, `localidad_amba`, `codigo_postal` (`1046`), `codigo_postal_argentino` (`C1046AAP`).
- `?x=-58.401981&y=-34.604792` (x = longitude, y = latitude) → 200, `Content-Type: application/json` (differs from the by-address case), same fields without the two postal-code keys.
- Unknown street, number out of range (`Corrientes 99999`, `Corrientes 0`, `Rivadavia 20000`) → 200 `text/plain` `ERROR: No se pudo normalizar o geocodificar la dirección.`. Street normalization is strict: `Avenida de Mayo 500` also returns this error.
- Missing parameters, `calle` without `altura`, or non-numeric `x`/`y` → 200 `text/html` help page.
- Point outside CABA (`x=-58.7567541&y=-34.6423652`, Moreno) → 200 JSON with every CABA field empty and `partido_amba`/`localidad_amba` filled. A point in the river or swapped lat/lon → 200 JSON with everything empty.
- `https://usig.buenosaires.gob.ar/apis/` fails certificate validation with curl (`unable to get local issuer certificate`); `http://` returns 200. The API host `ws.usig.buenosaires.gob.ar` works over https.
- Fixtures recaptured through the client's own request parameters: all five bodies byte-identical to the stored files.

## Tasks

- [x] T1 · Integration: config, client, model, probe, fixtures, client unit tests, client integration test (route: delegated writer, 2+ non-trivial files)
- [x] T2 · Geolocation: domain, adapter, endpoints, unit and integration tests (route: delegated writer, same)
- [x] T3 · Docs: `back/README.md` and this document (route: delegated writer, same unit of work)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /geolocation/address-context?street=Corrientes&number=2500` → 200 with `Balvanera`, `Comuna 3`, `1046`, `C1046AAP` and the `source` block.
- `GET /geolocation/address-context/by-coordinates?latitude=-34.604792&longitude=-58.401981` → 200 with postal codes in `null`.
- Unknown address or point outside CABA → 404. USIG down or unexpected payload → 502. Invalid params → 422.
- The response never contains cadastre or zoning fields.
- `GET /geolocation/addresses` unchanged.

## Checks

- `uv run pytest -q`
- `uv run pytest -q -m integration`
- `uv run python scripts/probes/usig.py Corrientes 2500`

## Progress / evidence

- 2026-10-31 · T1 RED: `uv run pytest -q tests/unit/usig` → `ModuleNotFoundError: No module named 'conco.integrations.usig'` (1 error during collection).
- 2026-10-31 · T1 GREEN: 10 passed. Probe: `Corrientes 2500` → Comuna 3 / Balvanera / 1046 / C1046AAP; `--coords -34.604792 -58.401981` → postal codes `null`; unknown street → "Dirección no encontrada en CABA.". Live client integration: 2 passed.
- 2026-10-31 · T1 commit `9647746` feat(back): add USIG datos útiles client.
- 2026-10-31 · T2 RED: `uv run pytest -q tests/unit/geolocation` → `ImportError: cannot import name 'get_address_context_provider' from 'conco.geolocation.api'` and `ImportError: cannot import name 'AddressContext' from 'conco.geolocation.domain'` (2 errors during collection).
- 2026-10-31 · T2 GREEN: full unit suite 109 passed. Live endpoint integration: 2 passed.
- 2026-10-31 · T2 commit `fadbb26` feat(back): expose CABA address context endpoints (558 changed lines, about 370 of them tests; above the ~400 planning heuristic, kept as one behavior unit).
- 2026-10-31 · Checks: `uv run pytest -q` → 109 passed, 10 deselected. `uv run pytest -q -m integration` → 10 passed (Georef, CABA trámites, USIG, live). `uv run python scripts/probes/usig.py Corrientes 2500` → Comuna 3 / Balvanera / 1046 / C1046AAP.
- 2026-10-31 · T3: README (responsibility, structure, API card with limitations, endpoint section, probe usage) and this document, committed together as `docs(back): document USIG address context and feature progress`.
- Decisions:
  - Not found is `None` in both layers (client and port), mapped to 404 by the router, like `caba_tramites`. The `ERROR:` text and an empty `comuna` or `barrio` are both "not found"; the HTML help page, any non-JSON body and HTTP errors are `UsigError` → 502.
  - The body is parsed regardless of `Content-Type` because USIG declares JSON as `text/javascript`.
  - The model only declares `comuna`, `barrio`, `codigo_postal`, `codigo_postal_argentino`; cadastre and zoning fields are ignored at parse time and never reach the domain (tested).
  - `Source` is defined again in `geolocation/domain.py` with the same shape as in `guidance/domain.py`, instead of importing across features or moving it to a shared module. Each feature stays independent; a shared kernel can be extracted when a third feature needs it.
  - The source URL is `http://usig.buenosaires.gob.ar/apis/` (https fails certificate validation) and lives in `config.py` as `usig_docs_url`, following the "no hardcoded URLs" convention.
  - Coordinates are validated only against general bounds (latitude -90..90, longitude -180..180). A CABA bounding box would duplicate geography USIG already knows and could clip border addresses; outside CABA returns 404.
  - Empty postal codes are mapped to `None` in the adapter.
- Note: `StarletteDeprecationWarning` (httpx with `starlette.testclient`) comes from the installed FastAPI/Starlette, not from this change.

## Environment variables pending for `back/.env.example`

The implementer cannot edit `back/.env*`. Add:

```bash
# USIG - datos útiles (Gobierno de la Ciudad de Buenos Aires)
USIG_BASE_URL=https://ws.usig.buenosaires.gob.ar
USIG_DOCS_URL=http://usig.buenosaires.gob.ar/apis/
USIG_TIMEOUT_SECONDS=10
```

## Next step

- User: add the three variables above to `back/.env.example`.
- User decision: push the branch and open the PR with base `feature/caba-tramites-integration`.
- Later (needs a product decision): chain Georef → USIG (coordinates from `/geolocation/addresses` into `/by-coordinates`), or use the USIG normalizer to accept free-text addresses.
