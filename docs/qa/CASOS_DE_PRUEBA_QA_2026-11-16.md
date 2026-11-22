# Casos de prueba QA (16/11/2026) — evaluación y backlog de implementación

> **Origen:** `38 casos de pruebas 16_11_26.xlsx` (Descargas/calculadora/licitaciones).
> **Sitio:** https://conco-omega.vercel.app · **API:** https://conco-api.onrender.com
> **Propósito de este documento:** volcar los hallazgos de QA a un formato revisable, evaluarlos y servir de backlog del PR donde se implementarán. La corrida original fue de **solo requests HTTP** (GET/OPTIONS): no hubo interacción real con navegador, por lo que casi todas las sugerencias apuntan a validación de UI, contrato y observabilidad.
> **Estado:** pendiente de implementación. Este PR contiene el documento; la implementación se hace aquí mismo, ítem por ítem.

## 1. Resumen ejecutivo

| Indicador | Resultado |
|---|---|
| Casos ejecutados | 38 |
| Aprobados | 37 |
| Fallidos | 0 |
| Bloqueados | 0 |
| Observaciones | 1 (`RUN-034`: detalle de trámite respondió 404 y luego 200) |

**Alcance (verbatim del Excel):** "1 observación en esta corrida: el detalle de un trámite respondió primero 404 y luego 200 al reintentar. En una verificación previa del 15/11, la búsqueda de actividades tardó 23,304 s la primera vez y 1,259 s al repetirla; causa no confirmada."

**Conclusión (verbatim):** "37 casos aprobados y 1 observación de consistencia temporal en la consulta de detalle. Revisar también la relevancia del orden de trámites y medir la latencia inicial de actividades."

**Limitación (verbatim):** "Los flujos UI, responsive, teclado/lector de pantalla, marcadores visuales y envío real de consulta quedan pendientes de navegador."

> Nota sobre el formato: `23,304 s` / `1,259 s` usa coma decimal en español, es decir ~23,3 s y ~1,26 s. Confirmar con QA antes de fijar un SLO.

## 2. Evaluación priorizada

La columna "Sugerencia" del Excel se agrupó en líneas de trabajo. **P0** = bloquea confianza o rendimiento percibido; **P1** = experiencia/validación del usuario; **P2** = robustez y seguimiento. Las decisiones de producto están marcadas explícitamente y **no** se asumen resueltas.

### QA-01 · P0 · Inconsistencia temporal en detalle de trámite (INC-01)
- **Evidencia:** `RUN-034`. Primer `GET /guidance/procedures/{uuid}` → HTTP 404; repetido con el mismo UUID → HTTP 200 con "Alta de habilitación de remises" y fuente oficial. Causa no confirmada.
- **Evaluación:** es la única desviación funcional de la corrida y afecta directamente la confianza en el catálogo. Puede ser cold start, recarga del loader, replicación de BD o caché; hoy no hay evidencia para elegir causa.
- **Propuesta:** reproducir en distintos momentos, correlacionar con logs de la API y del loader, verificar si el catálogo se reconstruye o si hay más de una réplica. Definir comportamiento esperado (retry transparente vs. 404 explícito) e instrumentar.
- **Área:** back + observabilidad. **Criterio de cierre:** reproduce documentado, causa identificada, fix o decisión de diseño registrada, y test de regresión.

### QA-02 · P0 · Latencia inicial de búsqueda de actividades
- **Evidencia:** resumen del Excel, verificación del 15/11 (23,304 s → 1,259 s al repetir).
- **Evaluación:** el patrón "primera llamada lenta" coincide con cold start / carga de embeddings; el usuario percibe el peor caso. Sin medición no se puede afirmar mejora.
- **Propuesta:** medir y registrar p50/p95 en frío y en caliente, identificar la fase responsable (carga de catálogo, embeddings, query pgvector) y optimizar o cachear. Definir umbral aceptable con producto.
- **Área:** back + infra. **Criterio de cierre:** métricas antes/después y umbral acordado.

