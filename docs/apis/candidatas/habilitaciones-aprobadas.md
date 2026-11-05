# Habilitaciones aprobadas (AGC)

Dataset de BA Data con los locales que la Agencia Gubernamental de Control (AGC) habilitó en la Ciudad, un archivo por año desde 2015. Cada fila trae el **rubro oficial** con el que se habilitó el local, su dirección, su comuna y las observaciones que la AGC le hizo.

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | Agencia Gubernamental de Control, Gobierno de la Ciudad de Buenos Aires |
| Metadatos | `https://data.buenosaires.gob.ar/api/3/action/package_show?id=habilitaciones-aprobadas` |
| Archivos | `https://cdn.buenosaires.gob.ar/datosabiertos/datasets/agencia-gubernamental-de-control/habilitaciones-aprobadas/habilitaciones-aprobadas<AÑO>.csv` (2020 a 2026), `habilitaciones-2019.csv` y `habilitaciones-2015-a-2018.csv`. También en XLSX |
| Tipo | Descarga completa. **No se puede consultar por registro** (`datastore_active=false`) |
| Acceso | Sin clave |
| Licencia | CC BY 2.5 AR |
| Volumen | 2025: 145.457 filas, 8.566 locales distintos y 530 rubros distintos |

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| Vocabulario de rubros de la AGC: decirle a la persona con qué nombre se habilita su actividad («barbería» → `PELUQUERIA Y BARBERIA`) | Ítem 2: orientación | [RN-04](../../REGLAS_DE_NEGOCIO.md) (orientativo) |
| Contar locales habilitados del mismo rubro en la comuna | Fuera del MVP actual | [RN-04](../../REGLAS_DE_NEGOCIO.md) |
| Resumir las observaciones más comunes de la AGC por rubro | Fuera del MVP actual | [RN-04](../../REGLAS_DE_NEGOCIO.md), [RN-05](../../REGLAS_DE_NEGOCIO.md) |

Los tres usos están desarrollados en [`../../ideas/aprovechar-habilitaciones-aprobadas.md`](../../ideas/aprovechar-habilitaciones-aprobadas.md).

**No resuelve** la relación rubro → trámites: solo da el nombre oficial del rubro.

## 3. Archivo

```bash
curl -s -A 'Mozilla/5.0' 'https://cdn.buenosaires.gob.ar/datosabiertos/datasets/agencia-gubernamental-de-control/habilitaciones-aprobadas/habilitaciones-aprobadas2025.csv' | head -3
```

Columnas: `razon_social, rubro, cod_postal_titular, domicilio, comuna, nropartidamatriz, telefono, disposicion, comentarios`.

Fila real abreviada:

```
"Sergio R. Estilistas S.R.L.","PELUQUERIA Y BARBERIA","1426","NEWBERY, JORGE 1718","14","412860","","DI-2016-18094468-   -DGHP","1.- DEBERA INDICAR HACIA DONDE COMUNICA LA PUERTA GRAFICADA EN EL SALON 01. ART. 2.1.4 CHYV.-"
```

## 4. Comportamiento observado

| Caso | Qué pasa |
|---|---|
| Un local con varias observaciones | Aparece **una fila por observación**, repitiendo el resto de los datos. Hay que agrupar por `razon_social` + `domicilio` para contar locales |
| Comentarios | Texto libre, con saltos de línea dentro del campo. Leerlo con un parser de CSV, no por líneas |
| Rubros | Nombres abreviados y en mayúsculas (`COM.MIN.DE CALZADOS EN GRAL., ART.DE CUERO...`). Un mismo local puede tener varios rubros |
| `package_show` | Responde JSON. `package_search` del mismo CKAN responde `Request Rejected` |
| Datos personales | `razon_social` puede ser el nombre de una persona. CONCO no debería mostrarlo: alcanzan el rubro, la comuna y los comentarios |

## 5. Pendientes y decisiones abiertas

- Los rubros de la AGC no coinciden con los del cuadro de usos de [Ciudad 3D](ciudad-3d.md) («1.5. Alimentación en general y gastronomía»). Falta ver si hay un cruce entre los dos.
- Se actualiza por año: decidir cada cuánto se vuelve a descargar.

## 6. Fuentes

- [Dataset en BA Data](https://data.buenosaires.gob.ar/dataset/habilitaciones-aprobadas)
- [Cómo habilitar tu local comercial en la Ciudad](https://buenosaires.gob.ar/tramites/como-habilitar-tu-local-comercial-en-la-ciudad)
