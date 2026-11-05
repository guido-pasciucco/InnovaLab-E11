# PR 09/09 — Referencia de las API (docs/09-apis-reference → feature/08-georef-caba-check)

**GitHub:** PR #70 — [chained 09/09] docs: add reference documentation for each external API

**En una frase:** Cerró la cadena con una biblioteca de fichas: una por cada servicio del Gobierno que CONCO consulta, todas con el mismo molde, más guías de recetas para que los próximos servicios no arranquen de cero.

## Qué se hace

1. Armó una biblioteca nueva dentro de la carpeta de documentos de CONCO: una portada con el índice general y una ficha por cada uno de los cinco servicios ya conectados (direcciones y puntos de la Nación, trámites de la Ciudad, datos útiles del mapa, la libreta de sedes cercanas y el Boletín Oficial).
2. Cada ficha sigue el mismo molde: quién lo publica, para qué lo usa CONCO, cómo pedirle cosas, qué pasa en la práctica, cómo está armado por dentro, permisos, tiempo de respuesta y fuente citada.
3. La portada enlaza todo en una tabla: por servicio, qué le compra CONCO, por qué ventanilla entra la gente, si hay llave o pagar y reglas de uso.
4. Anotó lo aprendido en la calle, que es lo que más ahorra después: por ejemplo, que un filtro del sitio del Gobierno corta la consulta según quién pregunta, que algunas respuestas "malas" llegan disfrazadas, y qué candidatos se evaluaron y por qué fueron descartados.
5. Dejó además dos guías al lado de la biblioteca: la receta paso a paso (once fases, de entender antes de pedir hasta entregar revisado) para integrar un servicio nuevo, y la lista de las que piden registro o pago, anotada con lo que contestó cada una cuando se la llamó sin cuenta ni clave.
6. Antes de abrir el PR revisó la columna vertebral verificando sesenta enlaces internos de punta a punta, y reconfirmó con llamadas reales los pedidos de ejemplo que quedaron escritos en las fichas.

## Secciones de código importantes

**La portada del recetario: el índice general** — `docs/apis/README.md`:

```markdown
| API | Proveedor | Para qué la usa CONCO | Endpoints de CONCO | Acceso | Licencia | Documento |
|---|---|---|---|---|---|---|
| Georef | Gobierno Nacional (datos.gob.ar) | Dirección → coordenadas; verificar que un punto esté en CABA | `GET /geolocation/addresses`, `GET /geolocation/location-check` | Sin clave | CC BY 4.0 | [georef.md](georef.md) |
| Trámites CABA (JSON:API) | Gobierno de la Ciudad (buenosaires.gob.ar) | Buscar trámites oficiales y mostrar requisitos, pasos, organismo y enlace | `GET /guidance/procedures`, `GET /guidance/procedures/{procedure_id}` | Sin clave | CC BY 2.5 AR | [tramites-caba.md](tramites-caba.md) |
| USIG datos útiles | USIG, Gobierno de la Ciudad | Barrio, comuna y código postal de una dirección o punto de CABA | `GET /geolocation/address-context`, `GET /geolocation/address-context/by-coordinates` | Sin clave | CC BY 2.5 AR | [usig-datos-utiles.md](usig-datos-utiles.md) |
| USIG EPOK | USIG, Gobierno de la Ciudad | Sedes y subsedes comunales más cercanas a un punto | `GET /geolocation/nearby-offices` | Sin clave (requiere User-Agent propio) | Asume CC BY 2.5 AR | [usig-epok.md](usig-epok.md) |
| Boletín Oficial CABA | Boletín Oficial, Gobierno de la Ciudad | Mostrar una ley o decreto como respaldo de un trámite | `GET /guidance/regulations/{regulation_type}/{number}/{year}` | Sin clave | Normas de acceso público | [boletin-oficial-caba.md](boletin-oficial-caba.md) |
```

Así queda la vitrina de entrada: de un vistazo se ve cada servicio del Gobierno, para qué lo usa CONCO, por qué ventanilla entra la gente y cómo se cita la fuente.

**El molde de las nueve secciones** — `docs/apis/README.md`:

