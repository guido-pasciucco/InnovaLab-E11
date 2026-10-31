# Producto digital: Sistema de Gestión Inteligente | TECBA

**Plan de trabajo semanal** — InnovaLab, Agencia de Habilidades para el Futuro.

> Transcripción en Markdown del PDF original "Sistema de Gestión Inteligente - TECBA". Para los términos clave, ver [GLOSARIO.md](GLOSARIO.md).

## Índice

1. [Identificación del Producto](#1-identificación-del-producto)
2. [Problemática](#2-problemática)
3. [Solución Propuesta](#3-solución-propuesta)
4. [Funcionalidades](#4-funcionalidades)
5. [Requisitos mínimos para aprobar (MVP)](#5-requisitos-mínimos-para-aprobar-mvp)
6. [Future Scope / Escalabilidad futura](#6-future-scope--escalabilidad-futura)
7. [Recomendación de tecnologías y herramientas](#7-recomendación-de-tecnologías-y-herramientas)
8. [Plan de trabajo semanal](#8-plan-de-trabajo-semanal)
9. [Consideraciones sobre licencias y escalabilidad](#9-consideraciones-sobre-licencias-y-escalabilidad)

---

## 1. Identificación del Producto

- **Nombre del proyecto sugerido:** A definir.
- **Tipo de producto:** Plataforma web inteligente de consulta y orientación para actividades comerciales, trámites e información territorial.
- **Usuarios principales:** Ciudadanos que necesiten realizar actividades comerciales, trámites o consultas vinculadas con una ubicación determinada dentro de la Ciudad.
- **Propósito:** Integrar y relacionar información proveniente de distintas fuentes del Gobierno para brindar respuestas simples, contextualizadas y accionables a partir de una necesidad concreta de la persona.
- **Interacción principal:** La persona podrá expresar en lenguaje natural **qué quiere hacer y dónde**, y la plataforma utilizará esa información para identificar y relacionar datos sobre trámites, requisitos, documentación, pasos a seguir e información territorial asociada.
- **Alcance inicial:** El MVP deberá abordar un caso de uso concreto, priorizando el **inicio de una nueva actividad comercial**, e integrar al menos tres fuentes de información, información territorial, visualización mediante mapa interactivo y consulta en lenguaje natural mediante IA.

## 2. Problemática

El Gobierno de la Ciudad dispone de grandes volúmenes de información distribuida entre distintos sistemas, plataformas, servicios y fuentes de datos abiertos. Estas fuentes pueden presentar estructuras, formatos, niveles de procesamiento y formas de acceso diferentes, lo que dificulta su integración y consulta conjunta.

Esta fragmentación se vuelve especialmente relevante cuando una persona necesita resolver una gestión concreta vinculada con una **actividad comercial y una ubicación determinada**, ya que la respuesta puede requerir combinar:

- Información territorial.
- Datos de contexto de la zona.
- Información sobre trámites.
- Requisitos y documentación.
- Pasos necesarios para avanzar con la gestión.

Actualmente, esta situación puede trasladar al ciudadano la complejidad de identificar **qué fuente consultar, dónde encontrar la información y cómo relacionar los resultados obtenidos**, generando una experiencia fragmentada.

La problemática no se reduce entonces únicamente a la existencia de múltiples fuentes, sino a la dificultad de **transformar información distribuida en una respuesta integrada, contextualizada y accionable** frente a una necesidad concreta.

La oportunidad consiste en simplificar esa experiencia mediante una herramienta que pueda partir de lo que la persona quiere hacer y dónde quiere hacerlo, integrar la información relevante y presentar una orientación clara sin exigirle conocer previamente los distintos sistemas, organismos o fuentes involucrados.

## 3. Solución Propuesta

Desarrollar una **plataforma web inteligente de consulta y orientación** que permita a la ciudadanía expresar qué actividad desea realizar y en qué ubicación de la Ciudad, para recibir una respuesta integrada construida a partir de distintas fuentes oficiales.

La solución combinará principalmente:

- Integración y relación de información proveniente de distintas fuentes.
- Información territorial y de contexto asociada a una ubicación.
- Información sobre trámites, requisitos, documentación y pasos a seguir.
- Consulta en lenguaje natural mediante Inteligencia Artificial.
- Visualización de información territorial sobre un mapa cuando corresponda.

La experiencia estará orientada a que la persona pueda comenzar desde su necesidad concreta, sin tener que conocer previamente qué sistema, portal u organismo debe consultar.

Por ejemplo:

> **"Quiero abrir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?"**

A partir de esa consulta, la plataforma deberá identificar la **actividad** y la **ubicación**, determinar qué fuentes resultan relevantes y relacionar la información disponible sobre trámites, requisitos, documentación, pasos e información territorial correspondiente.

La Inteligencia Artificial funcionará como una capa de **interacción e interpretación** sobre la información integrada. No deberá reemplazar las fuentes oficiales ni generar respuestas que no estén respaldadas por la información disponible.

### Flujo general

**Ingresar necesidad + ubicación → interpretar actividad y lugar → consultar fuentes relevantes → integrar información territorial, de contexto y de trámites → construir orientación → visualizar en mapa cuando corresponda → profundizar mediante IA.**

El objetivo será que la plataforma funcione como un **punto único de consulta y orientación**, transformando información distribuida en una respuesta concreta, contextualizada y accionable para la ciudadanía.

## 4. Funcionalidades

La plataforma deberá permitir transformar una necesidad concreta de la ciudadanía en una **respuesta integrada y contextualizada**, combinando información territorial, datos de contexto e información oficial sobre trámites y requisitos.

### Consulta por necesidad y ubicación

- Permitir que la persona exprese en lenguaje natural qué quiere hacer.
- Incorporar una dirección, punto o zona de la Ciudad como parte de la consulta.
- Identificar dentro de la consulta la **actividad** y la **ubicación** involucradas.
- Utilizar ambos elementos para determinar qué información resulta relevante.

Por ejemplo:

> **"Quiero abrir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?"**

### Integración de fuentes

La plataforma deberá poder consultar y relacionar información proveniente de múltiples fuentes oficiales.

Deberá permitir:

- Integrar al menos tres fuentes diferentes.
- Procesar información con estructuras y formatos distintos.
- Relacionar datos mediante variables o dimensiones compatibles.
- Identificar qué fuente aporta cada parte de la respuesta.
- Actualizar o reemplazar las fuentes cuando corresponda.

Entre las fuentes consideradas por TECBA se encuentran **IDECABA, BA Data, Ciudad 3D e información pública de trámites**, aunque la selección definitiva dependerá del caso de uso y de la disponibilidad técnica de cada fuente.

### Información sobre trámites

A partir de la actividad consultada, la plataforma deberá organizar la información oficial disponible sobre:

- Trámites relacionados.
- Requisitos.
- Documentación necesaria.
- Pasos a seguir.
- Información adicional necesaria para avanzar con la gestión.

La información deberá presentarse de manera ordenada, facilitando la construcción de un **camino feliz** para la persona.

### Información territorial y de contexto

A partir de una dirección, punto o zona, la plataforma podrá recuperar y relacionar información territorial disponible.

Según las fuentes integradas, podrá incluir:

- Características territoriales.
- Información geográfica.
- Datos demográficos o de contexto.
- Actividades o servicios registrados.
- Otras capas relevantes para la ubicación consultada.

### Mapa interactivo

- Visualizar la ubicación indicada por el usuario.
- Representar información territorial relacionada con ese punto o zona.
- Incorporar distintas capas de información cuando las fuentes lo permitan.
- Permitir seleccionar o explorar puntos o áreas en el mapa.
- Vincular la información visualizada con los datos y fuentes correspondientes.

### Consulta mediante Inteligencia Artificial

La IA funcionará como capa de interacción e interpretación sobre la información integrada.

Deberá permitir:

- Interpretar consultas realizadas en lenguaje natural.
- Reconocer actividad y ubicación.
- Recuperar la información relevante.
- Organizar los resultados provenientes de distintas fuentes.
- Generar respuestas contextualizadas.
- Resumir y explicar la información disponible.
- Permitir preguntas de profundización sobre la consulta inicial.

La IA **no deberá reemplazar las fuentes oficiales ni generar información que no esté respaldada por ellas**.

### Respuesta integrada y orientación

La respuesta deberá evitar presentar simplemente un conjunto de datos aislados.

La plataforma deberá poder organizar la información mostrando, cuando corresponda:

- Qué tiene que hacer la persona.
- Qué trámites debe realizar.
- Qué requisitos debe cumplir.
- Qué documentación necesita.
- Qué pasos debería seguir.
- Qué información territorial resulta relevante.
- Qué fuentes respaldan la orientación presentada.

### Trazabilidad de la información

- Identificar las fuentes utilizadas para construir cada respuesta.
- Mantener diferenciada la información proveniente de cada fuente.
- Evitar presentar como oficial información que no pueda respaldarse.
- Permitir reconocer el origen de los datos utilizados.

### Exploración territorial

Además del caso principal de actividad comercial, la plataforma podrá permitir seleccionar una ubicación o zona y consultar:

> **"¿Qué información hay disponible sobre esta zona?"**

A partir de allí podrá integrar y visualizar información territorial proveniente de las fuentes disponibles. Este segundo escenario está contemplado por TECBA como otro caso de uso para validar el modelo.

El núcleo funcional queda entonces:

**Consultar qué quiero hacer y dónde → interpretar → integrar fuentes → relacionar actividad + territorio + trámites → organizar pasos → visualizar en mapa → responder con IA respaldada por información oficial.**

## 5. Requisitos mínimos para aprobar (MVP)

Teniendo en cuenta las 12 semanas de desarrollo, el MVP deberá demostrar un **caso de uso concreto, completo y viable**, priorizando el inicio de una nueva actividad comercial y evitando intentar resolver desde el comienzo todos los trámites, actividades o fuentes posibles.

| Categoría | Requisitos mínimos para aprobar |
|-----------|---------------------------------|
| **Caso de uso** | Abordar al menos un caso concreto, priorizando el inicio de una nueva actividad comercial. |
| **Consulta inicial** | Permitir que la persona indique en lenguaje natural qué quiere hacer y dónde. |
| **Interpretación** | Identificar correctamente la actividad y la ubicación involucradas en la consulta. |
| **Fuentes** | Integrar y relacionar al menos **3 fuentes de información** relevantes para el caso seleccionado. |
| **Procesamiento** | Leer, transformar y preparar la información necesaria para poder utilizarla conjuntamente. |
| **Información territorial** | Incorporar información territorial o de contexto asociada a la ubicación consultada. |
| **Mapa interactivo** | Mostrar la ubicación y al menos una capa o información territorial relevante sobre un mapa. |
| **Información de trámites** | Recuperar y presentar información sobre trámites, requisitos, documentación y pasos relacionados con la actividad seleccionada. |
| **Camino feliz** | Construir un recorrido completo desde la consulta inicial hasta una orientación clara sobre qué debería hacer la persona para avanzar. |
| **IA** | Permitir consultas en lenguaje natural y generar respuestas contextualizadas utilizando únicamente la información proveniente de las fuentes integradas. |
| **Trazabilidad** | Identificar qué fuentes oficiales respaldan la información presentada. |
| **Profundización** | Permitir al usuario realizar al menos preguntas de seguimiento sobre la consulta inicial. |
| **Experiencia de uso** | Presentar la información de manera clara, integrada y comprensible, evitando que la persona tenga que recorrer distintos sistemas por separado. |
| **Entregable final** | Plataforma web funcional que permita demostrar el recorrido completo sin errores críticos. |

### Flujo mínimo funcional

**Ingresar qué quiere hacer y dónde → interpretar actividad y ubicación → consultar al menos 3 fuentes → integrar información territorial + contexto + trámites → visualizar ubicación en mapa → presentar requisitos, documentación y pasos → permitir preguntas mediante IA → mostrar las fuentes utilizadas.**

### Caso piloto sugerido

El caso de referencia planteado por TECBA es:

> **"Quiero abrir una cafetería en Av. Corrientes 2500. ¿Qué tengo que hacer?"**

A partir de esa necesidad, la plataforma debería poder relacionar información territorial, datos de contexto e información oficial sobre trámites para construir una orientación integrada.

### Condiciones del MVP

Para mantener un alcance realizable, **no será obligatorio** en esta primera versión:

- Resolver cualquier actividad comercial existente.
- Integrar todos los trámites de la Ciudad.
- Construir conectores universales para cualquier fuente.
- Incorporar múltiples casos de uso completos.
- Implementar analítica predictiva.
- Generar sistemas complejos de indicadores o alertas.
- Incorporar documentos o fuentes no estructuradas si no son necesarias para el caso seleccionado.
- Automatizar completamente la actualización de todas las fuentes.
- Implementar una arquitectura RAG compleja si las fuentes seleccionadas pueden resolverse mediante procesamiento estructurado.

La selección definitiva de fuentes deberá surgir durante el desarrollo del MVP, identificando qué información necesita el caso elegido, dónde se encuentra y cuál es el mecanismo técnico más adecuado para acceder e integrarla.

La prioridad es demostrar correctamente un único recorrido:

**necesidad concreta → integración de fuentes → información territorial → orientación sobre trámites → mapa → respuesta contextualizada mediante IA.**

## 6. Future Scope / Escalabilidad futura

Una vez validado el MVP sobre un caso de uso concreto, la plataforma podrá ampliar progresivamente la cantidad de actividades, trámites, fuentes y capacidades de consulta, manteniendo la misma lógica de **partir de una necesidad ciudadana y construir una respuesta integrada a partir de información oficial**.

| Categoría | Funcionalidades futuras |
|-----------|-------------------------|
| **Más actividades comerciales** | Incorporar nuevos rubros y tipos de actividades además del caso piloto utilizado en el MVP. |
| **Más trámites y gestiones** | Ampliar la cobertura hacia otros trámites, permisos, habilitaciones y servicios de la Ciudad. |
| **Más fuentes de información** | Integrar nuevas fuentes territoriales, administrativas y de datos abiertos. |
| **Conectores automáticos** | Incorporar conexiones mediante APIs u otros mecanismos para actualizar la información sin cargas manuales. |
| **Actualización automática** | Sincronizar periódicamente las fuentes y detectar cambios en requisitos, trámites o información territorial. |
| **Mapa avanzado** | Incorporar más capas territoriales, filtros, selección de áreas y nuevas formas de explorar información geográfica. |
| **Exploración territorial ampliada** | Permitir consultas más complejas sobre zonas, características territoriales, servicios, actividades y contexto urbano. |
| **IA avanzada** | Mejorar interpretación de consultas, preguntas de seguimiento, explicaciones y capacidad de relacionar mayor cantidad de fuentes. |
| **Citas y evidencias** | Mostrar con mayor detalle qué fuente, dato o sección oficial respalda cada parte de una respuesta. |
| **Historial de consultas** | Permitir recuperar consultas realizadas y volver a acceder a las orientaciones generadas. |
| **Personalización** | Adaptar respuestas según tipo de actividad, ubicación y contexto específico de la consulta. |
| **Alertas** | Permitir que una persona reciba avisos ante cambios relevantes en requisitos, trámites o condiciones vinculadas con una gestión. |
| **Reportes** | Generar resúmenes descargables con pasos, requisitos, documentación y fuentes utilizadas. |
| **Integraciones institucionales** | Conectar la plataforma con otros sistemas y servicios digitales del Gobierno de la Ciudad. |
| **Nuevos casos de uso** | Extender el modelo hacia otras necesidades ciudadanas que requieran combinar información de distintos sistemas. |

### Evolución de la consulta territorial

La consulta territorial podrá crecer como un segundo gran frente de la plataforma, permitiendo que la persona seleccione un punto o zona y explore información proveniente de fuentes como **IDECABA, BA Data, Ciudad 3D y otras disponibles**.

La arquitectura deberá permitir incorporar estas nuevas capacidades sin modificar la lógica central:

**necesidad ciudadana → ubicación → integración de fuentes → interpretación → orientación contextualizada → visualización territorial.**

De esta manera, el MVP valida un caso concreto, pero deja preparada la solución para escalar progresivamente hacia un **punto único de consulta sobre actividades, trámites e información territorial de la Ciudad**.

## 7. Recomendación de tecnologías y herramientas

Para el MVP se recomienda una arquitectura web que permita integrar fuentes heterogéneas, procesar información territorial, visualizar resultados sobre un mapa y utilizar Inteligencia Artificial como capa de consulta e interpretación. La selección tecnológica deberá priorizar un recorrido completo y viable para el caso de uso elegido, evitando construir desde el inicio una infraestructura preparada para cualquier tipo de trámite o fuente.

| Necesidad | Tecnologías / herramientas posibles |
|-----------|-------------------------------------|
| **Desarrollo web** | React / Next.js |
| **Lenguaje frontend** | JavaScript / TypeScript |
| **Backend / APIs** | Python + FastAPI |
| **Base de datos** | PostgreSQL / Supabase |
| **Información geoespacial** | PostgreSQL + PostGIS |
| **Autenticación** | Supabase Auth / JWT |
| **Procesamiento de datos** | Python / Pandas |
| **Carga de datos estructurados** | CSV / XLSX / JSON |
| **Procesamiento geográfico** | GeoPandas |
| **Formatos territoriales** | GeoJSON / KML / SHP, según las fuentes seleccionadas |
| **Mapa interactivo** | Leaflet / MapLibre GL / Mapbox, según necesidades y licenciamiento |
| **Geocodificación** | Servicio compatible para transformar direcciones en coordenadas |
| **Integración de fuentes** | APIs REST / procesamiento de datasets públicos |
| **Información de trámites** | API oficial cuando exista / mecanismo de consulta definido durante el relevamiento |
| **Inteligencia Artificial** | API de un modelo LLM |
| **Contexto para IA** | Recuperación de información procesada + prompts estructurados |
| **Trazabilidad** | Metadatos de fuentes, origen y fecha de actualización |
| **Testing de APIs** | Postman |
| **Diseño UX/UI** | Figma |
| **Flujos y arquitectura** | FigJam / Miro |
| **Gestión de QA** | Jira + Zephyr / herramienta equivalente |
| **Control de versiones** | Git + GitHub |
| **Hosting frontend** | Vercel |
| **Hosting backend** | Render / Railway |
| **Base de datos y almacenamiento** | Supabase |

TECBA contempla fuentes territoriales y de datos abiertos que pueden presentarse en formatos como **PDF, CSV, XLSX, KML, SHP y JSON**, mientras que para la información de trámites será necesario evaluar durante el MVP qué mecanismos de acceso están efectivamente disponibles.

### Criterio técnico para la IA

Para el MVP no sería necesario implementar desde el inicio una arquitectura RAG compleja si las fuentes seleccionadas pueden procesarse y estructurarse previamente.

La IA debería funcionar principalmente como capa de:

**interpretación de la consulta → identificación de actividad y ubicación → recuperación de información relevante → organización y explicación de la respuesta.**

Los datos sobre trámites, territorio y requisitos deberán provenir de las fuentes integradas; el modelo no deberá utilizarse como fuente de verdad. Esto respeta el criterio definido por TECBA de que la IA facilite la comprensión sin reemplazar ni contradecir las fuentes oficiales.

## 8. Plan de trabajo semanal

### Sprint Planning

#### Semana 0

**Objetivo:** organizar el equipo, definir el caso piloto y validar inicialmente las fuentes necesarias para construir el recorrido del MVP.

**Todos**
- Revisar problemática, solución, funcionalidades y requisitos del MVP.
- Definir roles, dinámica de trabajo y tablero de seguimiento.
- Confirmar el caso de uso piloto vinculado al inicio de una actividad comercial.
- Definir qué debería poder resolver el camino feliz.
- Identificar la información necesaria para responder correctamente al caso seleccionado.

**UX/UI**
- Definir el recorrido general de la ciudadanía: **consulta → ubicación → orientación → mapa → profundización**.
- Identificar las pantallas principales.
- Definir criterios iniciales de claridad, accesibilidad y presentación de información.

**Frontend**
- Configurar proyecto, repositorio y entorno.
- Definir estructura inicial de navegación y componentes.
- Evaluar técnicamente la integración del mapa interactivo.

**Backend**
- Configurar backend y base de datos.
- Definir arquitectura inicial para consultas, fuentes, ubicaciones y respuestas.
- Analizar mecanismos de acceso a las fuentes candidatas.
- Evaluar servicio de geocodificación necesario para trabajar con direcciones.

**BI, Data & Machine Learning**
- Identificar al menos **tres fuentes potencialmente útiles** para el caso piloto.
- Analizar estructura, disponibilidad y calidad de la información.
- Determinar cómo relacionar actividad, ubicación, territorio y trámites.
- Identificar campos o dimensiones comunes.

**QA**
- Definir estrategia inicial de testing.
- Identificar escenarios críticos del camino feliz.
- Definir criterios iniciales para validar exactitud de datos, ubicación y respuestas.

**✅ Entregable semanal**
- Equipo y roles definidos.
- Caso piloto seleccionado.
- Camino feliz inicial definido.
- Tres fuentes candidatas identificadas.
- Arquitectura inicial acordada.
- Estrategia de mapa y geocodificación evaluada.
- Repositorios y entornos configurados.

**❎ Dependencias semanal**
- Caso de uso priorizado.
- Disponibilidad de fuentes públicas.
- Acceso a herramientas y servicios necesarios.
- Validación inicial de mecanismos de consulta de las fuentes.

---

### Sprint 1 | Exploración

#### Semana 1

**Objetivo:** validar que las fuentes seleccionadas permiten responder el caso de uso y construir técnicamente la relación entre actividad, ubicación y trámites.

**Todos**
- Desglosar la pregunta del caso piloto en necesidades de información.
- Definir qué resultado debería recibir la persona.
- Identificar qué información aporta cada fuente.

**UX/UI**
- Diseñar el flujo inicial de consulta.
- Crear wireframes de búsqueda, ingreso de ubicación y presentación de resultados.
- Definir cómo mostrar requisitos, documentación y pasos.

**Frontend**
- Implementar estructura base de la plataforma.
- Crear primera interfaz de consulta.
- Preparar componente inicial de ubicación/mapa.

**Backend**
- Realizar primeras conexiones o procesos de lectura sobre las fuentes seleccionadas.
- Implementar prueba de geocodificación de direcciones.
- Definir estructura común para organizar la información recuperada.

**BI, Data & Machine Learning**
- Analizar las tres fuentes.
- Identificar variables territoriales, de actividad y de trámites.
- Realizar primeras transformaciones y relaciones.
- Documentar problemas de calidad o disponibilidad.

**QA**
- Validar acceso y respuesta de las fuentes.
- Crear casos de prueba para direcciones y consultas del caso piloto.
- Registrar riesgos o limitaciones encontradas.

**✅ Entregable semanal**
- Tres fuentes técnicamente evaluadas.
- Relación inicial entre actividad, ubicación y trámites definida.
- Primera dirección geocodificada.
- Wireframes principales disponibles.
- Interfaz base de consulta iniciada.
- Riesgos técnicos documentados.

**❎ Dependencias semanal**
- Fuentes identificadas en Semana 0.
- Acceso efectivo a la información.
- Caso piloto y resultado esperado definidos.

#### Semana 2

**Objetivo:** construir la primera versión funcional del recorrido **consulta + ubicación + información integrada**.

**Todos**
- Validar qué información mínima debe contener la respuesta.
- Definir el orden del camino feliz.
- Confirmar las tres fuentes definitivas del MVP.

**UX/UI**
- Completar wireframes del camino feliz.
- Diseñar estados de carga, error y falta de información.
- Diseñar primera versión del mapa y de la orientación paso a paso.

**Frontend**
- Implementar ingreso de actividad y ubicación.
- Integrar mapa básico.
- Mostrar ubicación consultada.
- Crear primera estructura visual para requisitos, documentación y pasos.

**Backend**
- Implementar servicios iniciales para recuperar información de las fuentes.
- Procesar actividad y ubicación.
- Relacionar los primeros resultados.
- Preparar una respuesta estructurada para el frontend.

**BI, Data & Machine Learning**
- Normalizar la información necesaria de las tres fuentes.
- Implementar primeras relaciones entre datos territoriales, contexto y trámites.
- Validar que el resultado sea consistente para el caso piloto.

**QA**
- Testear consultas válidas e inválidas.
- Validar ubicación y datos mostrados.
- Comparar la respuesta integrada con las fuentes originales.
- Definir criterios de aceptación del camino feliz.

**✅ Entregable semanal**
- Tres fuentes definitivas integradas inicialmente.
- Consulta de actividad y ubicación operativa.
- Mapa básico funcional.
- Primera información territorial disponible.
- Primera respuesta estructurada sobre trámites y requisitos.
- Camino feliz definido de punta a punta.

**❎ Dependencias semanal**
- Fuentes técnicamente viables.
- Geocodificación funcionando.
- Relaciones entre los datos identificadas.
- Información oficial suficiente para construir el caso piloto.

---

### Sprint 2 | Ideación

#### Semana 3

**Objetivo:** desarrollar la primera experiencia territorial integrada y transformar los datos procesados en información clara y útil para la ciudadanía.

**Todos**
- Validar la estructura final de la respuesta del caso piloto.
- Definir qué información territorial resulta realmente relevante para la actividad seleccionada.
- Acordar qué capas o datos deberán visualizarse en el mapa.
- Revisar el orden de requisitos, documentación y pasos del camino feliz.

**UX/UI**
- Diseñar la experiencia de resultados.
- Definir cómo convivirán mapa, información territorial y orientación sobre trámites.
- Diseñar jerarquías para diferenciar:
  - requisitos;
  - documentación;
  - pasos;
  - información territorial;
  - fuentes.
- Ajustar estados de información incompleta o no disponible.

**Frontend**
- Implementar la pantalla principal de resultados.
- Incorporar visualización de la ubicación en el mapa.
- Mostrar las primeras capas o datos territoriales.
- Implementar componentes para requisitos, documentación y pasos.
- Vincular visualmente cada bloque de información con su contexto correspondiente.

**Backend**
- Consolidar servicios para consultar las tres fuentes seleccionadas.
- Implementar la relación entre ubicación, actividad e información territorial.
- Preparar endpoints para mapa, trámites y datos de contexto.
- Estructurar la respuesta para que el frontend pueda presentar el camino feliz.

**BI, Data & Machine Learning**
- Procesar la información territorial necesaria.
- Validar relaciones entre las distintas fuentes.
- Preparar las capas o variables que se mostrarán sobre el mapa.
- Comprobar consistencia entre ubicación, actividad y resultados obtenidos.

**QA**
- Validar información territorial mostrada.
- Comparar los resultados con las fuentes originales.
- Testear direcciones diferentes dentro del alcance definido.
- Registrar inconsistencias geográficas o de datos.

**✅ Entregable semanal**
- Primera experiencia territorial integrada.
- Mapa con ubicación funcional.
- Información de las tres fuentes relacionada.
- Requisitos, documentación y pasos visibles.
- Primera versión visual del camino feliz disponible.

**❎ Dependencias semanal**
- Tres fuentes integradas inicialmente.
- Geocodificación operativa.
- Datos territoriales disponibles.
- Estructura de respuesta definida.

#### Semana 4

**Objetivo:** completar el camino feliz del caso piloto y consolidar la presentación integrada de trámites, territorio y contexto.

**Todos**
- Revisar el recorrido completo desde la necesidad inicial hasta la orientación final.
- Validar que la información presentada responda realmente a la consulta ciudadana.
- Definir qué información debe quedar fuera cuando no sea relevante para el caso.
- Acordar cómo se mostrará el respaldo de las fuentes.

**UX/UI**
- Ajustar el recorrido completo.
- Diseñar navegación entre mapa, pasos y detalle de información.
- Incorporar referencias visibles a las fuentes oficiales.
- Mejorar claridad y comprensión del camino feliz.

**Frontend**
- Implementar el recorrido completo de resultados.
- Incorporar interacción básica con el mapa.
- Permitir consultar información asociada a puntos, zonas o capas cuando corresponda.
- Mostrar fuentes y origen de la información.
- Ajustar visualización de requisitos, documentación y próximos pasos.

**Backend**
- Consolidar la integración de las tres fuentes.
- Mejorar reglas de relación entre actividad, ubicación y trámites.
- Incorporar metadatos de origen y actualización.
- Preparar la estructura que utilizará posteriormente la capa de IA.

**BI, Data & Machine Learning**
- Validar resultados para distintos escenarios dentro del caso piloto.
- Revisar calidad y consistencia de la información territorial.
- Documentar reglas de relación y transformaciones aplicadas.
- Preparar información estructurada para consultas posteriores en lenguaje natural.

**QA**
- Ejecutar testing completo del camino feliz.
- Validar que cada bloque de información esté respaldado por la fuente correspondiente.
- Probar escenarios de falta de datos o ubicación no reconocida.
- Validar funcionamiento e interacción del mapa.

**✅ Entregable semanal**
- **Camino feliz funcional sin IA.**
- Tres fuentes integradas y relacionadas.
- Información territorial y de trámites presentada conjuntamente.
- Mapa interactivo operativo.
- Requisitos, documentación y pasos organizados.
- Trazabilidad básica de fuentes disponible.

**❎ Dependencias semanal**
- Integración territorial de Semana 3.
- Tres fuentes estables.
- Información oficial suficiente para resolver el caso piloto.
- Mapa y geocodificación funcionando.

---

### Sprint 3 | Desarrollo

#### Semana 5

**Objetivo:** incorporar la primera versión de consulta mediante Inteligencia Artificial, utilizando como contexto únicamente la información integrada y validada del caso piloto.

**Todos**
- Definir qué preguntas deberá poder interpretar la IA dentro del MVP.
- Acordar qué información podrá utilizar para construir respuestas.
- Establecer criterios para evitar respuestas no respaldadas por las fuentes oficiales.
- Definir cómo se manejarán consultas ambiguas o fuera del alcance.

**UX/UI**
- Diseñar el espacio de consulta en lenguaje natural.
- Definir cómo se presentarán respuestas, fuentes y datos territoriales.
- Diseñar estados de carga, error y falta de información.
- Incorporar una experiencia clara para realizar preguntas de seguimiento.

**Frontend**
- Implementar la interfaz de consulta mediante IA.
- Mostrar la respuesta dentro del contexto del caso seleccionado.
- Integrar la respuesta con mapa, requisitos, documentación y pasos.
- Incorporar referencias visibles a las fuentes utilizadas.

**Backend**
- Integrar el servicio de IA seleccionado.
- Preparar el contexto a partir de la información procesada de las fuentes.
- Implementar la extracción de **actividad y ubicación** desde la consulta.
- Controlar que la respuesta utilice únicamente información disponible en las fuentes integradas.
- Implementar lógica básica para preguntas de seguimiento.

**BI, Data & Machine Learning**
- Preparar la información estructurada que utilizará la IA.
- Definir consultas y respuestas esperadas.
- Validar la consistencia entre respuestas, datos territoriales y trámites.
- Identificar casos donde la información disponible no sea suficiente para responder.

**QA**
- Testear consultas simples, ambiguas y fuera de alcance.
- Validar extracción de actividad y ubicación.
- Comparar las respuestas generadas contra las fuentes originales.
- Verificar que la IA no agregue información no respaldada.

**✅ Entregable semanal**
- Primera consulta mediante IA funcionando.
- Identificación de actividad y ubicación operativa.
- Respuestas contextualizadas sobre el caso piloto.
- Preguntas de seguimiento básicas disponibles.
- Referencias a fuentes visibles.
- Primer conjunto de consultas validado.

**❎ Dependencias semanal**
- Primera consulta mediante IA funcionando.
- Identificación de actividad y ubicación operativa.
- Respuestas contextualizadas sobre el caso piloto.
- Preguntas de seguimiento básicas disponibles.
- Referencias a fuentes visibles.
- Primer conjunto de consultas validado.

> Nota: en el PDF original, las dependencias de la Semana 5 repiten el contenido del entregable.

#### Semana 6

**Objetivo:** integrar todas las funcionalidades desarrolladas y alcanzar una primera versión completa del MVP.

**Todos**
- Revisar el recorrido completo desde la consulta inicial hasta la orientación final.
- Validar que el caso piloto responda a los requisitos definidos por TECBA.
- Detectar funcionalidades incompletas o inconsistencias.
- Priorizar ajustes para la segunda mitad del desarrollo.

**UX/UI**
- Revisar navegación y experiencia completa.
- Ajustar consulta, mapa, orientación, fuentes y preguntas de seguimiento.
- Unificar estados, mensajes y comportamientos.
- Validar que la respuesta sea comprensible para una persona que no conoce previamente los sistemas del Gobierno.

**Frontend**
- Integrar consulta, mapa, información territorial, trámites e IA.
- Consolidar navegación entre resultados y detalle.
- Mejorar visualización de requisitos, documentación, pasos y fuentes.
- Corregir inconsistencias de integración.

**Backend**
- Consolidar la integración de las tres fuentes.
- Integrar procesamiento territorial, trámites, geocodificación e IA dentro de un mismo flujo.
- Mejorar manejo de errores y ausencia de información.
- Consolidar trazabilidad básica de las fuentes.

**BI, Data & Machine Learning**
- Validar las relaciones entre las tres fuentes.
- Revisar consistencia de información territorial y de trámites.
- Verificar que las respuestas de IA correspondan con los datos disponibles.
- Ajustar reglas o transformaciones necesarias.

**QA**
- Ejecutar el primer testing end-to-end.
- Validar el caso piloto de punta a punta.
- Probar distintas consultas dentro del alcance.
- Registrar y priorizar bugs técnicos y de contenido.

**✅ Entregable semanal**
- **Primera versión integral del MVP.**
- Consulta de actividad y ubicación funcionando.
- Tres fuentes integradas.
- Información territorial disponible.
- Mapa interactivo operativo.
- Camino feliz completo.
- Consulta mediante IA integrada.
- Preguntas de seguimiento básicas.
- Trazabilidad de fuentes disponible.
- Primer testing completo realizado.

**❎ Dependencias semanal**
- Funcionalidades de las semanas anteriores integradas.
- Tres fuentes estables.
- Mapa y geocodificación funcionando.
- Información oficial suficiente para completar el caso piloto.
- Integración de IA operativa.

---

### Sprint 4 | Desarrollo

#### Semana 7

**Objetivo:** mejorar la confiabilidad de la información integrada y consolidar la trazabilidad entre consulta, respuesta y fuentes oficiales.

**Todos**
- Revisar qué información debe conservarse sobre cada fuente.
- Validar cómo comunicar información incompleta, desactualizada o no disponible.
- Acordar criterios para diferenciar datos territoriales, de contexto y de trámites.

**UX/UI**
- Mejorar la visualización del origen de la información.
- Diseñar estados para información disponible, incompleta o no encontrada.
- Ajustar la presentación de fuentes dentro de la orientación final.
- Revisar cómo se muestra el vínculo entre mapa, datos y trámites.

**Frontend**
- Incorporar referencias claras a las fuentes utilizadas.
- Mejorar estados de carga, error y falta de información.
- Permitir acceder desde una respuesta al detalle de la información que la respalda.
- Ajustar visualización de datos territoriales y capas del mapa.

**Backend**
- Consolidar metadatos de fuentes.
- Registrar origen y fecha de actualización cuando esté disponible.
- Mejorar validaciones sobre información recuperada.
- Gestionar correctamente respuestas parciales cuando alguna fuente no esté disponible.
- Reforzar la relación entre los datos utilizados y la respuesta generada.

**BI, Data & Machine Learning**
- Validar consistencia entre las tres fuentes.
- Revisar transformaciones y relaciones aplicadas.
- Identificar posibles contradicciones o faltantes.
- Ajustar reglas necesarias para mejorar la calidad de la información integrada.

**QA**
- Testear fuentes incompletas o temporalmente no disponibles.
- Validar que cada respuesta pueda vincularse con su fuente.
- Probar inconsistencias entre datos territoriales y de trámites.
- Verificar que la plataforma no presente como válida información sin respaldo.

**✅ Entregable semanal**
- Trazabilidad de fuentes consolidada.
- Origen de la información visible.
- Manejo de datos incompletos implementado.
- Relación entre respuesta, mapa y fuentes validada.
- Mayor confiabilidad del recorrido completo.

**❎ Dependencias semanal**
- MVP integral de Semana 6.
- Tres fuentes estables.
- Metadatos mínimos disponibles.
- Estructura de respuesta consolidada.

#### Semana 8

**Objetivo:** fortalecer la experiencia de consulta mediante IA y consolidar el MVP para la etapa de iteración.

**Todos**
- Definir las consultas prioritarias que deberá resolver correctamente el caso piloto.
- Revisar qué preguntas de seguimiento aportan valor.
- Acordar cómo deberá responder la plataforma cuando la consulta exceda la información disponible.

**UX/UI**
- Mejorar la experiencia conversacional.
- Diseñar sugerencias de preguntas de seguimiento.
- Diferenciar claramente:
  - respuesta principal;
  - pasos a seguir;
  - información territorial;
  - mapa;
  - fuentes utilizadas.
- Ajustar mensajes cuando no exista información suficiente.

**Frontend**
- Mejorar presentación de respuestas generadas mediante IA.
- Incorporar preguntas sugeridas.
- Facilitar navegación entre respuesta, mapa, requisitos y fuentes.
- Optimizar interacción con el mapa dentro del recorrido de consulta.

**Backend**
- Optimizar la preparación del contexto utilizado por la IA.
- Mejorar identificación de actividad y ubicación.
- Controlar que las preguntas de seguimiento mantengan el contexto de la consulta inicial.
- Incorporar manejo de consultas ambiguas, incompletas o fuera del alcance.
- Reforzar restricciones para evitar respuestas no respaldadas.

**BI, Data & Machine Learning**
- Construir un conjunto de consultas y respuestas esperadas.
- Validar resultados contra las fuentes oficiales.
- Ajustar la información estructurada utilizada por la IA.
- Revisar coherencia entre territorio, contexto y trámites.

**QA**
- Testear preguntas principales y de seguimiento.
- Probar variaciones de redacción para una misma necesidad.
- Validar consultas ambiguas o fuera del alcance.
- Comparar respuestas obtenidas con información oficial.
- Ejecutar nuevamente el flujo completo.

**✅ Entregable semanal**
- Consulta mediante IA estabilizada.
- Preguntas de seguimiento operativas.
- Respuestas respaldadas por las fuentes integradas.
- Manejo de consultas sin información suficiente.
- Mapa y orientación integrados dentro de la experiencia.
- **MVP completo listo para iteración y testing intensivo.**

**❎ Dependencias semanal**
- Trazabilidad consolidada.
- Tres fuentes disponibles.
- Información territorial y de trámites estable.
- Integración con IA operativa.
- Caso piloto suficientemente completo para realizar pruebas.

---

### Sprint 5 | Iterar

#### Semana 9

**Objetivo:** optimizar la calidad de la información, la experiencia de consulta y la consistencia de las respuestas a partir del testing integral del MVP.

**Todos**
- Revisar resultados del testing end-to-end.
- Priorizar bugs y ajustes según impacto.
- Validar nuevamente el caso piloto completo.
- Revisar si el recorrido responde correctamente a la necesidad ciudadana planteada.

**UX/UI**
- Ajustar navegación, jerarquías y presentación de resultados.
- Mejorar claridad de mapa, pasos, requisitos, documentación y fuentes.
- Revisar mensajes de error, falta de información o consultas fuera de alcance.
- Ajustar la experiencia conversacional y preguntas de seguimiento.

**Frontend**
- Corregir inconsistencias de interfaz.
- Mejorar interacción con el mapa.
- Optimizar tiempos de carga y comportamiento general.
- Ajustar la navegación entre respuesta, fuentes y detalle territorial.

**Backend**
- Optimizar integración y procesamiento de las fuentes.
- Mejorar manejo de errores y disponibilidad parcial de información.
- Revisar geocodificación y recuperación de datos territoriales.
- Ajustar preparación de contexto para la IA.
- Reforzar trazabilidad y respaldo de las respuestas.

**BI, Data & Machine Learning**
- Revisar calidad y consistencia de los datos integrados.
- Validar relaciones entre actividad, ubicación, territorio y trámites.
- Ajustar transformaciones y reglas de integración.
- Revisar respuestas generadas mediante IA contra las fuentes oficiales.

**QA**
- Realizar pruebas intensivas del flujo completo.
- Ejecutar pruebas de regresión.
- Probar variaciones de consultas, direcciones y preguntas de seguimiento.
- Registrar y priorizar bugs técnicos y de contenido.

**✅ Entregable semanal**
- MVP optimizado.
- Principales inconsistencias corregidas.
- Información territorial y de trámites revisada.
- Respuestas de IA validadas.
- Experiencia de consulta mejorada.
- Bugs documentados y priorizados.

**❎ Dependencias semanal**
- MVP completo de Semana 8.
- Tres fuentes estables.
- Datos y consultas suficientes para testing.
- Mapa, geocodificación e IA operativos.

#### Semana 10

**Objetivo:** realizar el testing final y alcanzar una versión candidata estable del MVP.

**Todos**
- Validar cada requisito mínimo del proyecto.
- Revisar el recorrido que se utilizará para demostrar la solución.
- Confirmar alcance final del caso piloto.
- Resolver ajustes funcionales pendientes.

**UX/UI**
- Resolver inconsistencias finales de experiencia.
- Revisar accesibilidad, estados y mensajes.
- Preparar el recorrido principal para la demo.
- Validar que una persona pueda comprender qué tiene que hacer sin conocer previamente las fuentes o sistemas involucrados.

**Frontend**
- Corregir bugs priorizados.
- Consolidar consulta, mapa, orientación y preguntas de seguimiento.
- Optimizar rendimiento general.
- Preparar una versión candidata estable.

**Backend**
- Validar estabilidad de integración con las tres fuentes.
- Revisar geocodificación, procesamiento territorial y lógica de trámites.
- Validar trazabilidad y disponibilidad de fuentes.
- Revisar estabilidad de la integración con IA.

**BI, Data & Machine Learning**
- Validar resultados finales del caso piloto.
- Confirmar consistencia entre fuentes, territorio, trámites y respuestas.
- Preparar ejemplos representativos para la demostración.
- Documentar limitaciones de información conocidas.

**QA**
- Ejecutar pruebas completas de punta a punta.
- Validar criterios de aceptación del MVP.
- Confirmar que las respuestas estén respaldadas por fuentes integradas.
- Verificar que no existan errores críticos o bloqueantes.

**✅ Entregable semanal**
- **Release Candidate estable.**
- Caso piloto completo validado.
- Tres fuentes integradas y funcionando.
- Mapa e información territorial operativos.
- Camino feliz completo.
- Consulta mediante IA estable.
- Bugs críticos resueltos.

**❎ Dependencias semanal**
- Testing de Semana 9 completado.
- Bugs priorizados.
- Fuentes y servicios disponibles.
- Funcionalidades principales operativas.

---

### Sprint 6 | Cierre

#### Semana 11

**Objetivo:** realizar la validación final del producto en condiciones cercanas a una demostración real y resolver los últimos errores críticos.

**Todos**
- Ejecutar el recorrido completo del caso piloto.
- Validar que cada requisito del MVP esté implementado.
- Revisar consistencia entre consulta, ubicación, fuentes, mapa, trámites e IA.
- Congelar el alcance: no incorporar nuevas funcionalidades.

**UX/UI**
- Realizar revisión final de experiencia y accesibilidad.
- Ajustar textos, jerarquías y estados.
- Validar que el camino de trámites sea fácil de interpretar.
- Revisar experiencia en distintas resoluciones.

**Frontend**
- Resolver bugs finales.
- Validar comportamiento responsive.
- Optimizar carga del mapa y presentación de resultados.
- Preparar la versión final para despliegue.

**Backend**
- Validar estabilidad de APIs y servicios.
- Comprobar disponibilidad y procesamiento de las tres fuentes.
- Revisar manejo de errores y fallbacks.
- Validar geocodificación, trazabilidad y conexión con IA.

**BI, Data & Machine Learning**
- Realizar control final de información integrada.
- Validar las respuestas de referencia contra las fuentes.
- Documentar transformaciones, relaciones y limitaciones conocidas.
- Confirmar que la IA no incorpore información sin respaldo.

**QA**
- Ejecutar testing de regresión final.
- Validar todos los criterios de aceptación.
- Realizar pruebas negativas y escenarios de falla.
- Confirmar ausencia de bugs críticos o bloqueantes.

**✅ Entregable semanal**
- Versión final funcional.
- MVP validado de punta a punta.
- Fuentes, mapa, trámites e IA verificados.
- Bugs críticos resueltos.
- Limitaciones conocidas documentadas.

**❎ Dependencias semanal**
- Release Candidate de Semana 10.
- Fuentes y servicios disponibles.
- Todos los requisitos mínimos implementados.

#### Semana 12

**Objetivo:** desplegar, documentar y presentar la solución desarrollada.

**Todos**
- Preparar demostración final.
- Documentar alcance alcanzado y decisiones tomadas.
- Registrar funcionalidades que quedan para Future Scope.
- Preparar presentación del problema, solución y recorrido del usuario.

**UX/UI**
- Preparar flujo visual para la demo.
- Documentar decisiones principales de experiencia.
- Organizar prototipos y archivos finales.

**Frontend**
- Realizar despliegue final de la aplicación web.
- Validar funcionamiento del entorno publicado.
- Documentar instalación, configuración y ejecución del frontend.

**Backend**
- Desplegar servicios necesarios.
- Documentar arquitectura, endpoints, variables de entorno e integraciones.
- Registrar configuración de fuentes, geocodificación e IA.
- Documentar procedimiento básico de mantenimiento.

**BI, Data & Machine Learning**
- Documentar fuentes utilizadas.
- Registrar procesos de transformación y relación.
- Preparar ejemplos que demuestren cómo se construye una respuesta desde las fuentes.
- Documentar limitaciones y oportunidades de ampliación.

**QA**
- Ejecutar smoke test sobre la versión publicada.
- Preparar reporte final de calidad.
- Documentar casos de prueba y resultados.
- Confirmar estado final de bugs.

**✅ Entregable semanal**
- **MVP desplegado y funcional.**
- Caso piloto demostrable de punta a punta.
- Al menos tres fuentes efectivamente integradas.
- Información territorial y mapa interactivo.
- Camino feliz de trámites, requisitos y documentación.
- Consulta y profundización mediante IA.
- Trazabilidad de las fuentes.
- Documentación técnica y funcional.
- Presentación final del proyecto.

**❎ Dependencias semanal**
- Validación final de Semana 11.
- Acceso a infraestructura de despliegue.
- Credenciales y servicios externos necesarios.
- Documentación de cada área completada.

## 9. Consideraciones sobre licencias y escalabilidad

Para el desarrollo del MVP se priorizará el uso de **herramientas open source, versiones gratuitas y planes iniciales**. Estos recursos podrían resultar suficientes para construir y validar el prototipo; sin embargo, según el volumen de consultas, geocodificación, mapas, almacenamiento o consumo de IA, podría ser necesario contratar algún servicio pago incluso durante el desarrollo.

A medida que la solución incorpore más actividades, fuentes, usuarios, consultas territoriales o integraciones institucionales, será necesario evaluar una infraestructura y esquema de licenciamiento acordes a ese crecimiento.
