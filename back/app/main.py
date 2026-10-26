from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CONCO API",
    description="API inicial para el MVP de orientación general sobre trámites.",
    version="0.1.0",
)

# Para desarrollo local. Ajustar los orígenes permitidos antes de publicar.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
