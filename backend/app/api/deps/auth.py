"""
Dependencias de autenticación / autorización para endpoints FastAPI.

Uso:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)): ...

    @router.post("/projects/{id}/push-bind")
    def push(... user: User = Depends(require_permission("projects.push_bind"))): ...
"""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import JWTError, decode_access_token
from app.models.user import User


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Resuelve el usuario autenticado a partir del header `Authorization: Bearer <jwt>`.

    Raises:
        UnauthorizedError: si falta el header, el token es inválido o el user no existe.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Falta header Authorization Bearer")

    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = decode_access_token(token)
    except JWTError as e:
        raise UnauthorizedError("Token inválido o expirado") from e

    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError("Token sin sujeto")

    try:
        user_id = int(sub)
    except (TypeError, ValueError) as e:
        raise UnauthorizedError("Token con sujeto malformado") from e

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Usuario no existe")
    if not user.is_active:
        raise UnauthorizedError("Usuario inactivo")

    return user


def require_permission(permission_code: str):
    """
    Dependencia parametrizada que exige un permiso específico.

    Superusers tienen todos los permisos automáticamente.
    """

    def _checker(user: User = Depends(get_current_user)) -> User:
        codes = user.permission_codes
        if "*" in codes or permission_code in codes:
            return user
        raise ForbiddenError(
            f"Falta permiso '{permission_code}'",
            details={"required": permission_code},
        )

    return _checker
