# USIG datos útiles

Servicio `datos_utiles` de la Unidad de Sistemas de Información Geográfica (USIG) del Gobierno de la Ciudad. CONCO lo usa para informar barrio, comuna y códigos postales de una dirección o de un punto de CABA.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | USIG, Gobierno de la Ciudad de Buenos Aires |
| URL base | `https://ws.usig.buenosaires.gob.ar` |
| Endpoint | `GET /datos_utiles` |
| Documentación oficial | <http://usig.buenosaires.gob.ar/apis/> (por `https` el certificado del sitio de documentación no valida; la API sí funciona por `https`) |
| Acceso | Sin clave de acceso; CORS `*` |
| Licencia | Creative Commons Reconocimiento 2.5 Argentina (CC BY 2.5 AR), según el pie de la documentación |
| Latencia observada | Entre 0,3 y 0,5 s |
| Estabilidad y riesgos | Servidor antiguo. **Todas las respuestas llegan con `200`, incluso los errores**, y el `Content-Type` no es confiable. La normalización de calles es estricta |

## 2. Para qué la usa CONCO

| Uso | MVP | Reglas |
|---|---|---|
| Barrio, comuna y código postal de una ubicación | Ítem 4: contexto de la ubicación aproximada | [RN-02](../REGLAS_DE_NEGOCIO.md) (si USIG no la ubica en la Ciudad, responde `404`), [RN-05](../REGLAS_DE_NEGOCIO.md) (cita la fuente) |
| No exponer catastro ni zonificación | Excluido del MVP, ítem 2 | [RN-04](../REGLAS_DE_NEGOCIO.md): `seccion_catastral` y `codigo_de_planeamiento_urbano` se ignoran al interpretar la respuesta |

## 3. Endpoints que llama CONCO

### `GET /datos_utiles`

| Modo | Parámetros |
|---|---|
| Por dirección | `calle` (sin espacios sobrantes) y `altura` |
| Por coordenadas | `x` (longitud) e `y` (latitud), en WGS84 |

```bash
curl -s 'https://ws.usig.buenosaires.gob.ar/datos_utiles?calle=Corrientes&altura=2500'
curl -s 'https://ws.usig.buenosaires.gob.ar/datos_utiles?x=-58.401981&y=-34.604792'
```

Respuesta real por dirección (`back/tests/fixtures/usig/datos_utiles_corrientes_2500.json`, abreviada):

```json
{
  "comuna": "Comuna 3",
  "barrio": "Balvanera",
  "comisaria": "7",
  "distrito_escolar": "Distrito Escolar   I",
  "seccion_catastral": "09",
  "codigo_de_planeamiento_urbano": "",
  "partido_amba": "",
  "codigo_postal": "1046",
  "codigo_postal_argentino": "C1046AAP"
}
```

Por coordenadas llegan los mismos campos **sin** `codigo_postal` ni `codigo_postal_argentino`.

## 4. Comportamiento observado

| Caso | Qué devuelve USIG | Cómo lo maneja CONCO |
|---|---|---|
| Dirección encontrada | `200`, `Content-Type: text/javascript`, cuerpo JSON | Se interpreta el cuerpo sin mirar el `Content-Type` → `200` |
| Por coordenadas | `200`, `Content-Type: application/json`, sin códigos postales | `postal_code` y `argentine_postal_code` en `null` |
| Calle inexistente o altura fuera de rango (`Corrientes 99999`, `Corrientes 0`, `Rivadavia 20000`, `Avenida de Mayo 500`) | `200` `text/plain`: `ERROR: No se pudo normalizar o geocodificar la dirección.` | El cliente devuelve `None` → `404` |
| Faltan parámetros, `calle` sin `altura`, o `x`/`y` no numéricos | `200` `text/html` con la página de ayuda | `UsigError` → `502` (CONCO valida antes: `422`) |
| Punto fuera de CABA (Moreno) | `200` JSON con los campos de CABA vacíos y `partido_amba`/`localidad_amba` completos | `comuna` o `barrio` vacíos → `None` → `404` |
| Punto en el río o latitud y longitud invertidas | `200` JSON con todo vacío | `404` |
| Código postal vacío | Cadena vacía | `null` en la respuesta de CONCO |
| Timeout o error HTTP | — | `UsigError` → `502` |

Dirección no encontrada (`back/tests/fixtures/usig/datos_utiles_calle_inexistente.txt`):

