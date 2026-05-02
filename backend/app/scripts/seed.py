"""
Seed inicial de DNS One.

Crea (idempotente):
- Permisos base del sistema
- Roles: admin, sales, viewer
- Usuario admin (de credenciales en .env)

Uso:
    docker compose exec backend python -m app.scripts.seed
"""
from __future__ import annotations

import logging
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.role import Permission, Role
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


# ---------------------------------------------------------------------------
# Catálogo base de permisos (códigos de la forma "recurso.acción")
# ---------------------------------------------------------------------------
BASE_PERMISSIONS: list[tuple[str, str]] = [
    # Productos
    ("products.read", "Ver catálogo de productos"),
    ("products.write", "Crear/editar productos"),
    # Clientes
    ("customers.read", "Ver clientes"),
    ("customers.write", "Crear/editar clientes"),
    # Proyectos / cotizaciones
    ("projects.read", "Ver proyectos-cotizaciones"),
    ("projects.write", "Crear/editar cotizaciones"),
    ("projects.push_bind", "Enviar cotización a BIND"),
    ("projects.pdf", "Descargar PDF de cotización"),
    # Sync
    ("sync.read", "Ver bitácora de sincronización"),
    ("sync.run", "Disparar sync manual"),
    # Usuarios / Roles
    ("users.read", "Ver usuarios"),
    ("users.write", "Crear/editar usuarios"),
    ("roles.write", "Gestionar roles y permisos"),
    # Configuración runtime
    ("settings.read", "Ver configuración (BIND, comercial)"),
    ("settings.write", "Editar configuración (BIND, comercial)"),
]

# Roles base con su mapping de permisos
BASE_ROLES: dict[str, dict] = {
    "admin": {
        "description": "Acceso total al sistema",
        "is_system": True,
        # admin obtiene todos los permisos abajo dinámicamente
    },
    "sales": {
        "description": "Vendedor: cotizaciones, clientes, productos (lectura)",
        "is_system": True,
        "permissions": {
            "products.read",
            "customers.read", "customers.write",
            "projects.read", "projects.write", "projects.push_bind", "projects.pdf",
            "sync.read",
        },
    },
    "viewer": {
        "description": "Solo lectura",
        "is_system": True,
        "permissions": {
            "products.read", "customers.read", "projects.read", "projects.pdf", "sync.read",
        },
    },
}


def upsert_permissions(db: Session) -> dict[str, Permission]:
    """Crea permisos faltantes y devuelve dict por código."""
    by_code: dict[str, Permission] = {}
    for code, desc in BASE_PERMISSIONS:
        p = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
        if p is None:
            p = Permission(code=code, description=desc)
            db.add(p)
            logger.info("Permiso creado: %s", code)
        else:
            p.description = desc
        by_code[code] = p
    db.flush()
    return by_code


def upsert_roles(db: Session, perms: dict[str, Permission]) -> dict[str, Role]:
    by_name: dict[str, Role] = {}
    all_codes = set(perms.keys())

    for name, cfg in BASE_ROLES.items():
        role = db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
        if role is None:
            role = Role(
                name=name,
                description=cfg["description"],
                is_system=cfg.get("is_system", False),
            )
            db.add(role)
            logger.info("Rol creado: %s", name)
        else:
            role.description = cfg["description"]

        # Asignar permisos
        if name == "admin":
            target_codes = all_codes
        else:
            target_codes = cfg.get("permissions", set())
        role.permissions = [perms[c] for c in sorted(target_codes)]
        by_name[name] = role

    db.flush()
    return by_name


def upsert_admin_user(db: Session, admin_role: Role) -> User:
    user = db.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    ).scalar_one_or_none()
    if user is None:
        user = User(
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_FULL_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_active=True,
            is_superuser=True,
            role_id=admin_role.id,
        )
        db.add(user)
        logger.info("Admin creado: %s", settings.ADMIN_EMAIL)
    else:
        # No reescribimos password si ya existe (evita pisar uno cambiado por el usuario)
        user.is_superuser = True
        user.is_active = True
        user.role_id = admin_role.id
        logger.info("Admin ya existía (%s) — se aseguró role + active", settings.ADMIN_EMAIL)

    return user


def main() -> int:
    db = SessionLocal()
    try:
        perms = upsert_permissions(db)
        roles = upsert_roles(db, perms)
        upsert_admin_user(db, roles["admin"])
        db.commit()
        logger.info("Seed completado correctamente.")
        return 0
    except Exception:
        db.rollback()
        logger.exception("Seed falló")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
