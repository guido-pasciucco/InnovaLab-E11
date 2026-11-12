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
    # Tiempo máximo que una búsqueda espera una conexión del pool antes de fallar.
    database_pool_timeout_seconds: float = 10.0
    # Modelo multilingüe que convierte texto en vectores. Si se cambia, hay que volver a
    # cargar los datos: los vectores de modelos distintos no se pueden comparar.
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    # Por debajo de esta similitud, una actividad no se sugiere.
    activity_min_similarity: float = 0.5


settings = Settings()
