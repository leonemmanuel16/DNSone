"""Router maestro de la API v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, customers, products, projects, settings as settings_api, sync

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
api_router.include_router(settings_api.router, prefix="/settings", tags=["settings"])
