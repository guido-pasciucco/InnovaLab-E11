# Elegir la ubicación haciendo clic en el mapa

**Estado:** para más adelante

## La idea

Además de escribir la dirección, la persona puede hacer clic en el mapa para marcar dónde quiere abrir su emprendimiento. CONCO toma ese punto y averigua a qué zona pertenece.

## Para qué sirve

- **Lugares sin dirección clara.** Un local en una galería, un puesto en una feria o una esquina sin numeración son más fáciles de señalar que de escribir.
- **Corregir un punto aproximado.** Si la dirección elegida cayó un poco corrida, la persona puede ajustar el marcador.
- **Explorar.** Quien todavía no tiene local puede tocar distintas zonas y comparar.

## Qué hay que tener en cuenta

- **Depende de otras partes del backend.** El chequeo «¿este punto es de la Ciudad?» (PR 08) y el contexto de barrio y comuna de USIG (PR 05) ya aceptan un punto del mapa. Esta idea los usa desde el front, así que esos PR tienen que estar mergeados.
- **Un punto no es una dirección.** El servicio de Georef que lee un punto (`/ubicacion`) devuelve provincia, departamento (comuna) y municipio, pero no calle ni altura. Hay que verificar si USIG puede devolver la dirección más cercana; si no, la consulta seguiría sin una dirección escrita.
- **Puntos fuera de la Ciudad.** Si el clic cae fuera de CABA, hay que avisarlo en lugar de seguir con la consulta.
- **En el teléfono.** Tocar con precisión en un mapa chico es difícil; conviene permitir arrastrar el marcador.

## Cuándo hacerla

Después del MVP y una vez mergeados los PR 05 y 08.
