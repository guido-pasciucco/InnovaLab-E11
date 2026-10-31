# Boletín Oficial de la Ciudad de Buenos Aires

API REST del Boletín Oficial de la Ciudad, donde se publica cada norma de CABA. CONCO la usa para mostrar una ley o un decreto (resumen, organismo, fecha, edición del Boletín y PDF) como **referencia** de la base normativa de un trámite.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | Boletín Oficial de la Ciudad de Buenos Aires, Gobierno de la Ciudad |
| URL base | `https://api-restboletinoficial.buenosaires.gob.ar` |
| Documentación oficial | <https://api-restboletinoficial.buenosaires.gob.ar/api/doc/> |
| Sitio que se cita como fuente | <https://boletinoficial.buenosaires.gob.ar> |
| Acceso | Sin clave de acceso |
| Licencia | Sin licencia explícita. Las normas son actos oficiales de publicación obligatoria y acceso público; se cita la fuente |
| Latencia observada | Entre 0,16 y 0,38 s |
| Tipos de norma | `tipoNorma=1` (Ley) y `tipoNorma=2` (Decreto), según `GET /obtenerFiltrosDeBusqueda` |
| Estabilidad y riesgos | Los filtros van **dentro de la ruta**, no en la query string. Errores con `200` (cuerpo HTML). `"normas": 0` es un número, no una lista. Un mismo tipo, número y año puede ser más de una norma |

## 2. Para qué la usa CONCO

| Uso | MVP | Reglas |
|---|---|---|
| Mostrar una ley o un decreto de la Ciudad con enlace al documento oficial (por ejemplo, Ley 6101 y Decreto 40/2019 de habilitaciones) | Ítem 3: enlaces a fuentes oficiales | [RN-05](../REGLAS_DE_NEGOCIO.md) (respaldo con fuente oficial), [RN-04](../REGLAS_DE_NEGOCIO.md) (la norma es una referencia: CONCO no interpreta su alcance ni decide si se aplica a un caso) |

## 3. Endpoints que llama CONCO

### `GET /obtenerResultado/tipoNorma=<id>&nNorma=<número>&anio=<año>`

| Filtro (en la ruta) | Valor que envía CONCO |
|---|---|
| `tipoNorma` | `1` (Ley) o `2` (Decreto); siempre se envía |
| `nNorma` | Número de la norma |
| `anio` | Año con **cuatro** dígitos; siempre se envía |

```bash
curl -s 'https://api-restboletinoficial.buenosaires.gob.ar/obtenerResultado/tipoNorma=1&nNorma=6101&anio=2018'
```

Respuesta real abreviada (`back/tests/fixtures/boletin_oficial/ley_6101_2018.json`):

```json
{
  "normas": [
    {
      "id": 435567,
      "nombre_tipo": "Ley",
      "numero_norma": 6101,
      "anio_norma": 18,
      "sumario": "Ley Marco de Regulación de actividades económicas de la Ciudad Autónoma de Buenos Aires",
      "nombre_reparticion": "Legislatura de la Ciudad de Buenos Aires",
      "boletines": [["5526", "27/12/2018", "http://api-restboletinoficial.buenosaires.gob.ar/download/1255814"]],
      "link_documento_normas": [["27/12/2018", "http://api-restboletinoficial.buenosaires.gob.ar/download/1255476"]]
    }
  ]
}
```

## 4. Comportamiento observado

| Caso | Qué devuelve el Boletín | Cómo lo maneja CONCO |
|---|---|---|
| Filtros en la ruta | `=` y `&` sin codificar dentro del path | httpx los envía tal cual (verificado con `raw_path`) |
| Año con dos dígitos (`anio=18`) | 0 resultados | Se envía siempre con cuatro dígitos |
| Año en la respuesta | Con dos dígitos (`"anio_norma": 18`) | El dominio usa el año pedido; el cliente acepta dos o cuatro dígitos al filtrar |
| Norma inexistente | `200` con `{"normas": 0, ...}` (un número) | Lista vacía → `404` |
| `nNorma` no numérico | `normas: 0` | CONCO valida antes (`422`) |
| Filtro inválido (`/obtenerResultado/foo=1`) | `200` `text/html`: `No hay criterio de búsqueda válido seleccionado` | `BoletinOficialError` → `502` |
| Sin `anio` | Mezcla años (Decreto 40 → 17 normas) | Se envía siempre el año y se vuelve a filtrar por tipo, número y año |
| Mismo tipo, número y año | Puede ser más de una norma: Decreto 40/2022 → dos (Área Jefe de Gobierno y Legislatura); Decreto 40/2010 → dos | El endpoint devuelve una **lista** (`regulations`) |
| Norma repetida | Decreto 40/2025 llega dos veces con el mismo id (868869) | Se descartan ids repetidos |
| Resoluciones y disposiciones | Se numeran por organismo: Resolución 100/2019 → 41 normas | No se admiten; solo `ley` y `decreto` |
| Norma antigua (Decreto 40/2010) | `nombre_reparticion: null` y enlace al documento `""` | `issuing_body` y `document_url` en `null` |
| `boletines` y `link_documento_normas` | Un elemento en las 365 normas revisadas | Se usa el primero; si faltan, la validación falla (`502`) en vez de citar sin fecha |
| Enlaces de descarga | Llegan como `http://.../download/N`; por `https://` responden `302` y terminan en el PDF | Se exponen con `https://` |
| Búsqueda por `palabras` | Frase exacta, resultados pobres | No se usa |
| `GET /getUrlDocument/...` | Cuerpo vacío | No se usa |
| Timeout, error HTTP o cuerpo no JSON | — | `BoletinOficialError` → `502` |