```markdown
| Sección | Qué responde |
|---|---|
| 1. Ficha | Quién la provee, URL base, documentación, acceso, licencia, latencia observada y riesgos |
| 2. Para qué la usa CONCO | Ítem del MVP y reglas de negocio (RN-xx) que cubre |
| 3. Endpoints que llama CONCO | Método, ruta, parámetros, `curl` listo para copiar y respuesta real abreviada |
| 4. Comportamiento observado | Caso → qué devuelve la API → cómo lo maneja CONCO |
| 5. Cómo se integra en CONCO | Módulo de integración, adaptador, endpoint de CONCO y códigos de respuesta |
| 6. Configuración | Variables de entorno y valores por defecto |
| 7. Tests y probe | Fixtures, tests y comando para explorar la API en forma aislada |
| 8. Pendientes | Decisiones abiertas |
| 9. Fuentes | URLs y fecha de verificación |
```

Todas las fichas usan el mismo índice de nueve apartados, así se pueden comparar dos servicios leyendo de punta a punta sin releer todo.

**Una ficha en acción: la del servicio nacional** — `docs/apis/georef.md`:

```markdown
| Dato | Valor |
|---|---|
| Proveedor | Gobierno Nacional (datos.gob.ar) |
| URL base | `https://apis.datos.gob.ar/georef/api` |
| Documentación oficial | <https://datosgobar.github.io/georef-ar-api/> |
| Acceso | Sin clave de acceso |
| Licencia | Creative Commons Atribución 4.0 Internacional (CC BY 4.0) |
| Latencia observada | `/direcciones` ~0,15 s; `/ubicacion` entre 0,02 y 0,12 s |
| Límites | La respuesta informa cabeceras `x-ratelimit-*` (observado: 200 por segundo, 6000 por minuto, 3.000.000 por día) |
| Estabilidad y riesgos | API documentada y estable. Las coordenadas son **aproximadas**. Una latitud fuera de rango responde `500` (CONCO lo evita validando antes) |
```

Así se ve el molde puesto en práctica: datos duros, permisos, cuánto tarda en contestar el servicio y qué riesgos tiene, todo en una tabla chica de la primera hoja. Es la ficha del servicio que la rama 02 conectó y la rama 08 extendió.

**Lo aprendido en la cancha, escrito para que no se olvide** — `docs/apis/usig-epok.md`:

```markdown
| Acceso | Sin clave de acceso; CORS `*`. **Requiere un User-Agent distinto al de curl** |
| Licencia | Sin licencia explícita. Se asume Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), como el resto de los datos de la Ciudad, y se cita la fuente |
| Latencia observada | `reverseGeocoderLugares` ~0,05–0,08 s; `getObjectContent` entre 0,1 y 0,2 s |
| Categorías | 182 publicadas; CONCO usa `sedes_de_comunas` |
| Estabilidad y riesgos | Un filtro BigIP corta la conexión según el User-Agent. Todo responde `200` con `Content-Type: text/javascript`. La categoría `centros_comerciales` está desactualizada (2008) |
```

Es de la ficha de la libreta de la rama 07: guarda lo que costó descubrir a fuerza de llamar al servicio —quién pregunta, cómo pregunta— para que nadie vuelva a descubrirlo a los golpes.

**El recetario para los que vengan después** — `docs/GUIA_INTEGRACION_APIS.md`:

```markdown
## Fase 0 · Entender la API antes de tocar código
...
## Fase 2 · Observar la respuesta real
...
## Fase 7 · Un único error hacia afuera
...
## Fase 10 · Documentar
...
## Fase 11 · Verificar y entregar
...
## Plantilla de archivos para una API nueva
...
## Errores que ya cometimos (y cómo evitarlos)
```

Además de las fichas, la biblioteca trae la receta con la que se integró cada servicio: once fases que empiezan entendiendo el servicio antes de pedirle nada, siguen observando su respuesta real y recién al final arman, prueban y entregan. Cierra con una lista de errores que el equipo ya cometió y cómo evitarlos.

## Por qué importa en la cadena

Con este PR cierra la cadena con una biblioteca de fichas y guías, lista para quien revise, extienda o sume un servicio nuevo.