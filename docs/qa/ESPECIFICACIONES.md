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

### 4. Entender mejor los trámites "que pueden aplicar" (QA-07)

**Cómo se entendió (ejemplo concreto):** en la pantalla de Orientación aparecen cinco preguntas —¿Vas a contratar personal?, ¿El local tiene menos de 200 m²?, ¿Vas a poner un cartel, marquesina o toldo?, ¿Está en un área de protección histórica?, ¿Continuás un local ya habilitado?— y abajo una lista de trámites. Algunos dicen **TRÁMITE OFICIAL** y otros **PUEDE APLICAR**. Al contestar *"Sí"* a *"¿Vas a contratar personal?"*, la lista cambia y aparece un aviso: *"Descartamos 2 trámites según tus respuestas"*. El problema es que nadie explica qué significa *PUEDE APLICAR*, ni **cuáles** eran esos 2 trámites, ni por qué desaparecieron. Parece magia.

**Lo que ya existe** (no rehacer): las cinco preguntas se muestran, la etiqueta *PUEDE APLICAR* existe y el aviso dice **cuántos** trámites se descartaron.

**Lo que pide cambiar:**

1. Al lado de **PUEDE APLICAR**, un textito: *"Este trámite depende de tus respuestas. Contestá las preguntas de arriba para saber si te aplica."*
2. En vez de *"Descartamos 2 trámites"*, decir **cuáles**: *"Descartamos: Habilitación exprés y Trámite de bajo impacto."*
3. Que las respuestas **no se pierdan** al cambiar de sección ni al recargar la página. Hoy siguen ahí porque todo vive en el mismo componente, pero al meter rutas se pueden borrar: hay que definirlo.
4. Que alguien que conoce el catálogo confirme que las reglas son correctas (por ejemplo, que contratar personal realmente haga aplicar cierto trámite).

**Por qué importa:** si no se explica, la persona no sabe si tiene que hacer ese trámite o no, y ve cómo la lista cambia sin entender por qué.

**Cómo sabremos que está listo:** contestando las cinco preguntas, la pantalla explica cada etiqueta, nombra los trámites descartados, y las respuestas siguen ahí después de navegar y recargar. Las reglas están aprobadas por el responsable del catálogo.

**Lo que NO se hace:** cambiar las reglas del catálogo por cuenta propia; primero las confirma el responsable.

**Contexto que lo aclaró:** el recorrido concreto con las cinco preguntas y el aviso de "Descartamos 2 trámites" sin nombres, que mostró exactamente dónde se queda corta la pantalla actual.

**Confirmado:** 22/11/2026.

### 5. Que cada paso tenga su propia dirección (FE-01)

**Cómo se entendió:** hoy la app es una sola página. Los pasos —Consulta, Análisis, Orientación, Mapa, Asistente— son como pestañas que se prenden y apagan adentro de la misma pantalla: la barra de dirección del navegador siempre dice lo mismo, aunque estés en el Mapa. El paso se guarda en una variable dentro del componente principal (`front/src/App.tsx:38`), no en la dirección.

**Por qué importa:** no se puede copiar un link a "Orientación" y mandarlo porque esa dirección no existe; el botón atrás del navegador no devuelve al paso anterior; y si recargás la página, volvés al inicio en vez de seguir donde estabas.

**Lo que pide el cambio:** que cada paso tenga su dirección —`/consulta`, `/analisis`, `/orientacion`, `/mapa`, `/asistente`— agregando una librería de rutas para React (`react-router-dom`). Así se puede compartir un paso, usar el botón atrás y recargar sin perder el lugar.

**Detalle importante:** si alguien entra directo a `/orientacion` sin haber hecho una consulta, no hay resultado para mostrar. Hay que hacer que lo mande al inicio: no dejar entrar a una página que necesita datos que todavía no existen.

**Ojo con el deploy:** hoy no hay configuración de reescritura en Vercel (`front/vercel.json` no existe), así que las direcciones nuevas podrían dar "página no encontrada" al abrirlas directo. Hay que verificarlo.

**Cómo sabremos que está listo:** al caminar por los pasos, la barra de dirección cambia; el botón atrás funciona; recargar en `/mapa` te deja en el mapa si hay una consulta hecha; y entrar a `/orientacion` sin consulta te lleva al inicio.

**Lo que NO se hace:** todavía no hacer clickeables los pasos de la barra (es el siguiente ítem), ni tocar el diseño.

