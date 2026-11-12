from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la API, leída de variables de entorno y del archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    georef_base_url: str = "https://apis.datos.gob.ar/georef/api"
    georef_timeout_seconds: float = 10.0

    caba_tramites_base_url: str = "https://buenosaires.gob.ar/jsonapi"
    caba_tramites_site_url: str = "https://buenosaires.gob.ar"
    caba_tramites_timeout_seconds: float = 10.0

    # Postgres con pgvector; por defecto, el Supabase local de back/supabase.
    database_url: str = "postgresql://postgres:postgres@127.0.0.1:55322/postgres"
    # Proveedor de embeddings: Cloudflare Workers AI (decisión: ADR-005).
    # Token de Cloudflare con permisos Workers AI Read+Edit.
    embedding_api_key: str | None = None
    cloudflare_account_id: str | None = None
    # Modelo servido por Workers AI; los vectores guardados quedan ligados a este nombre.
    cloudflare_embedding_model: str = "@cf/baai/bge-m3"
    # Tiempo máximo que una búsqueda espera una conexión del pool antes de fallar.
    database_pool_timeout_seconds: float = 10.0
    # Por debajo de esta similitud, una actividad no se sugiere. Calibrado para bge-m3
    # (eval set de 26 queries + 3 negativas, 2026-11-13): los matches correctos más
    # débiles rozan 0.56 y los negativos se quedan en 0.53 o menos.
    activity_min_similarity: float = 0.55


settings = Settings()
