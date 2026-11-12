# Levantar back y front en desarrollo

## Requisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| `uv` | última | Python y dependencias del backend |
| Docker | cualquiera reciente | Supabase local (base de datos) |
| `npx` (Node.js) | 20+ | Supabase CLI y frontend |

## 1. Base de datos (solo para búsqueda de actividades)

Desde `back/`, con Docker corriendo:

```bash
cd back
npx supabase start -x gotrue,realtime,storage-api,imgproxy,kong,mailpit,postgrest,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
uv run python -m conco.guidance.load_catalog
```

- El primer `supabase start` aplica las migraciones y expone Postgres en `127.0.0.1:55322`.
- `load_catalog` descarga los trámites de buenosaires.gob.ar y vectoriza las actividades (~600 MB de RAM en la API al usar el modelo de embeddings; la primera vez descarga ~220 MB del modelo).
- Si cambiás `src/conco/guidance/data/activities.json`, volvé a correr `load_catalog`.
- Sin esta base, el backend levanta igual pero `/guidance/activities` responde `503`.

## 2. Backend

```bash
cd back
uv sync            # solo la primera vez (o tras cambios en pyproject.toml)
make run           # = uv run uvicorn conco.main:app --reload
```

- API en `http://127.0.0.1:8000`
- Documentación interactiva: `http://127.0.0.1:8000/docs`
- Configuración en `back/.env` (ya existe; plantilla en `.env.example`). No requiere claves: Georef y la API de trámites de CABA son públicas.

## 3. Frontend

```bash
cd front
npm ci             # solo la primera vez
npm run dev
```

- App en `http://localhost:5173`
- `/api/*` se reenvía automáticamente al backend en `localhost:8000` (ver `vite.config.ts`).

## 4. Mock vs. backend real

`front/.env` tiene `VITE_USE_MOCK_API`:

- `true` (actual): los datos de consulta y asistente son simulados. Las sugerencias de direcciones y actividades **siempre** pegan al backend real.
- `false`: todo va contra el backend en `localhost:8000`.

## Checklist rápido

- [ ] `npx supabase start ...` (desde `back/`) → Postgres en `:55322`
- [ ] `uv run python -m conco.guidance.load_catalog`
- [ ] `make run` en `back/` → `http://127.0.0.1:8000/docs` responde
- [ ] `npm run dev` en `front/` → `http://localhost:5173`

## Troubleshooting

| Síntoma | Causa probable |
|---|---|
| `/guidance/activities` → 503 | Falta `supabase start` o `load_catalog` |
| El mapa no muestra marcador | Backend caído; el front acepta la dirección escrita igual |
| Cambios en `activities.json` no se ven | Re-correr `load_catalog` |
| `uv`/`npm` no instalados | Instalar `uv` (`curl -LsSf https://astral.sh/uv/install.sh \| sh`) y Node 20+ |
