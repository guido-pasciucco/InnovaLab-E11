# Feature: Boletín Oficial integration (CABA laws and decrees)

- **Branch:** `feature/boletin-oficial-integration` (stacked on `feature/usig-integration`)
- **Locator:** `odd/tasks/boletin-oficial-integration.md` · Engram topic `odd/boletin-oficial-integration/tasks`

## Objective

Given a norm type (law or decree), number and year, show the frontend the official City of Buenos Aires norm: summary, issuing body, publication date, bulletin edition and PDF link, always citing the official source.

## Problem / why

Procedures returned by `/guidance/procedures` rest on City laws and decrees (for example, Ley 6101 regulates economic activities and Decreto 40/2019 implements it). CONCO had no way to show that legal basis from an official source. The Boletín Oficial is where every City norm is published, so it is the authoritative reference (RN-05). The norm is shown as a reference only, never as a legal determination (RN-04).

API choice: delegated by the user on 2026-10-31. Source: Boletín Oficial de la Ciudad de Buenos Aires REST API (`https://api-restboletinoficial.buenosaires.gob.ar`, docs at `/api/doc/`), no key. No explicit license; norms are public official acts, cited as "Boletín Oficial de la Ciudad de Buenos Aires" with `https://boletinoficial.buenosaires.gob.ar`.

Free-text search (`palabras`) was discarded on purpose: it is exact-phrase and returns weak results.

## Scope

- `src/conco/config.py`: `boletin_oficial_base_url`, `boletin_oficial_site_url`, `boletin_oficial_timeout_seconds`.
- `src/conco/integrations/boletin_oficial/`: client `find_norms(norm_type, number, year)`, `BoletinOficialNormType` (Ley, Decreto), models, single `BoletinOficialError`.
- `scripts/probes/boletin_oficial.py`.
- `src/conco/guidance/`: domain (`RegulationType`, `Regulation`, `RegulationRegistry`, `RegulationLookupError`), adapter `BoletinOficialRegulationRegistry`, endpoint `GET /guidance/regulations/{regulation_type}/{number}/{year}`.
- Real fixtures, unit tests (client, adapter, API) and integration tests (client, API).
- Docs: `back/README.md`.

Out of scope: resolutions, dispositions and other norm types; free-text search; bulletin editions (`/obtenerUltimoBoletin`-style data); annexes (`link_anexo`); linking procedures to their norms automatically; caching; persistence; frontend.

## Constraints

- Only `integrations/boletin_oficial/` knows the Boletín URL, path-embedded filters and response quirks.
- `/guidance/procedures*` and `/geolocation/*` keep their behavior.
- Every response cites the official source (RN-05). The norm is a reference, not a legal determination (RN-04).
- No new runtime dependencies, no database.
- `back/.env*` is not editable by the implementer: defaults in `config.py` make everything work.
- English identifiers, Spanish docs and messages. No AI attribution in commits.

## Observed API behavior (2026-10-31)

- `GET /obtenerResultado/tipoNorma=1&nNorma=6101&anio=2018` → 200 `application/json`, one norm (Ley 6101). Filters go inside the path; httpx sends `=` and `&` unencoded (`raw_path` checked) and the live API accepts it.
- Type ids from `GET /obtenerFiltrosDeBusqueda`: 1 Ley, 2 Decreto, 3 Resolución, 4 Disposición (plus others such as Fe de erratas, Acta).
- `anio` must have four digits (`anio=18` → 0 results) while the response returns two (`"anio_norma": 18`).
- Not found → 200 `{"normas": 0, ...}` (a number). Invalid filter (`/obtenerResultado/foo=1`) → 200 `text/html` `No hay criterio de búsqueda válido seleccionado`. A non-numeric `nNorma` returns `normas: 0`, not the HTML.
- Without `anio`, Decreto 40 returns 17 norms of different years.
- **Same type, number and year can be several norms:** Decreto 40/2022 → two (Área Jefe de Gobierno and Legislatura); Decreto 40/2010 → two. Decreto 40/2025 returns the same norm (id 868869) twice.
- Resolución 100/2019 → 41 norms from different bodies (resolutions are numbered per body) → not supported.
- Old norms: `nombre_reparticion` is `null` and the document link is `""` (Decreto 40/2010).
- `boletines` and `link_documento_normas` had exactly one element in all 365 norms checked (every Decreto of 2019 and Ley of 2018).
- Download links come as `http://.../download/N`; the `https://` version answers 302 and ends in the PDF (`application/pdf`).
- `GET /getUrlDocument/...` returns an empty body → not used.
- Latency 0.16–0.38 s.

