# Versionado de catálogos e ingesta incremental

**Estado:** para más adelante

## La idea

Traquear en la base las versiones de los catálogos oficiales ingeridos (trámites de la Ciudad, y a futuro otros) y detectar diferencias contra la fuente, para **solo subir a la base lo que cambió** en vez de reconstruir todo en cada corrida.

## Por qué

- `uv run python -m conco.guidance.load_catalog` hoy es **reconstrucción total**: baja los ~870 trámites publicados, recalcula los embeddings de los alias (Cloudflare Workers AI) y hace `truncate` + re-insert de `procedures`, `activities`, `activity_aliases` y `activity_procedures` en una sola transacción.
- Eso garantiza consistencia y es atómico, pero: la presión sobre la API oficial y el costo de embeddings se pagan en cada corrida aunque no cambió nada, y hay que recordarlo a mano cada vez.
- Con requerimientos migrados a la base (`procedure_requirements`, ver [../pendientes/requerimientos-checklist.md](../pendientes/requerimientos-checklist.md)), cada re-migración total también re-descarga y re-parsea los detalles de los ~18 trámites referenciados.

## Cómo funcionaría

1. **Tabla de versiones** (por fuente/catálogo): `catalog_versions (name, source_url, fetched_at, changed_at_max, content_hash)` — una fila por corrida e inscripción de la versión observada en la fuente.
2. **Marcas de cambio por registro**: guardar en `procedures` el `changed_at` que publica la API (ya se guarda) y un hash del contenido normalizado con el que se cargó cada fila.
3. **Diferenciación por consolidación**: al correr la ingesta, bajar la lista publicada, comparar `id` + `changed_at` + hash contra la tabla, y solo:
   - insertar los trámites nuevos referenciados;
   - re-pedir el detalle (y re-escribir sus `procedure_requirements`) solo de los que cambiaron;
   - marcar como `unpublished` (o borrar, según política RN-05) los que la fuente ya no publica.
4. **Guía de actualización** en `back/README.md`: cómo disparar la ingesta incremental, cómo forzar reconstrucción total, y cómo verificar.

## Qué hay que tener en cuenta

- La API de la Ciudad **no publica historial**: `changed_at` es lo único para detectar cambios; si la Ciudad corrige el cuerpo de un trámite sin tocar `changed_at` (o con fecha igual), un hash de contenido lo atrapa — por eso hacen falta ambos.
- El embeddinado de alias no es parte del `changed_at` de los trámites: sigue siendo reconstrucción puntual al cambiar `activities.json`, no en cada ingesta.
- Atomicidad se mantiene igual: todo en una transacción; si la diferenciación falla, la base queda en la versión anterior.
- Log/mostrable: `ingest_report` con altas, bajas, actualizados y sin cambios, para poder auditar que la ingesta hizo lo que decía.
- Sigue siendo necesario poder reconstruir total (880 trámites de una) para emergencias y bootstrap — la ingesta incremental es el modo normal, no el único.
- No antes de que exista la tabla de versiones y las marcas de contenido: sin ellas, «incremental» es imposible de verificar.

## Cuándo evaluarla

Después del backfill de requerimientos y de la primera re-corrida de `load_catalog` en producción/demo repetida; medir cuánto pesa una corrida hoy y recién ahí decidir si la diferenciación se justifica.