Sin resultados (`back/tests/fixtures/boletin_oficial/ley_6101_2019_sin_resultados.json`):

```json
{"normas":0,"filtros":{"subsecciones":null,"tipo":null,"subtipo":null,"reparticion":null,"tipo_subtipo":null,"anios":null,"seccion":null}}
```

Filtro inválido (`back/tests/fixtures/boletin_oficial/criterio_invalido.html`):

```text
No hay criterio de búsqueda válido seleccionado
```

## 5. Cómo se integra en CONCO

| Capa | Ubicación | Qué hace |
|---|---|---|
| Cliente | [`back/src/conco/integrations/boletin_oficial/client.py`](../../back/src/conco/integrations/boletin_oficial/client.py) | `find_norms(norm_type, number, year)`; `BoletinOficialNormType` (Ley, Decreto) y `NORM_TYPE_IDS` |
| Modelos | [`back/src/conco/integrations/boletin_oficial/models.py`](../../back/src/conco/integrations/boletin_oficial/models.py) | `BoletinOficialResults`, `BoletinOficialNorm`; reescriben los enlaces a `https://` |
| Error | `BoletinOficialError` | HTML, cuerpo inesperado, error HTTP o timeout |
| Adaptador | [`back/src/conco/guidance/infrastructure.py`](../../back/src/conco/guidance/infrastructure.py) | `BoletinOficialRegulationRegistry` |
| Error de dominio | [`back/src/conco/guidance/domain.py`](../../back/src/conco/guidance/domain.py) | `RegulationLookupError` |

### `GET /guidance/regulations/{regulation_type}/{number}/{year}`

| Parámetro | Validación |
|---|---|
| `regulation_type` | `ley` o `decreto` |
| `number` | Entero mayor o igual a 1 |
| `year` | Año con cuatro dígitos, entre 1900 y 2100 |

| Código | Cuándo |
|---|---|
| `200` | `{"regulations": [...], "source": {...}}` con al menos una norma: `type`, `number`, `year`, `summary`, `issuing_body`, `publication_date`, `bulletin_number`, `document_url` |
| `404` | No hay normas con ese tipo, número y año |
| `422` | Parámetros inválidos |
| `502` | El Boletín Oficial no respondió o devolvió algo inesperado |

## 6. Configuración

| Variable | Por defecto |
|---|---|
| `BOLETIN_OFICIAL_BASE_URL` | `https://api-restboletinoficial.buenosaires.gob.ar` |
| `BOLETIN_OFICIAL_SITE_URL` | `https://boletinoficial.buenosaires.gob.ar` |
| `BOLETIN_OFICIAL_TIMEOUT_SECONDS` | `10.0` |

Definidas en [`back/src/conco/config.py`](../../back/src/conco/config.py).

## 7. Tests y probe

| Tipo | Ruta |
|---|---|
| Fixtures | `back/tests/fixtures/boletin_oficial/`: `ley_6101_2018.json`, `ley_6101_2019_sin_resultados.json`, `decreto_40_2010.json`, `decreto_40_2019.json`, `decreto_40_2022.json`, `decreto_40_2025.json`, `decreto_40_sin_anio.json`, `criterio_invalido.html` |
| Unitarios | `back/tests/unit/boletin_oficial/test_client.py`, `back/tests/unit/guidance/test_boletin_oficial_registry.py`, `back/tests/unit/guidance/test_regulations_api.py` |
| Integración (API real) | `back/tests/integration/boletin_oficial/test_client.py`, `back/tests/integration/guidance/test_regulations_api.py` |

```bash
uv run python scripts/probes/boletin_oficial.py ley 6101 2018
uv run python scripts/probes/boletin_oficial.py decreto 40 2019
```

## 8. Pendientes y decisiones abiertas

- Agregar `BOLETIN_OFICIAL_*` a `back/.env.example` (tarea del usuario).
- Aceptar la forma de lista (`regulations`) en lugar de una sola norma (decisión del usuario, pendiente según el seguimiento).
- Vincular cada trámite con las normas que cita y decidir si conviene admitir resoluciones con un filtro por organismo. Requiere decisión de producto.
- Búsqueda por texto, ediciones del Boletín y anexos (`link_anexo`) quedaron fuera de alcance.

## 9. Fuentes

- Documentación: <https://api-restboletinoficial.buenosaires.gob.ar/api/doc/>
- Sitio: <https://boletinoficial.buenosaires.gob.ar>
- Seguimiento: [boletin-oficial-integration](../../odd/tasks/boletin-oficial-integration.md)

Fecha de verificación: 2026-10-31.
