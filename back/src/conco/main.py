import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg_pool import AsyncConnectionPool, PoolTimeout

from conco.config import settings
from conco.geolocation.api import router as geolocation_router
from conco.guidance.api import router as guidance_router
from conco.guidance.embeddings import FastEmbedTextEmbedder

logger = logging.getLogger(__name__)


def _log_warmup_failure(task: asyncio.Task[None]) -> None:
    """Registra si la carga del modelo de embeddings falló en segundo plano."""
    if task.cancelled():
        return
    if (error := task.exception()) is not None:
        logger.error("No se pudo precargar el modelo de embeddings: %s", error)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Abre el pool de base de datos y carga el modelo de embeddings en segundo plano."""
    # Si la base no responde al arrancar, la API sigue en pie: las consultas fallarán
    # con 503 hasta que la base vuelva, igual que antes de tener pool.
    pool: AsyncConnectionPool | None = None
    try:
        candidate = AsyncConnectionPool(settings.database_url, min_size=1, max_size=10, open=False)
        await candidate.open()
        pool = candidate
    except (psycopg.Error, PoolTimeout) as exc:
        logger.error("No se pudo abrir el pool de base de datos: %s", exc)
    app.state.activity_pool = pool
    warm_up = asyncio.create_task(asyncio.to_thread(FastEmbedTextEmbedder().warm_up))
    warm_up.add_done_callback(_log_warmup_failure)
    try:
        yield
    finally:
        warm_up.cancel()
        if pool is not None:
            await pool.close()


app = FastAPI(
    title="CONCO API",
    description="API inicial para el MVP de orientación general sobre trámites.",
    version="0.1.0",
    lifespan=lifespan,
)

# Los orígenes permitidos se configuran con CORS_ORIGINS en el archivo .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(geolocation_router)
app.include_router(guidance_router)


@app.get("/health", tags=["Estado"])
def health_check() -> dict[str, str]:
    """Permite comprobar que la API está funcionando."""
    return {"status": "ok"}


@app.get("/", tags=["Inicio"])
def root() -> dict[str, str]:
    """Devuelve información básica de la API."""
    return {"name": "CONCO API", "version": "0.1.0", "docs": "/docs"}
