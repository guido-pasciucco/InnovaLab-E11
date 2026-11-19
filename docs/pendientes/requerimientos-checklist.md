# Requerimientos como checklist agregado (diseño)

> Estado: **diseño cerrado con el dueño del producto (2026-11-12). Estado de implementación: migración `procedure_requirements` creada y backfill corrido en la base local (193 ítems para 18 trámites, 2026-11-12). Sigue pendiente: exposición en la API + front (diseño abajo).**
> Contexto: [HABILITACION_Y_CATALOGO.md](HABILITACION_Y_CATALOGO.md) · fuente normativa del relevamiento: [TRAMITES_Y_REQUERIMIENTOS.md](../habilitacion-caba/TRAMITES_Y_REQUERIMIENTOS.md) (Notion, 2026-11-10, @Malena).

## Decisiones del dueño (2026-11-12)

- **A.** Solo los requerimientos que publica la API oficial de la Ciudad; **sin** complemento curado del relevamiento en este ciclo.
- **C.** El panel mock «Fuentes consultadas» (`front/src/Componentes/SourceList.tsx`, alimentado por `front/src/api/mock.ts` con las 3 fuentes «piloto») se **reemplaza** por el checklist de requerimientos + una lista de fuentes reales. Ubicación: **al costado de los trámites** (la `side-column` actual, junto a «Lo que entendimos»).
- **D.** Este documento es la referencia del diseño.
- **Persistencia.** Los requerimientos se **migran a la base de datos**, relacionados con los trámites existentes (FK a `procedures`), como el resto del catálogo cargado por el loader.

## Hallazgos de datos (verificados 2026-11-12)

1. La API de trámites de la Ciudad (`node/tramites_obelisco`) publica requisitos **por trámite** (párrafo `item_requisito_tramite`: título opcional + cuerpos HTML). Verificado en vivo:
   - «Habilitación de actividad económica» (`338718b4-a2a0-44af-baa4-083f5d834b12`): miBA nivel 3 · Formulario de conformación (DJ) · **Anexo Técnico** firmado por profesional (encomienda, croquis).
   - «Habilitación exprés» (`15e0394b-c7b5-4f93-bc25-ee012d695aec`): ≤200 m² · sin inflamables · accesibilidad · sin galerías/áreas especiales · etc.
2. No existe API pública de **requerimientos por rubro** ni de **«comunes para todos»**: Ciudad 3D da mixtura de usos (no requisitos), BA Data `habilitaciones-aprobadas` da vocabulario de rubros (no requisitos), datos.gob.ar no tiene nada para CABA (re-verificado hoy), el JSON:API no tiene nodos de rubro.
3. El backend **ya integra** el detalle: `ProcedureDetail.requirements` ([back/src/conco/guidance/domain.py:32](../../back/src/conco/guidance/domain.py)) con endpoint `GET /guidance/procedures/{id}` ([back/src/conco/guidance/api.py:171](../../back/src/conco/guidance/api.py)). Pero **el front nunca lo llama**: los requisitos no se muestran hoy.
4. Traslape con el relevamiento: los «requerimientos comunes» del doc (plano/croquis, encomienda + declaración responsable, burocracia miBA) ya están publicados por la API por trámite. Por decisión A, no se duplican a mano.

## Diseño

### 1. Base de datos (migración `20261112000001_procedure_requirements.sql` — aplicada en la base local el 2026-11-12)

```sql
create table public.procedure_requirements (
    procedure_id uuid not null references public.procedures(id) on delete cascade,
    position     int  not null,   -- orden dentro del trámite (orden de la página, plano por cuerpo)
    text         text not null,   -- texto plano del cuerpo (field_cuerpo), una sola línea
    heading      text,            -- field_texto del ítem, si tiene (p. ej. «Requisitos obligatorios») — migración 20261112000002
    primary key (procedure_id, position)
);
```

- Los cuerpos (`field_cuerpo`) quedan como texto **plano** de una sola línea, sin HTML. Los encabezados (`field_texto`) se guardan como columna propia (`heading`), separados del cuerpo — nada viaja fusionado. El orden original se preserva con `position` (aplanado ítem→cuerpos).
- `load_catalog` trunca con `cascade` y reescribe la tabla en la misma transacción; para refrescar **solo** los requerimientos (sin tocar el resto) existe:

  ```bash
  uv run python -m conco.guidance.load_requirements
  ```

  Lee los `id` presentes en `procedures`, pide el detalle oficial de cada uno y reescribe la tabla. Si algún trámite ya no existe en la fuente, **no toca la base** y falla listando los faltantes.

### 2. Loader extendido — implementado

`load_catalog` llama `get_procedure(id)` para los ~18 trámites referenciados y guarda los ítems en la misma transacción que el resto (fallo de un detalle → el loader falla entero, la base queda como estaba). Rediseño evitado adrede: no hay forma de accidentalmente dejar la base sin requerimientos al reconstruir el catálogo. `load_requirements` (`back/src/conco/guidance/load_requirements.py`) comparte la misma lógica de fetch/reescritura para el refresco puntual.

### 3. Lectura y agregado

- `activity_directory` gana un método/join que trae requisitos de los trámites de la actividad.
- Agregar en respuesta de `GET /guidance/activities/{slug}/procedures`:

