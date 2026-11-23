# Especificaciones de experiencia (navegación y orientación)

Documento de referencia para **implementar** los cambios de experiencia pedidos el 22/11/2026. Sigue el formato de [las especificaciones de QA](../qa/ESPECIFICACIONES.md): cada entrada tiene el punto en lenguaje simple, por qué importa, cómo sabremos que está listo, qué NO se hace y las decisiones que lo cerraron. Una entrada marcada **Propuesta** todavía espera confirmación del dueño del producto y no se implementa hasta que se confirme.

## Entradas

### UX-1. "Editar consulta" vuelve al paso 1 con el formulario vacío

**Estado:** confirmada.

**Cómo se entendió:** desde la orientación, el botón "Editar consulta" lleva al paso 1, pero la actividad y la dirección aparecen vacías. Quien quiere cambiar solo la dirección tiene que volver a escribir todo. Lo esperable es que el formulario aparezca con la consulta actual cargada, lista para corregir.

**Causa en el código:** el formulario solo recibe valores iniciales cuando se abre una búsqueda del historial (`prefill`). "Editar consulta" solo navega al paso 1 (`front/src/App.tsx:249`) y el formulario arranca vacío (`front/src/App.tsx:304`).

**Cómo sabremos que está listo:**

- Al tocar "Editar consulta", el paso 1 muestra la actividad y la dirección de la consulta actual, ya seleccionadas (no hace falta volver a elegirlas del autocompletado).
- Se puede cambiar un solo campo y volver a consultar.
- "Volver a editar" del paso de análisis (si sigue existiendo, ver UX-3) se comporta igual.
- Abrir una búsqueda del historial sigue funcionando como hoy.

**Lo que NO se hace:** cambiar el formulario ni el autocompletado.

### UX-2. Navegación repetida: Orientación, Mapa y Asistente aparecen dos veces

**Estado:** confirmada (22/11/2026: quedan solo los pasos de arriba).

**Cómo se entendió:** en los pasos 3 a 5 conviven dos navegaciones con los mismos destinos: los pasos de arriba (Consulta · Análisis · Orientación · Mapa · Asistente) y las pestañas a la derecha de "Tu consulta" (Orientación · Mapa · Asistente). Es redundante y obliga a decidir cuál usar.

**Cómo sabremos que está listo:**

- Se quitan las pestañas de la barra "Tu consulta". Esa barra sigue mostrando la actividad, la dirección, "Editar consulta" y "Actualizar".
- Orientación, Mapa y Asistente se abren solo desde los pasos de arriba.
- Junto con UX-3, los pasos de arriba quedan: Consulta · Orientación · Mapa · Asistente.

**Lo que NO se hace:** cambiar las direcciones de cada pantalla (`/orientacion`, `/mapa`, `/asistente`): siguen pudiendo compartirse y recargarse.

**Decisión:** se eligió la barra de pasos porque se ve en todas las pantallas, incluida "Consulta"; las pestañas solo aparecían del paso 3 en adelante. Se aceptó que Mapa y Asistente se vean como pasos aunque sean vistas del mismo resultado.

### UX-3. "Análisis" es solo una pantalla de carga

**Estado:** confirmada.

**Cómo se entendió:** el paso 2 solo aparece mientras se procesa la consulta. Una vez terminada, volver a él no aporta nada: muestra lo mismo que la barra "Tu consulta". No tiene sentido que sea un paso navegable.

**Cómo sabremos que está listo:**

- Mientras se procesa la consulta se sigue viendo la pantalla de carga.
- Terminada la consulta, "Análisis" no se puede abrir desde la navegación ni aparece el botón "← Volver al análisis" de la orientación.
- Con "Atrás" del navegador desde la orientación no se vuelve a la pantalla de carga.

**Lo que NO se hace:** quitar la pantalla de carga ni lo que muestra mientras trabaja.

### UX-4. La lista "Antes de empezar: lo que tenés que conseguir" es demasiado larga

**Estado:** confirmada (22/11/2026: se eligió la pestaña agrupada frente a poner los requerimientos dentro de cada trámite o dejarlos en un lateral compacto).

**Cómo se entendió:** la lista de requerimientos está en la columna lateral de la orientación (`front/src/Componentes/RequirementsChecklist.tsx`) y muestra todos los requerimientos juntos, cada uno con los trámites de los que sale. Con muchos ítems el scroll es largo, y cuesta ver qué requerimiento corresponde a qué trámite.

**Objetivo:** que sea fácil ver los requerimientos y, a la vez, saber a qué trámite pertenece cada uno.

**Diseño acordado:**

- La orientación pasa a tener dos pestañas en la columna principal: **Trámites (N)** y **Qué tenés que conseguir (M)**.
- En "Qué tenés que conseguir", los requerimientos se agrupan por trámite en bloques que se abren y cierran, cada uno con su avance ("2 de 5"). Los requerimientos que piden varios trámites van en un grupo propio al principio, "Sirve para varios trámites", para no repetirlos.
- Cada tarjeta de trámite muestra "Necesitás N cosas →", que abre la otra pestaña en el grupo de ese trámite.
- La columna lateral solo muestra el avance total de requerimientos y un enlace a la pestaña.

**Cómo sabremos que está listo:** desde un trámite se llega a sus requerimientos con un clic, y desde un requerimiento se ve a qué trámite pertenece; ninguna de las dos listas obliga a un scroll largo en la columna lateral.

**Lo que NO se hace:** cambiar qué requerimientos trae la API ni cómo se marcan; lo marcado se sigue guardando igual.
