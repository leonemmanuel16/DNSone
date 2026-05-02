"""Generadores de códigos de negocio (folios internos, etc.)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


def generate_project_code(db: Session, *, prefix: str = "DNS") -> str:
    """
    Genera código de proyecto con formato `DNS-YYYY-NNNNN`.

    El correlativo es por año basado en el conteo de proyectos del año.
    Para producción con concurrencia alta, considerar un sequence Postgres.

    Ejemplo: DNS-2026-00001, DNS-2026-00002, ...
    """
    year = datetime.now().year
    pattern = f"{prefix}-{year}-%"

    last = db.execute(
        select(Project.code)
        .where(Project.code.like(pattern))
        .order_by(Project.code.desc())
        .limit(1)
    ).scalar_one_or_none()

    if last:
        try:
            last_seq = int(last.split("-")[-1])
        except (ValueError, IndexError):
            last_seq = 0
    else:
        last_seq = 0

    return f"{prefix}-{year}-{last_seq + 1:05d}"
