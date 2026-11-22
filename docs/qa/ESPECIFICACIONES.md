# Especificaciones

Este es el documento de referencia para **implementar**. Cada especificación se escribe solo cuando el dueño del producto confirma que entendió el punto, y queda registrada con el contexto en que se entendió. No se agrega nada por adelantado.

Cada entrada tiene: el punto en lenguaje simple, por qué importa, lo que pidió QA, cómo sabremos que está listo, qué NO se hace, y el contexto y las decisiones que lo cerraron. El nivel de detalle es el mismo de la explicación oral, para que al retomar el trabajo no se haga de otro modo.

## Entradas confirmadas

### 1. El trámite que a veces aparece y a veces no (QA-01)

**Cómo se entendió:** al pedir el detalle de un trámite, la primera vez el sistema contestó como si no existiera; al repetir exactamente lo mismo, apareció con todos sus datos ("Alta de habilitación de remises" y su fuente). Importa porque quien se topa con el primer intento puede creer que ConCo no tiene ese trámite y se va con una idea equivocada. Es como un ascensor que a veces para en el piso: la información está, pero no siempre te la da. Lo esperable es que pase siempre lo mismo: que aparezca siempre, o que se diga con claridad que no está.

**Cómo sabremos que está listo:** probando varias veces y en distintos momentos, el trámite sale siempre igual, y con una nota simple que explique qué era lo que fallaba.

**Lo que NO se hace:** cambiar cómo se ve la pantalla ni revisar otros trámites. Solo este problema.

**Contexto que lo aclaró:**

- La comparación con un enlace que te lleva a una página de "no encontrado": no era un cartel lindo en la pantalla, era la respuesta del sistema. Eso es lo que significa el 404 que anotó QA.
- La aclaración de que la prueba se hizo contra la API, sin abrir la página: por eso sabemos qué contestó el sistema, pero no qué vio una persona.
- Tu observación de que en la pantalla solo se busca por actividad y no hay buscador de trámites: era correcta. La búsqueda por nombre existe solo en la API y se usó para armar la prueba; no está pensado agregarla a la pantalla.
- Por eso las dudas quedaron como [consultas para testing](CONSULTAS_PARA_QA.md), no como trabajo del proyecto.

**Decisiones y arquitectura acordadas (22/11/2026):**

- **Endpoints que el front no usa:** `/guidance/procedures` (buscar trámites por nombre) y `/guidance/procedures/{procedure_id}` (detalle por ID). El front solo usa `/guidance/activities/{slug}/procedures`, que ya trae el detalle. Son los que usó QA en RUN-028 a RUN-035. Se pueden quitar, pero como paso aparte: hay que actualizar esos casos y el contrato OpenAPI. Quitarlos **no** corrige la causa.
- **Causa del 404:** no lo inventa ConCo. La API externa de la Ciudad redirige a una página HTML cuando un ID no está publicado; nuestro cliente lo traduce a 404. Al repetir, respondió bien. Apunta a la fuente oficial, no a Render (`back/src/conco/integrations/caba_tramites/client.py:142`).

  **Flujo de errores a definir:** tres casos distintos, con mensajes para la persona:

  | Situación | Respuesta | Mensaje |
  |---|---|---|
  | El trámite realmente no existe | 404 | "No encontramos ese trámite." |
  | La fuente no responde o falla | 503 | "No pudimos consultar los trámites. Intentá de nuevo." |
  | Todavía se está cargando | 503 | "Estamos cargando los trámites, volvé a intentar." |

  **Backend (FastAPI):**

  - Una familia de errores propios con tres datos: código, mensaje en español y estado HTTP. Un único manejador (`@app.exception_handler`) convierte todos a la misma forma. Mantener el campo `detail` que ya usan el front y QA, y agregar arriba `code` y `request_id`. Así no se rompe nada.
  - No tocar el formato del 422: los casos de QA lo validan tal cual.
  - Manejador genérico para 500: mensaje genérico al usuario, el detalle técnico solo en los logs.
  - Request ID en cada respuesta, para poder seguir el rastro del 404→200 en los logs. Es lo que hoy falta para diagnosticar.
  - Reintento acotado (1 o 2) solo en consultas de lectura cuando el error es transitorio de la fuente.
  - Separar `/health` de `/ready`: `/health` = "el proceso está vivo" (lo usa el ping); `/ready` = "la base y el catálogo están listos" (para saber si puede responder). Un monitor no debe confundir una cosa con la otra.

  **Frontend (React + TypeScript):**

  - `ApiError` hoy es muy pobre: solo guarda el estado y el texto crudo (`front/src/api/client.ts:12`). Extenderlo para entender `code` y `message`, y traducirlos a mensajes en español. Distinguir sin conexión, timeout y cancelación (cancelar no es error, no hay que mostrar nada).
  - Un solo lugar que traduzca códigos a mensajes, para que el mismo error se diga igual en todo el sitio.
  - Un error boundary (componente de clase con `getDerivedStateFromError` / `componentDidCatch`) al nivel raíz y por sección, con botón "Reintentar". Ojo: eso atrapa errores de render; los errores de la API los maneja el cliente, no el boundary.
  - Tres niveles de aviso: al lado del campo (validación), dentro de la sección (los avisos que ya existen, como "No pudimos cargar los trámites") y una pantalla de respaldo para lo inesperado.

