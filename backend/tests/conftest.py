"""Configuración global de pytest."""
from __future__ import annotations

import os

# Asegurar que las settings cargan defaults sanos en tests
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_for_pytest_only")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("BIND_USE_MOCK", "true")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
