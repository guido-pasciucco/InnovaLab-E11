# Modificaciones pendientes — testing de QA y frontend

> Este documento contiene **solo el trabajo que falta hacer**. No repite los 38 casos ni sus resultados: para eso está [CASOS_DE_PRUEBA_QA_2026-11-16.md](CASOS_DE_PRUEBA_QA_2026-11-16.md).
>
> - **Parte A** — pendientes que salen del testing de QA del 16/11.
> - **Parte B** — pedidos nuevos del dueño del producto (no vienen del testing): routing, historial local y pasos navegables.
>
> Se implementan en el PR #82, rama `feat/qa-casos-prueba-16-11-26`.

## Cómo usar este documento

1. Elegir un ID del backlog (QA-xx o FE-xx).
2. Implementarlo con su criterio de cierre.
3. Tildar el ítem en la checklist final con el commit o el link al test que lo cubre.

## Parte A — Pendientes del testing de QA

| ID | Modificación pendiente | Evidencia | Prioridad | Criterio de cierre |
|---|---|---|---|---|
| QA-01 | Diagnosticar y corregir la inconsistencia del detalle de trámite (INC-01): 404 y luego 200 con el mismo UUID. | `RUN-034` | P0 | Reproducción documentada, causa identificada, fix o decisión de diseño y test de regresión. |
| QA-02 | Medir y reducir la latencia inicial de la búsqueda de actividades. | Resumen 15/11 (~23,3 s en frío vs ~1,26 s al repetir) | P0 | Métricas antes/después y umbral acordado con producto. |
| QA-03 | Cubrir la UI con pruebas de navegador: render/montaje de React, errores de consola, CORS real, mapa, UTF-8 y respeto de `limit`. | Limitación global; `RUN-001/002/003/007/009/010/018/025` | P1 | Smoke + flujo principal en CI, con comparación visual y revisión de accesibilidad. |
| QA-04 | Reflejar en el frontend las validaciones de la API (umbrales, patrones, rangos de `limit`) y traducir los 422 a mensajes legibles. | `RUN-011` a `016`, `020` a `024`, `027`, `030` a `033` | P1 | Cada regla tiene test de UI; ningún error técnico se muestra crudo. |
| QA-05 | Definir un golden set de ranking de actividades y trámites, y un umbral para no mostrar coincidencias débiles como certezas. | `RUN-019/026/029` | P1 | Golden set versionado y test de ranking en CI. |
| QA-06 | Versionar el contrato OpenAPI, verificarlo contra el front, mantener la allowlist CORS y alertar si `/health` cae. | `RUN-004/005/006/008/024/033` | P2 | Contrato con check en CI y alerta activa. |
| QA-07 | Explicar visualmente «Puede aplicar», conservar las respuestas de contexto y mostrar los trámites excluidos. | `RUN-036/037/038` | P2 | Reglas confirmadas por el responsable del catálogo y UI verificada. |
| QA-08 | Resolver las decisiones de producto abiertas (otras provincias, mensaje sin sugerencia útil, selección en el mapa). | `RUN-017/026/009/010` | P2 | Decisiones registradas antes de tocar código. |

## Parte B — Pedidos nuevos del frontend

Evidencia del estado actual:

- `front/package.json` no incluye ningún router; `front/src/App.tsx:38` mantiene el paso en `useState<Step>(1)`.
- La barra de pasos son `<div>` en `front/src/App.tsx:201-210`: no son clickeables ni navegables.
- Los enlaces del footer usan `href="#"` con `preventDefault` (`front/src/App.tsx:437-460`).
- No hay `localStorage`, `sessionStorage` ni `indexedDB` en `front/src/`.
- No hay `front/vercel.json`: las rutas profundas requieren verificar el fallback SPA en la configuración de Vercel.
- Los ejemplos de la home están en `front/src/Componentes/QueryForm.tsx:7-12` (arreglo `examples`) y en el bloque `Probá con un ejemplo` de la línea 74.

| ID | Modificación pendiente | Dependencias | Criterio de cierre |
|---|---|---|---|
| FE-01 | Incorporar enrutamiento real con `react-router-dom` y rutas `/`, `/analisis`, `/orientacion`, `/mapa`, `/asistente`. Verificar la versión estable con `npm view react-router-dom version` antes de fijarla. | — | Navegar entre pasos cambia la URL; recargar una ruta funciona; un acceso directo sin resultado redirige a `/`. |
| FE-02 | Hacer clickeables los pasos de la barra (y los tabs internos y enlaces del footer) con `Link`/`NavLink`, deshabilitando los pasos aún no desbloqueados. | FE-01 | Navegación por teclado y lector de pantalla; estados activo/completado/bloqueado visibles. |
| FE-03 | Mostrar el historial de búsquedas en la misma pantalla del paso 1, con el diseño descripto más abajo. | FE-01 (para abrir el resultado) | El historial se ve sin salir de la pantalla de consulta; se puede limpiar; funciona en móvil. |
| FE-04 | Persistir el historial en `localStorage` con normalización, dedupe, tope y rehidratación de la consulta. | FE-03 | Recargar la página conserva el historial; las reglas de privacidad y el problema del `consultationId` están resueltos. |
| FE-05 | Quitar los ejemplos de la página principal: el bloque «Probá con un ejemplo» con los chips `Cafetería`, `Almacén` y `Peluquería`. | — | El formulario de inicio ya no muestra ejemplos ni rellena los campos con datos de prueba. |