### QA-03 · P1 · Cobertura E2E de UI (el hueco más grande)
- **Evidencia:** limitación global; `RUN-001`, `RUN-002`, `RUN-003`, `RUN-007`, `RUN-009`, `RUN-010`, `RUN-018`, `RUN-025`.
- **Evaluación:** los 38 casos prueban contrato HTTP, no interfaz. Quedan sin verificar render/montaje de React, errores de consola, CORS desde el dominio real, selección de dirección y marcador en mapa, UTF-8 desde el campo, selección de actividad → carga de trámites y respeto del parámetro `limit`.
- **Propuesta:** prueba de navegador (Playwright o equivalente) con smoke initial + flujo completo; comparación visual móvil/escritorio; cobertura de teclado y lector de pantalla en los componentes interactivos.
- **Área:** front + QA. **Criterio de cierre:** CI ejecuta el smoke y el flujo principal; capturas y resultados de accesibilidad revisados.

### QA-04 · P1 · Validación y errores legibles en el frontend
- **Evidencia:** `RUN-011` a `RUN-016`, `RUN-020` a `RUN-024`, `RUN-027`, `RUN-030` a `RUN-033`.
- **Reglas extraídas de la API (ya vigentes, hay que reflejarlas en UI):**
  - direcciones: `address` obligatorio, ≥3 caracteres, patrón `\S`; `limit` 1–10.
  - actividades: `query` 2–100 caracteres, patrón `\S`; `limit` 1–10.
  - trámites: `query` ≥3 caracteres, patrón `\S`; `limit` 1–20; `procedure_id` UUID válido.
- **Propuesta:** no consultar por debajo del umbral, recortar espacios, mostrar error junto al campo en texto claro (sin exponer el `detail` técnico), contador de caracteres en el campo de actividades, y alinear límites front ↔ API ↔ OpenAPI.
- **Área:** front (principal) + back (documentación). **Criterio de cierre:** cada regla tiene su test de UI y el error 422 siempre se traduce a mensaje legible.

### QA-05 · P1 · Calidad del ranking de resultados
- **Evidencia:** `RUN-019`, `RUN-026`, `RUN-029` (y `RUN-018` como salida correcta).
- **Evaluación:** QA pidió "ejemplos de ranking esperado" y advirtió que coincidencias débiles podrían mostrarse como certezas; en `RUN-029` el primer resultado ("Alta de habilitación de remises" ) puede ser menos relevante que "Habilitación de actividad económica".
- **Propuesta:** golden set de consultas con ranking esperado, umbral de similitud por debajo del cual no se sugiere, y revisión del orden con producto.
- **Área:** back + producto. **Criterio de cierre:** golden set versionado y test de ranking en CI.

### QA-06 · P2 · Contrato, CORS y monitoreo
- **Evidencia:** `RUN-004`, `RUN-005`, `RUN-006`, `RUN-008`, `RUN-024`, `RUN-033`.
- **Propuesta:** versionar el contrato OpenAPI y verificarlo contra el front; conservar allowlist explícita de orígenes (CORS ya pasó con origen Vercel y rechazo de externo); documentar límites en OpenAPI; alertar si `/health` cae; mantener versión y `/docs` en la respuesta raíz (hoy OK).
- **Área:** back + infra. **Criterio de cierre:** contrato versionado con check en CI y alerta de health activa.

### QA-07 · P2 · Claridad del contexto de actividad
- **Evidencia:** `RUN-036`, `RUN-037`, `RUN-038`.
- **Propuesta:** explicar visualmente el estado "Puede aplicar" y cómo refinar con respuestas; conservar la respuesta seleccionada al cambiar de sección; mostrar trámites excluidos con claridad. **Requiere validación con el responsable del catálogo** antes de cambiar reglas.
- **Área:** front + back + producto. **Criterio de cierre:** reglas confirmadas por el dueño del catálogo y UI verificada con las 5 preguntas.

### QA-08 · P2 · Decisiones de producto pendientes
- **Evidencia:** `RUN-017` (provincia alternativa Córdoba), `RUN-026` (sin sugerencia útil), `RUN-009`/`RUN-010` (mapa y UTF-8).
- **Preguntas abiertas:** ¿el producto cubre otras provincias o solo CABA? ¿qué mensaje mostrar cuando no hay sugerencia útil? ¿se habilita selección de provincia/punto en el mapa?
- **Área:** producto. **Criterio de cierre:** decisión registrada antes de tocar código.

## 3. Checklist de implementación

Marca cada ítem cuando esté **implementado, probado y con evidencia** (commit o link al test).

