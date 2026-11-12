# InnovaLab-E11 — ConCo

Sistema inteligente de orientación sobre trámites comerciales para emprendedores de CABA. El backend consume APIs oficiales (Georef y la API de trámites de buenosaires.gob.ar), y el frontend guía a la persona en cinco pasos: consulta, análisis, orientación, mapa y asistente.

## Estructura

| Carpeta | Descripción | README |
|---|---|---|
| `back/` | API en FastAPI (Python + uv). Único punto que consume APIs externas. | [back/README.md](back/README.md) |
| `front/` | SPA en React + TypeScript + Vite. | [front/README.md](front/README.md) |
| `docs/` | Documentación del proyecto. | — |
| `odd/` | Registro de desarrollo orgánico (ODD). | — |

## Levantar en desarrollo

```bash
# 1. Base de datos local (solo para búsqueda de actividades; requiere Docker)
cd back
npx supabase start -x gotrue,realtime,storage-api,imgproxy,kong,mailpit,postgrest,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
uv run python -m conco.guidance.load_catalog

# 2. Backend  → http://127.0.0.1:8000  (docs en /docs)
make run

# 3. Frontend → http://localhost:5173  (en otra terminal)
cd ../front
npm ci && npm run dev
```

Guía completa con troubleshooting: [GUIA_LEVANTAR.md](GUIA_LEVANTAR.md).

## Stack

- **Backend:** FastAPI, Pydantic, httpx, Cloudflare Workers AI (embeddings) + pgvector, Postgres (Supabase local), `uv`.
- **Frontend:** React 18, TypeScript, Vite, Leaflet.
- **Fuentes de datos:** Georef (direcciones), API JSON:API de trámites de la Ciudad de Buenos Aires.
