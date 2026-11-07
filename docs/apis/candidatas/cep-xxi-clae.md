# CEP XXI: diccionario CLAE y establecimientos productivos

Datasets del Centro de Estudios para la Producción (CEP XXI, Ministerio de Producción de la Nación). El **diccionario CLAE** da cada código de actividad de ARCA con su descripción oficial. El dataset de **establecimientos productivos** da locales reales con su ubicación y su código CLAE.

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | CEP XXI, Ministerio de Producción de la Nación |
| Portal | `https://datos.produccion.gob.ar/api/3/` (CKAN) |
| Diccionario CLAE | `https://cdn.produccion.gob.ar/cdn-cep/clae_agg.csv` |
| Establecimientos | Dataset `distribucion-geografica-de-los-establecimientos-productivos`; archivo principal `https://cdn.produccion.gob.ar/cdn-cep/establecimientos-productivos/distribucion_establecimientos_productivos_sexo.csv` |
| Tipo | Descarga completa. No se puede consultar por registro |
| Acceso | Sin clave |
| Licencia | Establecimientos: CC BY 4.0 |

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| Traducir la actividad al código CLAE que la persona declara en ARCA y AGIP («cafetería» → `561014`) | Ítem 2: orientación | [RN-04](../../REGLAS_DE_NEGOCIO.md) (orientativo) |
| Semilla de textos para la [búsqueda semántica](../../ideas/busqueda-semantica-tramites.md): las descripciones traen ejemplos («Incluye: bares, cervecerías, pubs, cafeterías») | Ítem 2 | [RN-01](../../REGLAS_DE_NEGOCIO.md) (pendiente) |
| Ver qué CLAE declaran los locales reales cerca de la dirección | Fuera del MVP actual | [RN-03](../../REGLAS_DE_NEGOCIO.md) |

**No resuelve** la relación CLAE → trámites.

## 3. Archivos

```bash
curl -s 'https://cdn.produccion.gob.ar/cdn-cep/clae_agg.csv' | head -2
```

Columnas: `clae6, clae6_desc, clae3, clae3_desc, clae2, clae2_desc, letra, letra_desc`.

Fila real:

```
561014,"Servicios de expendio de bebidas en bares (Incluye: bares, cervecerías, pubs, cafeterías)",561, Servicios de expendio de comidas y bebidas,56,Servicios de expendio de alimentos y bebidas,I, SERVICIOS DE ALOJAMIENTO Y SERVICIOS DE COMIDA
```

El archivo de establecimientos trae, entre otras, las columnas `cuit, sucursal, anio, lat, lon, clae6` y `provincia_id` (CABA es `2`).

## 4. Comportamiento observado

| Caso | Qué pasa |
|---|---|
| Descripciones | Muchas incluyen ejemplos entre paréntesis, útiles para buscar por sinónimos |
| Actividades parecidas | Una misma palabra cae en varios códigos: «café» aparece en tostado (`107911`), venta mayorista (`463154`) y bares (`561014`). Hay que elegir entre candidatos |
| CKAN de datos.produccion.gob.ar | `package_search?q=clae` responde 19 datasets. Ningún recurso permite consultas por registro |

## 5. Pendientes y decisiones abiertas

- AGIP usa el nomenclador NAES, no el CLAE. La tabla de equivalencias NAES ↔ CLAE solo está publicada en PDF o Excel (Comisión Arbitral, RG 19/2025).
- El archivo de establecimientos es grande: medir su tamaño antes de decidir si se carga en la base.

## 6. Fuentes

- [Dataset CLAE en datos.gob.ar](https://www.datos.gob.ar/dataset/produccion_d74be529-c469-4cbc-8b30-c14b44833330/archivo/produccion_3eff9730-b215-4768-8474-426736bf8bcd)
- [Comisión Arbitral, RG 19/2025 (NAES)](https://ed.comarb.gob.ar/resoluciones/resoluciones/gr/2025/2025-19.pdf)
