# Ciudad 3D en el mapa

Objetivo: incorporar el cuadro de usos oficial de Ciudad 3D a la sección de mapa, resolviendo la parcela (SMP) desde el punto de la consulta con USIG Catastro.
Branch: `feat/ciudad-3d-mapa` (desde `main` 452ca24). PR: [#85](https://github.com/guido-pasciucco/InnovaLab-E11/pull/85) contra `main`. Delivery: work-unit commits en la rama; push/PR autorizados por el usuario el 2026-11-26; deploys pendientes. RDD off (global).
Test runners: backend `cd back && uv run pytest`, frontend `cd front && npm test` / `npm run typecheck` / `npm run build`.

## Specs

**S1** — Pedido original del usuario (verbatim): "quiero incorporar el tema de ciudad 3d que es una de las apis que tiene mas datos para que le de mas info a la seccion de mapa"

**S2** — Decisión de producto tomada por el usuario (respuesta a la pregunta de alcance, verbatim): "Cuadro de usos completo". Descripción de la opción elegida (verbatim): "Sumar mixtura de usos y rubros permitidos con condiciones. Es lo más rico en datos, pero exige definir cómo se elige el rubro (RN-01) y revisar RN-04, porque hoy está prohibido decir si una actividad es apta para ese lote.".
Interpretación autorizada: mostrar la tabla oficial completa como dato de referencia navegable (10 categorías, rubros agrupados, condiciones por rubro bajo demanda) con fuente oficial y disclaimer. **No** se agrega traducción automática actividad→rubro (RN-01 queda abierta) y **no** se afirma que la actividad de la persona esté permitida en el lote.

**S3** — Backend (USIG Catastro + Ciudad 3D):
- `GET /territory/use-table?lat=&lng=` resuelve `GET /catastro/parcela/` → SMP, y devuelve `smp`, dirección oficial, `mix_area` (`/cur3d/mixtura_usos/?smp=`), y las 10 categorías (`/cur3d/categorias/`) con sus rubros (`/cur3d/cuadrosdeuso/rubros/?categoria=&mixtura=`). Sin `smp` (parcela fuera de CABA, respuesta `{}`) se devuelve un resultado vacío con limitation, no un 500.
- `GET /territory/rubro-referencias?smp=&categoria=&mixtura=&rubro=` devuelve `permitido_mixtura_de_usos`, `bicicletas`, `estacionamientos`, `cargaydescarga` y `observaciones` de `/cur3d/cuadrosdeuso/referencias/`.
- Todas las rutas de USIG llevan barra final y cabecera `User-Agent` no-curl (`CONCO/0.1` por defecto); sin esa cabecera la conexión se corta.
- Reutilizar `conco.config.settings` (base URL + timeout nuevos), el patrón de cliente httpx con alias Pydantic de `conco.integrations.georef`, el adaptador dominio de `conco.geolocation.infrastructure`, `ConcoError` de `conco.errors`, y el registro de router de `conco.main`. Un error aguas arriba se traduce al cuerpo de error estándar con código propio.
- Verificado con llamadas reales el 2026-11-26: `lng=-58.4055&lat=-34.6040` → SMP `013-099-018`; mixtura `4`; rubros `categoria=1&mixtura=4`; referencias `rubro=102`. No hay endpoint bulk para las 401 referencias.

**S4** — Front (sección de mapa):
- `MapPanel` muestra un panel con la parcela (SMP + dirección oficial), el área de mixtura, las 10 categorías desplegables con sus rubros, y las condiciones del rubro seleccionado.
- El panel cita la fuente oficial (USIG / Ciudad 3D, Gobierno de la Ciudad) e indica explícitamente que es información de referencia, no una confirmación catastral ni un dictamen sobre si la actividad está permitida (RN-04, `docs/REGLAS_DE_NEGOCIO.md`).
- Si no hay punto o la parcela no se resuelve, mostrar un estado claro; el mapa y las capas ilustrativas existentes siguen funcionando igual.
- Reutilizar `front/src/api/client.ts` (`request`, `ApiError`, flag mock), los tipos de `front/src/types.ts`, y el patrón de fetch con `AbortSignal`.

**S5** — Tests (RED → GREEN → REFACTOR):
- Backend: fixtures reales en `back/tests/fixtures/usig/`, tests unitarios con `respx` en `back/tests/unit/usig/`, cubriendo successful chain, `User-Agent` enviado, barras finales, parcela vacía `{}`, SMP inválido con `{"error":...}` y timeout/error de red.
- Front: tests colocated para el transform de categorías/rubros y para los clientes del API, con el patrón existente de `front/src/api/client.test.ts`.
- Chequeo diferencial: ejecutar los comandos compartidos (`/geolocation/addresses`, `POST /consultations`, render de `MapPanel` sin punto) contra la base y contra el cambio; sin diferencias no pedidas.

**S6** — Docs: actualizar el estado de `docs/apis/pendientes/ciudad-3d.md` y `docs/apis/pendientes/usig-catastro.md` (de candidata a integrada, con los nuevos endpoints) y `docs/apis/README.md`. No se modifica RN-04: el panel se presenta como orientación general con fuente, no como determinación legal.

**S7** — Risk: la integración agrega dos clientes HTTP externos y un endpoint público nuevo. No cambia datos persistidos ni contratos existentes; agrega rutas y un panel. Requiere verificación focused de los clientes y del render con/sin punto.

**S8** — Caché: `usig_cache_ttl_seconds` (300 por defecto) y `usig_cache_max_entries` (256) en `Settings`. Caché TTL/LRU en el cliente USIG para respuestas GET exitosas, con clave `(path, params ordenados)`; errores nunca se cachean. `use-table` pasa de 13 llamadas por consulta repetida a 0 en caliente. Tests: hit, expiración por TTL, evicción por tamaño, errores no cacheados y aislamiento entre tests.

**S9** — Ubicación aproximada visible: el SMP se muestra como **estimado** y la respuesta incluye una limitación explícita de RN-03 ("la ubicación es aproximada; puede corresponder a la parcela vecina"). Aplica a `use-table` y a `rubro-referencias`. El front muestra las limitaciones cerca de los datos de parcela, no solo en las condiciones del rubro.

**S10** — Filtro de rubros: buscador `type="search"` en el panel que filtra rubros por nombre dentro de cada categoría, normalizando acentos y mayúsculas (reutilizar el criterio de `front/src/history/searchHistory.ts`), con estado vacío claro y accesible.

**S11** — Mixtura verificada server-side: `/territory/rubro-referencias` sigue aceptando `mixtura` por compatibilidad de contrato, pero el adaptador **deriva la mixtura desde el SMP** con `get_mix_area(smp)` y usa ese valor aguas arriba. Test: enviar `mixtura` incorrecta y verificar que USIG recibe la derivada.

**S12** — Geometría real de la parcela (verificada en vivo 2026-11-26): `GET /catastro/geometria/?smp=013-099-018` → HTTP 200, `FeatureCollection` con `geometry.type == "MultiPolygon"`. Nuevo `GET /territory/parcel-geometry?smp=` → `{"geometry": <GeoJSON geometry>|null, "source": ..., "limitations": [...]}`. El front dibuja esa geometría con `GeoJSON` dentro del `MapContainer`, desactiva la capa demo "Parcela" cuando hay geometría real y reetiqueta la capa de zonificación ilustrativa. Si no hay geometría, mantiene el comportamiento actual.

**S13** — Entrega: push a `origin` y PR #85 contra `main` autorizados y ejecutados. Deploys de Render/Vercel pendientes de autorización.

**S14** — Bug reportado con screenshot: con dirección "JUANA DE IBARBOUROU 123, Comuna 6" el panel queda vacío y el mapa sigue mostrando capas ilustrativas ("Distrito comercial", "Parcela y catastro", etc.) que parecen datos reales. Diagnosticado: el punto de Georef devuelve `{}` en `/catastro/parcela/`, y USIG `normalizar` responde `Calle inexistente: JUANA DE IBARBOUROU 123` (aunque Georef conoce la calle). Verificado en vivo que `https://datosabiertos-catastro-apis.buenosaires.gob.ar/catastro/parcela/?codigo_calle=3174&altura=2801&geocodificar=true&srid=4326` resuelve SMP `013-099-018` para `CORRIENTES 2801`. Fix: (a) `GET /territory/use-table` acepta `address` opcional y, si el punto no da SMP, intenta `normalizar` → `cod_calle` + `altura` → parcela; (b) sin parcela real, el front oculta las capas ilustrativas y su leyenda, dejando marcador y estado vacío. Para la dirección reportada el resultado sigue vacío, pero deja de mostrar datos falsos; para direcciones que USIG conoce, aparece el cuadro real.

## Tasks

- **T1** — S3 backend (clientes USIG + dominio + router + tests) — delegado (unidad paralela) — ✅ commits `989bc8a` + fix `b25768b` — RED 3 collection errors → GREEN 32 tests nuevos; suite completa 203 passed / 13 deselected; integración 7 passed. El fix agregó 2 tests de cableado real (los fakes inyectados tapaban un `AttributeError` en producción).
- **T2** — S4 front (tipos + clientes + panel + tests) — delegado (unidad paralela) — ✅ commit `55fc9f6` — RED módulo ausente + 5 tests fallidos → GREEN 93 tests; typecheck y build OK.
- **T3** — S5/S6 verificación diferencial + docs + cierre — inline — ✅ verificado; commit de docs en este slice.
- **T4** — S8, S9 (back), S11, S12 (back) — caché + limitación de ubicación aproximada + mixtura derivada + endpoint de geometría — delegado (unidad paralela) — ✅ commit `00c4d14` — RED→GREEN en las 4 reglas; 51 tests de `usig`; suite 220 passed / 13 deselected; integración 7 passed; differential base-vs-change idéntico.
- **T5** — S9 (front), S10, S12 (front) — etiqueta "estimado" + filtro de rubros + dibujo de geometría real — delegado (unidad paralela) — ✅ commit `6050250` — RED 13 tests → GREEN 106 tests; typecheck y build OK; comportamiento sin geometría preservado por tests existentes.
- **T6** — S13 verificación final + docs + pregunta de entrega — inline — ✅ verificación local; push + PR #85 autorizados y ejecutados; deploys pendientes.
- **T7** — S14 backend: fallback por dirección (normalizar → código de calle + altura) en `/territory/use-table` — delegado (unidad paralela) — ✅ commit `c20920c` — RED 17 tests → GREEN 68 en `usig`; suite 237 passed / 13 deselected; integración 7 passed; prueba real-DI en vivo con `CORRIENTES 2801` → SMP `013-099-018`.
- **T8** — S14 front: enviar `address` y ocultar capas ilustrativas cuando no hay parcela real — delegado (unidad paralela) — ✅ commit `fc67450` — RED 5 tests → GREEN 113 tests; typecheck y build OK; differential de render sin punto y URL sin `address` byte-idéntico.

## Log

**L1** (2026-11-26): "quiero incorporar el tema de ciudad 3d que es una de las apis que tiene mas datos para que le de mas info a la seccion de mapa"

**L2** (2026-11-26): Decisión de producto del usuario: "Cuadro de usos completo". Se elige mostrar el cuadro oficial completo navegable, sin traducción actividad→rubro y sin afirmar que la actividad esté permitida en el lote, para no convertir la orientación en determinación legal (RN-04).

**L3** (2026-11-26): Verificación en vivo con `curl -A 'CONCO/0.1'`: Catastro devuelve SMP `013-099-018` para `lng=-58.4055&lat=-34.6040`; `mixtura_usos` → `{"usos":[4,0,0]}`; `cuadrosdeuso/rubros?categoria=1&mixtura=4` → 63 rubros; `referencias?...&rubro=102` → permisos y condiciones. Sin endpoint bulk: 10 categorías, 401 rubros, condiciones bajo demanda.

**L4** (2026-11-26): El explorador reportó "RN-39"; el documento real es RN-04 (`docs/REGLAS_DE_NEGOCIO.md`: CONCO no determina si una actividad está permitida ni confirma zonificación/catastro). Corregido en el análisis. `docs/MVP_SCOPE.md` excluye confirmación automática de zonificación/catastro; el panel se enmarca como referencia con fuente, no confirmación.

**L5** (2026-11-26): RDD desactivado por decisión global (`gentle-ai review mode status`: off). Sin ceremonia de review nativa.

**L6** (2026-11-26): Route declaration — T1 y T2 se delegan en paralelo por Writer trigger (dos unidades de comportamiento independientes, superficies `back/**` y `front/**`, cada una con varios archivos y tests, >100 líneas). T3 inline. El contrato de la API entre ambas unidades queda fijado en S3/S4.

**L7** (2026-11-26): Verificación final observada — `cd back && uv run pytest`: 201 passed, 13 deselected (1 warning preexistente de Starlette); `cd back && uv run pytest -m integration`: 7 passed; `cd front && npm test`: 93 passed; `cd front && npm run typecheck`: OK; `cd front && npm run build`: OK. Spot check del padre: 32 tests de `tests/unit/usig` y 93 tests de front re-corrent OK. Chequeo diferencial de `GET /geolocation/addresses` contra una copia de HEAD: respuestas byte-idénticas. `gentle-ai review assess` informó `high/unassessable` por archivos sin trackear; clasificación no utilizable, sin ítem de alto riesgo nombrado y RDD off, así que no se inició review nativo.

**L8** (2026-11-26): Correcciones aceptadas durante la implementación: `/cuadrosdeuso/rubros/` devuelve `{"rubros": [...]}` (no una lista) y un SMP inválido responde `200` con cuerpo vacío/`usos: null`; ambos casos quedaron pinados con tests. Scratch `/tmp/opencode/territory-diff.jmAQtD` creado fuera del worktree y eliminado por el padre.

**L9** (2026-11-26): Bug reportado por el usuario al seguir el flujo: `GET /territory/use-table` respondía `500` con `AttributeError: 'UsigTerritoryService' object has no attribute 'resolve'`. Reproducido en el servidor local con curl. Causa: los puertos y los fakes de los tests usaban `resolve()`, pero el adaptador real exponía `resolve_use_table()` / `resolve_references()`; los tests inyectaban fakes y nunca ejercitaban la DI real. Fix `b25768b`: dos adaptadores delgados (`UsigUseTableResolver`, `UsigRubroReferencesResolver`) exponen `resolve()` y delegan en el servicio compartido. Se agregaron dos tests sin `dependency_overrides` que pasan por la DI real con respx. Verificado: 203 tests backend, y en vivo `/territory/use-table` → 200 con SMP `013-099-018`, mix `4`, 10 categorías; `/territory/rubro-referencias` → 200 con `permitido_mixtura_de_usos`. Lección: un puerto con fakes no prueba el cableado de la inyección de dependencias.

**L10** (2026-11-26): "podrias resolver todos" — el usuario pide implementar las 6 mejoras propuestas. Se reabre el feature con S8–S13 y T4–T6. La entrega remota (S13) queda condicionada a autorización explícita de destino, operación y credencial.

**L11** (2026-11-26): Geometría verificada en vivo con `curl -A 'CONCO/0.1'`: `GET /catastro/geometria/?smp=013-099-018` → HTTP 200, `FeatureCollection` con `geometry.type: "MultiPolygon"` (5322 bytes). Cambia el plan original: se dibuja la parcela real y se desactiva la capa demo de parcela.

**L12** (2026-11-26): Route declaration — T4 y T5 se delegan en paralelo por Writer trigger (dos unidades independientes, superficies `back/**` y `front/**`, cada una con varios archivos y tests). T6 inline. Contrato nuevo fijado en S8–S12, en especial `GET /territory/parcel-geometry?smp=` → `{"geometry": <GeoJSON geometry>|null, "source": ..., "limitations": [...]}`.

**L13** (2026-11-26): Verificación final de las 5 mejoras de código — backend 220 passed / 13 deselected, integración 7 passed; front 106 tests, typecheck y build OK. Spot check del padre re-corriendo suites: mismos números. Differential base-vs-change de clientes USIG intactos: byte-idéntico. El endpoint de geometría se validó con DI real + respx (`MultiPolygon`), no contra un servidor local porque el usuario lo había detenido. Scratch `/tmp/opencode/usig-diff.5WPRck` creado fuera del worktree y eliminado por el padre.

**L14** (2026-11-26): S13 (push, PR, deploy Render, deploy Vercel) NO se ejecuta: el usuario todavía no autorizó destino, operación y credencial/sesión. Se pregunta al finalizar.

**L15** (2026-11-26): El usuario autorizó "Push + PR a origin" (opción elegida explícitamente, sin deploys). Se pusheó `feat/ciudad-3d-mapa` a `origin` y se abrió el PR [#85](https://github.com/guido-pasciucco/InnovaLab-E11/pull/85) contra `main`, con descripción derivada del ODD document. Los deploys de Render y Vercel siguen sin autorizar. No se configuró `pr-description` en el repo; no había referencias `#NNN` que resolver, así que no hizo falta configurar namespaces.

**L16** (2026-11-26): Reporte del usuario: "de momento creo que solo veo losdatos mockeados y creo que por alguna razon no se usan los datos de ciudad 3d". Con screenshot del estado vacío junto a capas ilustrativas. Verificado: no es modo mock (el texto del mock sería "Modo demostración: …"); es una respuesta real del backend. `GET /catastro/parcela/` devuelve `{}` para el punto informado y USIG `normalizar` devuelve `Calle inexistente` para esa dirección. El visor oficial usa además `datosabiertos-catastro-apis.buenosaires.gob.ar/catastro/parcela/?codigo_calle=&altura=`, verificado con CORRIENTES 2801 → SMP `013-099-018`. Se reabre el feature con S14/T7/T8.

**L17** (2026-11-26): Route declaration — T7 y T8 se delegan en paralelo por Writer trigger (superficies `back/**` y `front/**`, cada una con código, tests y docs de su lado). El contrato nuevo es `GET /territory/use-table?lat=&lng=&address=<opcional>` y el callback del front `onParcelResolved(hasParcel)` para ocultar capas ilustrativas sin parcela real.

**L18** (2026-11-26): Verificación del fix S14 — backend 237 passed / 13 deselected, integración 7 passed, front 113 tests + typecheck + build OK. El fallback se probó por DI real contra USIG: punto que falla + `address=CORRIENTES 2801` → SMP `013-099-018`, mix `4`, 10 categorías y limitación de resolución por dirección. Para la dirección reportada (`JUANA DE IBARBOUROU 123`) USIG responde "calle inexistente", así que el estado vacío es correcto, pero el mapa ya no muestra capas ilustrativas. Scratch `/tmp/opencode/usig-t7-diff.DR57ys`, `/tmp/opencode/usig-t7-diff.jI6pMh` e `/tmp/opencode/innovalab-t8-diff.hTIJJp` eliminados por el padre.
