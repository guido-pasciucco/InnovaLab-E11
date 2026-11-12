# Ciudad 3D (Código Urbanístico por parcela)

Servicio de USIG que publica los datos del Código Urbanístico por parcela: distrito, edificabilidad, protección patrimonial, afectaciones y **el cuadro de usos** (qué rubros se permiten y con qué condiciones). Es el backend del visor [Ciudad 3D](https://ciudad3d.buenosaires.gob.ar). Se consulta por SMP, que se obtiene con [USIG Catastro](usig-catastro.md).

**Estado:** candidata, no integrada. Verificada con llamadas reales el 2026-11-05.

## 1. Ficha

| Dato | Valor |
|---|---|
| Proveedor | USIG, Gobierno de la Ciudad de Buenos Aires |
| URL base | `https://epok.buenosaires.gob.ar/cur3d` |
| Endpoints probados | `GET /mixtura_usos/`, `/categorias/`, `/cuadrosdeuso/rubros/`, `/cuadrosdeuso/referencias/`, `/seccion_edificabilidad/`, `/afectaciones/` |
| Documentación oficial | No hay documentación pública. Las rutas salen del código del visor (ver sección 5) |
| Acceso | Sin clave de acceso. Mismo servidor que [EPOK](../en-pr/usig-epok.md): con el User-Agent por defecto de curl la conexión se corta; con cualquier otro (o ninguno) responde |
| Licencia | Sin licencia explícita. Se asume CC BY 2.5 AR, como el resto de los datos de la Ciudad |
| Latencia observada | `seccion_edificabilidad` ~2 s; `mixtura_usos` ~0,6 s; `afectaciones` ~0,4 s; `cuadrosdeuso/*` ~0,05–0,08 s |
| Estabilidad y riesgos | Sin documentación: los campos y las rutas pueden cambiar sin aviso. Un SMP inexistente responde `200` con un objeto `error`, no con `404`. Las rutas sin barra final responden `301` |

## 2. Para qué podría servir

| Uso | MVP | Reglas |
|---|---|---|
| **Responder si un rubro está permitido en la dirección** y con qué condiciones (superficie máxima, estacionamiento, carga y descarga) | Ítems 1 y 2: consulta inicial y orientación | [RN-01](../../REGLAS_DE_NEGOCIO.md) (falta definir cómo se elige el rubro), [RN-04](../../REGLAS_DE_NEGOCIO.md) (orientativo, no es una determinación legal), [RN-05](../../REGLAS_DE_NEGOCIO.md) (cita la fuente) |
| Ofrecer el nomenclador oficial de rubros como lista cerrada para el buscador | Ítem 1: consulta inicial | [RN-01](../../REGLAS_DE_NEGOCIO.md) |
| Avisar que el inmueble está catalogado o en un Área de Protección Histórica y sumar el trámite «Consulta obligatoria para inmuebles en APH o catalogados» | Ítem 2: orientación sobre trámites | [RN-04](../../REGLAS_DE_NEGOCIO.md), [RN-05](../../REGLAS_DE_NEGOCIO.md) |
| Avisar afectaciones (riesgo hídrico, ensanche o apertura de calle) | Fuera del MVP actual | [RN-04](../../REGLAS_DE_NEGOCIO.md) |

Flujo para saber si una actividad está permitida:

```
SMP ──mixtura_usos──▶ área de mixtura (1–4)
categoría + mixtura ──cuadrosdeuso/rubros──▶ rubros (id y nombre)
categoría + mixtura + rubro ──cuadrosdeuso/referencias──▶ permitido / condiciones
```

**Lo que la API no resuelve:** traducir la actividad que escribe la persona («cafetería») al rubro oficial («1.5. Alimentación en general y gastronomía»). Ese paso sigue siendo una decisión de producto ([RN-01](../../REGLAS_DE_NEGOCIO.md)).

### ¿Por qué no enviar a la persona directo al visor Ciudad 3D?

El visor es una herramienta para profesionales (arquitectos, gestores). Para saber si puede abrir una cafetería, la persona tendría que:

1. Encontrar su parcela en el mapa.
2. Entender términos técnicos: mixtura de usos, FOT, plusvalía, enrase.
3. **Saber de antemano** que una cafetería es el rubro «1.5. Alimentación en general y gastronomía», dentro de la categoría «Comercial», y buscarlo en el cuadro de usos.
4. Interpretar referencias como «Ver art. 3.6.1.1» y los requisitos de estacionamiento.
5. Y aun así **no saber qué trámites hacer**: el visor no los menciona.

Lo que agrega CONCO:

| Visor Ciudad 3D | CONCO |
|---|---|
| Hay que conocer el rubro oficial | La persona escribe su actividad («cafetería») |
| Muestra todo: edificabilidad, plusvalía, afectaciones | Muestra solo lo relevante para esa actividad |
| Lenguaje técnico del Código Urbanístico | Lenguaje simple: «Podés, con estas condiciones» |
| Termina en «permitido o no» | Sigue con los trámites, sus requisitos y la sede más cercana |
| Una sola fuente | Integra Georef, Catastro, Ciudad 3D, Trámites CABA y EPOK |

Ciudad 3D es una **fuente de datos** de CONCO, no una alternativa. Conviene enlazarlo como «Ver el detalle técnico de tu parcela en Ciudad 3D», para que la persona o su profesional profundicen, y para citar la fuente oficial ([RN-05](../../REGLAS_DE_NEGOCIO.md)).

El riesgo es el inverso: si CONCO muestra los mismos datos con el mismo lenguaje técnico, no aporta nada. Su valor está en **traducir e integrar**, no en repetir.

## 3. Endpoints

Todas las rutas llevan barra final.

### `GET /cur3d/mixtura_usos/`

Área de mixtura de usos de la parcela. Define qué rubros se permiten y con qué límites.

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/mixtura_usos/?smp=013-099-018'
```

```json
{"usos": [4, 0, 0]}
```

No se verificó qué representan el segundo y el tercer valor; el primero es el área de mixtura.

### `GET /cur3d/categorias/`

Las 10 categorías de uso del Código Urbanístico. No recibe parámetros.

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/categorias/'
```

```json
[
  {"id": 1, "nombre": "Comercial"},
  {"id": 2, "nombre": "Depositos, Almacenamiento y logística"},
  {"id": 3, "nombre": "Servicios"},
  {"id": 4, "nombre": "Alojamiento"},
  {"id": 5, "nombre": "Transporte"},
  {"id": 6, "nombre": "Diversiones publicas, cultura, culto y recreacion"},
  {"id": 7, "nombre": "Educacion"},
  {"id": 8, "nombre": "Sanidad"},
  {"id": 9, "nombre": "Residencial"},
  {"id": 10, "nombre": "Industria"}
]
```

### `GET /cur3d/cuadrosdeuso/rubros/`

| Parámetro | Valor |
|---|---|
| `categoria` | Id de categoría (1–10) |
| `mixtura` | Área de mixtura (1–4) |

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/cuadrosdeuso/rubros/?categoria=1&mixtura=4'
```

Respuesta real abreviada:

```json
{
  "rubros": [
    {"rubro": "1.4.3. Maxikiosco", "rubro_id": 169},
    {"rubro": "1.5. Alimentación en general y gastronomía", "rubro_id": 102},
    {"rubro": "1.8.2. Farmacia", "rubro_id": 66}
  ],
  "total": 63,
  "categoria": "Comercial"
}
```

Cantidad de rubros por categoría con `mixtura=4`: Comercial 63, Depósitos 8, Servicios 67, Alojamiento 17, Transporte 27, Diversiones 56, Educación 33, Sanidad 47, Residencial 8, Industria 75 (401 en total). Comercial devuelve los mismos 63 rubros con `mixtura=1`: la lista no se filtra por mixtura; el permiso está en `referencias`.

### `GET /cur3d/cuadrosdeuso/referencias/`

| Parámetro | Valor |
|---|---|
| `categoria` | Id de categoría |
| `mixtura` | Área de mixtura |
| `rubro` | `rubro_id` de la respuesta anterior |

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/cuadrosdeuso/referencias/?categoria=1&mixtura=4&rubro=102'
```

```json
{
  "permitido_mixtura_de_usos": [{"detalle": "Permitido en el Área de Mixtura de Usos"}],
  "bicicletas": [{"detalle": "Salón de 150m² o más: 30%, como mínimo, de la cantidad de los módulos de estacionamientos"}],
  "estacionamientos": [{"detalle": "Salón de 150m2 o más: 20%, como mínimo, de la superficie total del salón"}],
  "cargaydescarga": [{"detalle": "No tiene requerimiento"}],
  "observaciones": "No incluye música y canto, espectáculos en vivo, etc. \nver art. 3.6.1.1. Ver art. 3.6.1.1"
}
```

El mismo rubro con `mixtura=1` responde `"permitido_mixtura_de_usos": [{"detalle": "Superficie máxima 200m2"}]`.

### `GET /cur3d/seccion_edificabilidad/`

Edificabilidad, distrito y protección patrimonial de la parcela (parámetro `smp`).

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/seccion_edificabilidad/?smp=013-099-018'
```

Respuesta real abreviada:

```json
{
  "altura_max": [31.2, 0.0, 0.0, 0.0],
  "altura_max_plano_limite": 38.2,
  "plusvalia": {"incidencia_uva": 50.0, "alicuota": 0.18, "distrito_cpu": "C3 I"},
  "fot": {"fot_medianera": 4.0, "fot_perim_libre": 4.0, "fot_semi_libre": 4.0},
  "parcelas_linderas": {"smp_linderas": ["013-099-013", "013-099-012"], "aph_linderas": false},
  "catalogacion": {
    "denominacion": null,
    "proteccion": "CAUTELAR",
    "estado": "CPU/CUr",
    "ley_3056": "SI",
    "catalogacion": "SINGULAR"
  },
  "afectaciones": {"riesgo_hidrico": 0, "lep": 0, "ensanche": 0, "apertura": 0, "ci_digital": 0},
  "superficie_parcela": 3475.0,
  "link_imagen": {"croquis_parcela": "http://www.ssplan.buenosaires.gov.ar/croquis_parcela/imagenes/9/69/013-099-018_0000477969.pdf"}
}
```

### `GET /cur3d/afectaciones/`

Mismo parámetro `smp`. Devuelve solo el bloque de afectaciones y responde más rápido que `seccion_edificabilidad`:

```bash
curl -s -A 'CONCO/0.1' 'https://epok.buenosaires.gob.ar/cur3d/afectaciones/?smp=013-099-018'
```

```json
{"riesgo_hidrico": 0, "lep": 0, "ensanche": 0, "apertura": 0, "ci_digital": 0}
```

## 4. Comportamiento observado

| Caso | Qué devuelve |
|---|---|
| SMP válido | `200` con JSON (`Content-Type: application/json`) |
| SMP inexistente (`999-999-999`) en `seccion_edificabilidad` | `200` con `{"error": "ObjetoTerritorial matching query does not exist."}` |
| Ruta sin barra final (`/cur3d/categorias`) | `301` a la misma ruta con barra |
| Rutas inventadas (`/cur3d/usos/`, `/cur3d/distrito/`, `/cur3d/parcela_plusvalia/`) | `302` sin datos: no existen |
| Rubro no permitido en la mixtura | No se probó |
| Campos `0` / `""` | Las afectaciones usan `0` para «no aplica» y los distritos especiales vienen como strings vacíos |
| Croquis | `link_imagen` apunta a PDFs en `ssplan.buenosaires.gov.ar` por `http`, no `https` |

## 5. Cómo se encontraron las rutas

El visor publica su configuración en `https://ciudad3d.buenosaires.gob.ar/config.js` (`urlAPI: 'https://epok.buenosaires.gob.ar'`), y su bundle JavaScript (`/assets/index-*.js`) arma todas las rutas sobre esa base. Rutas encontradas, además de las de la sección 3:

| Ruta | Parámetros | Probada |
|---|---|---|
| `/catastro/parcela/` | `lng`, `lat` o `smp` | Sí, ver [usig-catastro.md](usig-catastro.md) |
| `/catastro/geometria/` | `smp` | No |
| `/cur3d/fichadecatalogacion/` | `smp` | No |
| `/cur3d/monumento_historico_nacional/` | `smp` | No |
| `/cur3d/obras/` | `smp` | No |
| `/cur3d/inspecciones/` | `smp` | No |
| `/cur3d/sade/` | `smp` | No |
| `/cur3d/constitucion_estado_parcelario/` | `smp` | No |
| `/cur3d/parcela_en_microcentro/` | `smp` | No |
| `/cur3d/parcelas_plausibles_a_enrase/` | `smp` | No |
| `/cur3d/calcular_plusvalia/` | `smp`, `area_edificar` | No |
| `https://fotos.usig.buenosaires.gob.ar/getDatosFotos` y `/getFoto` | `smp` (y `i`, `w`) | No |

El nombre del bundle cambia con cada versión del visor; las rutas pueden cambiar sin aviso.

## 6. Pendientes y decisiones abiertas

- **Cómo se elige el rubro** a partir de lo que escribe la persona ([RN-01](../../REGLAS_DE_NEGOCIO.md)): lista cerrada de rubros en el buscador, mapeo curado «actividad → rubro» o una IA que elija entre los 401 rubros.
- Probar un rubro no permitido y documentar la respuesta.
- Confirmar el significado del segundo y tercer valor de `mixtura_usos.usos`.
- Confirmar qué campo representa el distrito vigente: el único observado es `plusvalia.distrito_cpu`.
- La latencia de `seccion_edificabilidad` (~2 s) pide pensar en caché si se consulta en cada búsqueda.

## 7. Fuentes

- Llamadas reales a `https://epok.buenosaires.gob.ar/cur3d/` (2026-11-05).
- Configuración y código del visor: `https://ciudad3d.buenosaires.gob.ar/config.js` y `/assets/index-CCSdEon9.js` (2026-11-05).
