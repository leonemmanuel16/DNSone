"""
Generación de PDF de cotización con WeasyPrint + Jinja2.

La plantilla vive en `app/pdf/templates/quote.html`.

Pendiente: ajustar el diseño para igualar el PDF actual de Bind ERP cuando
tengamos una muestra. Ver `docs/decisions.md`.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import settings
from app.models.project import Project

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_quote_pdf(project: Project) -> bytes:
    """
    Renderiza el PDF de la cotización y lo devuelve como bytes.

    Args:
        project: el `Project` cargado con `customer` y `items`.

    Returns:
        Contenido binario del PDF.
    """
    template = _jinja_env.get_template("quote.html")

    ctx = {
        "company": {
            "name": "Data Network Solutions",
            "short": "DNS",
            "tagline": "DNS One — Cotizaciones",
            "address": "—",
            "phone": "—",
            "email": "ventas@dns.com.mx",
            "website": "dns.com.mx",
        },
        "project": project,
        "customer": project.customer,
        "items": project.items,
        "today": date.today(),
        "settings": settings,
    }

    html = template.render(**ctx)
    pdf_bytes: bytes = HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf()
    logger.info("PDF generado para project=%s (%d bytes)", project.code, len(pdf_bytes))
    return pdf_bytes
