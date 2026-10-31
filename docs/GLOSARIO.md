# Glosario del proyecto

Términos clave de la propuesta **"Sistema de Gestión Inteligente | TECBA"** (InnovaLab), para que todo el equipo hable el mismo idioma.

> Fuente principal: PDF de la propuesta "Sistema de Gestión Inteligente - TECBA" (plan de trabajo semanal, 12 semanas), transcripto en [PROPUESTA_TECBA.md](PROPUESTA_TECBA.md).

---

## Organización y contexto

### TECBA (Tecnología de Buenos Aires)
Identidad tecnológica del Gobierno de la Ciudad Autónoma de Buenos Aires (GCBA), vinculada a la transformación digital y la innovación pública. Surge de la integración de la **Secretaría de Innovación y Transformación Digital** con la **Agencia de Sistemas de Información (ASI)**. En el proyecto, es el organismo que plantea la problemática, sugiere las fuentes y define el caso piloto.

- Sitio oficial: <https://buenosaires.gob.ar/gcaba_historico/innovacionytransformaciondigital/tecba>
- Confirmación del nombre "Tecnología de Buenos Aires (TECBA)" en el Boletín Oficial de la Ciudad (17/11/2025): <https://documentosboletinoficial.buenosaires.gob.ar/publico/ck_PE-DIS-MJGGC-DGTALINF-110-25-7249.pdf>

### Ciudadanía / usuario principal
Persona que necesita realizar una actividad comercial, un trámite o una consulta vinculada a una ubicación dentro de la Ciudad. No se asume que conozca los sistemas, portales u organismos del Gobierno.

---

## Producto y problema

### Sistema de Gestión Inteligente
Plataforma web inteligente de **consulta y orientación** para actividades comerciales, trámites e información territorial. Nombre de trabajo del producto (el nombre definitivo del proyecto es "CONCO", ver [MVP_SCOPE.md](MVP_SCOPE.md)).

### Fragmentación de la información
Problema central: la información del Gobierno está distribuida entre sistemas, plataformas y fuentes con estructuras, formatos y formas de acceso distintas. El ciudadano termina cargando con la complejidad de saber **qué fuente consultar, dónde encontrarla y cómo relacionar los resultados**.

### Punto único de consulta y orientación
Objetivo del producto: que la persona arranque desde su necesidad concreta y reciba en un solo lugar una respuesta integrada, sin tener que recorrer varios sistemas.

### Respuesta integrada, contextualizada y accionable
Lo que la plataforma debe devolver: no datos sueltos, sino una orientación que combina territorio, contexto y trámites, adaptada a la consulta, y que le dice a la persona **qué hacer a continuación**.

### Orientación
Respuesta organizada que indica qué tiene que hacer la persona: trámites, requisitos, documentación, pasos, información territorial relevante y fuentes que la respaldan. Es **orientación general**, no una determinación legal.

---

## Conceptos funcionales

### Consulta por necesidad y ubicación
Interacción principal: la persona expresa en lenguaje natural **qué quiere hacer y dónde**. Ejemplo: *"Quiero abrir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?"*.

### Actividad
El "qué" de la consulta: la actividad comercial o gestión que la persona quiere realizar (ej.: abrir una cafetería). La plataforma debe identificarla dentro del texto libre.

### Ubicación
El "dónde" de la consulta: una dirección, punto o zona de la Ciudad. Se usa para recuperar información territorial y para mostrar el lugar en el mapa.

### Lenguaje natural
Forma de consultar escribiendo como se habla, sin formularios ni términos técnicos. La IA se encarga de interpretarla.

### Trámite
Gestión oficial que la persona debe realizar ante el Gobierno (ej.: una habilitación comercial). La plataforma organiza los trámites relacionados con la actividad consultada.

### Requisitos
Condiciones que la persona debe cumplir para avanzar con un trámite o actividad.

### Documentación
Papeles o archivos que la persona necesita presentar o tener disponibles para la gestión.

### Pasos a seguir
Secuencia ordenada de acciones para avanzar con la gestión, desde la consulta inicial hasta el objetivo.

