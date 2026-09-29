"""Configuración del servicio leída del entorno (12-Factor III)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.domain.constants import MAX_PDF_SIZE_BYTES


class Settings(BaseSettings):
    """Config por entorno; los defaults son valores de desarrollo seguros."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    max_pdf_size_bytes: int = MAX_PDF_SIZE_BYTES
    cors_origins: str = ""
    log_level: str = "INFO"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Singleton: el entorno se lee una sola vez por proceso."""
    return Settings()
