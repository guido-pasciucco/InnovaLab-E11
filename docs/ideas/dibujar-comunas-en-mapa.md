# Dibujar las comunas en el mapa

**Estado:** para más adelante

## La idea

En el mapa del paso 4 se dibuja el límite de la comuna donde queda la dirección, y opcionalmente el de las 15 comunas de la Ciudad, como una capa que se puede prender y apagar.

## Para qué sirve

- **Entender la zona.** La persona ve en qué comuna está y qué tan cerca queda del límite con otra.
- **Dar contexto a los trámites.** Varias gestiones se hacen en la sede de la comuna; ver el límite ayuda a entender por qué le corresponde una sede y no otra.
- **Aprovechar lo que ya existe.** El mapa del front ya sabe mostrar capas de información (`territorialFeatures`, en formato GeoJSON); solo falta que el backend las envíe.

## Qué hay que tener en cuenta

- **Georef entrega los límites solo como shapefile.** El endpoint `/departamentos` (donde están las comunas de CABA, con IDs `02007` a `02105`) devuelve los polígonos únicamente con `formato=shp`, un ZIP que el navegador no puede dibujar. El backend tiene que convertirlo a GeoJSON.
- **Los límites casi no cambian.** Conviene convertirlos una sola vez y guardarlos en el proyecto en lugar de pedirlos a Georef en cada consulta.
- **Peso de la capa.** Los polígonos detallados pueden pesar bastante; puede hacer falta simplificarlos para que el mapa cargue rápido en el teléfono.
- **Otra fuente posible.** El portal de datos de la Ciudad también publica las comunas; vale comparar cuál está más actualizada.

## Cuándo hacerla

Después del MVP. Es independiente de las otras ideas.
