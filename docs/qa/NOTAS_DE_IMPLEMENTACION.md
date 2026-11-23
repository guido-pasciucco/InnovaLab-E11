# Notas de implementación de las especificaciones

Qué se implementó de [ESPECIFICACIONES.md](ESPECIFICACIONES.md), qué falla se explicó y qué queda en manos del dueño del producto. El detalle técnico de cada tarea está en `odd/tasks/qa-especificaciones.md`.

## Estado por especificación

| # | Pedido | Estado | Queda pendiente |
|---|---|---|---|
| 1 | QA-01 — el trámite que a veces aparece | Implementado | Repetir RUN-034 contra Render después del deploy. |
| 2 | QA-02 — la primera búsqueda tarda | `/health` sigue liviano; pasos documentados abajo | Crear la tarea en cron-job.org, medir y acordar el número aceptable. |
| 3 | QA-04 — mensajes de error que se entienden | Implementado | — |
| 4 | QA-07 — entender «Puede aplicar» | Puntos 1, 2 y 3 implementados | Punto 4: que el responsable del catálogo apruebe las reglas (tabla abajo). |
| 5 | FE-01 — una dirección por paso | Implementado | Abrir una ruta directo en Vercel después del deploy. |
| 6 | FE-02 — pasos clickeables | Implementado | Decidir el destino de los enlaces del pie que todavía no tienen página. |
| 7 | FE-03 — búsquedas recientes | Implementado | — |
| 8 | FE-04 — historial que no se borra | Implementado | — |
| 9 | FE-05 — sacar los ejemplos | Implementado | — |

## 1. Qué fallaba en el trámite que aparecía y desaparecía (QA-01)

**La nota simple:** cuando la API de trámites de la Ciudad no encuentra un trámite, no responde «no existe»: redirige a una página web. ConCo tomaba esa redirección como «no encontrado» en el primer intento. En la prueba de QA, el mismo pedido repetido trajo el trámite bien, así que la redirección fue algo momentáneo de la fuente oficial, no un dato que faltara en ConCo.

**Qué cambió:**

- Ante una falla momentánea de la fuente (demora, corte, error 502, 503 o 504) o esa redirección, ConCo reintenta una sola vez antes de responder. Solo dice «No encontramos ese trámite.» si la fuente lo confirma dos veces.
- Cada respuesta lleva un código de seguimiento (`X-Request-ID`) que también queda en los logs. Si vuelve a pasar, se busca ese código en los logs de Render y se ve el pedido exacto.
- Los tres casos se dicen distinto:

| Situación | Respuesta | Mensaje |
|---|---|---|
| El trámite realmente no existe | 404 | «No encontramos ese trámite.» |
| La fuente no responde o falla | 503 | «No pudimos consultar los trámites. Intentá de nuevo.» |
| Todavía se está cargando | 503 | «Estamos cargando los trámites, volvé a intentar.» |

«Todavía se está cargando» quiere decir que la base responde pero el catálogo de actividades está vacío (todavía no se cargó). `/ready` informa lo mismo: `/health` dice si el proceso está vivo y `/ready` si la base y el catálogo están listos.

**Cómo comprobarlo:** repetir RUN-034 (`GET /guidance/procedures/338718b4-1774-4db3-bd2e-f4a5ffc1d335`) varias veces y en distintos momentos. Tiene que salir siempre igual. Si alguna vez falla, anotar el `X-Request-ID` de la respuesta.

## 2. Mantener despierta la API en Render (QA-02)

Esto se configura fuera del código y lo hace el dueño, porque requiere crear una cuenta. La lista para tildar, paso a paso dentro de cron-job.org, está en [GUIA_CRON_JOB_ORG.md](GUIA_CRON_JOB_ORG.md).

