# Qué cambió en ConCo: antes y después

Resumen para todo el equipo de los cambios hechos a partir de las pruebas de QA del 16/11 y la revisión de la página. No hace falta saber programar para leerlo.

## De un vistazo

| Tema | Antes | Después |
|---|---|---|
| Trámite que a veces no aparecía | Un mismo trámite podía decir «no existe» y al rato aparecer. | ConCo vuelve a intentar antes de responder. Solo dice «No encontramos ese trámite.» si de verdad no está. |
| Mensajes de error | A veces se veían textos técnicos en inglés o difíciles de entender. | Siempre un mensaje claro en español, que dice qué pasó y qué hacer. |
| Primera búsqueda lenta | Después de un rato sin uso, la primera búsqueda tardaba mucho. | Queda listo el aviso automático que mantiene despierto el servidor (falta activarlo, ver abajo). |
| Errores al completar el formulario | El aviso aparecía lejos del campo o con texto técnico. | El aviso aparece al lado del campo que hay que corregir, y la actividad muestra cuántas letras llevás (por ejemplo `12/100`). |
| «Puede aplicar» | No se entendía qué quería decir. | Una nota explica que depende de las respuestas y que hay que contestar las preguntas. |
| Trámites descartados | Decía «Descartamos 2 trámites», sin decir cuáles. | Dice cuáles: «Descartamos: Habilitación exprés y Trámite de bajo impacto.» |
| Respuestas a las preguntas | Se perdían al cambiar de paso o recargar la página. | Se conservan. |
| Dirección de cada paso | Toda la página tenía la misma dirección. No se podía compartir ni volver atrás. | Cada paso tiene su dirección (`/consulta`, `/analisis`, `/orientacion`, `/mapa`, `/asistente`). Funciona el botón Atrás del navegador y recargar te deja donde estabas. |
| Barra de pasos | Era solo decorativa. | Se puede tocar para ir a un paso. Los pasos que todavía no se pueden usar se ven desactivados. Funciona con teclado y con lector de pantalla. |
| Búsquedas anteriores | No quedaba registro. Había que escribir todo de nuevo. | Panel «Búsquedas recientes» con las últimas búsquedas. «Ver» las repite con un clic. |
| Ejemplos en la página de inicio | Había un bloque «Probá con un ejemplo». | Se sacó. |
| Enlaces del pie de página | Algunos no llevaban a ningún lado. | Los que tienen destino funcionan. Los que todavía no tienen página dicen «(próximamente)». |

## Cada cambio, contado simple

### 1. El trámite que aparecía y desaparecía

- **Antes:** en la prueba de QA, un trámite respondió «no existe» y, repitiendo lo mismo, apareció bien. La fuente oficial de la Ciudad a veces falla un instante, y ConCo lo tomaba como «no existe».
- **Después:** si la fuente falla, ConCo prueba una vez más antes de responder. Ahora se distinguen tres situaciones:
  - El trámite no existe: «No encontramos ese trámite.»
  - La fuente oficial no responde: «No pudimos consultar los trámites. Intentá de nuevo.»
  - Los datos todavía se están cargando: «Estamos cargando los trámites, volvé a intentar.»
- **Extra:** cada respuesta lleva un código de seguimiento. Si alguien reporta un problema, con ese código se encuentra el pedido exacto en los registros del servidor.

### 2. La primera búsqueda que tardaba

- **Antes:** el servidor gratuito se «duerme» cuando nadie lo usa. La primera persona que entraba esperaba bastante.
- **Después:** está todo preparado para que un servicio gratuito (cron-job.org) visite el servidor cada 10 minutos y no lo deje dormirse. **Todavía hay que crear esa tarea** (ver «Qué falta»).

### 3. Mensajes que se entienden

- **Antes:** si escribías algo muy corto o solo espacios, podía aparecer un error técnico.
- **Después:** la página revisa lo escrito antes de buscar y avisa al lado del campo, por ejemplo «Escribí al menos 3 caracteres». Si algo falla sin aviso, aparece un mensaje amable con el botón «Reintentar» en lugar de una pantalla rota.

### 4. Entender «Puede aplicar»

- **Antes:** algunos trámites decían «Puede aplicar» sin más explicación. Además, el aviso de descartados no decía cuáles eran, y las respuestas a las preguntas se borraban al recargar.
- **Después:** hay una nota al lado de «Puede aplicar», el aviso nombra los trámites descartados y las respuestas se mantienen.

### 5 y 6. Navegar por pasos

- **Antes:** la dirección de la página no cambiaba, así que no se podía volver atrás ni recargar sin perder todo. La barra de pasos no se podía usar.
- **Después:** cada paso tiene su dirección y la barra de pasos se puede tocar. Si alguien entra directo a un paso que necesita una búsqueda (por ejemplo `/mapa`) sin haberla hecho, la página lo lleva al inicio.

### 7 y 8. Búsquedas recientes

- **Antes:** cada visita empezaba de cero.
- **Después:** en el primer paso aparece «Búsquedas recientes» con actividad, dirección y hace cuánto se buscó. En computadora es una tarjeta al costado; en el celular, una sección que se abre y se cierra.
  - Se muestran hasta 5; el resto está en «Ver todas». Se guardan hasta 10 y no se repiten.
  - **Ver** completa el formulario y repite la búsqueda.
  - **Actualizar** (arriba, en la barra de la consulta) vuelve a buscar por si cambió algo.
  - **Limpiar historial** borra todo.
  - **Privacidad:** el historial queda solo en ese navegador. No se manda a ningún servidor.

### 9. Ejemplos de la página de inicio

- **Antes:** había un bloque «Probá con un ejemplo».
- **Después:** se sacó, como se pidió.

## Qué falta y quién lo hace

| Pendiente | Quién |
|---|---|
| Crear la tarea en cron-job.org que visite el servidor cada 10 minutos, y acordar cuánto puede tardar como máximo la primera búsqueda. Los pasos están en [NOTAS_DE_IMPLEMENTACION.md](NOTAS_DE_IMPLEMENTACION.md). | Dueño del producto |
| Revisar y aprobar las reglas que deciden cuándo aplica cada trámite. La tabla está lista para firmar en las notas. | Responsable del catálogo |
| Definir a dónde llevan Centro de ayuda, Accesibilidad, Términos, Privacidad y redes sociales. | Dueño del producto |
| Después de publicar: abrir `/mapa` directo en la página publicada y repetir la prueba del trámite que fallaba (RUN-034). | QA |

## Cómo probarlo

1. Entrar a la página, hacer una búsqueda y avanzar hasta el mapa.
2. Recargar: tiene que seguir en el mapa.
3. Tocar Atrás en el navegador: tiene que volver al paso anterior.
4. Volver al inicio: la búsqueda tiene que aparecer en «Búsquedas recientes».
5. Escribir una sola letra en la dirección: tiene que aparecer el aviso al lado del campo.
