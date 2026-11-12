# Pendientes — Habilitación comercial y catálogo de actividades

> Tareas importantes que quedan por hacer en el módulo de habilitación/catálogo de la app.
> Contexto: ver `docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md` (fuente del relevamiento) y `odd/tasks/activity-semantic-search.md` (estado del módulo).
> Generado: 2026-11-12, a partir del relevamiento y las decisiones de esa sesión.

## Decisiones ya tomadas (contexto)

- La app asigna trámites **según la actividad que la persona quiere realizar** (catálogo curado, no los 868 de la Ciudad completos).
- El set de actividades se **mantiene y se amplía**, no se reduce por solapamiento: sacando entradas la persona que abre exactamente ese rubro recibe «No encontramos una actividad parecida».
- La base se limpia por el **loader** (guardar solo los referenciados), no quitando actividades.
- Set objetivo: **9 actividades** — las 6 actuales + **carnicería, hotel, óptica** (ver sección «Ampliar catálogo curado»).

## Tareas pendientes

### 1. ~~Loader: guardar solo los trámites referenciados~~ ✅ Hecho (2026-11-12)

`load_catalog.py` ahora guarda únicamente los trámites referenciados por `activities.json` (mantiene la validación «todo id curado existe en la lista publicada»). Evidencia: `uv run pytest` → 107 passed, `-m database` → 5 passed; recarga con 870 publicados → **16 referenciados guardados**; base local verificada (16 filas en `procedures`, todas referenciadas). Menciones de «868» actualizadas en `GUIA_PRESENTACION.md`, `back/README.md` y S4/L7 de `odd/tasks/activity-semantic-search.md`.

- Trade-off explícito: si RN-01 aprueba búsqueda semántica **sobre trámites**, habrá que volver a traer el catálogo completo con embeddings. No se pierde información: los trámites se re-descargan con el loader.

### 2. ~~Ampliar catálogo curado (9 actividades)~~ ✅ Hecho (2026-11-12)

Las 3 actividades nuevas se agregaron a `activities.json` con ids verificados contra la API de la Ciudad y recargadas en la base: **870 publicados → 18 referenciados guardados, 9 actividades, 53 alias**. Evidencia: `uv run pytest` → 108 passed (test RED → GREEN `test_repo_catalog_has_the_nine_agreed_activities`), `-m database` → 5 passed. Notas de kiosco y peluquería reforzadas con el doc. Alias cargados: carnicería (carne, venta de carne, frigorífico, carnicería y fiambrería, carnes), hotel (hostel, alojamiento turístico, alojamiento, b&b, pensión, hospedaje), óptica (anteojos, lentes, óptica comercial, lentes de contacto, gafas).

Pendiente de dominio (no bloquea la carga): el alcance exacto de «Prestadores Turísticos» vs la Ley 4.631 para hotel.

**Carnicería** (alimentos reforzado):
- Tronco común ya curado (habilitación económica, transmisión/exprés, Ingresos Brutos, registro de empleadores, rúbrica laboral, visado de anuncio, consulta APH).
- Curso de Manipulación de Alimentos — id `c5e44825-3fc3-4abe-86cf-ec8dfa68f7fc` (lo comparten cafetería/foodtruck).
- Reasignar desde Restaurante: *Inscripción en el Registro de Generadores Especiales de Residuos Sólidos Urbanos para Fracción Húmedos* — id `1304fa97-1f5f-48d7-b867-d30ca2f78689` (candidata natural para carnicería; pendiente confirmación de dominio).
- Los requisitos específicos (proveedores SENASA, cadena de frío, libreta sanitaria) **no son trámites de la Ciudad**: no existen en la API. Van como **notas** del trámite principal, no como filas nuevas.
- Aliases sugeridos: «carnicería», «carne», «venta de carne», «frigorífico», «carnicería y fiambrería».

**Hotel** (sectorial turismo — la mejor candidata: tiene trámites reales publicados):
- Inscripción en el Registro de Prestadores Turísticos — id `e459e8d6-684d-4441-9aaf-a1c19c98453b` (Ente de Turismo, sector `turistico`).
- Solicitud de rúbrica del libro de pasajeros para alojamientos turísticos — id `b8a8c54e-c743-48ce-853d-e5bece3bc904` (cita la Ley 4.631).
- Exclusión del Registro de Generadores … para Locales Gastronómicos y **Hoteleros** — id `266d2abd-ffd7-4407-ba10-2499509c3ea0` (ya curado para cafetería/restaurante; aplica a hoteleros).
- Tronco común. Nota: complementar con lo del doc (Registro de Alojamientos Turísticos, Ley 4.631, autoprotección de mayor grupo) como requerimiento, no como trámite.
- Aliases sugeridos: «hotel», «hostel», «alojamiento turístico», «alojamiento», «b&b», «pensión».

**Óptica** (sanitario):
- La habilitación sanitaria (Min. Salud, Ley 7.314) **no está publicada en la API de trámites** — el trámite más cercano, «Seguridad en establecimientos de salud privados» (id `e3460c1f-7a57-4d44-99b3-2952f7bd08b9`), es un canal de **denuncias** y NO debe presentarse como habilitación (RN-04).
- Tramitar: tronco común + nota explícita: la habilitación sanitaria del Ministerio de Salud (Decreto 41/2014 para farmacia / Ley 7.314 para ópticas) es un organismo distinto, no está en esta API; ver `docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md` § Ópticas.
- Aliases sugeridos: «óptica», «anteojos», «lentes», «óptica comercial».