### Información territorial
Datos asociados a una ubicación: características territoriales, información geográfica, actividades o servicios registrados y otras capas relevantes del lugar consultado.

### Datos de contexto
Información complementaria de la zona, por ejemplo datos demográficos, que ayuda a entender el entorno de la ubicación consultada.

### Capa (de información)
Conjunto de datos territoriales que se puede superponer sobre el mapa (ej.: zonificación, servicios, actividades registradas). El MVP debe mostrar al menos una.

### Mapa interactivo
Visualización de la ubicación consultada y de la información territorial relacionada, con posibilidad de seleccionar o explorar puntos y áreas, vinculada a los datos y fuentes correspondientes.

### Exploración territorial
Segundo caso de uso contemplado por TECBA: seleccionar una zona y preguntar *"¿Qué información hay disponible sobre esta zona?"*. Es un frente secundario frente al caso principal de actividad comercial.

### Profundización / preguntas de seguimiento
Preguntas posteriores que la persona hace sobre la consulta inicial, manteniendo el contexto. El MVP debe permitir al menos preguntas básicas de seguimiento.

### Trazabilidad
Capacidad de identificar **qué fuente oficial respalda cada parte de la respuesta**, mantener diferenciado el origen de cada dato y evitar presentar como oficial información que no pueda respaldarse.

### Metadatos de fuentes
Datos sobre los datos: origen, fecha de actualización y fuente de cada información. Son la base técnica de la trazabilidad.

---

## Fuentes de información

### Fuente oficial
Origen de información del Gobierno de la Ciudad que respalda la respuesta. El MVP debe integrar **al menos tres fuentes**.

### Integración de fuentes
Consultar, procesar y relacionar información de múltiples fuentes con estructuras y formatos distintos, usando variables o dimensiones compatibles (ej.: dirección, barrio, rubro).

### IDECABA
Infraestructura de Datos Espaciales de la Ciudad de Buenos Aires. Reúne información geográfica oficial del GCBA (capas, mapas y servicios geoespaciales). Fuente candidata para la información territorial.

### BA Data
Portal de datos abiertos del GCBA, con datasets públicos descargables (CSV, JSON, GeoJSON, etc.). Fuente candidata para datos territoriales y de contexto.

### Ciudad 3D
Plataforma del GCBA con información urbanística por parcela (normativa del Código Urbanístico, catastro, usos). Fuente candidata para información territorial asociada a una dirección.

### Información pública de trámites
Información oficial sobre trámites, requisitos y documentación. Durante el MVP hay que relevar qué mecanismo de acceso existe (API oficial u otro).

### Datos abiertos
Información pública publicada por el Gobierno para que cualquiera pueda usarla y reutilizarla.

### Fuente estructurada / no estructurada
Estructurada: datos con formato tabular o definido (CSV, JSON, GeoJSON). No estructurada: documentos como PDFs o texto libre. El MVP no está obligado a incorporar fuentes no estructuradas si el caso no las necesita.

---

## Inteligencia Artificial

### Capa de interacción e interpretación
Rol de la IA en el producto: interpretar la consulta, reconocer actividad y ubicación, recuperar información relevante y organizar y explicar la respuesta. **No es la fuente de verdad.**

### Respuesta respaldada
Regla clave: la IA no debe reemplazar ni contradecir las fuentes oficiales, ni generar información que no esté respaldada por ellas.

### LLM (Large Language Model)
Modelo de lenguaje de gran escala, consumido vía API, que la plataforma usa para entender y redactar respuestas en lenguaje natural.

### Prompt estructurado
Instrucción armada por el backend que le pasa al LLM la consulta y la información ya procesada de las fuentes, para que responda solo con ese contexto.

### Contexto para IA
Información procesada y validada de las fuentes integradas que se entrega al modelo para construir la respuesta.

### RAG (Retrieval-Augmented Generation)
Arquitectura en la que el modelo busca información relevante en una base de documentos antes de responder. El PDF aclara que **no es obligatoria en el MVP** si las fuentes pueden procesarse de forma estructurada.

### Consulta ambigua / fuera de alcance
Consulta que la plataforma no puede interpretar con claridad o que excede la información disponible. Debe manejarse explícitamente, sin inventar respuestas.

