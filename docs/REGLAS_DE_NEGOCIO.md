# Reglas de negocio vigentes

Reglas de negocio con las que el equipo está trabajando **en este momento** en CONCO.

> **Importante:** este documento refleja lo que se planea construir hoy. Puede diferir de la planificación original ([PROPUESTA_TECBA.md](PROPUESTA_TECBA.md)) y puede volver a acercarse a ella más adelante. Ante una diferencia entre ambos documentos, **este es el que manda para el desarrollo actual**.

## Estados

| Estado | Significado |
|---|---|
| **Vigente** | Decidida. Se implementa así. |
| **Pendiente de validar** | Se trabaja con esta regla, pero falta confirmar que sea factible o que cumpla lo que pide el MVP. |

## Reglas

### RN-01 — La búsqueda inicial se hace con un buscador, no con IA

- **Estado:** Pendiente de validar
- **Regla:** el punto de entrada es un buscador donde la persona indica la actividad y la dirección. No se usa una IA para interpretar la consulta en primera instancia.
- **Diferencia con la planificación:** la propuesta plantea una consulta en lenguaje natural interpretada por IA (ej.: *"Quiero abrir una cafetería en Av. Corrientes 2500"*).
- **Qué falta validar:**
  - Que el buscador sea suficiente para cumplir los requisitos del MVP de *consulta inicial* e *interpretación* (ver [PROPUESTA_TECBA.md §5](PROPUESTA_TECBA.md)).
  - Qué rol cumple la IA, si cumple alguno (por ejemplo, solo preguntas de seguimiento).

### RN-02 — Alcance geográfico: solo CABA

- **Estado:** Vigente
- **Regla:** solo se aceptan ubicaciones dentro de la Ciudad Autónoma de Buenos Aires. Las búsquedas de direcciones se restringen a CABA.

### RN-03 — La dirección se convierte en una ubicación aproximada

- **Estado:** Vigente
- **Regla:** la dirección ingresada se geocodifica con la API Georef para obtener coordenadas y mostrarla en el mapa. La ubicación se presenta como **aproximada**.
- Si la dirección no se encuentra, se le informa a la persona en lugar de mostrar una ubicación inventada.

### RN-04 — Se brinda orientación general, no una determinación legal

- **Estado:** Vigente
- **Regla:** CONCO orienta sobre trámites, requisitos y pasos. **No** determina si una actividad está permitida en un inmueble concreto ni confirma información de zonificación o catastro.

### RN-05 — Toda información se respalda con una fuente oficial

- **Estado:** Vigente
- **Regla:** cada dato que se muestra indica de qué fuente oficial proviene e incluye un enlace a ella cuando existe.
- No se presenta como oficial ninguna información que no pueda respaldarse con una fuente.

### RN-06 — CONCO no gestiona trámites ni garantiza resultados

- **Estado:** Vigente
- **Regla:** la plataforma no presenta solicitudes ante organismos ni garantiza que un trámite vaya a ser aprobado.

### RN-07 — Las limitaciones del prototipo se muestran siempre

- **Estado:** Vigente
- **Regla:** la persona debe ver de forma clara que la orientación es general y que tiene que verificar los requisitos con la autoridad correspondiente.

### RN-08 — Caso piloto: inicio de una actividad comercial

- **Estado:** Vigente
- **Regla:** el MVP se enfoca en un único caso: abrir una nueva actividad comercial. El caso de referencia es una cafetería en Av. Corrientes 2500. No se busca cubrir cualquier actividad ni todos los trámites de la Ciudad.

## Resumen de pendientes

| Regla | Qué falta validar |
|---|---|
| RN-01 | Factibilidad del buscador como entrada y rol de la IA. |

## Cómo mantener este documento

- Cuando cambie una regla, actualizarla acá en el mismo cambio que la implementa.
- Cuando se valide una regla pendiente, pasarla a **Vigente** o reescribirla según lo decidido.
- No borrar el número de una regla descartada: marcarla como descartada para no reutilizar el ID.

## Documentos relacionados

- [MVP_SCOPE.md](MVP_SCOPE.md) — alcance incluido y excluido del MVP.
- [PROPUESTA_TECBA.md](PROPUESTA_TECBA.md) — planificación original.
- [GLOSARIO.md](GLOSARIO.md) — definición de los términos usados.