- [ ] **INC-01** — reproducir y diagnosticar el 404 → 200 de `RUN-034` (QA-01)
- [ ] Medir latencia fría/caliente de actividades y fijar umbral (QA-02)
- [ ] Smoke E2E: render, montaje React y sin errores de consola (QA-03)
- [ ] E2E flujo principal: dirección → actividad → trámites → detalle (QA-03)
- [ ] Verificación visual móvil/escritorio y accesibilidad teclado/lector (QA-03)
- [ ] Umbrales de validación en UI (direcciones, actividades, trámites) (QA-04)
- [ ] Recorte de espacios, contador de caracteres y errores legibles (QA-04)
- [ ] Límites `limit` alineados front ↔ API ↔ OpenAPI (QA-04)
- [ ] Golden set de ranking y umbral de coincidencia débil (QA-05)
- [ ] Contrato OpenAPI versionado + check en CI (QA-06)
- [ ] Alerta de `/health` y allowlist CORS documentada (QA-06)
- [ ] UI de contexto: "Puede aplicar", respuestas persistentes, trámites excluidos (QA-07)
- [ ] Resolver decisiones de producto de QA-08 y registrarlas
- [ ] Verificar en UI título, resumen y enlace oficial del detalle (RUN-034/035)

## 4. Incidencia INC-01 — detalle (RUN-034)

- **Caso:** "Detalle de trámite existente" · `GET /guidance/procedures/338718b4-1774-4db3-bd2e-f4a5ffc1d335`
- **Esperado:** HTTP 200 con ID coincidente y fuente.
- **Obtenido (verbatim):** "Primera consulta GET devolvió HTTP 404; al repetirla con el mismo UUID, devolvió HTTP 200 y el detalle 'Alta de habilitación de remises'. La disponibilidad del detalle fue inconsistente entre intentos."
- **Nota del ejecutor:** "Conviene repetir en distintos momentos y revisar logs/consistencia del catálogo; causa de la diferencia no confirmada."
- **Sugerencia QA:** "Verificar que la UI muestre título, resumen y enlace oficial correctos."

## 5. Notas de ejecución relevantes

- `RUN-007`: el primer control Python leyó el header CORS con distinta capitalización; se reconfirmó con `curl`. No es un defecto de la API, pero sí una alerta para automatizar la aserción de headers.
- `RUN-015` a `RUN-017`, `RUN-022` a `RUN-025`, `RUN-032` a `RUN-034`: verificar siempre que la UI respete la cantidad devuelta por `limit`.
- Todas las solicitudes fueron GET/OPTIONS de solo lectura: **no se enviaron POST ni se creó información**.

## 6. Los 38 casos (transcripción del Excel)

Tabla con los campos útiles para evaluación. La fuente original (pasos, responsable, fecha y evidencia por caso) sigue siendo el `.xlsx` listado arriba.

