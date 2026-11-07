# OpenStreetMap: sinónimos de actividades y negocios cercanos

Cuatro servicios abiertos sobre los datos de OpenStreetMap (OSM). Juntos permiten pasar de lo que escribe la persona («barbería») a una etiqueta OSM (`shop/hairdresser`) y buscar negocios de ese tipo cerca de una dirección.

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05 (salvo Overpass).

## 1. Ficha

| Servicio | URL | Qué hace | Acceso | Verificación |
|---|---|---|---|---|
| iD tagging schema (traducción `es`) | `https://cdn.jsdelivr.net/npm/@openstreetmap/id-tagging-schema@6/dist/translations/es.json` | Diccionario en español de tipos de lugar con sus sinónimos | Archivo estático, sin clave | `200`, ~593 KB |
| Nominatim | `https://nominatim.openstreetmap.org/search` | Busca lugares por texto («peluqueria, Palermo») | Sin clave. Máximo 1 consulta por segundo. **Exige un User-Agent que identifique la aplicación** | `200` con User-Agent propio; `403` con el de un navegador |
| Photon | `https://photon.komoot.io/api/` | Busca lugares cerca de un punto, filtrando por etiqueta | Sin clave, uso razonable | `200` |
| Overpass API | `https://overpass-api.de/api/interpreter` | Consultas espaciales («cafés a menos de 300 m») | Sin clave | **No verificada**: `406` y servidores saturados (`502`/`504`) |

Licencia de los datos: ODbL 1.0 («© OpenStreetMap contributors»). Hay que citarla.

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| Normalizar la actividad que escribe la persona usando los sinónimos en español | Ítem 1: entrada de la actividad | [RN-01](../../REGLAS_DE_NEGOCIO.md) (pendiente) |
| Mostrar en el mapa negocios del mismo tipo cerca de la dirección | Ítem 4: mapa | [RN-03](../../REGLAS_DE_NEGOCIO.md), [RN-04](../../REGLAS_DE_NEGOCIO.md) |

No es una fuente oficial: sirve como apoyo, no para orientar sobre trámites ([RN-05](../../REGLAS_DE_NEGOCIO.md)).

## 3. Ejemplos

Sinónimos (extracto real de `es.json`, en `es.presets.presets`):

| Etiqueta | Nombre | Sinónimos |
|---|---|---|
| `amenity/cafe` | Cafetería | café, cafetería, té, salón de té, casa de té, bar, restaurante |
| `shop/hairdresser` | Peluquería | peluquería, peluquero, peluquera, barbería, barbero, pelo, corte, salón |
| `shop/kiosk` | Quiosco | kiosko, kiosco, kiosquero, puesto, golosinas, cigarrillo |

Nominatim:

```bash
curl -s -A 'CONCO/0.1 (prototipo InnovaLab)' 'https://nominatim.openstreetmap.org/search?q=peluqueria,+Palermo,+Buenos+Aires&format=jsonv2&limit=1'
```

Devuelve, entre otros, `"category":"shop","type":"hairdresser"` con `lat` y `lon`.

Photon, cafés cerca de un punto:

```bash
curl -s 'https://photon.komoot.io/api/?q=cafe&lat=-34.6&lon=-58.4&osm_tag=amenity:cafe&limit=5'
```

Devuelve un `FeatureCollection` con `"osm_key":"amenity","osm_value":"cafe"`.

## 4. Comportamiento observado

| Caso | Qué pasa |
|---|---|
| Nominatim con User-Agent de navegador | `403` |
| Sinónimos ambiguos | «bar» aparece como sinónimo de cafetería; hay que elegir entre varias etiquetas posibles |
| Cobertura | Depende de lo que cargó la comunidad: puede faltar un negocio o estar cerrado |

## 5. Pendientes y decisiones abiertas

- Política de uso: Nominatim y Photon públicos no son para uso intensivo. Si se usan en producción, conviene caché o un servidor propio.
- Verificar Overpass en otro momento o con otro servidor.

## 6. Fuentes

- [Política de uso de Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
- [Photon](https://photon.komoot.io)
- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [id-tagging-schema](https://github.com/openstreetmap/id-tagging-schema)
