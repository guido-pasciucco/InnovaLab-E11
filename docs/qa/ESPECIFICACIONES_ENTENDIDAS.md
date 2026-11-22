# Especificaciones entendidas

Este archivo se completa **solo cuando vos confirmás que entendiste** un punto. Recién ahí se escribe la entrada, con el contexto en el que lo entendiste.

Cada entrada tiene tres cosas:

| Campo | Qué guarda |
|---|---|
| **El punto** | El nombre del pendiente, en lenguaje simple. |
| **Cómo lo entendiste** | Tu explicación del problema y por qué importa, con tus palabras. |
| **Contexto que te lo aclaró** | El ejemplo, la comparación o la explicación que te hizo entender el punto. |

## Entradas confirmadas

### 1. El trámite que a veces aparece y a veces no (QA-01)

**Cómo se entendió:** al pedir el detalle de un trámite, la primera vez el sistema contestó como si no existiera; al repetir exactamente lo mismo, apareció con todos sus datos ("Alta de habilitación de remises" y su fuente). Importa porque quien se topa con el primer intento puede creer que ConCo no tiene ese trámite. Lo esperable es que pase siempre lo mismo: que aparezca siempre, o que se diga con claridad que no está.

**Contexto que lo aclaró:**

- La comparación con un enlace que te lleva a una página de "no encontrado": no era un cartel lindo en la pantalla, era la respuesta del sistema.
- La aclaración de que la prueba se hizo contra la API, sin abrir la página: por eso sabemos qué contestó el sistema, pero no qué vio una persona.
- Tu observación de que en la pantalla solo se busca por actividad y no hay buscador de trámites: era correcta. La búsqueda por nombre existe solo en la API y se usó para armar la prueba; no está pensado agregarla a la pantalla.
- Por eso las dudas quedaron como consultas para testing, no como trabajo del proyecto.

**Confirmado:** 22/11/2026.

## Cómo se usa

1. Te explico un pendiente, de a uno, en lenguaje simple y sin detalles de implementación.
2. Si te queda claro, me decís «lo entendí» y, si querés, qué fue lo que te lo aclaró.
3. Solo en ese momento escribo la entrada acá, con ese contexto.
