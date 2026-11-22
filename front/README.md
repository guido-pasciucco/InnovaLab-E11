# ConCo — Frontend

Frontend de ConCo desarrollado con React, TypeScript y Vite. La experiencia se organiza en cinco etapas:

1. **Consulta:** actividad, dirección y ejemplos rápidos.
2. **Análisis:** revisión de los datos ingresados y consulta al servicio.
3. **Orientación:** trámites/requisitos orientativos, lista de revisión y fuentes.
4. **Mapa:** visualización territorial con Leaflet.
5. **Asistente:** envío de preguntas de seguimiento.

## Requisitos

- Node.js 20 o superior (recomendado).
- npm.

## Ejecutar en desarrollo

Desde esta carpeta (`front`):

```bash
npm ci
npm run dev
```

Abrí la URL local que informe Vite (normalmente `http://localhost:5173`).

## Verificar y compilar

```bash
npm run typecheck
npm test
npm run build
npm run preview
```

`npm test` corre con Vitest los tests de los módulos sin interfaz: validación, cliente de la API y traducción de errores, rutas de los pasos, sesión y historial.

## Rutas

Cada paso tiene su dirección: `/consulta`, `/analisis`, `/orientacion`, `/mapa` y `/asistente` (`react-router-dom`). La barra de pasos es clickeable: el paso actual queda marcado, los que ya tienen datos se pueden abrir y los demás se ven deshabilitados. Entrar a un paso que necesita una consulta (por ejemplo `/orientacion`) sin haberla hecho lleva a `/consulta`.

La consulta abierta en la pestaña (resultado, trámites, respuestas de contexto y marcas) se guarda en `sessionStorage`, así que recargar `/mapa` sigue mostrando el mapa. En Vercel, `vercel.json` reescribe cualquier ruta a `index.html` para que las direcciones abiertas directo carguen la app.

## Búsquedas recientes

El paso 1 muestra «Búsquedas recientes» cuando hay historial: una tarjeta al costado en escritorio y una sección plegable en móvil. Se guarda solo en este navegador (`localStorage`, clave `conco.search-history.v1`) con actividad, dirección, fecha, un resumen breve y lo necesario para repetir la búsqueda; hasta 10 búsquedas, sin duplicar las repetidas. «Ver» completa el formulario y vuelve a consultar; «Actualizar» (en la barra de la consulta) repite la consulta actual; «Limpiar historial» lo borra.

## Errores y validación

- Los campos se validan antes de enviar, con los mismos límites que la API: actividad de 2 a 100 caracteres (con contador visible), dirección de 3 a 200, sin aceptar solo espacios. El error aparece al lado del campo.
- `src/api/errors.ts` es el único lugar que traduce los errores a mensajes: usa el `code` que devuelve la API y distingue sin conexión, demora (90 s) y cancelación (que no muestra nada). Nunca se muestra el detalle técnico de un 422.
- Un error inesperado al dibujar la pantalla muestra un aviso con «Reintentar» dentro del paso, o una pantalla de respaldo si falla toda la app.

## Configuración de API

Copiá `.env.example` a `.env` si necesitás personalizar la conexión:

- `VITE_API_BASE_URL`: URL base de la API. Por defecto `/api`.
- `VITE_USE_MOCK_API`: usar datos simulados para la consulta y el asistente cuando el valor no sea `false`, hasta que el backend publique esos endpoints. Para llamar al backend, configurá `false` y una URL de API válida.

El buscador de direcciones no tiene datos simulados: siempre consulta al backend (`GET /geolocation/addresses`). En desarrollo, Vite reenvía `/api` al backend en `http://localhost:8000` (quitando el prefijo `/api`), así que el backend tiene que estar levantado.

## Buscador de direcciones

- El campo de dirección sugiere direcciones normalizadas de Georef a medida que se escribe (desde 3 caracteres, con 300 ms de espera entre pedidos).
- Hay que elegir una sugerencia para continuar; su coordenada es la que muestra el mapa del paso 4.
- Si el servicio de direcciones no responde, se acepta la dirección escrita y el mapa se muestra sin marcador.

## Buscador de actividades

- El campo de actividad sugiere actividades curadas parecidas por significado a lo que se escribe (`GET /guidance/activities`, desde 2 caracteres): «quiero poner una barbería» sugiere «Peluquería».
- Elegir una sugerencia es opcional. Si se elige, el paso 3 muestra los trámites oficiales que suelen aplicar a esa actividad (`GET /guidance/activities/{slug}/procedures`), con cuándo aplica cada uno, el enlace a buenosaires.gob.ar y la fuente citada.
- Con una actividad elegida, el paso 3 muestra «Contanos más de tu comercio»: preguntas de sí, no o no sé (personal, menos de 200 m², mesas en la vereda, cartel, edificio protegido, continuar un local habilitado). Cada respuesta vuelve a pedir los trámites con esas respuestas; los que no corresponden se descartan (el aviso dice cuáles) y los que dependen de una pregunta sin responder se marcan «Puede aplicar», con una nota que explica que dependen de las respuestas.
- Si no se elige ninguna, o si no se pudieron cargar los trámites, el paso 3 muestra la orientación general de siempre.
- Necesita la base de datos del backend levantada y cargada (ver `back/README.md`, «Búsqueda de actividades»).

## Consideraciones funcionales

- El frontend conserva los servicios `submitConsultation` y `submitFollowUp` y el modelo de datos existente.
- La respuesta mock está identificada como demostración; no equivale a una validación oficial de habilitaciones o zonificación.
- El marcador geográfico de la respuesta mock es ilustrativo. Para producción, el backend debe geocodificar la dirección y devolver coordenadas y capas territoriales verificadas.
- El asistente depende de la integración configurada en el backend; con mock devuelve una respuesta demostrativa.
- El diseño se implementó tomando como referencia la paleta y la estructura de las vistas HTML/CSS/JS suministradas (cinco pasos, barra de consulta, orientación, mapa y asistente). No se recibió una exportación/captura verificable del frame de Figma, por lo que no se afirma una coincidencia píxel a píxel con ese archivo.