```jsonc
{
  "activity": {...},
  "questions": [...],
  "procedures": [...],
  "requirements": [
    {
      "id": "req-<hash>",
      "text": "Contar con usuario y clave miBA nivel 3.",
      "heading": null,
      "origins": [
        { "procedure_id": "3387…", "procedure_title": "Habilitación de actividad económica",
          "official_url": "https://buenosaires.gob.ar/tramites/habilitacion-de-actividad-economica" }
      ]
    }
  ],
  "requirements_note": "Fuente oficial: páginas de los trámites. Es una orientación general; verificá siempre con el organismo."
}
```

- **Desduplicación**: clave = texto normalizado (strip HTML, minúsculas, sin acentos, espacios colapsados). Los ítems duplicados entre trámites se **fusionan** sumando sus `origins` (miBA aparece en todos). Opcional: mapa de sinónimos curados para casos que no coinciden al 100 % (p. ej. «Anexo Técnico» entre trámites) — decidir en implementación con los fixtures reales.
- Filas `items` jsonb → se aplanan en un ítem por cuerpo (un checklist item por cuerpo no vacío).

### 4. Front

- `side-column` de la pantalla de resultados: reemplazar el panel «Fuentes consultadas» (`SourceList`) por:
  1. **Panel «Antes de empezar: lo que tenés que conseguir»** (subtítulo/nota con la palabra «requerimientos») — checklist único; cada ítem = texto + «del trámite: {título} ↗» (el enlace oficial de su origen). Checkbox con progreso propio (mismo patrón que la lista de trámites).
  2. **Fuentes reales** — lista slim derivada de los trámites mostrados (título + URL oficial + «CC BY 2.5 AR» de la fuente, RN-05). Nada de placeholders «piloto».
- El botón/Progreso del checklist de trámites no cambia. El avance de requerimientos es independiente.
- En modo mock (`VITE_USE_MOCK_API=true`): quitar las 3 fuentes «piloto» de `mock.ts`; la consulta demo sigue marcada como demostración en su `summary`/`limitations` (honestidad heredada), y las fuentes reales salen de `activityProcedures.source`.

### 5. Degradación y honestidad

- No hay llamadas de detalle en la consulta: la presión sobre la API de la Ciudad ocurre en el loader (en lote, una sola vez por carga), no por usuario.
- Datos tan frescos como el último `load_catalog` → documentar como mantenimiento rutinario (re-ejecutar tras cambios grandes del catálogo; idealmente cron semanal — decisión de despliegue, no de este diseño).
- Toda ítem del checklist enlaza la página oficial origen → RN-05 cumplido por construcción; RN-04: la sección cierra con el disclaimer de siempre («orientación general; la autoridad manda»).
- Nunca HTML de terceros en el front; todo pasa por texto plano en el loader.

### 6. Verificación prevista (cuando se autorice implementar)

- RED (tests): agregado con fixtures de 2 trámites que repiten miBA → una sola vez con dos `origins`; ítems por cuerpo; degradación si falta detalle en la base; `requirements` presente aunque `procedures` quede vacío por contexto; fuentes de cada ítem.
- Loader: idempotencia y atomicidad (fallo a mitad → base intacta).
- Front: render de panel + fuentes reales; ausencia de las fuentes «piloto».
- Suite completa (`uv run pytest -q` + lint/types del front) verde antes de cerrar.

### 7. Fuera de alcance de este ciclo (y por qué)

- Complemento curado del relevamiento (título sobre el local, DNI/CUIT, matafuegos, tasa): decisión A — otro ciclo.
- Forma jurídica / superficie graduada / edificio-instalaciones: tarea 5 del módulo.
- Ciudad 3D y variable «uso permitido en la zona»: decisión de API pendiente.
- Requisitos por patrón de rubro como first-class: ya viven, cuando corresponden, en los trámites específicos curados.

### 8. Preguntas abiertas — cerradas (2026-11-12)

- [x] **Desduplicación**: solo **clave normalizada** en v1 (minúsculas, sin acentos, sin HTML, espacios colapsados). Sin mapa de sinónimos curado; si los fixtures reales muestran variantes que no fusionan, se evalúa como parche después.
- [x] **Frecuencia de `load_catalog`**: documentada como mantenimiento manual en `back/README.md` (re-ejecutar tras cambios de catálogo o por rutina). **Sin** job automático por ahora — el cron es una decisión de despliegue independiente, fuera de este cambio. La idea de **versionado e ingesta incremental** quedó documentada aparte: [../ideas/catalogo-versionado-incremental.md](../ideas/catalogo-versionado-incremental.md).
- [x] **Empaquetado**: **todo en un solo PR** — migración + loader + respuesta de la API + front (panel + fuentes reales) + limpieza de `mock.ts`.
- [x] **Nombre del panel**: «Antes de empezar: lo que tenés que conseguir», con «requerimientos» en la nota o tooltip del panel.

## Referencias

- API en vivo: `https://buenosaires.gob.ar/jsonapi/node/tramites_obelisco/{id}` (probado 2026-11-12).
- Código: `back/src/conco/integrations/caba_tramites/`, `back/src/conco/guidance/`, `back/supabase/migrations/`.
- Fuentes de datos del módulo: `activities.json` (9 actividades / 53 alias / 18 trámites referenciados).
