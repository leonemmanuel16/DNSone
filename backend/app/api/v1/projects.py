"""
Endpoints de proyectos-cotizaciones.

Incluye:
- CRUD básico
- Gestión de partidas (items)
- Recálculo de totales/margen
- Push a BIND
- Generación de PDF
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, require_permission
from app.core.db import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.enums import ProjectStatus
from app.models.project import Project, QuoteItem
from app.models.user import User
from app.schemas.common import Page
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    QuoteItemCreate,
    QuoteItemRead,
    QuoteItemUpdate,
)
from app.services.pricing import (
    LineInput,
    calculate_project,
    quote_item_to_input,
)
from app.utils.codes import generate_project_code

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
def _persist_calculations(project: Project) -> None:
    """Recalcula y persiste totales en el proyecto y en cada partida."""
    line_inputs: list[LineInput] = [quote_item_to_input(it) for it in project.items]
    calc = calculate_project(line_inputs, global_discount_pct=project.discount_pct)

    project.subtotal_cost = calc.subtotal_cost
    project.subtotal_sale = calc.subtotal_sale
    project.discount_amount = calc.discount_amount
    project.tax_total = calc.tax_total
    project.grand_total = calc.grand_total
    project.margin_pct = calc.margin_pct

    for item, lc in zip(project.items, calc.lines, strict=True):
        item.line_cost_total = lc.line_cost_total
        item.line_sale_total = lc.line_sale_total
        item.line_margin_pct = lc.line_margin_pct


def _get_project_or_404(db: Session, project_id: int) -> Project:
    p = db.get(Project, project_id)
    if p is None:
        raise NotFoundError("Proyecto no encontrado", details={"project_id": project_id})
    return p


# ---------------------------------------------------------------------------
# Listado / detalle
# ---------------------------------------------------------------------------
@router.get("", response_model=Page[ProjectRead])
def list_projects(
    status: ProjectStatus | None = None,
    customer_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Page[ProjectRead]:
    stmt = select(Project).where(Project.is_archived.is_(False))
    if status:
        stmt = stmt.where(Project.status == status)
    if customer_id:
        stmt = stmt.where(Project.customer_id == customer_id)

    total = len(db.execute(select(Project.id).select_from(stmt.subquery())).all())
    rows = db.execute(
        stmt.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return Page[ProjectRead](
        items=[ProjectRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Project:
    return _get_project_or_404(db, project_id)


# ---------------------------------------------------------------------------
# Crear / actualizar
# ---------------------------------------------------------------------------
@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Project:
    if db.get(Customer, body.customer_id) is None:
        raise ValidationError("Cliente no existe", details={"customer_id": body.customer_id})

    code = generate_project_code(db)

    project = Project(
        code=code,
        name=body.name,
        notes=body.notes,
        customer_id=body.customer_id,
        currency=body.currency,
        exchange_rate=body.exchange_rate,
        discount_pct=body.discount_pct,
        valid_until=body.valid_until,
        status=ProjectStatus.DRAFT,
        created_by_id=user.id,
    )
    db.add(project)
    db.flush()  # para tener project.id

    for idx, item_in in enumerate(body.items, start=1):
        db.add(
            QuoteItem(
                project_id=project.id,
                position=item_in.position or idx,
                product_id=item_in.product_id,
                sku=item_in.sku,
                description=item_in.description,
                qty=item_in.qty,
                unit_cost=item_in.unit_cost,
                unit_price=item_in.unit_price,
                discount_pct=item_in.discount_pct,
                tax_pct=item_in.tax_pct,
            )
        )
    db.flush()
    db.refresh(project)

    _persist_calculations(project)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Project:
    project = _get_project_or_404(db, project_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    _persist_calculations(project)
    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------
@router.post("/{project_id}/items", response_model=QuoteItemRead, status_code=201)
def add_item(
    project_id: int,
    body: QuoteItemCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> QuoteItem:
    project = _get_project_or_404(db, project_id)

    item = QuoteItem(
        project_id=project.id,
        position=body.position,
        product_id=body.product_id,
        sku=body.sku,
        description=body.description,
        qty=body.qty,
        unit_cost=body.unit_cost,
        unit_price=body.unit_price,
        discount_pct=body.discount_pct,
        tax_pct=body.tax_pct,
    )
    db.add(item)
    db.flush()
    db.refresh(project)
    _persist_calculations(project)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{project_id}/items/{item_id}", response_model=QuoteItemRead)
def update_item(
    project_id: int,
    item_id: int,
    body: QuoteItemUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> QuoteItem:
    project = _get_project_or_404(db, project_id)
    item = db.get(QuoteItem, item_id)
    if item is None or item.project_id != project_id:
        raise NotFoundError("Partida no encontrada", details={"item_id": item_id})

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    db.flush()
    db.refresh(project)
    _persist_calculations(project)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{project_id}/items/{item_id}", status_code=204)
def delete_item(
    project_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Response:
    project = _get_project_or_404(db, project_id)
    item = db.get(QuoteItem, item_id)
    if item is None or item.project_id != project_id:
        raise NotFoundError("Partida no encontrada", details={"item_id": item_id})

    db.delete(item)
    db.flush()
    db.refresh(project)
    _persist_calculations(project)
    db.commit()
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Recálculo, Push BIND, PDF
# ---------------------------------------------------------------------------
@router.post("/{project_id}/recalculate", response_model=ProjectRead)
def recalculate(
    project_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Project:
    project = _get_project_or_404(db, project_id)
    _persist_calculations(project)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/push-bind", response_model=ProjectRead)
def push_to_bind(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("projects.push_bind")),
) -> Project:
    """
    Envía la cotización a Bind ERP.

    Crea una versión-snapshot, llama al cliente BIND vía
    `bind_sync_service.push_quote_to_bind()` y persiste `bind_quote_id` y `bind_folio`.
    """
    from app.integrations.bind.bind_sync_service import push_quote_to_bind

    project = _get_project_or_404(db, project_id)

    if Decimal(project.grand_total) <= 0 or not project.items:
        raise ValidationError("La cotización no tiene partidas o total cero")

    push_quote_to_bind(db, project=project, user_id=user.id)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/pdf")
def get_pdf(
    project_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Response:
    """Devuelve el PDF de la cotización."""
    from app.pdf.quote_pdf import render_quote_pdf

    project = _get_project_or_404(db, project_id)
    pdf_bytes = render_quote_pdf(project)
    filename = f"cotizacion_{project.code}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
