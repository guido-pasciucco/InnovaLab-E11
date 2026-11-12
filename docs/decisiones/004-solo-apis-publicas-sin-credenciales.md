# ADR-004: Solo APIs públicas sin credenciales; las que piden registro quedan para después

**Fecha:** 2026-11-12
**Estado:** Vigente
**Contexto relacionado:** [RN-05](../REGLAS_DE_NEGOCIO.md), [apis/APIS_CON_REGISTRO.md](../apis/APIS_CON_REGISTRO.md), [apis/README.md](../apis/README.md)

## Contexto

CONCO consume APIs externas de gobierno y proveedores. Al relevar el ecosistema (2026-10-31) aparecieron dos categorías: APIs abiertas (Georef, trámites CABA, USIG, Boletín Oficial) y APIs que exigen cuenta, token, certificado o pago (Claude API, Mapbox, Google Maps, ARCA, etc.). La decisión fue qué integrar en el MVP y qué dejar como candidata.

## Decisión

- **Fase actual: solo APIs oficiales, públicas y sin clave.** Las 5 integradas (Georef, Trámites CABA, USIG datos útiles, USIG EPOK, Boletín Oficial CABA) no requieren autenticación.
- **Las APIs con credenciales se documentan pero no se integran**: relevadas con fecha, requerimiento y costo en `apis/APIS_CON_REGISTRO.md`, cada una con la razón por la que queda para después.
- **Candidatas descartadas quedan registradas con motivo**: ~23 APIs evaluadas con llamadas reales y descartadas con razón concreta en `apis/README.md`, para no re-evaluarlas.
- **Si alguna se integra a futuro**: credenciales en `.env` (nunca en código), `SecretStr` de Pydantic, tests sin credenciales reales.

## Por qué

### 1. Velocidad del MVP sin fricción administrativa

Pedir cuentas, certificados o tarjetas de facturación (Google Maps exige cuenta de facturación aunque haya crédito) agrega días de tramitación sin valor para el caso piloto. Las APIs públicas cubren todo el flujo: dirección → coordenadas → comuna → trámites → fuente oficial.

### 2. Alineación con RN-05 y RN-08

El valor del producto es orientación respaldada por fuentes oficiales. Las APIs de gobierno abiertas son exactamente eso. Los proveedores comerciales (Mapbox, Google) aportan mapas/geocoding alternativos que Georef y USIG ya cubren — complejidad extra sin caso de uso nuevo.

### 3. La IA queda condicionada a RN-01

Claude API es la candidata natural para interpretación con IA, pero RN-01 (buscador, no IA) sigue pendiente de validar. Integrar la API antes de resolver la regla sería trabajo prematuro.

### 4. Registro de descartes = no repetir trabajo

Cada descarte quedó documentado con evidencia de llamadas reales (anti-bots de BA Data, endpoints 404 de ARCA, cobertura nula de Wikidata). Eso evita re-descubrir lo mismo en cada ciclo.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Integrar Claude API ya | Bloqueada por RN-01 pendiente + costo por uso + credenciales. |
| Mapbox/MapTiler/Google como mapa base | USIG ya provee tiles oficiales sin clave; Georef cubre geocodificación. |
| ARCA (datos de CUIT) | Requiere certificado digital + Clave Fiscal; el MVP no gestiona trámites (RN-06). |
| APIs de transporte | Aportan "cómo llegar", fuera del caso piloto. |

## Consecuencias

**Positivas:** MVP desbloqueado sin burocracia; cero secretos que gestionar; fuentes 100% oficiales (refuerza RN-05).

**Negativas / deuda aceptada:**

- Si Georef falla o no encuentra una dirección, no hay geocodificador de respaldo (OpenCage queda como candidata documentada).
- Sin LLM, la interpretación de consultas complejas es limitada — trade-off de RN-01.
- Las APIs públicas pueden cambiar o desaparecer (varias candidatas murieron en el relevamiento); los docs con fecha de verificación son la mitigación.

## Qué revisaría esta decisión

- Validación de RN-01 (si se aprueba IA → Claude API entra en evaluación).
- Si Georef muestra fallas en producción → OpenCage/Mapbox como respaldo.
- Si el producto crece más allá del caso piloto (transporte, padrón, etc.) → revisar `apis/APIS_CON_REGISTRO.md`.

## Referencias

- Decisión de fase: `docs/apis/APIS_CON_REGISTRO.md` (relevamiento 2026-10-31)
- Descartes con evidencia: `docs/apis/README.md` (secciones "Candidatas descartadas")
- Integradas: `docs/apis/README.md` tabla de APIs + `docs/apis/*.md`
