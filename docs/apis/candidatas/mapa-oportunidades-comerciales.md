# Mapa de Oportunidades Comerciales (MOC)

Datasets históricos de la plataforma MOC del Gobierno de la Ciudad. Por rubro y por zona, dan nivel de riesgo, índices de apertura, cierre y supervivencia, y facturación promedio. La plataforma web está discontinuada; solo quedan los CSV.

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | Gobierno de la Ciudad de Buenos Aires |
| Metadatos | `https://data.buenosaires.gob.ar/api/3/action/package_show?id=mapa-oportunidades-comerciales-moc` |
| Archivos | `https://cdn.buenosaires.gob.ar/datosabiertos/datasets/innovacion-transformacion-digital/mapa-oportunidades-comerciales-moc/` + `rubros.csv`, `zonas.csv`, `apertura.csv`, `cierre.csv`, `demografia.csv`, `zonas-moc.geojson` |
| Tipo | Descarga completa, datos históricos (no se actualizan) |
| Acceso | Sin clave |

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| Contexto del rubro en la zona: riesgo, aperturas y cierres | Fuera del MVP actual | [RN-04](../../REGLAS_DE_NEGOCIO.md) (orientativo, nunca una recomendación) |

## 3. Archivo

`rubros.csv` usa `;` como separador. Columnas principales: `MOC_RUBROS_ID; MOC_ZONAS_ID; RUBRO; NIVEL_RIESGO; FACTURACION_PROM_ACTUAL; INDICE_APERTURA; INDICE_CIERRE; INDICE_SUPERVIVENCIA; ...`

Fila real abreviada:

```
1;1;INSUMOS PARA EL HOGAR;5;1;3;1;0.00;16.67;0.00;...
```

## 4. Comportamiento observado

| Caso | Qué pasa |
|---|---|
| Zonas sin datos | Los valores vienen como el texto `NULL` |
| Rubros | Propios del MOC (`BARES Y CAFES`, `RESTAURANTES`), distintos de los de la AGC y del CLAE |

## 5. Pendientes y decisiones abiertas

- Los datos son viejos: si se muestran, hay que aclarar la fecha.
- Mostrar «riesgo» puede leerse como consejo de negocio; revisar contra [RN-04](../../REGLAS_DE_NEGOCIO.md).

## 6. Fuentes

- [Dataset en BA Data](https://data.buenosaires.gob.ar/dataset/mapa-oportunidades-comerciales-moc)
