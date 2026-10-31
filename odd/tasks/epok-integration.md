# Feature: USIG EPOK integration (nearby municipal offices in CABA)

- **Branch:** `feature/epok-integration` (stacked on `feature/boletin-oficial-integration`)
- **Locator:** `odd/tasks/epok-integration.md` · Engram topic `odd/epok-integration/tasks`

## Objective

Given a point in CABA (latitude/longitude), tell the frontend which City municipal offices (sedes y subsedes comunales) are closest, with address, phone, neighborhood, commune, distance and a link to the commune page, always citing the official source.

## Problem / why

CONCO orients entrepreneurs about procedures, but many City procedures end with in-person attention at a commune office. The user already gets the neighborhood and commune of an address (USIG datos útiles); the next useful step is "where do I go". EPOK is the City's own places service, so it is the official source for those offices.

API choice: delegated by the user on 2026-10-31. Source: USIG EPOK (Gobierno de la Ciudad de Buenos Aires), `https://epok.buenosaires.gob.ar`, no key, CORS `*`. No explicit license; assumed CC BY 2.5 AR like the other City data, and the source is cited.

## Scope

- `src/conco/config.py`: `epok_base_url`, `epok_user_agent`, `epok_timeout_seconds`, `epok_radius_meters`.
- `src/conco/integrations/epok/`: client (`find_nearby`, `get_object`), models, single `EpokError`, category constant `COMMUNE_OFFICES_CATEGORY = "sedes_de_comunas"`.
- `scripts/probes/epok.py`.
- `src/conco/geolocation/`: domain (`NearbyOffice`, `NearbyOfficeFinder`, `NearbyOfficeError`, reuses `Source`), adapter `EpokNearbyOfficeFinder`, endpoint `GET /geolocation/nearby-offices`.
- Real fixtures, unit tests (client, adapter, API) and integration tests (client, API).
- Docs: `back/README.md`.

Out of scope: other EPOK categories (`oficinas_de_empleo`, `centros_integracion_laboral`, `comunas_sstrabajo`, `centros_comerciales`), converting the GKBA centroid to WGS84 coordinates, caching, persistence, frontend.

## Constraints

- Only `integrations/epok/` knows the EPOK URL, parameters, User-Agent quirk and response shape.
- Existing endpoints (`/geolocation/addresses`, `/geolocation/address-context*`, `/guidance/*`) keep their behavior.
- Every response cites the official source (RN-05).
- No new runtime dependencies, no database.
- `back/.env*` is not editable by the implementer: defaults in `config.py` make everything work.
- English identifiers, Spanish docs and messages. No AI attribution in commits.

## Observed API behavior (2026-10-31)

- A BigIP filter drops requests with curl's default User-Agent (`curl/8.5.0` → connection closed without a response, httpx raises `RemoteProtocolError`). httpx's default UA and custom UAs work. The client always sends `User-Agent: CONCO/0.1` (`EPOK_USER_AGENT`).
- `GET /reverseGeocoderLugares/?x=-58.4021372&y=-34.6047137&categorias=sedes_de_comunas&radio=3000` → 200 in ~0.05 s, `Content-Type: text/javascript`, JSON `{"totalFull":7,"instancias":[{"nombre","id","distancia",...}],"total":7}`. `distancia` is a string in meters and the list is not sorted by distance.
- Missing `radio`, missing `x`/`y`, unknown category or nothing in range → 200 `{"totalFull":0,"instancias":[],"total":0}`: "no results", not an error. `radio=10` at the sample point reproduces it.
- `GET /getObjectContent/?id=sedes_de_comunas%7C5` → 200 in ~0.1–0.2 s, `text/javascript`, JSON with `contenido` (list of `nombreId`/`valor`: `nombre`, `direccion` with trailing spaces, `telefonos`, `barrio` in uppercase, `comuna`, `tramites_y_servicios` as an HTML `<a href>`, `observaciones`), `fechaUltimaModificacion`, `direccionNormalizada`, `ubicacion.centroide` (GKBA, not WGS84).
- Unknown or missing id → 200 `{}`.
- Fixtures captured with the client's own parameters and User-Agent.

## Tasks