**Confirmado:** 22/11/2026 (el dueño indicó "dale" para registrar y continuar).

### 6. Que se pueda hacer clic en los pasos (FE-02)

**Cómo se entendió:** la barra de pasos —Consulta, Análisis, Orientación, Mapa, Asistente— es solo dibujo: son cajitas con números que no responden al clic (`front/src/App.tsx:206`). Los únicos botones que cambian de paso son los de abajo (*"Ver mapa →"*, *"← Volver a orientación"*) y las pestañitas chicas que aparecen cuando ya hay una consulta. Los enlaces del pie de página son falsos: parecen links, pero no llevan a ningún lado (`front/src/App.tsx:437-460`).

**Por qué importa:** si el paso está a la vista, uno espera poder apretarlo. Hoy no pasa nada y da la sensación de que la interfaz está incompleta.

**Lo que pide el cambio:** que las cajitas sean clickeables de verdad y lleven a su dirección. Depende de la especificación 5: primero las direcciones, después los clics. Los enlaces internos y del pie también deben llevar a un lugar real en vez de no hacer nada.

**Reglas de habilitación:**

- si todavía no se hizo la consulta, no tiene sentido ir a Orientación, Mapa o Asistente porque no hay nada que mostrar;
- el paso en el que estás va marcado;
- los pasos ya visitados se pueden apretar;
- los que vienen después y aún no se pueden usar se ven, pero están deshabilitados.

**Cómo sabremos que está listo:** se pueden recorrer los pasos apretando la barra; el teclado funciona (Tab y Enter); y un lector de pantalla anuncia en qué paso estás y cuáles no están disponibles.

**Lo que NO se hace:** cambiar el diseño de la barra ni agregar pasos nuevos.

**Confirmado:** 22/11/2026.

### 7. Ver las búsquedas anteriores en la misma pantalla (FE-03)

**Cómo se entendió:** hoy, cuando se hace una consulta y después se quiere repetir o ver qué se buscó, no hay forma: la pantalla no guarda nada. Si se recarga o se aprieta *"Nueva consulta"*, se borra todo (`startOver()` en `front/src/App.tsx:123`). No hay `localStorage`, `sessionStorage` ni `indexedDB` en `front/src/`.

**Lo que pide el cambio:** un panel **"Búsquedas recientes"** dentro del paso 1 (Consulta), abajo del formulario. En escritorio, una tarjetita al costado; en móvil, una sección plegable. No es una página nueva: está en la misma pantalla.

```text
Búsquedas recientes (3)                    [Limpiar]
Peluquería · Av Corrientes 2500     hace 2 h   [Ver]
Barbería · Córdoba 1234             ayer       [Ver]
Cafetería · Corrientes 1500         12/11      [Ver]
```

Al apretar un registro se rellena el formulario con esa actividad y dirección y se abre el resultado. Un botón **"Actualizar"** permite volver a consultar por si cambió algo. Se muestran hasta 5 ítems; el resto queda detrás de *"Ver todas"*. Si no hay historial, el panel no se muestra.

**Por qué ese formato y no otro:** se descartó un desplegable dentro del buscador (mezcla las sugerencias de la API con las búsquedas propias), una página `/historial` aparte (rompe el pedido de "misma pantalla") y una ventanita emergente (molesto para uso repetido). Se reutilizan los estilos que ya existen (`panel`, `query-pill`, `chip`, `secondary`).

**Cómo sabremos que está listo:** se ven las búsquedas sin salir de la pantalla de consulta, se puede limpiar el historial y funciona igual en celular y computadora.

**Lo que NO se hace todavía:** guardar las búsquedas de forma permanente para que sobrevivan a un recarque (es el siguiente ítem). Este punto depende de la especificación 5 para poder abrir el resultado.

**Confirmado:** 22/11/2026.

## Cómo se usa

1. Te explico un pendiente, de a uno, en lenguaje simple y con el mismo detalle que vas a ver acá.
2. Si te queda claro, me decís «lo entendí» y, si querés, qué fue lo que te lo aclaró.
3. Solo en ese momento escribo la entrada acá, con su contexto y las decisiones que surgieron.

Los pendientes que todavía no se confirmaron están en [PENDIENTES_QA_Y_FRONTEND.md](PENDIENTES_QA_Y_FRONTEND.md). Las dudas para testing están en [CONSULTAS_PARA_QA.md](CONSULTAS_PARA_QA.md).