## Tasks

- [x] T1 · Integration: config, client, models, probe, fixtures, client unit and integration tests (route: delegated writer, 2+ non-trivial files)
- [x] T2 · Guidance: domain, adapter, endpoint, unit and integration tests (route: delegated writer, same)
- [x] T3 · Docs: `back/README.md` and this document (route: delegated writer, same unit of work)

## Acceptance criteria

- `uv run pytest` passes offline.
- `GET /guidance/regulations/ley/6101/2018` → 200 with summary, Legislatura, `2018-12-27`, bulletin 5526, `https://` document URL and the `source` block.
- `GET /guidance/regulations/decreto/40/2022` → 200 with two norms.
- Unknown norm → 404. Boletín down, HTML or unexpected payload → 502. Invalid type, number < 1 or year outside 1900–2100 → 422.
- Existing endpoints unchanged.

## Checks

- `uv run pytest -q`
- `uv run pytest -q -m integration`
- `uv run python scripts/probes/boletin_oficial.py ley 6101 2018`

## Progress / evidence

- 2026-10-31 · T1 RED: `uv run pytest -q tests/unit/boletin_oficial` → `ModuleNotFoundError: No module named 'conco.integrations.boletin_oficial'` (1 error during collection).
- 2026-10-31 · T1 GREEN: 15 passed. Live client integration: 2 passed. Probe `ley 6101 2018` → id 435567 with https links; `ley 6101 2019` → "Norma no encontrada.".
- 2026-10-31 · T1 commit `e8ee97c` feat(back): add Boletín Oficial CABA norms client (447 lines, about 200 of them tests and 8 one-line fixtures).
- 2026-10-31 · T2 RED: `uv run pytest -q tests/unit/guidance` → `ImportError: cannot import name 'Regulation' from 'conco.guidance.domain'` and `ImportError: cannot import name 'get_regulation_registry' from 'conco.guidance.api'` (2 errors during collection).
- 2026-10-31 · T2 GREEN: full unit suite 143 passed. Live endpoint integration: 2 passed.
- 2026-10-31 · T2 commit `c84b574` feat(back): expose CABA regulation lookup endpoint (460 changed lines, about 300 of them tests; above the ~400 planning heuristic, kept as one behavior unit). It also carries a line-wrap of one `client.py` statement from T1.
- 2026-10-31 · Checks: `uv run pytest -q` → 143 passed, 14 deselected. `uv run pytest -q -m integration` → 14 passed (all APIs, live). Probe `ley 6101 2018` → Ley 6101, Legislatura, 2018-12-27.
- 2026-10-31 · T3: README (responsibility, structure, API card with limitations, endpoint section, probe usage) and this document, committed together.
- Decisions:
  - **The endpoint returns a list (`regulations`), not a single `regulation`.** Observed: one type + number + year can be two different decrees (Executive and Legislature). Returning only the first would silently pick one norm and mislead (RN-05). Empty list → 404.
  - Only laws and decrees are supported: resolutions and dispositions are numbered per issuing body, so number + year is ambiguous by design.
  - The client always sends type, number and four-digit year, then filters the response again by type name, number and year (two or four digits) and drops repeated ids.
  - Download URLs are rewritten to `https://` in the integration models; an empty document link becomes `None`. `issuing_body` and `document_url` are nullable because both were observed empty.
  - `boletines` and `link_documento_normas` require at least one element (365/365 observed); the adapter uses the first. A norm without them would fail validation (502) instead of producing a citation without a date.
  - The domain `year` is the requested four-digit year, since the API only returns two digits.
  - `Source` is reused from `guidance/domain.py` (same feature).
- Note: `StarletteDeprecationWarning` (httpx with `starlette.testclient`) comes from the installed FastAPI/Starlette, not from this change.

## Environment variables pending for `back/.env.example`

The implementer cannot edit `back/.env*`. Add:

```bash
# Boletín Oficial de la Ciudad de Buenos Aires
BOLETIN_OFICIAL_BASE_URL=https://api-restboletinoficial.buenosaires.gob.ar
BOLETIN_OFICIAL_SITE_URL=https://boletinoficial.buenosaires.gob.ar
BOLETIN_OFICIAL_TIMEOUT_SECONDS=10
```

## Next step

- User: add the three variables above to `back/.env.example`.
- User decision: accept the list response shape (`regulations`) instead of a single `regulation`.
- User decision: push the branch and open the PR with base `feature/usig-integration`.
- Later (needs a product decision): link each procedure to the norms it cites, and decide whether resolutions are worth supporting with an issuing-body filter.