- Fuentes: [FastAPI – Handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [React – Error boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary).

**Confirmado:** 22/11/2026.

### 2. La primera búsqueda tarda demasiado (QA-02)

**Cómo se entendió:** en una verificación anterior, la primera búsqueda de actividades tardó unos 23 segundos y la misma búsqueda repetida, poco más de 1 segundo. Es como un motor frío: cuesta arrancar y después anda bien. Importa porque esa primera vez es lo que ve alguien que recién entra: si espera 23 segundos, puede pensar que se trabó y cerrar la página antes de ver nada. Lo esperable es que la primera búsqueda no se sienta tan lenta o, si no se puede mejorar mucho, saber por qué tarda y hasta cuánto tiempo damos por aceptable.

**Cómo sabremos que está listo:** midiendo cuánto tarda la primera búsqueda y cuánto las siguientes, y teniendo un número acordado del tipo "hasta acá está bien".

**Lo que NO se hace:** cambiar cómo se ve la pantalla ni tocar otras búsquedas.

**Contexto y decisión (22/11/2026):**

- Tu observación de que el responsable parece ser Render, que es donde está publicada la API.
- **Lo que dice Render:** el plan gratis duerme el servicio después de 15 minutos sin visitas; cuando llega una visita nueva, tarda aproximadamente 1 minuto en despertar y muestra una página de carga. Te dan 750 horas gratis por mes; mientras está dormido, no consume horas.
- **La trampa de los pings:** mantenerlo despierto las 24 horas consume unas 730 de esas 750 horas, o sea casi todo el presupuesto mensual. Y Render puede reiniciar el servicio cuando quiera, así que los pings no garantizan cero esperas. En su documentación dicen que el plan gratis no es para producción.
- **Las opciones que se evaluaron:** el plan pagado más bajo ($7/mes, workspace Hobby $0 + compute $7) era la solución limpia, pero quedó descartado por decisión del dueño: no hay presupuesto, todo tiene que ser gratis.
- **La solución elegida:** cron-job.org, gratis de verdad — sin límite mensual de ejecuciones, sin tarjeta, intervalo mínimo de 1 minuto. Se configura una tarea que visita `https://conco-api.onrender.com/health` **cada 10 minutos** (no 15, para dejar margen por si se atrasa). Son unas 4.300 visitas por mes. UptimeRobot gratis (50 monitores, chequeos cada 5 minutos) quedó como alternativa que además avisa si la API cae y cubre el pendiente QA-06. Con uno alcanza.
- **Recaudos:** el ping va siempre a `/health`, nunca a `/guidance/activities` ni a una búsqueda, porque esos consultan APIs externas y las estaríamos golpeando cada 10 minutos. Revisar el consumo en Render (*Billing → Monthly Included Usage*): un servicio despierto 24/7 usa ~730 de 750 horas, así que no debe haber otro servicio gratis despierto.
- **Cómo validar que funciona:** mirar el historial de ejecuciones de cron-job.org (debe decir *success*) y comprobar que en Render el servicio figure como *Live* en vez de *Spin down*. Si al día siguiente sigue en *Live*, ya está.
- **Qué no se hace:** armar un script propio con GitHub Actions cada 5 minutos (los cron se atrasan y los minutos son limitados). Para eso ya existen los monitores.
- **Aclaración:** la causa de Render es muy probable, pero no quedó confirmada. Antes de darla por segura hay que medir: esperar más de 15 minutos sin pedidos, llamar a `/health` y repetir enseguida.
- Fuentes: [Render – Deploy for Free](https://render.com/docs/free), [Render – Pricing](https://render.com/pricing), [cron-job.org](https://cron-job.org/en/), [UptimeRobot plan gratuito](https://uptimerobot.com/status-page).

**Confirmado:** 22/11/2026.

### 3. Mensajes de error que se entienden (QA-04)

**Cómo se entendió:** cuando alguien carga mal un dato en el formulario, la de QA pide que no se envíe el pedido, que se limpien los espacios de más, que el error aparezca al lado del campo en palabras de persona, que el campo de actividad tenga un contador de caracteres a la vista y que los mínimos y máximos sean los mismos en la página y en la API. Importa porque un mensaje como *"string_pattern_mismatch"* no le dice a nadie qué corregir; en cambio *"Escribí al menos 3 caracteres"*, sí.

**Lo que pidió ella, con sus palabras:**

- "Mostrar una validación legible antes de enviar la solicitud."
- "Recortar espacios y mostrar el error junto al campo."
- "Evitar llamada desde la UI antes del umbral de escritura."
- "Agregar contador/límite visible al campo."

**Qué se pide, en detalle:**

- No consultar por debajo del umbral: dirección desde 3 caracteres, actividad desde 2 y hasta 100, trámites desde 3, patrón `\S` (no solo espacios).
- Recortar espacios y mostrar el error junto al campo, sin exponer el `detail` técnico.
- Contador de caracteres visible en el campo de actividad.
- Límites de resultados: 1 a 10 en direcciones y actividades, 1 a 20 en trámites; alineados entre front, API y OpenAPI.

**Cómo sabremos que está listo:** probando los casos que ella nombró —campo vacío, muy corto, solo espacios, texto demasiado largo, límites fuera de rango y UUID inválido— y viendo que en cada uno aparece un mensaje claro y no se manda el pedido.

**Lo que NO se hace:** cambiar las reglas de validación de la API (ella pidió conservarlas) ni rediseñar el formulario.

**Contexto que lo aclaró:**

- La comparación entre el mensaje técnico y el mensaje en español, que es lo que hace que la persona sepa qué corregir.
- La decisión de arquitectura de errores tomada para la especificación 1 aplica acá: un único lugar que traduzca los códigos a mensajes en español, `ApiError` extendido para entender `code` y mensaje, y tres niveles de aviso (al lado del campo, dentro de la sección y pantalla de respaldo). El error boundary atrapa errores de render; los errores de la API los maneja el cliente.

**Confirmado:** 22/11/2026 (el dueño indicó que "ya quedó lo de errores").

## Cómo se usa

1. Te explico un pendiente, de a uno, en lenguaje simple y con el mismo detalle que vas a ver acá.
2. Si te queda claro, me decís «lo entendí» y, si querés, qué fue lo que te lo aclaró.
3. Solo en ese momento escribo la entrada acá, con su contexto y las decisiones que surgieron.

Los pendientes que todavía no se confirmaron están en [PENDIENTES_QA_Y_FRONTEND.md](PENDIENTES_QA_Y_FRONTEND.md). Las dudas para testing están en [CONSULTAS_PARA_QA.md](CONSULTAS_PARA_QA.md).