```text
ERROR: No se pudo normalizar o geocodificar la dirección.
```

Punto fuera de CABA (`back/tests/fixtures/usig/datos_utiles_coordenadas_fuera_de_caba.json`, abreviado):

```json
{"comuna": "", "barrio": "", "seccion_catastral": "", "partido_amba": "Moreno", "localidad_amba": "Mariano Moreno"}
```

## 5. Cómo se integra en CONCO

| Capa | Ubicación | Qué hace |
|---|---|---|
| Cliente | [`back/src/conco/integrations/usig/client.py`](../../back/src/conco/integrations/usig/client.py) | `get_datos_utiles_by_address(street, number)` y `get_datos_utiles_by_coordinates(longitude, latitude)`; clasifica por el cuerpo |
| Modelo | [`back/src/conco/integrations/usig/models.py`](../../back/src/conco/integrations/usig/models.py) | `UsigDatosUtiles`: solo `comuna`, `barrio`, `codigo_postal`, `codigo_postal_argentino` |
| Error | `UsigError` | Página de ayuda HTML, cuerpo no JSON, error HTTP o timeout |
| Adaptador | [`back/src/conco/geolocation/infrastructure.py`](../../back/src/conco/geolocation/infrastructure.py) | `UsigAddressContextProvider` |
| Error de dominio | [`back/src/conco/geolocation/domain.py`](../../back/src/conco/geolocation/domain.py) | `AddressContextError` |

### `GET /geolocation/address-context`

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `street` | Sí | Entre 2 y 100 caracteres, no solo espacios |
| `number` | Sí | Entero entre 1 y 99999 |

### `GET /geolocation/address-context/by-coordinates`

| Parámetro | Obligatorio | Validación |
|---|---|---|
| `latitude` | Sí | Entre -90 y 90 |
| `longitude` | Sí | Entre -180 y 180 |

Se validan solo los rangos generales: un recuadro de CABA duplicaría lo que USIG ya sabe y podría recortar direcciones del borde.

| Código | Cuándo |
|---|---|
| `200` | `{"context": {"neighborhood", "commune", "postal_code", "argentine_postal_code"}, "source": {...}}` |
| `404` | USIG no encuentra la dirección o la ubicación está fuera de CABA |
| `422` | Parámetros inválidos |
| `502` | USIG no respondió o devolvió algo inesperado |

## 6. Configuración

| Variable | Por defecto |
|---|---|
| `USIG_BASE_URL` | `https://ws.usig.buenosaires.gob.ar` |
| `USIG_DOCS_URL` | `http://usig.buenosaires.gob.ar/apis/` (URL que se cita como fuente) |
| `USIG_TIMEOUT_SECONDS` | `10.0` |

Definidas en [`back/src/conco/config.py`](../../back/src/conco/config.py).

## 7. Tests y probe

| Tipo | Ruta |
|---|---|
| Fixtures | `back/tests/fixtures/usig/`: `datos_utiles_corrientes_2500.json`, `datos_utiles_coordenadas_corrientes_2500.json`, `datos_utiles_coordenadas_fuera_de_caba.json`, `datos_utiles_calle_inexistente.txt`, `datos_utiles_sin_parametros.html` |
| Unitarios | `back/tests/unit/usig/test_client.py`, `back/tests/unit/geolocation/test_usig_context_provider.py`, `back/tests/unit/geolocation/test_address_context_api.py` |
| Integración (API real) | `back/tests/integration/usig/test_client.py`, `back/tests/integration/geolocation/test_address_context_api.py` |

```bash
uv run python scripts/probes/usig.py Corrientes 2500
uv run python scripts/probes/usig.py --coords -34.604792 -58.401981   # latitud longitud
```

## 8. Pendientes y decisiones abiertas

- Agregar `USIG_*` a `back/.env.example` (tarea del usuario).
- Encadenar Georef → USIG (coordenadas de `/geolocation/addresses` hacia `/by-coordinates`) o usar el normalizador de USIG para aceptar direcciones en texto libre. Requiere decisión de producto.
- Los demás campos de `datos_utiles` (comisaría, área hospitalaria, distrito escolar) quedaron fuera de alcance.

## 9. Fuentes

- Documentación: <http://usig.buenosaires.gob.ar/apis/>
- Servicio: <https://ws.usig.buenosaires.gob.ar/datos_utiles>
- Seguimiento: [usig-integration](../../odd/tasks/usig-integration.md)

Fecha de verificación: 2026-10-31.
