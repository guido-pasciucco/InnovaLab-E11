# Guardar en caché las búsquedas de direcciones

**Estado:** para más adelante

## La idea

El backend recuerda por un tiempo las respuestas de Georef. Si alguien busca algo que ya se buscó hace poco, responde con lo guardado en lugar de volver a preguntarle a Georef.

## Para qué sirve

- **Protegerse de los límites de Georef.** La API está en estado *alpha* y sus cuotas de uso sin autenticación no están definidas. El autocompletado hace un pedido cada vez que la persona deja de escribir, así que los pedidos se acumulan rápido.
- **Responder más rápido.** Una respuesta guardada sale al instante; Georef puede tardar segundos.
- **Seguir funcionando si Georef falla un rato.** Las direcciones ya buscadas siguen disponibles aunque el servicio esté caído.

## Qué hay que tener en cuenta

- **Puede que se reutilice poco.** Muchas búsquedas del autocompletado son textos a medio escribir y únicos. Antes de construirla conviene medir cuántas búsquedas se repiten.
- **Normalizar antes de guardar.** «corrientes 2500» y «Corrientes  2500» tienen que dar la misma entrada; el cliente de Georef ya quita los espacios sobrantes.
- **Dónde guardarla.** En memoria del proceso es lo más simple, pero se pierde al reiniciar y no se comparte entre varias instancias; un servicio como Redis resuelve eso a cambio de más infraestructura.
- **Cuánto tiempo guardar.** Las direcciones cambian poco, así que un tiempo largo (horas o días) es razonable; los errores no se guardan.
- **Otra opción.** Georef ofrece un token con cuotas más altas (pidiéndolo a datosargentina@sicyt.gob.ar); puede ser suficiente sin caché.

## Cuándo hacerla

Cuando haya uso real para medir, o antes si Georef empieza a rechazar pedidos.
