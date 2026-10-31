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


settings = Settings()
