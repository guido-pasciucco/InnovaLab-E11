# APIs candidatas

APIs probadas con llamadas reales que **todavía no están integradas** en CONCO. Cada documento registra qué devuelve la API, cómo se comportó y para qué podría servir, para decidir si se integra.

Cuando una candidata se integra, su documento pasa a [`../`](../README.md) con la estructura completa de 9 secciones.

| API | Proveedor | Para qué podría servir | Verificada | Documento |
|---|---|---|---|---|
| USIG Catastro | USIG, Gobierno de la Ciudad | Punto → parcela (SMP), superficie, pisos y locales | 2026-11-05 | [usig-catastro.md](usig-catastro.md) |
| Ciudad 3D (Código Urbanístico) | USIG, Gobierno de la Ciudad | Parcela → rubros permitidos y sus condiciones, distrito, protección patrimonial y afectaciones | 2026-11-05 | [ciudad-3d.md](ciudad-3d.md) |
| Habilitaciones aprobadas (CSV) | AGC, Gobierno de la Ciudad | Nombres oficiales de rubro de la AGC, locales habilitados por comuna y observaciones de la AGC | 2026-11-05 | [habilitaciones-aprobadas.md](habilitaciones-aprobadas.md) |
| Diccionario CLAE y establecimientos (CSV) | CEP XXI, Ministerio de Producción | Actividad → código CLAE de ARCA; CLAE de los locales reales cercanos | 2026-11-05 | [cep-xxi-clae.md](cep-xxi-clae.md) |
| OpenStreetMap (iD tagging schema, Nominatim, Photon, Overpass) | Comunidad OSM | Sinónimos en español de actividades y negocios similares cercanos en el mapa | 2026-11-05 | [openstreetmap.md](openstreetmap.md) |
| Mapa de Oportunidades Comerciales (CSV históricos) | Gobierno de la Ciudad | Riesgo, aperturas y cierres por rubro y zona | 2026-11-05 | [mapa-oportunidades-comerciales.md](mapa-oportunidades-comerciales.md) |

## Por revisar

Encontradas el 2026-11-05 pero sin verificar a fondo. No tienen documento propio todavía.

| Fuente | Qué podría aportar | Estado |
|---|---|---|
| SAIJ (`https://www.saij.gob.ar/busqueda?o=0&p=10&f=Total&v=colapsada&r=titulo:habilitacion`) | Normativa relacionada con cada trámite. Responde JSON sin documentación oficial | Responde `200`. El filtro por jurisdicción CABA devolvió 0 resultados: falta encontrar el parámetro correcto |
| BA Data: `relevamiento-usos-suelo`, `carteles-luminosos`, `permisos-uso-espacio-publico-area-gastronomica`, `oferta-establecimientos-gastronomicos`, `calzada-gastronomica`, `emprendedores` | Usos del suelo, permisos de publicidad y de veredas | Aparecen en `package_list`; `package_show` no respondió JSON en la prueba (bloqueo anti-bots) |

## Flujo posible

```
Dirección ──Georef──▶ punto ──Catastro──▶ SMP ──Ciudad 3D──▶ área de mixtura de usos
                                                           ──▶ catalogación, afectaciones
rubro + mixtura ──Ciudad 3D (cuadro de usos)──▶ permitido / condiciones
```

Las dos usan el mismo servidor que [USIG EPOK](../usig-epok.md) (`epok.buenosaires.gob.ar`) y comparten su filtro por User-Agent. Ninguna tiene documentación pública: las rutas salen del código del visor Ciudad 3D.

## Lo que sigue sin resolver

El relevamiento del 2026-11-05 confirmó que **ninguna fuente pública traduce una actividad en su rubro y en sus trámites**. Las candidatas de CSV y de OSM dan los nombres oficiales de la actividad (rubro de la AGC, código CLAE) y sinónimos, pero no los trámites.

Ciudad 3D responde si un **rubro** oficial está permitido en una parcela, pero ninguna API traduce la actividad que escribe la persona («cafetería») a ese rubro («1.5. Alimentación en general y gastronomía»). Esa traducción, y la relación «rubro → trámites», siguen siendo una decisión de producto ([RN-01](../../REGLAS_DE_NEGOCIO.md)); ver [`../../ideas/busqueda-semantica-tramites.md`](../../ideas/busqueda-semantica-tramites.md).
