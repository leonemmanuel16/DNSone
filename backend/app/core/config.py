"""
Configuración global de la aplicación.

Lee variables de entorno con `pydantic-settings`. Todos los valores tienen
default razonable para desarrollo local; en producción se pasan por `.env`.
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno tipadas."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---- App ----
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "DNS One"
    APP_TIMEZONE: str = "America/Monterrey"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ---- DB ----
    DATABASE_URL: str = "postgresql+psycopg2://dnsone:dnsone_change_me@db:5432/dns_one"

    # ---- Auth / JWT ----
    JWT_SECRET_KEY: str = "change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8h

    # ---- Admin seed ----
    ADMIN_EMAIL: str = "admin@dns.com.mx"
    ADMIN_PASSWORD: str = "ChangeMe123!"
    ADMIN_FULL_NAME: str = "DNS One Administrator"

    # ---- Reglas comerciales ----
    DEFAULT_CURRENCY: Literal["USD", "MXN"] = "USD"
    DEFAULT_EXCHANGE_RATE_USD_MXN: Decimal = Field(default=Decimal("19.00"))
    DEFAULT_TAX_PCT: Decimal = Field(default=Decimal("16.00"))
    PRICE_DECIMAL_PLACES: int = 2

    # ---- BIND ----
    BIND_BASE_URL: str = ""
    BIND_API_TOKEN: str = ""
    BIND_TIMEOUT_SECONDS: int = 30
    BIND_MAX_RETRIES: int = 3
    BIND_USE_MOCK: bool = True

    # ---- Scheduler ----
    SYNC_INTERVAL_MINUTES: int = 30
    SCHEDULER_ENABLED: bool = True

    # ---- PDF ----
    PDF_TEMPLATE_NAME: str = "dns_one_quote"
    PDF_OUTPUT_DIR: str = "/app/pdf_output"

    # ---- Despliegue ----
    GITHUB_REPO_URL: str = "https://github.com/leonemmanuel16/dnsone"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convierte la cadena CSV a lista, eliminando vacíos."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Singleton de configuración. Cacheado para no releer .env por request."""
    return Settings()


# Instancia compartida (uso directo)
settings = get_settings()
