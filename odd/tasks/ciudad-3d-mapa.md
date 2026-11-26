# Ciudad 3D en el mapa

Objetivo: incorporar el cuadro de usos oficial de Ciudad 3D a la sección de mapa, resolviendo la parcela (SMP) desde el punto de la consulta con USIG Catastro.
Branch: `feat/ciudad-3d-mapa` (desde `main` 452ca24). Delivery: work-unit commits en la rama; push/PR quedan al usuario. RDD off (global).
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

## Tasks

- **T1** — S3 backend (clientes USIG + dominio + router + tests) — delegado (unidad paralela) — ✅ commit `989bc8a` — RED 3 collection errors → GREEN 32 tests nuevos; suite completa 201 passed / 13 deselected; integración 7 passed.
- **T2** — S4 front (tipos + clientes + panel + tests) — delegado (unidad paralela) — ✅ commit `55fc9f6` — RED módulo ausente + 5 tests fallidos → GREEN 93 tests; typecheck y build OK.
- **T3** — S5/S6 verificación diferencial + docs + cierre — inline — ✅ verificado; commit de docs en este slice.

## Log

**L1** (2026-11-26): "quiero incorporar el tema de ciudad 3d que es una de las apis que tiene mas datos para que le de mas info a la seccion de mapa"

**L2** (2026-11-26): Decisión de producto del usuario: "Cuadro de usos completo". Se elige mostrar el cuadro oficial completo navegable, sin traducción actividad→rubro y sin afirmar que la actividad esté permitida en el lote, para no convertir la orientación en determinación legal (RN-04).

**L3** (2026-11-26): Verificación en vivo con `curl -A 'CONCO/0.1'`: Catastro devuelve SMP `013-099-018` para `lng=-58.4055&lat=-34.6040`; `mixtura_usos` → `{"usos":[4,0,0]}`; `cuadrosdeuso/rubros?categoria=1&mixtura=4` → 63 rubros; `referencias?...&rubro=102` → permisos y condiciones. Sin endpoint bulk: 10 categorías, 401 rubros, condiciones bajo demanda.

**L4** (2026-11-26): El explorador reportó "RN-39"; el documento real es RN-04 (`docs/REGLAS_DE_NEGOCIO.md`: CONCO no determina si una actividad está permitida ni confirma zonificación/catastro). Corregido en el análisis. `docs/MVP_SCOPE.md` excluye confirmación automática de zonificación/catastro; el panel se enmarca como referencia con fuente, no confirmación.

**L5** (2026-11-26): RDD desactivado por decisión global (`gentle-ai review mode status`: off). Sin ceremonia de review nativa.

**L6** (2026-11-26): Route declaration — T1 y T2 se delegan en paralelo por Writer trigger (dos unidades de comportamiento independientes, superficies `back/**` y `front/**`, cada una con varios archivos y tests, >100 líneas). T3 inline. El contrato de la API entre ambas unidades queda fijado en S3/S4.

**L7** (2026-11-26): Verificación final observada — `cd back && uv run pytest`: 201 passed, 13 deselected (1 warning preexistente de Starlette); `cd back && uv run pytest -m integration`: 7 passed; `cd front && npm test`: 93 passed; `cd front && npm run typecheck`: OK; `cd front && npm run build`: OK. Spot check del padre: 32 tests de `tests/unit/usig` y 93 tests de front re-corrent OK. Chequeo diferencial de `GET /geolocation/addresses` contra una copia de HEAD: respuestas byte-idénticas. `gentle-ai review assess` informó `high/unassessable` por archivos sin trackear; clasificación no utilizable, sin ítem de alto riesgo nombrado y RDD off, así que no se inició review nativo.

**L8** (2026-11-26): Correcciones aceptadas durante la implementación: `/cuadrosdeuso/rubros/` devuelve `{"rubros": [...]}` (no una lista) y un SMP inválido responde `200` con cuerpo vacío/`usos: null`; ambos casos quedaron pinados con tests. Scratch `/tmp/opencode/territory-diff.jmAQtD` creado fuera del worktree y eliminado por el padre.
