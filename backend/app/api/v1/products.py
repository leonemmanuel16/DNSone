"""Endpoints de productos (catálogo local sincronizado con BIND)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.core.db import get_db
from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.user import User
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter()


@router.get("", response_model=Page[ProductRead])
def list_products(
    q: str | None = Query(default=None, description="Búsqueda libre por SKU/nombre/marca"),
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Page[ProductRead]:
    stmt = select(Product)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Product.sku.ilike(like), Product.name.ilike(like), Product.brand.ilike(like))
        )
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    total = db.execute(
        select(Product.id).select_from(stmt.subquery())
    ).all()
    total_count = len(total)

    rows = db.execute(
        stmt.order_by(Product.sku).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return Page[ProductRead](
        items=[ProductRead.model_validate(r) for r in rows],
        total=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado", details={"product_id": product_id})
    return product


@router.post("", response_model=ProductRead, status_code=201)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Product:
    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado", details={"product_id": product_id})

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return product
