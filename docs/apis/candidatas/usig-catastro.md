# USIG Catastro (parcela por punto)

Servicio de catastro de USIG (Gobierno de la Ciudad). Dado un punto, devuelve la parcela que lo contiene: su identificador (SMP), la dirección oficial y datos del edificio.

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | USIG, Gobierno de la Ciudad de Buenos Aires |
| URL base | `https://epok.buenosaires.gob.ar` |
| Endpoint | `GET /catastro/parcela/` |
| Documentación oficial | No se encontró documentación pública del endpoint |
| Acceso | Sin clave de acceso. **Requiere un User-Agent distinto al de curl**: con el de curl la conexión se corta sin respuesta (igual que [EPOK](../usig-epok.md)) |
| Licencia | Sin licencia explícita. Se asume CC BY 2.5 AR, como el resto de los datos de la Ciudad. El campo `fuente` de la respuesta indica `AGIP (2008)` |
| Latencia observada | ~0,05–0,09 s |
| Estabilidad y riesgos | Responde `200` con `Content-Type: text/javascript` aunque el cuerpo es JSON. Los datos del edificio vienen de AGIP (2008) y pueden estar desactualizados |

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| Obtener el SMP de la dirección, necesario para consultar [Ciudad 3D](ciudad-3d.md) | Ítem 4: ubicación | [RN-03](../../REGLAS_DE_NEGOCIO.md) (la dirección es una ubicación aproximada) |
| Mostrar datos del inmueble (superficie, pisos, si es propiedad horizontal) como contexto | Fuera del MVP actual | [RN-04](../../REGLAS_DE_NEGOCIO.md) (orientativo, no es una determinación legal) |

## 3. Endpoint

### `GET /catastro/parcela/`

| Parámetro | Valor |
|---|---|
| `lng` | Longitud (WGS84) |
| `lat` | Latitud (WGS84) |

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/catastro/parcela/?lng=-58.4055&lat=-34.6040'
```

Respuesta real abreviada:

```json
{
  "direccion": "CORRIENTES AV. 2801",
  "smp": "013-099-018",
  "seccion": "013",
  "manzana": "099",
  "parcela": "018",
  "centroide": [-58.405841404148475, -34.60415646867973],
  "srid": 4326,
  "superficie_total": "3506.00",
  "superficie_cubierta": "24895.00",
  "frente": "61.75",
  "fondo": "56.78",
  "propiedad_horizontal": "Si",
  "pisos_bajo_rasante": "0",
  "pisos_sobre_rasante": "10",
  "unidades_funcionales": "153",
  "locales": "0",
  "fuente": "AGIP (2008)",
  "cantidad_puertas": 28,
  "puertas": [{"calle": "CORRIENTES AV.", "altura": 2801, "codigo_calle": 3174}]
}
```

## 4. Comportamiento observado

| Caso | Qué devuelve |
|---|---|
| Punto dentro de una parcela de CABA | `200` con los datos de la parcela |
| Punto fuera de CABA (`lng=-58.0&lat=-34.0`) | `200` con `{}` (no hay error ni `404`) |
| User-Agent de curl | La conexión se corta sin respuesta (curl sale con código 52) |
| Números como texto | `superficie_total`, `pisos_sobre_rasante`, `locales` y otros llegan como strings |

## 5. Pendientes y decisiones abiertas

- Decidir si CONCO necesita el SMP: solo hace falta si se integra [Ciudad 3D](ciudad-3d.md).
- El punto de Georef es aproximado ([RN-03](../../REGLAS_DE_NEGOCIO.md)): puede caer en la parcela vecina o en la calle. Hay que definir qué hacer cuando la respuesta es `{}`.

## 6. Fuentes

- Llamadas reales a `https://epok.buenosaires.gob.ar/catastro/parcela/` (2026-11-05).