- [x] T1 · Integration: config, client, models, probe, fixtures, client unit tests, client integration test (route: delegated writer, 2+ non-trivial files)
- [x] T2 · Geolocation: domain, adapter, endpoint, unit and integration tests (route: delegated writer, same)
- [x] T3 · Docs: `back/README.md` and this document (route: delegated writer, same unit of work)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /geolocation/nearby-offices?latitude=-34.6047137&longitude=-58.4021372` → 200 with up to 3 offices sorted by distance and the `source` block.
- Nothing in range → 200 with `offices: []`. EPOK down or unexpected payload → 502. Invalid params (including `limit` outside 1..5) → 422.
- Existing endpoints unchanged.

## Checks

- `uv run pytest -q`
- `uv run pytest -q -m integration`
- `uv run python scripts/probes/epok.py -34.6047137 -58.4021372`

## Progress / evidence

- 2026-10-31 · T1 RED: `uv run pytest -q tests/unit/epok` → `ModuleNotFoundError: No module named 'conco.integrations.epok'` (1 error during collection).
- 2026-10-31 · T1 GREEN: 11 passed. Probe `-34.6047137 -58.4021372` → 7 offices sorted by distance (Sede Comunal 2 at 940.95 m first) and its content. Live client integration: 1 passed.
- 2026-10-31 · T1 commit `32d64a1` feat(back): add USIG EPOK nearby places client (378 lines).
- 2026-10-31 · T2 RED: `uv run pytest -q tests/unit/geolocation` → `ImportError: cannot import name 'NearbyOffice' from 'conco.geolocation.domain'` and `ImportError: cannot import name 'get_nearby_office_finder' from 'conco.geolocation.api'` (2 errors during collection).
- 2026-10-31 · T2 GREEN: full unit suite 184 passed. Live endpoint integration: 1 passed; a point in Moreno (-34.6423652, -58.7567541) → 200 with `offices: []`.
- 2026-10-31 · T2 commit `86e255e` feat(back): expose nearby CABA commune offices endpoint (586 changed lines, about 390 of them tests; above the ~400 planning heuristic, kept as one behavior unit).
- 2026-10-31 · Checks: `uv run pytest -q` → 184 passed, 16 deselected. `uv run pytest -q -m integration` → 16 passed (all live APIs). `uv run python scripts/probes/epok.py -34.6047137 -58.4021372` → 7 offices, closest Sede Comunal 2 (940.95 m).
- 2026-10-31 · T3: README (responsibility, structure, API card with the User-Agent quirk, endpoint section, probe usage) and this document, committed together as `docs(back): document EPOK nearby offices and feature progress`.
- Decisions:
  - Nothing in range is an empty list (200), not 404: "no office nearby" is a valid answer, unlike "address not in CABA".
  - The client sends `User-Agent` from config on every request, so behavior does not depend on httpx's default UA.
  - The client sorts by distance (EPOK does not) and returns `None` for `{}` in `getObjectContent`. Empty or non-JSON bodies, unexpected JSON, HTTP errors, timeouts and dropped connections are `EpokError` → 502.
  - The adapter fetches the content of only the top `limit` places, concurrently with `asyncio.gather`; one failing content request fails the whole call (502) instead of returning a partial list silently.
  - An office whose content is `{}` or has no address (`direccion` nor `direccionNormalizada`) is skipped, so the list can be shorter than `limit`. No extra places are fetched to fill the gap.
  - `neighborhood` and `commune` are `str | None` (not required) because they come from optional content fields; `name` falls back to the reverse-search name.
  - `info_url` is the first `http`/`https` `href` of `tramites_y_servicios`, extracted with stdlib `html.parser`; any other content (no link, `javascript:`) is `None`, so no HTML reaches the client.
  - Texts are kept as published (uppercase neighborhood, `URIBURU JOSE E., Pres. 1022`); formatting is a frontend concern.
  - `limit` defaults to 3, max 5. Radius is `EPOK_RADIUS_METERS` (3000 m). Coordinates are validated only against general bounds, like `/address-context/by-coordinates`.
  - `Source` reused from `geolocation/domain.py`; URL is `settings.epok_base_url`.
- Note: `StarletteDeprecationWarning` (httpx with `starlette.testclient`) comes from the installed FastAPI/Starlette, not from this change.

## Environment variables pending for `back/.env.example`

The implementer cannot edit `back/.env*`. Add:

```bash
# USIG - EPOK, lugares de la Ciudad (Gobierno de la Ciudad de Buenos Aires)
EPOK_BASE_URL=https://epok.buenosaires.gob.ar
EPOK_USER_AGENT=CONCO/0.1
EPOK_TIMEOUT_SECONDS=10
EPOK_RADIUS_METERS=3000
```

## Next step

- User: add the four variables above to `back/.env.example`.
- User decision: push the branch and open the PR with base `feature/boletin-oficial-integration`.
- Later (needs a product decision): chain address → coordinates (Georef or USIG) → nearby offices in the frontend flow; add other EPOK categories (`oficinas_de_empleo`, `centros_integracion_laboral`).
