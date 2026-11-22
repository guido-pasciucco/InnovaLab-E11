# Consultas para testing

Consultas para entender cómo se armó la prueba del 16/11. **No son tareas ni pedidos de cambios**: son preguntas para quien ejecutó el testing, para que las responda cuando pueda. Están escritas en lenguaje simple.

| # | Consulta | Para qué se pregunta | Respuesta |
|---|---|---|---|
| 1 | ¿Las pruebas se hicieron llamando a la API directamente, sin abrir la página en un navegador? | El informe dice que fueron solicitudes de solo lectura y que "no valida interacción visual". Queremos saber si alguien miró una pantalla o solo vio la respuesta del sistema. | Pendiente |
| 2 | ¿La búsqueda del trámite se hizo directamente sobre la API? | El informe muestra una dirección con la palabra "habilitación". Es solo para entender cómo se armó el caso: **no está pensado agregar un buscador de trámites en la pantalla**. | Pendiente |
| 3 | ¿De dónde salió el identificador del trámite que se usó en la prueba del detalle? | ¿Vino de la búsqueda anterior, de una lista del catálogo o se copió de otro lugar? | Pendiente |
| 4 | En el primer intento, ¿qué se vio exactamente: un cartel, una pantalla vacía o solo un código de error en la herramienta usada? | Sabemos que el sistema contestó que no encontraba el trámite, pero no sabemos qué vio una persona. | Pendiente |
| 5 | Al repetir la misma consulta, ¿apareció enseguida o pasaron unos segundos? | Ayuda a entender si el dato todavía se estaba cargando o si fue otra cosa. | Pendiente |
| 6 | ¿Se probó en otros momentos y siempre pasó lo mismo, o fue solo esa vez? | Necesitamos saber si es algo que se repite o un caso aislado. | Pendiente |

## Cómo se usa

Cuando testing conteste, se completa la última columna con sus palabras. Estas consultas **no generan trabajo en el proyecto**: sirven para entender cómo se hizo la prueba y dejar constancia de la respuesta.
