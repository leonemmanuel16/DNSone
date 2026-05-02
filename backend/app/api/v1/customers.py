"""Endpoints de clientes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.models.user import User
from app.schemas.common import Page
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter()


@router.get("", response_model=Page[CustomerRead])
def list_customers(
    q: str | None = Query(default=None),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Page[CustomerRead]:
    stmt = select(Customer)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Customer.name.ilike(like), Customer.code.ilike(like), Customer.tax_id.ilike(like))
        )
    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)

    total_count = len(db.execute(select(Customer.id).select_from(stmt.subquery())).all())
    rows = db.execute(
        stmt.order_by(Customer.name).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return Page[CustomerRead](
        items=[CustomerRead.model_validate(r) for r in rows],
        total=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None:
        raise NotFoundError("Cliente no encontrado", details={"customer_id": customer_id})
    return cust


@router.post("", response_model=CustomerRead, status_code=201)
def create_customer(
    body: CustomerCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Customer:
    cust = Customer(**body.model_dump())
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


@router.patch("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Customer:
    cust = db.get(Customer, customer_id)
    if cust is None:
        raise NotFoundError("Cliente no encontrado", details={"customer_id": customer_id})

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(cust, k, v)
    db.commit()
    db.refresh(cust)
    return cust
