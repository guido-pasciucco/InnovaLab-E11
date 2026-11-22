# Especificaciones

Este es el documento de referencia para **implementar**. Cada especificación se escribe solo cuando el dueño del producto confirma que entendió el punto, y queda registrada con el contexto en que se entendió. No se agrega nada por adelantado.

Cada entrada tiene tres cosas:

| Campo | Qué guarda |
|---|---|
| **El punto** | El nombre del pendiente, en lenguaje simple. |
| **Cómo se entendió** | La explicación del problema y por qué importa. |
| **Contexto que lo aclaró** | El ejemplo, la comparación o la decisión que cerró el tema. |

## Entradas confirmadas

### 1. El trámite que a veces aparece y a veces no (QA-01)

**Cómo se entendió:** al pedir el detalle de un trámite, la primera vez el sistema contestó como si no existiera; al repetir exactamente lo mismo, apareció con todos sus datos ("Alta de habilitación de remises" y su fuente). Importa porque quien se topa con el primer intento puede creer que ConCo no tiene ese trámite. Lo esperable es que pase siempre lo mismo: que aparezca siempre, o que se diga con claridad que no está.

**Contexto que lo aclaró:**

- La comparación con un enlace que te lleva a una página de "no encontrado": no era un cartel lindo en la pantalla, era la respuesta del sistema.
- La aclaración de que la prueba se hizo contra la API, sin abrir la página: por eso sabemos qué contestó el sistema, pero no qué vio una persona.
- Tu observación de que en la pantalla solo se busca por actividad y no hay buscador de trámites: era correcta. La búsqueda por nombre existe solo en la API y se usó para armar la prueba; no está pensado agregarla a la pantalla.
- Por eso las dudas quedaron como consultas para testing, no como trabajo del proyecto.

**Decisiones y arquitectura acordadas (22/11/2026):**

- **Endpoints que el front no usa:** `/guidance/procedures` (buscar trámites por nombre) y `/guidance/procedures/{procedure_id}` (detalle por ID). El front solo usa `/guidance/activities/{slug}/procedures`, que ya trae el detalle. Son los que usó QA en RUN-028 a RUN-035. Se pueden quitar, pero como paso aparte: hay que actualizar esos casos y el contrato OpenAPI. Quitarlos **no** corrige la causa.
- **Causa del 404:** no lo inventa ConCo. La API externa de la Ciudad redirige a una página HTML cuando un ID no está publicado; nuestro cliente lo traduce a 404. Al repetir, respondió bien. Apunta a la fuente oficial, no a Render (`back/src/conco/integrations/caba_tramites/client.py:142`).
- **Flujo de errores a definir:** tres casos distintos — no existe (404, "No encontramos ese trámite"), la fuente falló (503, "No pudimos consultar los trámites. Intentá de nuevo"), todavía se está cargando (503, "Estamos cargando los trámites, volvé a intentar").
- **Backend (FastAPI):** familia de errores propios con código, mensaje y estado; un único manejador que convierte todo a la misma forma; conservar el campo `detail` que ya usan el front y QA y agregar `code` y `request_id`; no cambiar el formato del 422; manejador genérico de 500 con el detalle técnico solo en logs; request ID para seguir el rastro; reintento acotado solo en lecturas transitorias; separar `/health` (proceso vivo, lo usa el ping) de `/ready` (base y catálogo listos).
- **Frontend (React + TypeScript):** extender `ApiError` para entender `code` y mensaje y traducirlos a español; distinguir sin conexión, timeout y cancelación; un único lugar que traduzca códigos a mensajes; un error boundary (componente de clase con `getDerivedStateFromError` / `componentDidCatch`) al nivel raíz y por sección con botón "Reintentar"; tres niveles de aviso — al lado del campo, dentro de la sección y pantalla de respaldo. El boundary atrapa errores de render; los de la API los maneja el cliente.
- Fuentes: [FastAPI – Handling errors](https://fastapi.tiangolo.com/tutorial/handling-errors/), [React – Error boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary).

**Confirmado:** 22/11/2026.

### 2. La primera búsqueda tarda demasiado (QA-02)

**Cómo se entendió:** en una verificación anterior, la primera búsqueda de actividades tardó unos 23 segundos y la misma búsqueda repetida, poco más de 1 segundo. Es como un motor frío: cuesta arrancar y después anda bien. Importa porque esa primera espera es lo que ve alguien que recién entra: puede pensar que se trabó e irse. Lo esperable es saber por qué tarda y hasta cuánto tiempo damos por aceptable.

**Contexto que lo aclaró:**

- Tu observación de que el responsable parece ser Render, que es donde está publicada la API.
- La confirmación de que el plan gratis duerme el servicio a los 15 minutos sin visitas y tarda cerca de 1 minuto en despertar; además, da 750 horas gratis por mes.
- La solución que elegimos dentro de "todo gratis": un servicio gratuito (cron-job.org) que visite cada 10 minutos el endpoint `/health`, que ya existe y solo responde "estoy vivo" sin consultar nada más. UptimeRobot gratis quedó como alternativa que también avisa si la API cae.
- Los dos recaudos que surgieron: no mandar el ping a una búsqueda porque molesta a las APIs externas, y no dejar otro servicio gratis de Render despierto porque se agotan las 750 horas del mes.

**Aclaración:** la causa de Render es muy probable, pero no quedó confirmada. Antes de darla por segura hay que medir: esperar más de 15 minutos sin pedidos, llamar a `/health` y repetir enseguida.

**Confirmado:** 22/11/2026.

### 3. Mensajes de error que se entienden (QA-04)

**Cómo se entendió:** cuando alguien carga mal un dato en el formulario, la de QA pide que no se envíe el pedido, que se limpien los espacios de más, que el error aparezca al lado del campo en palabras de persona, que el campo de actividad tenga un contador de caracteres a la vista y que los mínimos y máximos sean los mismos en la página y en la API. Los mínimos que ella enumeró: dirección desde 3 caracteres, actividad desde 2 y hasta 100, y cantidad de resultados entre 1 y 10 (hasta 20 en trámites).

**Contexto que lo aclaró:**

- Un mensaje como *"string_pattern_mismatch"* no le dice a nadie qué corregir; en cambio *"Escribí al menos 3 caracteres"*, sí.
- La decisión de arquitectura de errores tomada para la especificación 1 aplica acá: un único lugar que traduzca los códigos a mensajes en español, `ApiError` extendido para entender `code` y mensaje, y tres niveles de aviso (al lado del campo, dentro de la sección y pantalla de respaldo).
- El error boundary atrapa errores de render; los errores de la API los maneja el cliente. No se cambian las reglas de validación de la API (ella pidió conservarlas) ni el formato del 422.

**Confirmado:** 22/11/2026 (el dueño indicó que "ya quedó lo de errores").

## Cómo se usa

1. Te explico un pendiente, de a uno, en lenguaje simple.
2. Si te queda claro, me decís «lo entendí» y, si querés, qué fue lo que te lo aclaró.
3. Solo en ese momento escribo la entrada acá, con su contexto y las decisiones que surgieron.

Los pendientes que todavía no se confirmaron están en [PENDIENTES_QA_Y_FRONTEND.md](PENDIENTES_QA_Y_FRONTEND.md). Las dudas para testing están en [CONSULTAS_PARA_QA.md](CONSULTAS_PARA_QA.md).
