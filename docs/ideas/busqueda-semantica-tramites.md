# Relacionar la actividad con los trámites usando búsqueda semántica

**Estado:** para más adelante (depende de RN-01)

## La idea

Vectorizar los trámites oficiales de la Ciudad con un modelo de embeddings y guardarlos en una base con búsqueda vectorial. Cuando la persona indica su actividad (por ejemplo, «cafetería»), se vectoriza ese texto y se buscan los trámites más cercanos por significado, no por coincidencia de palabras.

## Para qué sirve

- **Resolver el problema central del producto.** La API de trámites de CABA solo busca por texto en el título: «caf» devuelve 0 resultados. La persona piensa en su actividad y la Ciudad organiza los trámites por tipo («Habilitación de actividad económica»). Falta un puente entre los dos vocabularios.
- **No inventar trámites.** La búsqueda solo devuelve trámites reales del catálogo oficial, con su enlace (RN-04, RN-05). Opcionalmente, un LLM puede reordenar o explicar los resultados, pero siempre eligiendo entre ellos.
- **Crecer con más fuentes.** Con 868 trámites alcanzaría con tenerlos en memoria; la base vectorial se justifica al sumar normativa, Código Urbanístico o Boletín Oficial.

## Cómo funcionaría

1. **Ingesta (periódica, offline):** traer los trámites publicados, armar un texto por trámite (título, resumen, requisitos, organismo), generar su embedding y guardarlo con su id y enlace oficial.
2. **Consulta:** vectorizar la actividad con **el mismo modelo** y pedir los vecinos más cercanos (por ejemplo, los 10 primeros).

Si se cambia de modelo, hay que volver a vectorizar todo: los vectores de modelos distintos no son comparables.

## Opción gratuita evaluada

| Pieza | Elección | Notas |
|---|---|---|
| Base de datos | Supabase (plan gratuito) con pgvector | pgvector es open source. El proyecto gratuito se pausa si no se usa: verificarlo antes de una demo. |
| Backend + modelo | VM de Oracle Cloud Always Free | FastAPI y el modelo en el mismo proceso, para evitar un salto de red extra. |
| Modelo | Multilingüe liviano, por ejemplo `paraphrase-multilingual-MiniLM-L12-v2` o `intfloat/multilingual-e5-small` | Los trámites están en español. La elección final queda pendiente de una prueba comparativa. |

Elegir regiones cercanas para la VM y Supabase: cada búsqueda cruza de una a otra.

## Qué hay que tener en cuenta

- **El cuello de botella es la memoria, no el tiempo.** Vectorizar una frase corta tarda milisegundos, pero el modelo tiene que estar cargado todo el tiempo. Valores aproximados, sin medir:
  - Modelo multilingüe liviano con PyTorch en fp32: unos 0,8–1 GB de proceso.
  - El mismo modelo con ONNX Runtime (por ejemplo, la librería `fastembed`) y cuantizado a int8: unos 300–400 MB.
- **VM de 1 GB.** Entra con ONNX + int8, justo. Agregar swap como red de seguridad. Las VM Ampere A1 (ARM) del plan gratuito de Oracle ofrecen mucha más memoria, pero suele faltar capacidad en las regiones populares. Confirmar las condiciones actuales del plan gratuito.
- **Supabase tiene embeddings integrados** en Edge Functions (`gte-small`), pero el modelo apunta a inglés.
- **Datos desactualizados.** La copia local queda vieja hasta la próxima ingesta; mostrar la fecha de actualización que ya devuelve la API.
- **RN-01 sigue pendiente.** Hoy dice «buscador, no IA». Hay que validar con producto si un modelo de embeddings entra en esa regla.

## Alternativa sin modelo en producción

Si la entrada es una **lista cerrada de actividades** (cafetería, peluquería, kiosco…), se puede precalcular offline la relación «actividad → trámites» y guardarla ya resuelta. En producción solo queda una consulta común: gratis, rápida, determinística y revisable a mano. Se pierde el texto libre: una actividad fuera de la lista no tiene resultados.

## Cuándo hacerla

Después de decidir RN-01. Para el MVP alcanza con la alternativa precalculada; la búsqueda semántica en vivo, cuando se sumen más fuentes o texto libre.