| ID | Módulo | Caso de prueba | Tipo | Prio | Datos de prueba | Resultado esperado | Estado | Sugerencia / incidencia |
|---|---|---|---|---|---|---|---|---|
| RUN-001 | Sitio publicado | Disponibilidad y documento inicial | Disponibilidad | Crítica | GET sin autenticación | HTTP 200; HTML de ConCo contiene root de React y título esperado. | Aprobado | Agregar prueba sintética en navegador que confirme render del formulario y errores de consola. |
| RUN-002 | Sitio publicado | Carga de bundle JavaScript | Integración | Alta | Recurso referenciado en el HTML | HTTP 200; recurso JavaScript de la aplicación descargado. | Aprobado | Automatizar carga en navegador para confirmar que React monta el formulario y no arroja errores. |
| RUN-003 | Sitio publicado | Carga de hoja de estilos | Integración | Media | Recurso CSS referenciado en el HTML | HTTP 200; CSS no vacío. | Aprobado | Agregar comparación visual con capturas para móvil y escritorio. |
| RUN-004 | API | Health check | Integración | Crítica | GET /health | HTTP 200 y status=ok. | Aprobado | Monitorear este endpoint y alertar si queda fuera de servicio. |
| RUN-005 | API | Información raíz | Integración | Media | GET / | HTTP 200 e identificación de ConCo API. | Aprobado | Mantener la versión y documentación visibles en la respuesta raíz. |
| RUN-006 | API | Esquema OpenAPI | Integración | Media | GET OpenAPI | HTTP 200; documenta endpoints de geolocalización y guidance. | Aprobado | Versionar el contrato y verificarlo contra el bundle del frontend. |
| RUN-007 | Integración / CORS | Preflight desde origen Vercel | Integración | Alta | OPTIONS; Origin Vercel, GET, Content-Type | HTTP 200 y permite exactamente el origen del sitio publicado. | Aprobado | Agregar prueba fetch automatizada desde el propio dominio Vercel. |
| RUN-008 | Integración / CORS | Origen externo no permitido | Seguridad | Media | OPTIONS; Origin externo no autorizado | El servidor no refleja el origen externo en Access-Control-Allow-Origin. | Aprobado | Conservar una allowlist explícita de dominios autorizados. |
| RUN-009 | Direcciones | Dirección Corrientes 2500 | Integración / validación | Alta | {'address': 'Corrientes 2500', 'limit': 5} | HTTP 200 con dirección normalizada, comuna y coordenadas. | Aprobado | Confirmar también selección en la UI y marcador del mapa. |
| RUN-010 | Direcciones | Dirección con acento: Córdoba | Integración / validación | Alta | {'address': 'Córdoba 1234'} | HTTP 200 con arreglo addresses; el acento no rompe la consulta. | Aprobado | Probar caracteres UTF-8 desde el campo publicado y revisar Network. |
| RUN-011 | Direcciones | Parámetro address ausente | Integración / validación | Alta | Sin parámetros | HTTP 422 por parámetro obligatorio ausente. | Aprobado | Mostrar una validación legible antes de enviar la solicitud. |
| RUN-012 | Direcciones | Dirección menor al mínimo | Integración / validación | Alta | {'address': 'ab'} | HTTP 422 por longitud mínima de 3 caracteres. | Aprobado | No consultar desde la UI antes del umbral y conservar la validación backend. |
| RUN-013 | Direcciones | Dirección solo espacios | Integración / validación | Alta | {'address': '   '} | HTTP 422 por entrada sin contenido útil. | Aprobado | Recortar espacios y mostrar el error junto al campo. |
| RUN-014 | Direcciones | Límite de resultados cero | Integración / validación | Alta | {'address': 'Corrientes 2500', 'limit': 0} | HTTP 422 por límite inferior a 1. | Aprobado | Mantener límites del frontend y API alineados. |
| RUN-015 | Direcciones | Límite de resultados mayor a 10 | Integración / validación | Alta | {'address': 'Corrientes 2500', 'limit': 11} | HTTP 422 por superar el máximo permitido. | Aprobado | Documentar el máximo y mostrar errores de parámetro con claridad. |
| RUN-016 | Direcciones | Límite de resultados igual a 1 | Integración / validación | Alta | {'address': 'Corrientes 2500', 'limit': 1} | HTTP 200 con hasta una dirección. | Aprobado | Verificar que la interfaz no muestre más opciones que las solicitadas. |
| RUN-017 | Direcciones | Provincia alternativa Córdoba | Integración / validación | Alta | {'address': 'Córdoba 1234', 'province': 'cordoba'} | HTTP 200 y estructura válida, aunque no haya coincidencias. | Aprobado | Si el producto cubre otras provincias, permitir elegir provincia en la experiencia. |
| RUN-018 | Actividades | “barbería” sugiere Peluquería | Integración / validación | Alta | {'query': 'barbería', 'limit': 5} | HTTP 200; primera sugerencia Peluquería con alias barbería. | Aprobado | La coincidencia de actividad se observó; verificar selección, valor mostrado y carga de trámites desde la interfaz. |
| RUN-019 | Actividades | Consulta semántica de cafetería | Integración / validación | Alta | {'query': 'quiero abrir una cafetería'} | HTTP 200 y arreglo activities con sugerencias estructuradas. | Aprobado | Definir ejemplos de ranking esperado por actividad para detectar sugerencias débiles. |
| RUN-020 | Actividades | Query de un carácter | Integración / validación | Alta | {'query': 'a'} | HTTP 422 por longitud mínima. | Aprobado | Evitar llamada desde la UI antes del umbral de escritura. |
| RUN-021 | Actividades | Query de espacios | Integración / validación | Alta | {'query': '   '} | HTTP 422 por query sin contenido. | Aprobado | Recortar entrada y traducir el error a texto claro. |
| RUN-022 | Actividades | Límite de actividades cero | Integración / validación | Alta | {'query': 'peluquería', 'limit': 0} | HTTP 422; límite fuera del rango permitido. | Aprobado | Mantener validación consistente entre cliente y servidor. |
| RUN-023 | Actividades | Límite de actividades mayor a 10 | Integración / validación | Alta | {'query': 'peluquería', 'limit': 11} | HTTP 422; máximo 10. | Aprobado | Documentar y comprobar el límite en OpenAPI. |
| RUN-024 | Actividades | Límite de actividades igual a 1 | Integración / validación | Alta | {'query': 'barbería', 'limit': 1} | HTTP 200 con a lo sumo una sugerencia. | Aprobado | Confirmar que la UI respete la cantidad de opciones devueltas. |
| RUN-025 | Actividades | Query con tilde | Integración / validación | Alta | {'query': 'peluquería'} | HTTP 200 y arreglo activities válido. | Aprobado | Mantener UTF-8 en todos los pasos de búsqueda. |
| RUN-026 | Actividades | Query de actividad poco común | Integración / validación | Alta | {'query': 'actividad zxqv no existente'} | HTTP 200 y arreglo activities válido; no error 5xx. | Aprobado | No mostrar coincidencias débiles como certezas; comunicar cuando no haya sugerencia útil. |
| RUN-027 | Actividades | Query mayor a 100 caracteres | Integración / validación | Alta | {'query': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'} | HTTP 422 por exceder el máximo. | Aprobado | Agregar contador/límite visible al campo. |
| RUN-028 | Trámites | Búsqueda de habilitación | Integración / validación | Media | {'query': 'habilitación', 'limit': 3} | HTTP 200 con fuente oficial y “Habilitación de actividad económica” entre resultados. | Aprobado | Revisar ranking: el primer resultado puede ser menos relevante que el trámite económico exacto. |
| RUN-029 | Trámites | Query de dos caracteres | Integración / validación | Media | {'query': 'ab'} | HTTP 422 por mínimo de 3 caracteres. | Aprobado | Informar mínimo de búsqueda en la interfaz. |
| RUN-030 | Trámites | Query solo espacios | Integración / validación | Media | {'query': '   '} | HTTP 422 por falta de contenido útil. | Aprobado | Recortar entrada y evitar exponer detalle técnico. |
| RUN-031 | Trámites | Límite cero | Integración / validación | Media | {'query': 'habilitación', 'limit': 0} | HTTP 422 por límite inferior a 1. | Aprobado | Validar rango y explicar el rechazo de forma legible. |
| RUN-032 | Trámites | Límite mayor a 20 | Integración / validación | Media | {'query': 'habilitación', 'limit': 21} | HTTP 422; máximo 20. | Aprobado | Mantener límites documentados y consistentes. |
| RUN-033 | Trámites | Límite igual a 1 | Integración / validación | Media | {'query': 'habilitación', 'limit': 1} | HTTP 200 con hasta un trámite. | Aprobado | Comprobar que la respuesta respeta el parámetro limit. |
| RUN-034 | Trámites | Detalle de trámite existente | Integración / validación | Media | /338718b4-1774-4db3-bd2e-f4a5ffc1d335 | HTTP 200 con ID coincidente y fuente. | Observación | Verificar que la UI muestre título, resumen y enlace oficial correctos. **Incidencia INC-01: 404 → 200 al reintentar; ver detalle más abajo.** |
| RUN-035 | Trámites | UUID inválido | Integración / validación | Media | /no-es-un-uuid | HTTP 422 por identificador con formato incorrecto. | Aprobado | Devolver un error entendible si este detalle se solicita desde la UI. |
| RUN-036 | Contexto de actividad | Peluquería sin respuestas de contexto | Integración | Alta | Sin respuestas | HTTP 200 con activity, preguntas y lista de trámites. | Aprobado | Explicar visualmente “Puede aplicar” y cómo refinar con respuestas. |
| RUN-037 | Contexto de actividad | Personal = Sí | Integración | Alta | has_employees=true | HTTP 200; pregunta refleja true y trámite de empleadores aplica. | Aprobado | Mostrar respuesta seleccionada y conservarla al cambiar de sección. |
| RUN-038 | Contexto de actividad | Personal = No | Integración | Alta | has_employees=false | HTTP 200; pregunta refleja false y trámite de empleadores no queda como aplica. | Aprobado | Validar reglas con responsable del catálogo y mostrar trámites excluidos con claridad. |
