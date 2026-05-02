"""
Cliente HTTP para Bind ERP.

Encapsula las llamadas al API real con:
- timeouts configurables
- retries con backoff exponencial
- normalización de errores HTTP
- modo mock (sin red) controlado por config

Resolución de configuración (precedencia, de mayor a menor):
  1. Argumentos explícitos al constructor
  2. Fila `app_settings` en DB (vía `get_bind_client(db)`)
  3. Variables de entorno (`app.core.config.settings`)

Esto permite que el usuario edite credenciales BIND desde la UI sin reiniciar.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.bind import _mock_data

logger = logging.getLogger(__name__)


class BindClient:
    """Cliente del API de Bind ERP."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        use_mock: bool | None = None,
    ) -> None:
        self.base_url = (base_url or settings.BIND_BASE_URL).rstrip("/")
        self.token = token or settings.BIND_API_TOKEN
        self.timeout = timeout if timeout is not None else settings.BIND_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.BIND_MAX_RETRIES
        self.use_mock = settings.BIND_USE_MOCK if use_mock is None else use_mock

        if not self.use_mock and not (self.base_url and self.token):
            raise IntegrationError(
                "Bind no configurado: faltan BIND_BASE_URL o BIND_API_TOKEN",
                details={"hint": "Activa modo mock o completa la config en /settings"},
            )

    # ------------------------------------------------------------------
    # API público
    # ------------------------------------------------------------------
    def get_products(self, *, page: int = 1, page_size: int = 100) -> list[dict[str, Any]]:
        if self.use_mock:
            logger.info("[MOCK] BindClient.get_products → %d productos", len(_mock_data.MOCK_BIND_PRODUCTS))
            return _mock_data.MOCK_BIND_PRODUCTS
        return self._request("GET", "/products", params={"page": page, "page_size": page_size})

    def get_customers(self, *, page: int = 1, page_size: int = 100) -> list[dict[str, Any]]:
        if self.use_mock:
            logger.info("[MOCK] BindClient.get_customers → 0 (sin fixture)")
            return []
        return self._request("GET", "/customers", params={"page": page, "page_size": page_size})

    def create_quote(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.use_mock:
            logger.info("[MOCK] BindClient.create_quote payload=%s", payload)
            return _mock_data.mock_create_quote_response(payload)
        return self._request("POST", "/quotes", json=payload)

    def get_quote_status(self, bind_quote_id: str) -> dict[str, Any]:
        if self.use_mock:
            logger.info("[MOCK] BindClient.get_quote_status %s", bind_quote_id)
            return _mock_data.mock_quote_status(bind_quote_id)
        return self._request("GET", f"/quotes/{bind_quote_id}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.request(method, url, params=params, json=json, headers=headers)
                logger.debug("BIND %s %s -> %s", method, path, resp.status_code)
                if resp.status_code >= 400:
                    raise IntegrationError(
                        f"BIND respondió {resp.status_code}",
                        details={
                            "method": method,
                            "path": path,
                            "status": resp.status_code,
                            "body": resp.text[:500],
                        },
                    )
                return resp.json()
        except httpx.TimeoutException as e:
            raise IntegrationError(
                f"Timeout llamando a BIND ({path})",
                details={"timeout_seconds": self.timeout},
            ) from e
        except httpx.TransportError as e:
            raise IntegrationError(f"Error de red llamando a BIND ({path}): {e}") from e


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_bind_client(db: Session | None = None) -> BindClient:
    """
    Construye un `BindClient` leyendo config primero desde DB y luego desde env.

    Esta es la forma recomendada de obtener un cliente. Permite que la
    configuración cambiada desde la UI tome efecto sin reiniciar el backend.

    Args:
        db: sesión SQLAlchemy. Si es None, solo se usan env vars.
    """
    if db is None:
        return BindClient()

    from app.models.app_setting import AppSetting

    row = db.get(AppSetting, 1)
    if row is None:
        return BindClient()

    return BindClient(
        base_url=row.bind_base_url or settings.BIND_BASE_URL,
        token=row.bind_api_token or settings.BIND_API_TOKEN,
        timeout=row.bind_timeout_seconds,
        max_retries=row.bind_max_retries,
        use_mock=row.bind_use_mock,
    )