1. Crear una cuenta gratis en [cron-job.org](https://cron-job.org/en/) (no pide tarjeta).
2. Crear una tarea que haga `GET https://conco-api.onrender.com/health` **cada 10 minutos**.
3. El ping va siempre a `/health`, nunca a `/guidance/activities` ni a una búsqueda: esos consultan APIs externas.
4. Validar: en cron-job.org el historial tiene que decir *success*, y en Render el servicio tiene que figurar como *Live*. Si al día siguiente sigue en *Live*, ya está.
5. Revisar el consumo en Render (*Billing → Monthly Included Usage*): un servicio despierto todo el mes usa unas 730 de las 750 horas gratis, así que no tiene que haber otro servicio gratis despierto.

Si en lugar de cron-job.org se usa UptimeRobot, puede vigilar `/ready` para avisar si la API no puede responder; el ping para mantenerla despierta sigue siendo `/health`.

**Medir antes de darlo por resuelto:** esperar más de 15 minutos sin pedidos y correr dos veces seguidas:

```bash
curl -s -o /dev/null -w "%{time_total}\n" "https://conco-api.onrender.com/guidance/activities?query=peluqueria"
```

La primera medición es la búsqueda «en frío» y la segunda la normal. **Pendiente:** acordar el número aceptable para la primera búsqueda («hasta acá está bien»).

## 4. Reglas del catálogo para revisar (QA-07, punto 4)

La pantalla ya explica «Puede aplicar», nombra los trámites descartados y conserva las respuestas. Falta que alguien que conoce el catálogo confirme estas reglas. Están en `back/src/conco/guidance/data/activities.json`; no se cambiaron.

| Trámite | Aplica cuando… | Actividades |
|---|---|---|
| Habilitación de actividad económica | «¿Vas a continuar un local que ya está habilitado?» = No | 8 de 9 |
| Habilitación de actividad económica exprés | «¿El local tiene menos de 200 m²?» = Sí y «¿Vas a continuar un local que ya está habilitado?» = No | 7 de 9 |
| Transmisión de autorización de actividad económica | «¿Vas a continuar un local que ya está habilitado?» = Sí | 8 de 9 |
| Solicitud de permiso de área gastronómica | «¿Vas a poner mesas y sillas en la vereda?» = Sí | Cafetería, Restaurante |
| Consulta de usos - Visado de anuncio publicitario (frontal, saliente) marquesina y/o toldos | «¿Vas a poner un cartel, una marquesina o un toldo?» = Sí | 8 de 9 |
| Inscripción en el Registro de Empleadores | «¿Vas a contratar personal?» = Sí | 9 de 9 |
| Solicitud de rúbrica de documentación laboral | «¿Vas a contratar personal?» = Sí | 9 de 9 |
| Consulta obligatoria para inmuebles en APH o catalogados | «¿El inmueble está en un área de protección histórica (APH) o está catalogado?» = Sí | 8 de 9 |

Aprobado por: ____________________ Fecha: ____________

## 5 y 6. Rutas en Vercel y enlaces del pie

- `front/vercel.json` reescribe cualquier ruta a `index.html`. Después del deploy, abrir directo `/mapa` y `/orientacion` en el dominio de Vercel: tiene que cargar la app (sin consulta, vuelve a `/consulta`).
- Los enlaces del pie que tienen destino ya llevan a un lugar real: los pasos, la sección «Cómo funciona», el sitio oficial de trámites y Datos abiertos de la Ciudad. Centro de ayuda, Accesibilidad, Términos y condiciones, Política de privacidad y las redes sociales no tienen página ni cuenta todavía: quedan como texto «(próximamente)» en lugar de enlaces que no llevaban a ningún lado. **Pendiente:** definir sus destinos.

## 8. Qué pasa con el asistente al abrir una búsqueda vieja (FE-04)

El número de consulta que usa el asistente no se guarda en el servidor: lleva adentro la actividad elegida. Por eso no hace falta guardar consultas en el backend. Como el historial no guarda la respuesta, «Ver» completa el formulario y vuelve a consultar, y esa consulta nueva trae un número válido para el asistente. «Actualizar», en la barra de la consulta, repite la consulta actual por si cambió algo.

## Otros hallazgos

- La consola del navegador muestra un aviso de claves repetidas en el panel de requisitos (`RequirementsChecklist`) cuando un mismo trámite figura dos veces como origen de un requisito. Ya pasaba antes de este cambio y no se tocó.
