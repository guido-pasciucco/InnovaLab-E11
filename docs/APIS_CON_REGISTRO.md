# APIs que requieren token o registro

Relevamiento del 2026-10-31. En la fase actual se priorizan APIs abiertas (Georef, trámites de la Ciudad, USIG). Las APIs de este documento quedan como opción para más adelante, porque antes de integrarlas hay que crear una cuenta, pedir credenciales o, en algunos casos, pagar.

Cada una se llamó **sin credenciales** para confirmar que exige autenticación. La columna "Sin credenciales" muestra lo que respondió.

## Resumen

| API | Proveedor | Qué aportaría a CONCO | Qué hay que gestionar | Costo | Sin credenciales |
|---|---|---|---|---|---|
| API Transporte | Gobierno de la Ciudad de Buenos Aires | Transporte público cercano a la dirección | Registro gratuito → `client_id` y `client_secret` | Gratuita | `401 Authentication denied` |
| Claude API | Anthropic | Interpretar consultas en lenguaje natural o responder preguntas de seguimiento (RN-01) | Cuenta + API key | Pago por uso | `401 x-api-key header is required` |
| Mapbox (geocoding y mapas) | Mapbox | Mapa base y geocodificación alternativa a Georef | Cuenta + access token | Plan gratuito con límite; luego pago por uso | `401 NO_TOKEN` |
| MapTiler (geocoding y mapas) | MapTiler | Mapa base y geocodificación alternativa | Cuenta + API key | Plan gratuito con límite | `403 Missing key` |
| Google Maps Platform | Google | Geocodificación y lugares cercanos | Cuenta + API key + cuenta de facturación | Pago por uso con crédito mensual | `200` con mensaje de error: requiere API key |
| OpenCage Geocoder | OpenCage | Geocodificación alternativa a Georef | Cuenta + API key | Plan gratuito con límite diario | `401` |
| Web services de ARCA (ex AFIP) | ARCA | Consultar datos de inscripción de una CUIT | Certificado digital asociado a una CUIT con Clave Fiscal; ambiente de homologación para pruebas | Gratuita | El servicio de autenticación (WSAA) responde, pero cada consulta exige un ticket firmado con el certificado |

## Detalle

### API Transporte (GCBA)

Datos abiertos de transporte de la Ciudad: colectivos, subte, ecobici y estacionamiento. Las credenciales se piden con un registro gratuito y se envían como parámetros de la URL. Aporta poco al caso piloto: solo serviría para informar cómo llegar al local.

### Claude API (Anthropic)

Modelo de lenguaje para interpretar una consulta como *"Quiero abrir una cafetería en Av. Corrientes 2500"* y relacionarla con los trámites oficiales. Hoy RN-01 define que la entrada es un buscador y no una IA, y el rol de la IA está pendiente de validar. Las respuestas siempre deberían citar la fuente oficial (RN-05) y no presentarse como determinación legal (RN-04).

### Mapbox y MapTiler

Proveedores de mapas base (tiles) y geocodificación. La propuesta original menciona Mapbox como opción para el mapa. Como alternativa sin registro existen los tiles oficiales de USIG, que ya se verificaron.

### Google Maps Platform

Geocodificación y búsqueda de lugares con buena cobertura. Exige asociar una cuenta de facturación aunque el uso entre en el crédito mensual gratuito, por eso es la opción con más trámite administrativo.

### OpenCage Geocoder

Geocodificador basado en datos abiertos (OpenStreetMap y otras fuentes). Sirve como respaldo si Georef no encuentra una dirección, por ejemplo en calles sin numeración cargada.

### Web services de ARCA (ex AFIP)

Servicios SOAP para consultar el padrón de contribuyentes. Requieren generar un certificado digital desde Clave Fiscal y autenticarse en el WSAA antes de cada consulta. Probablemente queda fuera del MVP, que no gestiona trámites (RN-06).

## Si se integra alguna

- Las credenciales van en `back/.env`, nunca en el código ni en el repositorio.
- En `back/.env.example` se declara la variable **sin el valor real**, por ejemplo `TRANSPORTE_CLIENT_ID=`.
- En `config.py` se declaran con tipo `SecretStr` de Pydantic para que no se impriman en logs.
- Los tests unitarios no usan credenciales reales; los de integración se saltean si la variable no está definida.

## Fuentes

- API Transporte: <https://apitransporte.buenosaires.gob.ar>
- Claude API: <https://docs.anthropic.com>
- Mapbox: <https://docs.mapbox.com/api/search/geocoding/>
- MapTiler: <https://cloud.maptiler.com/account/keys/>
- Google Maps Platform: <https://developers.google.com/maps/documentation/geocoding>
- OpenCage: <https://opencagedata.com/api>
- ARCA web services: <https://www.afip.gob.ar/ws/>