### Diseño propuesto del historial (FE-03 / FE-04)

**Recomendación:** un panel plegable «Búsquedas recientes» dentro del paso 1 (Consulta), debajo del formulario. En escritorio se muestra como tarjeta compacta al costado; en móvil, como sección plegable debajo del formulario. Reutiliza las clases existentes (`panel`, `query-pill`, `chip`, `secondary`) en lugar de introducir un componente nuevo con otro lenguaje visual.

```text
Búsquedas recientes (3)                       [Limpiar]
┌────────────────────────────────────────────────────────┐
│ Peluquería · Av Corrientes 2500        hace 2 h   [Ver] │
│ Barbería · Córdoba 1234                ayer       [Ver] │
│ Cafetería · Corrientes 1500            12/11      [Ver] │
└────────────────────────────────────────────────────────┘
```

- Al hacer clic en un registro se restaura la consulta en el formulario y se abre el resultado guardado. Un botón explícito «Actualizar» vuelve a consultar a la API.
- Se muestran como máximo 5 ítems; el resto queda detrás de «Ver todas». Sin resultados, el panel no se renderiza.
- Se guarda el mínimo necesario: `conco.search-history.v1` como arreglo de `{ id, activity, activitySlug, address, normalizedAddress, createdAt }`. Tope de 10 registros y dedupe por actividad + dirección normalizados. **No** guardar la respuesta completa ni el chat.
- El history es solo local: botón «Limpiar historial», sin envío a analytics y con una nota breve de privacidad.

**Alternativas evaluadas:**

| Opción | Por qué no se recomienda |
|---|---|
| Desplegable dentro del autocompletado de actividad | Mezcla dos conceptos distintos (sugerencias de la API vs. búsquedas propias) y queda oculto. |
| Página dedicada `/historial` | Contradice el pedido de mostrarlo «en la misma pantalla» y agrega otra ruta que mantener. |
| Modal o toast | Mal comportamiento para uso repetido: fuerza abrir y cerrar cada vez. |

**Dos precisiones importantes:**

1. [docs/ideas/cache-busquedas-direcciones.md](../ideas/cache-busquedas-direcciones.md) propone un caché **de backend** para las respuestas de Georef. El pedido actual es un caché **local de historial en el frontend**: son cosas distintas y pueden convivir.
2. El asistente usa `submitFollowUp(result.consultationId, …)` (`front/src/App.tsx:150`), un identificador que vive en el servidor. Al recargar la página, el `consultationId` guardado alcanza para mostrar la orientación, pero **no** para seguir haciendo preguntas. Antes de implementar «Ver resultado» hay que decidir: repetir la consulta al abrir un registro histórico, o persistir las consultas en el backend.

### Alcance de FE-05

Quitar el arreglo `examples`, su comentario asociado y el bloque JSX «Probá con un ejemplo» en `QueryForm.tsx`. Los estilos `.examples` y `.examples-title` (`front/src/style.css:77-78`) quedan sin uso y también se eliminan. **No** eliminar `.example-chips` ni `.chip`: el asistente los usa para las preguntas sugeridas en `front/src/App.tsx:387-389`.

## Checklist unificado

- [ ] QA-01 — diagnosticar INC-01 y registrar causa + fix
- [ ] QA-02 — medir latencia fría/caliente y fijar umbral
- [ ] QA-03 — smoke E2E y flujo principal en CI
- [ ] QA-03 — comparación visual móvil/escritorio y accesibilidad
- [ ] QA-04 — umbrales de validación en UI
- [ ] QA-04 — errores 422 legibles y límites alineados con OpenAPI
- [ ] QA-05 — golden set de ranking y umbral de coincidencia débil
- [ ] QA-06 — contrato versionado, allowlist CORS y alerta de `/health`
- [ ] QA-07 — UI de contexto con reglas confirmadas
- [ ] QA-08 — decisiones de producto registradas
- [ ] FE-01 — enrutamiento con rutas de los cinco pasos y fallback SPA
- [ ] FE-02 — pasos, tabs y enlaces del footer navegables por teclado
- [ ] FE-03 — panel «Búsquedas recientes» en el paso 1
- [ ] FE-04 — persistencia local, dedupe, limpieza y rehidratación
- [ ] FE-05 — quitar los ejemplos «Probá con un ejemplo» del formulario principal

## Dependencias y riesgos

- FE-02 depende de FE-01; FE-03 necesita FE-01 para abrir el resultado de un registro histórico.
- FE-04 tiene una decisión pendiente sobre `consultationId` que puede requerir trabajo en el backend.
- QA-08 bloquea cualquier cambio de reglas del catálogo.
- Las rutas profundas (`/mapa`, `/asistente`) pueden devolver 404 en producción si Vercel no reescribe a `index.html`.

## Próximo paso

Arrancar con FE-01 + FE-02 como primer slice (routing y pasos navegables, sin tocar el historial), verificar los deep links en Vercel y recién después sumar FE-03 + FE-04. La decisión sobre `consultationId` se toma antes de implementar «Ver resultado».
