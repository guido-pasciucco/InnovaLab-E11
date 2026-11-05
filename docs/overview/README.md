# Overview

Explicación simple de cómo funciona la app, separada por funcionalidad.

## 1. Consulta inicial

El usuario expresa en lenguaje natural **qué quiere hacer** y **dónde**:

- `QueryForm` — formulario con dos campos: actividad ("abrir una cafetería") y dirección ("Av. Corrientes 2500"). Incluye ejemplos precargados.
- `InterpretacionConsulta` — pantalla de revisión que muestra lo entendido, permite editar actividad y dirección, y confirma antes de enviar.

**Salida:** `ConsultationRequest { activity, address }` → `POST /consultations`.

## 2. Geolocalización (resolución territorial)

El backend convierte la dirección de texto en territorio, en dos pasos:

**2.1. Dirección → coordenadas** (Georef `/direcciones`)

- Entrada: dirección libre del usuario.
- Salida: dirección normalizada + punto `{ lat, lng }`.
- Implementación: `back/src/conco/integrations/georef/client.py` → `search_addresses()`.

**2.2. Coordenadas → comuna** (Georef `/ubicacion`)

- Entrada: `{ lat, lng }` del paso anterior.
- Salida: provincia, departamento, comuna (ej. "Comuna 3 · CABA").
- **Por qué importa:** la comuna es la clave que usan IDECABA y BA Data para identificar una zona.

## 3. Integración de fuentes

Con la comuna identificada, el backend cruza la información de las fuentes oficiales:

- **Trámites** — requisitos, documentación y pasos para la actividad consultada.
- **Territorio** — datos de contexto de la zona (zonificación, comercios, etc.).
- Cada dato queda asociado a su fuente para trazabilidad.

## 4. Resultados

El front recibe `ConsultationResponse` y muestra:

- `summary` — orientación general de la consulta.
- `steps` — camino feliz: qué hacer, en orden.
- `point` + `territory` — pin en el mapa (`MapPanel`) con la comuna identificada.
- `territorialFeatures` — capas GeoJSON opcionales sobre el mapa.
- `sources` — fuentes oficiales que respaldan cada dato (`SourceList`).
- `limitations` — aclaraciones sobre qué no se pudo verificar.

## 5. Profundización

`submitFollowUp()` permite preguntas de seguimiento sobre la consulta ya realizada (`POST /consultations/{id}/follow-up`).

## Quién hace qué

| Pieza | Rol |
|-------|-----|
| Front (React) | Formulario, revisión, mapa, resultados. Nunca habla con Georef directamente. |
| Backend (FastAPI) | Orquesta el flujo completo. |
| Geolocalización (Georef) | Direcciones → coordenadas → comuna/provincia. |
| IDECABA / BA Data | Datos territoriales por comuna. |
| Trámites CABA | Requisitos y pasos de la actividad. |

> **Nota:** la orientación con IA (redacción en lenguaje natural sobre las fuentes) está contemplada en TECBA pero todavía no forma parte del flujo.
