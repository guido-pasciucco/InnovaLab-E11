from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from conco.config import settings

app = FastAPI(
    title="CONCO API",
    description="API inicial para el MVP de orientación general sobre trámites.",
    version="0.1.0",
)

# Los orígenes permitidos se configuran con CORS_ORIGINS en el archivo .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Estado"])
def health_check() -> dict[str, str]:
    """Permite comprobar que la API está funcionando."""
    return {"status": "ok"}


@app.get("/", tags=["Inicio"])
def root() -> dict[str, str]:
    """Devuelve información básica de la API."""
    return {"name": "CONCO API", "version": "0.1.0", "docs": "/docs"}