---

## Alcance y metodología

### MVP (Producto Mínimo Viable)
Primera versión funcional que demuestra **un caso de uso concreto, completo y viable** en 12 semanas, priorizando el inicio de una nueva actividad comercial.

### Caso de uso
Situación concreta que la plataforma resuelve de punta a punta.

### Caso piloto
Caso de referencia planteado por TECBA para validar el MVP: abrir una cafetería en Av. Corrientes 2500.

### Camino feliz (happy path)
Recorrido completo y sin errores desde la consulta inicial hasta una orientación clara sobre qué hacer para avanzar.

### Flujo mínimo funcional
Ingresar qué y dónde → interpretar actividad y ubicación → consultar al menos 3 fuentes → integrar territorio + contexto + trámites → visualizar en mapa → presentar requisitos, documentación y pasos → permitir preguntas con IA → mostrar fuentes utilizadas.

### Future Scope / Escalabilidad futura
Funcionalidades que quedan fuera del MVP (más actividades, conectores automáticos, alertas, historial, reportes, integraciones institucionales, etc.) pero para las que la arquitectura debe quedar preparada.

### Sprint
Bloque de trabajo de dos semanas. El plan tiene: Sprint Planning (semana 0), Exploración, Ideación, Desarrollo (x2), Iterar y Cierre.

### Entregable semanal / Dependencias semanal
Entregable: lo que debe estar terminado al cierre de la semana. Dependencias: lo que tiene que estar resuelto antes para poder lograrlo.

### Release Candidate
Versión candidata a ser la final, estable y con bugs críticos resueltos (objetivo de la semana 10).

### Testing end-to-end
Prueba del recorrido completo de punta a punta, como lo haría un usuario real.

### Smoke test
Prueba rápida sobre la versión publicada para verificar que lo esencial funciona.

### Pruebas de regresión
Pruebas que verifican que los cambios nuevos no rompieron funcionalidades que ya andaban.

---

## Términos técnicos

### Geocodificación
Transformar una dirección escrita (ej.: "Av. Corrientes 2500") en coordenadas geográficas (latitud/longitud) para ubicarla en el mapa y cruzarla con datos territoriales.

### Información geoespacial
Datos que tienen una posición en el espacio (puntos, líneas, polígonos). Se almacenan con PostgreSQL + PostGIS y se procesan con GeoPandas.

### Formatos territoriales
- **GeoJSON:** JSON con geometrías geográficas; estándar web.
- **KML:** formato XML de geometrías, popularizado por Google Earth.
- **SHP (Shapefile):** formato clásico de los sistemas GIS.

### Formatos de datos estructurados
**CSV, XLSX y JSON**: formatos tabulares o de objetos en los que suelen publicarse los datasets abiertos.

### API REST
Interfaz para que dos sistemas se comuniquen por HTTP. Se usa para consultar fuentes y para conectar frontend con backend.

### Endpoint
Ruta concreta de una API que devuelve o recibe un tipo de información (ej.: datos del mapa, trámites, contexto).

### Conector
Componente que accede a una fuente y trae su información de forma automática. Los conectores universales para cualquier fuente quedan fuera del MVP.

### Normalización de datos
Transformar datos de fuentes distintas a una estructura común para poder relacionarlos.

### Fallback
Comportamiento alternativo cuando algo falla (ej.: una fuente no responde), para devolver una respuesta parcial en lugar de romper el flujo.

---

## Roles del equipo

| Rol | Responsabilidad principal |
|-----|---------------------------|
| **UX/UI** | Recorrido de la ciudadanía, wireframes, jerarquías visuales, estados de carga/error y accesibilidad. |
| **Frontend** | Interfaz web, consulta, mapa, visualización de resultados y fuentes. |
| **Backend** | APIs, base de datos, acceso a fuentes, geocodificación e integración con IA. |
| **BI, Data & Machine Learning** | Análisis, transformación y relación de las fuentes; calidad de datos; información estructurada para la IA. |
| **QA** | Estrategia de testing, casos de prueba, validación contra fuentes oficiales y gestión de bugs. |
