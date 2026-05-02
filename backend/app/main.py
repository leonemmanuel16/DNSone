"""
DNS One — punto de entrada FastAPI.

Responsabilidades:
- Configurar la app (CORS, exception handlers, middleware de logging)
- Montar el router v1
- Lifespan: arrancar y detener el scheduler de jobs (sync BIND cada 30 min)
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.jobs.scheduler import shutdown_scheduler, start_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Arranca el scheduler al iniciar la app y lo detiene al cerrarla."""
    configure_logging(settings.LOG_LEVEL)
    logger.info("Iniciando DNS One backend (env=%s)", settings.APP_ENV)

    if settings.SCHEDULER_ENABLED:
        start_scheduler()
        logger.info("Scheduler iniciado (sync cada %d min)", settings.SYNC_INTERVAL_MINUTES)
    else:
        logger.info("Scheduler deshabilitado por configuración")

    yield

    logger.info("Deteniendo DNS One backend")
    if settings.SCHEDULER_ENABLED:
        shutdown_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    description="API de DNS One — CRM + ERP + Cotizaciones, integrado con Bind ERP.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Exception handlers ----
@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    """Convierte errores de dominio en respuestas HTTP estructuradas."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


# ---- Health check ----
@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Endpoint de salud del servicio."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "0.1.0",
    }


# ---- API v1 ----
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["meta"])
async def root() -> dict:
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
        "api": "/api/v1",
    }
