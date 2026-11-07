# Aprovechar las habilitaciones aprobadas de la AGC

**Estado:** para más adelante (después del MVP)

## La idea

Usar el dataset de [habilitaciones aprobadas](../apis/candidatas/habilitaciones-aprobadas.md), los locales que la AGC habilitó en la Ciudad desde 2015, para darle a la persona tres datos que hoy ninguna API ofrece.

## Para qué sirve

1. **Decir cómo se llama su actividad para la Ciudad.** La persona escribe «barbería» y CONCO muestra: «Para la Ciudad, tu actividad se habilita como **PELUQUERIA Y BARBERIA**». Le sirve para saber qué completar en el trámite real. No dice qué trámites hacer.
2. **Mostrar que la actividad existe en la zona.** Por ejemplo: «En tu comuna hay 12 peluquerías habilitadas en 2025». Da confianza, pero no garantiza nada sobre su local ([RN-04](../REGLAS_DE_NEGOCIO.md)).
3. **Avisar de las observaciones más comunes.** La columna `comentarios` guarda lo que la AGC les observó a locales reales. Por ejemplo, a una peluquería: «DEBERA PRESENTAR EL PLANO REGISTRADO DE VENTILACION MECANICA». Agrupando los comentarios de cada rubro, CONCO podría decir: «A las peluquerías se les suele pedir el plano de ventilación mecánica». Es la propuesta con más valor: esa información no está en ninguna API ni en las fichas de trámites.

## Cómo funcionaría

1. **Ingesta (periódica, offline):** descargar los CSV por año, leerlos con un parser de CSV (los comentarios tienen saltos de línea) y guardar rubro, comuna y comentarios. Agrupar por `razon_social` + `domicilio`, porque cada observación es una fila.
2. **Rubro:** relacionar la actividad con el rubro de la AGC, con la misma [búsqueda semántica](busqueda-semantica-tramites.md) que se piensa usar para los trámites.
3. **Conteo por comuna:** cantidad de locales distintos del rubro en la comuna que devuelve [USIG datos útiles](../apis/usig-datos-utiles.md).
4. **Observaciones frecuentes:** agrupar comentarios parecidos por rubro (por artículo citado o por similitud de texto) y mostrar los más repetidos.

## Qué hay que tener en cuenta

- **No es una determinación legal** ([RN-04](../REGLAS_DE_NEGOCIO.md)): las observaciones se presentan como «suele pedirse», citando la fuente ([RN-05](../REGLAS_DE_NEGOCIO.md)).
- **Datos personales:** `razon_social` puede ser el nombre de una persona. No mostrarlo; alcanzan el rubro, la comuna y los comentarios.
- **Comentarios en texto libre:** abreviados y con referencias a artículos («ART. 4.6.6.2 DEL CE»). Agruparlos bien es el trabajo más difícil.
- **Rubros distintos entre fuentes:** los de la AGC no coinciden con los de [Ciudad 3D](../apis/candidatas/ciudad-3d.md) ni con el [CLAE](../apis/candidatas/cep-xxi-clae.md).
- **Volumen:** 2025 tiene unas 145.000 filas; todos los años juntos conviene tenerlos en una base, no en memoria.
