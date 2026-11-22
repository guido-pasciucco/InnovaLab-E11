# Consultas para QA

Preguntas que surgieron al leer el informe de testing y que necesitan respuesta de quien ejecutó las pruebas. Están escritas en lenguaje simple. **Ninguna está respondida todavía**: no damos por seguro lo que no sabemos.

| # | Pregunta | Contexto (por qué surge) | Respuesta de QA |
|---|---|---|---|
| 1 | ¿Las pruebas se hicieron llamando a la API directamente, sin abrir la página en un navegador? | El informe dice que fueron solicitudes de solo lectura y que "no valida interacción visual". Queremos saber si alguien miró una pantalla o solo vio la respuesta del sistema. | Pendiente |
| 2 | ¿Cómo se buscó el trámite "Alta de habilitación de remises" si en la pantalla solo se puede buscar por actividad? | En la interfaz no hay un buscador de trámites por nombre. En la API sí existe esa búsqueda, y el informe muestra una dirección con la palabra "habilitación". Confirmar si se usó la API directamente y qué se escribió. | Pendiente |
| 3 | ¿De dónde salió el identificador del trámite que se usó en la segunda mitad de la prueba? | ¿Vino de la búsqueda anterior, de una lista del catálogo o se copió de otro lugar? | Pendiente |
| 4 | En el primer intento, ¿qué se vio exactamente: un cartel, una pantalla vacía o solo un código de error en la herramienta usada? | Sabemos que el sistema contestó que no encontraba el trámite, pero no sabemos qué vio una persona. | Pendiente |
| 5 | Al repetir la misma consulta, ¿apareció enseguida o pasaron unos segundos? | Ayuda a entender si el dato todavía se estaba cargando o si fue otra cosa. | Pendiente |
| 6 | ¿Se probó en otros momentos y siempre pasó lo mismo, o fue solo esa vez? | Necesitamos saber si es algo que se repite o un caso aislado. | Pendiente |

## Cómo se usa

Cuando QA responda, se completa la última columna con las palabras de QA. Si una respuesta cambia algo de lo que entendimos, se corrige el pendiente correspondiente en [PENDIENTES_QA_Y_FRONTEND.md](PENDIENTES_QA_Y_FRONTEND.md).
