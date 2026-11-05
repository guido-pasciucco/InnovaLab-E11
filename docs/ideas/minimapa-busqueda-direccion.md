# Minimapa que acompaña la búsqueda de dirección

**Estado:** postergada (después del MVP)

> **Decisión (5/11/2026):** queda como idea y no entra en el MVP. Por ahora el foco está en tener el MVP listo para la pre-presentación; esta mejora se retoma después.

## La idea

Mientras la persona escribe su dirección en el primer paso, aparece un mapa chico debajo del campo. A medida que elige o recorre las sugerencias, el mapa muestra dónde queda cada una.

Hoy el mapa recién aparece en el paso 4, cuando la consulta ya está hecha. Si la persona eligió la dirección equivocada, se entera tarde.

## Para qué sirve

- **Confirmar antes de seguir.** La persona ve con sus propios ojos que el punto está en su cuadra, no en otra parte de la ciudad.
- **Evitar confusiones entre calles parecidas.** Por ejemplo, una misma avenida que pasa por varias comunas, o calles con nombres casi iguales.
- **Dar confianza.** Ver el lugar en el mapa hace sentir que la aplicación entendió bien lo que se le pidió.
- **Ayudar cuando la dirección es aproximada.** En calles sin numeración registrada, el mapa muestra la zona de la calle, y la persona puede darse cuenta de si le sirve o no.

## Cómo se vería

1. La persona empieza a escribir, por ejemplo «Corrientes 25…».
2. Aparece la lista de sugerencias y, debajo, el minimapa.
3. Al pasar por cada sugerencia, el marcador se mueve hacia esa dirección.
4. Al elegir una, el marcador queda fijo y se puede seguir al paso siguiente.
5. Si la dirección no tiene ubicación, el minimapa lo avisa en lugar de mostrar un punto inventado.

## Qué hay que tener en cuenta

- **La primera pantalla se vuelve más pesada.** Hoy carga rápido; un mapa agrega peso y puede demorar en teléfonos o conexiones lentas.
- **Se repite en parte con el paso 4.** Habría que decidir si el paso 4 sigue mostrando el mismo mapa o pasa a enfocarse en la información del territorio.
- **Espacio en el teléfono.** En pantallas chicas, el mapa y la lista de sugerencias compiten por el lugar.
- **La ubicación es aproximada.** El punto lo calcula el servicio nacional de direcciones; conviene aclararlo para que nadie lo tome como una ubicación exacta.

## Cuándo hacerla

No antes de terminar el MVP de la pre-presentación. Después, conviene esperar a ver cómo se usa el buscador actual. Si en las pruebas aparecen personas que eligen la dirección equivocada, esta idea pasa a ser prioridad.
