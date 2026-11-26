import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg
from psycopg_pool import AsyncConnectionPool, PoolTimeout

from conco.config import settings
from conco.consultation.api import router as consultation_router
from conco.geolocation.api import router as geolocation_router
from conco.errors import ConcoError, InternalError
from conco.guidance.api import get_activity_directory, router as guidance_router
from conco.guidance.domain import ActivityDirectory, ActivityDirectoryError
from conco.guidance.embeddings import create_embedder
from conco.request_id import REQUEST_ID_HEADER, RequestIdMiddleware, resolve_request_id
from conco.territory.api import router as territory_router

# Sin handlers propios (por ejemplo en Render), las líneas INFO por petición no se verían.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
# httpx registra en INFO cada URL saliente, que incluye lo que la persona buscó: solo advertencias.
logging.getLogger("httpx").setLevel(logging.WARNING)

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
        candidate = AsyncConnectionPool(
            settings.database_url,
            min_size=1,
            max_size=10,
            timeout=settings.database_pool_timeout_seconds,
            open=False,
        )
        await candidate.open()
        pool = candidate
    except (psycopg.Error, PoolTimeout) as exc:
        logger.error("No se pudo abrir el pool de base de datos: %s", exc)
    app.state.db_pool = pool
    warm_up = asyncio.create_task(asyncio.to_thread(create_embedder().warm_up))
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

# Se agrega antes que CORS para que CORS quede como el middleware más externo.
app.add_middleware(RequestIdMiddleware)

# Los orígenes permitidos se configuran con CORS_ORIGINS en el archivo .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # El navegador solo deja leer los encabezados expuestos explícitamente.
    expose_headers=[REQUEST_ID_HEADER],
)


def _request_id(request: Request) -> str:
    """Id asignado por el middleware; si falta, se genera uno para no responder sin id."""
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = resolve_request_id(None)
        request.state.request_id = request_id
    return request_id


def _error_response(error: ConcoError, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "request_id": request_id, "detail": error.message},
        headers={REQUEST_ID_HEADER: request_id},
    )


@app.exception_handler(ConcoError)
async def handle_conco_error(request: Request, error: ConcoError) -> JSONResponse:
    """Convierte cualquier error propio al mismo cuerpo: código, request id y mensaje."""
    return _error_response(error, _request_id(request))


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    """Error no previsto: mensaje genérico a la persona y el traceback solo en los logs.

    Este manejador corre fuera de los middlewares propios, por eso agrega el encabezado
    `X-Request-ID` explícitamente.
    """
    request_id = _request_id(request)
    logger.error(
        "Error inesperado en %s %s request_id=%s",
        request.method,
        request.url.path,
        request_id,
        exc_info=error,
    )
    return _error_response(InternalError(), request_id)

app.include_router(geolocation_router)
app.include_router(guidance_router)
app.include_router(consultation_router)
app.include_router(territory_router)


@app.get("/health", tags=["Estado"])
def health_check() -> dict[str, str]:
    """Permite comprobar que la API está funcionando."""
    return {"status": "ok"}


@app.get("/ready", tags=["Estado"])
async def readiness_check(
    directory: Annotated[ActivityDirectory, Depends(get_activity_directory)],
) -> JSONResponse:
    """Indica si la base responde y el catálogo de actividades está cargado.

    A diferencia de `/health`, hace consultas: no se usa para el ping de mantenimiento.
    """
    try:
        loaded = await directory.catalog_ready()
    except ActivityDirectoryError:
        checks = {"database": "error", "catalog": "error"}
    else:
        checks = {"database": "ok", "catalog": "ok" if loaded else "empty"}
    ready = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )


@app.get("/", tags=["Inicio"])
def root() -> dict[str, str]:
    """Devuelve información básica de la API."""
    return {"name": "CONCO API", "version": "0.1.0", "docs": "/docs"}
