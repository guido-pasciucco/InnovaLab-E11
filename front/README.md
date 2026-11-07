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
npm run build
npm run preview
```

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

- El campo de actividad sugiere actividades curadas parecidas por significado a lo que se escribe (`GET /guidance/activities`, desde 3 caracteres): «quiero poner una barbería» sugiere «Peluquería».
- Elegir una sugerencia es opcional. Si se elige, el paso 3 muestra los trámites oficiales que suelen aplicar a esa actividad (`GET /guidance/activities/{slug}/procedures`), con cuándo aplica cada uno, el enlace a buenosaires.gob.ar y la fuente citada.
- Con una actividad elegida, el paso 3 muestra «Contanos más de tu comercio»: preguntas de sí, no o no sé (personal, menos de 200 m², mesas en la vereda, cartel, edificio protegido, continuar un local habilitado). Cada respuesta vuelve a pedir los trámites con esas respuestas; los que no corresponden se descartan y los que dependen de una pregunta sin responder se marcan «Puede aplicar».
- Si no se elige ninguna, o si no se pudieron cargar los trámites, el paso 3 muestra la orientación general de siempre.
- Necesita la base de datos del backend levantada y cargada (ver `back/README.md`, «Búsqueda de actividades»).

## Consideraciones funcionales

- El frontend conserva los servicios `submitConsultation` y `submitFollowUp` y el modelo de datos existente.
- La respuesta mock está identificada como demostración; no equivale a una validación oficial de habilitaciones o zonificación.
- El marcador geográfico de la respuesta mock es ilustrativo. Para producción, el backend debe geocodificar la dirección y devolver coordenadas y capas territoriales verificadas.
- El asistente depende de la integración configurada en el backend; con mock devuelve una respuesta demostrativa.
- El diseño se implementó tomando como referencia la paleta y la estructura de las vistas HTML/CSS/JS suministradas (cinco pasos, barra de consulta, orientación, mapa y asistente). No se recibió una exportación/captura verificable del frame de Figma, por lo que no se afirma una coincidencia píxel a píxel con ese archivo.