Reforzar notas de lo ya curado (sin cambiar trámites), tomando del doc:
- **Kiosco**: si solo vende productos envasados alcanza con que estén aprobados por el Código Alimentario; sin curso de manipulación si no hay manipulación/fraccionamiento.
- **Peluquería**: habilitación estándar + condiciones higiénicas (esterilización de instrumental, productos ANMAT).

### 3. ~~Reasignación del CAA (decisión abierta)~~ ✅ Hecho (2026-11-12)

Aplicada la opción (a), tal como recomienda el doc: el **CAA es tronco común en las 9 actividades** (Ley 123: todas las actividades se categorizan SRE/CRE; el trámite rige igual aunque el rubro sea simple — solo pasa a crecer en exigencia cuando el impacto es mayor). Además, *Inscripción en el Registro de Generadores Especiales de Residuos Sólidos Urbanos para Fracción Húmedos* (`1304fa97-1f5f-48d7-b867-d30ca2f78689`) se **movió de Restaurante a Carnicería** (le calza al rubro carne: grandes volúmenes de residuos húmedos). Evidencia: RED → GREEN `test_caa_is_tronco_comun_and_hummedos_lives_in_carniceria`; `uv run pytest` → 109 passed, `-m database` → 5 passed; recarga del loader: 18 referenciados, 9 actividades, 53 alias (los ids ya se contaban). Nota: el CAA va al final del listado de cada actividad (orden de revisión); Restaurante conserva su posición original.

### 4. Revisión de dominio del curado (RN-04)

Todo el archivo `activities.json` es un **borrador pendiente de revisión de dominio** (L6 del doc de tasks). Incluye las 3 actividades nuevas de arriba (especialmente hotel: el alcance exacto de «Prestadores Turísticos» vs la Ley 4.631; y el Registro Único de Instituciones Deportivas para gimnasio, descartado por evidencia — ver abajo).

Gimnasio quedó **descartado de la ampliación**: su único match en la API es «Inscripción en el Registro Único de Instituciones Deportivas» (id `b1bdbd59-59fd-4e43-95cd-74c01ec561ee`, «abierta a todas las instituciones deportivas»), cuyo encuadre para gimnasios comerciales (Ley 139, Registro de Gimnasios de la Ciudad) es dudoso. Si dominio confirma que aplica, se suma como tercera actividad sectorial.

### 5. Extender las variables de contexto (futuro, documentado)

El doc define 6 variables que activan requisitos; la app tiene 6 preguntas pero **no coinciden**:

| Variable del doc | Estado en la app |
|---|---|
| Rubro/actividad | ✅ es la actividad elegida |
| Ubicación (zona/mixtura, Ciudad 3D) | ❌ falta (solo hay `protected_building` para APH) |
| Superficie | ⚠️ solo `under_200_m2`; el doc distingue <200 Exprés / <500 DDRR-A / >500 DDRR C/P |
| Forma jurídica del titular | ❌ falta |
| Personal | ✅ `has_employees` |
| Edificio e instalaciones | ⚠️ solo `protected_building` (falta ascensor/contra incendio → registro de instalaciones) |

`ContextAnswers` rechaza campos desconocidos (`extra="forbid"`), así que ampliar implica: nuevas preguntas en el código + `applies_when` nuevos en el curado + tests. Alcance grande — evaluar en su propio ciclo.

### 6. Requerimientos como segundo checklist (futuro)

El doc propone mostrarle a la persona **dos checklists**: «qué tenés que conseguir antes de empezar» (requerimientos: DNI/CUIT, título sobre el local, plano, habilitaciones edilicias, accesibilidad, tasa) y «qué gestiones tenés que hacer» (trámites). La app hoy solo cubre trámites. El modelo de datos y la fuente (sección «Requerimientos» de `TRAMITES_Y_REQUERIMIENTOS.md`) ya están relevados.

### 7. RN-01 y búsqueda semántica sobre trámites (bloqueada por decisión de producto)

`docs/ideas/busqueda-semantica-tramites.md` está **pendiente de RN-01** («buscador, no IA»). Si RN-01 aprueba aplicar embeddings a trámites: se vectoriza el catálogo completo (otra vez los 868) y esta limpieza (tarea 1) se revierte parcialmente. Relevante antes de decidir.

## Referencias

- `docs/habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md` — relevamiento completo (tronco común, específicos por rubro, requerimientos, 6 variables, patrones).
- `odd/tasks/activity-semantic-search.md` — estado del módulo (S1–S7, L1–L6, RN-04).
- `docs/PROPUESTA_TECBA.md` — alcance MVP (caso piloto: cafetería en Av. Corrientes 2500; §6 future scope = ampliación progresiva).
- `back/src/conco/guidance/` — código del módulo (`activity_directory.py`, `domain.py`, `load_catalog.py`, `data/activities.json`).
