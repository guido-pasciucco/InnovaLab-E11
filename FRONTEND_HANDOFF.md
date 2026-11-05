# Entrega de actualización del frontend ConCo

Se actualizó `front/src/App.tsx`, `front/src/Componentes/QueryForm.tsx` y `front/src/style.css`.

La aplicación ahora presenta un flujo de cinco etapas (Consulta, Análisis, Orientación, Mapa y Asistente), manteniendo los contratos de API y los tipos existentes. La vista de mapa reutiliza React-Leaflet. Se conservan el backend, la documentación y la configuración general del repositorio.

Para ejecutar, consultar `front/README.md`.

**Validación realizada:** `tsc -b --pretty false` finalizó correctamente. La compilación de Vite no pudo completarse en este entorno porque el ZIP de origen no contiene el paquete opcional de Rollup correspondiente a Linux (`@rollup/rollup-linux-x64-gnu`). En una instalación limpia con `npm ci` en el equipo local, npm debería resolver las dependencias opcionales según la plataforma. No se debe interpretar la verificación de TypeScript como una compilación de producción completa.

**Diseño:** la implementación sigue los fragmentos HTML/CSS/JS suministrados y la paleta ConCo (#1D3343, #035C80, #FFCD02, #F1F5F7). No se recibió una captura/exportación del frame de Figma para contrastar detalles visuales exactos.
