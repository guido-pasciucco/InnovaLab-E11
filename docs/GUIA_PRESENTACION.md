# Guía para la presentación

Qué mostrar, qué decir y qué **no** prometer. Estado al 2026-11-05 (rama `feature/04-caba-tramites-integration`, PR #65).

## En una frase

La persona escribe qué quiere hacer y dónde. CONCO **ubica la dirección con datos oficiales** y le muestra **los trámites oficiales de la Ciudad que suelen aplicar a su actividad**, con enlace a la fuente. El análisis del paso 2, las capas del mapa y el asistente todavía son **demostración**.

## Qué es real y qué es demostración

| Paso de la pantalla | Qué se ve | Estado | De dónde sale |
|---|---|---|---|
| 1 · Actividad | Sugerencias mientras se escribe («barbería» → Peluquería) | ✅ Real | Base propia con actividades curadas + búsqueda semántica (embeddings) |
| 1 · Dirección | Autocompletado con direcciones normalizadas de CABA | ✅ Real | API Georef (Gobierno Nacional) |
| 2 · Análisis | Pantalla de «interpretando tu consulta» | ⚠️ Demostración | Espera simulada; no hay análisis real |
| 3 · Orientación (con actividad elegida) | Trámites oficiales, cuándo aplica cada uno, resumen, enlace y fuente | ✅ Real | API de trámites de la Ciudad + relación curada |
| 3 · Preguntas de contexto | «¿Vas a contratar personal?», «¿menos de 200 m²?»… descartan trámites en vivo | ✅ Real | Condiciones de la relación curada |
| 3 · Orientación (sin actividad elegida) | Tres pasos genéricos | ⚠️ Demostración | Datos fijos del frontend |
| 3 · Fuentes | «Trámites del Gobierno de la Ciudad», con licencia | ✅ Real | API de trámites de la Ciudad |
| 3 · Fuentes | «Guía oficial de habilitaciones (fuente piloto)» y dos datasets piloto | ⚠️ Demostración | Datos fijos del frontend |
| 4 · Mapa | Marcador en la dirección elegida | ✅ Real | Coordenadas de Georef |
| 4 · Mapa | Capas territoriales (zonificación, etc.) | ❌ No existe | Ninguna fuente integrada |
| 5 · Asistente | Respuesta a preguntas | ⚠️ Demostración | Texto fijo; no hay IA conectada |

> Para la demo, el frontend tiene que usar los datos simulados de la consulta (`VITE_USE_MOCK_API` sin definir o distinto de `false`). El backend todavía no tiene `/consultations`: con `false`, el envío falla.

## Cómo funciona la búsqueda por detrás

**Preparación (una vez, con `load_catalog`):**

1. Se traen de la API de la Ciudad los 868 trámites publicados y se guardan en Postgres.
2. Se lee la lista curada (`activities.json`): cada actividad con sus sinónimos y sus trámites, con una nota de cuándo aplica cada uno.
3. Un modelo de embeddings convierte cada nombre y sinónimo de actividad («peluquería», «barbería», «estética»…) en un vector de 384 números que representa su **significado**. Los vectores se guardan en la base (pgvector).

**En cada búsqueda:**

1. La persona escribe «quiero poner una barbería». El backend convierte ese texto en un vector con el **mismo** modelo.
2. Postgres compara ese vector con los de todos los sinónimos (similitud coseno: cuánto apuntan en la misma dirección) y devuelve las actividades más parecidas, descartando las que quedan por debajo de 0.5.
3. La persona elige «Peluquería» de la lista.
4. El backend busca en la lista curada los trámites de esa actividad y los devuelve con su nota, su resumen, el enlace oficial y la fuente. En este paso no interviene la IA: es una consulta común a la base.

```text
"quiero poner una barbería" → vector → actividad más parecida: Peluquería (0.85)
                                        → trámites curados de Peluquería → pantalla
```

**Por qué así:** la IA solo resuelve el **vocabulario** (barbería ≈ peluquería). Qué trámites corresponden lo decide una lista que una persona puede revisar, así que nunca aparecen trámites inventados. Buscar directamente en los textos de los trámites no funcionaba, porque ninguno menciona actividades.

## Guion sugerido (5 minutos)

1. **El problema.** «Quiero abrir una cafetería en Av. Cabildo 2040: ¿qué trámites necesito?». La información oficial existe, pero está organizada por trámite, no por actividad.
2. **Dirección real.** Escribir `Av. Santa Fe 1800` y elegir la sugerencia. Decir: «normalizamos la dirección con Georef, la API oficial de direcciones, y la ubicamos en el mapa».
3. **Actividad con otras palabras.** Escribir `quiero poner una barbería`. Aparece **Peluquería · parecido a «barbería»**. Decir: «el sistema entiende el significado, no solo las palabras: barbería no aparece en ningún lado y aun así encuentra peluquería».
4. **Trámites oficiales.** Enviar y mostrar el paso 3: Habilitación de actividad económica (y la exprés), cartel o toldo, Registro de Empleadores. Señalar **«Cuándo aplica»** y el enlace a buenosaires.gob.ar. Decir: «cada trámite viene de la Ciudad y cita su fuente».
5. **Más contexto, lista más precisa.** En «Contanos más de tu comercio», responder «No» a personal y «Sí» a menos de 200 m²: desaparecen el Registro de Empleadores y la rúbrica laboral. Después «Sí» a continuar un local ya habilitado: las habilitaciones se reemplazan por la Transmisión. Decir: «la habilitación es una sola; lo que cambia según tu comercio son los trámites que se suman».
6. **Honestidad del sistema.** Volver, escribir `quiero abrir un gimnasio`: «No encontramos una actividad parecida». Decir: «si no sabemos, lo decimos; no inventamos trámites».
7. **Mapa.** Mostrar el marcador. Aclarar que las capas territoriales todavía no están.
8. **Cierre.** Próximos pasos: validar la lista curada con alguien del área, sumar actividades, Código Urbanístico para saber si la actividad está permitida en esa dirección.

Consultas que salen bien: `cafetería`, `abrir una confitería`, `quiero poner una barbería`, `vender pizzas`, `food truck`, `local de ropa`.

Evitar en vivo: `abrir un maxikiosco` y `local de zapatillas` (sugieren Restaurante primero) y `oficina` (sugiere Peluquería). Para mostrar el caso «no encontramos», usar `quiero abrir un gimnasio`.

## Lo que todavía no hace

- **No dice si la actividad está permitida en esa dirección.** Eso depende del Código Urbanístico (usos por zona), que es otra fuente y no está integrada.
- **Personaliza poco.** Seis preguntas de sí o no descartan trámites, pero no decide entre habilitación común y exprés (eso depende del rubro y la zona, en el Código Urbanístico) y las condiciones son un borrador sin validar.
- **No analiza la consulta.** El paso 2 es una espera simulada; no hay IA interpretando el texto.
- **El asistente no responde de verdad.** Devuelve un texto fijo.
- **El mapa no tiene capas.** Solo el marcador de la dirección.
- **No muestra requisitos ni pasos de cada trámite en la pantalla**, aunque el backend ya los tiene (`GET /guidance/procedures/{id}`); hoy se llega a ellos por el enlace oficial.

## Limitaciones a conocer

### Actividades curadas

- **Son 6:** cafetería, restaurante, kiosco, peluquería, comercio minorista y foodtruck, con 34 sinónimos y 12 trámites distintos. Cualquier otra actividad no tiene trámites.
- **Es un borrador sin validar.** La relación actividad → trámites la armó el equipo técnico eligiendo entre los 74 trámites que la Ciudad marca como «de negocio». Tiene que revisarla alguien que conozca habilitaciones antes de mostrarse a usuarios reales (RN-04). Es orientación general, no una determinación legal.
- **Las sugerencias pueden fallar con palabras cortas o poco comunes.** El modelo da similitudes altas sin sentido: «abrir un maxikiosco» sugiere Restaurante antes que Kiosco (aunque «maxikiosco» solo encuentra Kiosco), y «oficina», que no está en el catálogo, sugiere Peluquería en vez de decir que no hay coincidencia. Por eso la persona elige de la lista y el sistema nunca elige solo.
- **El umbral de 0.5 se ajustó a mano** con pocas consultas; con más actividades hay que revisarlo.
- **Se actualiza a mano.** Agregar una actividad es editar `back/src/conco/guidance/data/activities.json` y volver a correr la carga.

### API Georef (direcciones)

- **Está en estado *alpha*** y sus cuotas de uso sin autenticación no están publicadas. El autocompletado hace un pedido cada vez que la persona deja de escribir; con mucho uso podría empezar a rechazar pedidos (hay un token con más cuota que se pide por mail).
- **Algunas calles no tienen numeración** en Georef: con «calle + altura» no encuentra nada. El frontend ofrece la calle con una ubicación aproximada y lo avisa.
- **Las coordenadas son aproximadas** (RN-03) y a veces vienen vacías: ahí el mapa no muestra marcador.
- **Solo CABA** (RN-02). Si Georef no responde, se puede continuar con la dirección escrita, sin mapa.

### API de trámites de la Ciudad

- **No tiene documentación pública.** Es el JSON:API del sitio Drupal de buenosaires.gob.ar: puede cambiar sin aviso. Si cambia, la API de CONCO responde un error controlado, pero la búsqueda deja de funcionar hasta adaptarla.
- **Solo busca por texto en el título**: «caf» devuelve 0 resultados. Por eso hizo falta la relación curada.
- **Ningún trámite menciona actividades.** «Habilitación de actividad económica» sirve igual para una cafetería que para una peluquería.
- **Copia local.** Los trámites que se muestran con cada actividad salen de una copia en la base, que se actualiza al correr la carga (868 trámites publicados). Si la Ciudad cambia un trámite, la copia queda vieja hasta la próxima carga; la pantalla no muestra la fecha de actualización, aunque la API la devuelve.
- **Licencia:** Creative Commons Reconocimiento 2.5 Argentina; por eso se cita la fuente.

### Infraestructura

- **Necesita una base de datos** Postgres con la extensión pgvector (en desarrollo, el Supabase local de `back/supabase/`).
- **El modelo de embeddings corre dentro de la API** y ocupa unos 600 MB de RAM. La primera vez se descarga (~220 MB); hasta que termina de cargar, las primeras búsquedas pueden tardar.
- **Todo gratis**, pero el despliegue tiene que entrar en esa memoria (la VM gratuita de 1 GB de Oracle queda justa).

## Preguntas probables

- **¿Usan IA?** Sí, para entender lo que escribe la persona (embeddings). Qué trámites corresponden a cada actividad lo decide una lista revisable, no la IA. Así nunca aparecen trámites inventados.
- **¿Por qué no le preguntan todo a un modelo de lenguaje?** Porque podría inventar trámites o requisitos. Preferimos datos oficiales con fuente y una relación que alguien pueda revisar.
- **¿Qué pasa si escribo algo raro?** Si no hay una actividad parecida, lo dice y muestra la orientación general.
- **¿Está actualizado?** Los trámites vienen de la Ciudad y se recargan con un comando; falta programar esa recarga.
- **¿Cuánto cuesta?** Las dos APIs son gratuitas y sin clave; el modelo es open source y corre en nuestro servidor.

## Checklist antes de presentar

Desde `back/` (con Docker):

```bash
npx supabase start -x gotrue,realtime,storage-api,imgproxy,kong,mailpit,postgrest,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
uv run python -m conco.guidance.load_catalog
uv run uvicorn conco.main:app --port 8000
```

Desde `front/`:

```bash
npm run dev
```

- [ ] La carga terminó con «Cargados 868 trámites y 6 actividades».
- [ ] Esperar unos segundos después de levantar el backend para que cargue el modelo.
- [ ] Probar una vez cada consulta del guion antes de entrar.
- [ ] Con internet: Georef y la Ciudad se consultan en vivo.
