"""Initial schema — DNS One MVP

Crea todas las tablas: usuarios, roles, permisos, clientes, productos,
proyectos (cotizaciones), partidas, versiones, logs de sync e integraciones.

Revision ID: 0001
Revises:
Create Date: 2026-05-01
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- roles ----
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # ---- permissions ----
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    # ---- role_permissions (assoc) ----
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer, sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    # ---- customers ----
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tax_id", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("billing_address", sa.String(500)),
        sa.Column("shipping_address", sa.String(500)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("bind_customer_id", sa.String(100)),
        sa.Column("bind_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_customers_code", "customers", ["code"])
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_index("ix_customers_tax_id", "customers", ["tax_id"])
    op.create_index("ix_customers_bind_customer_id", "customers", ["bind_customer_id"])

    # ---- products ----
    op.create_table(
        "products",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("brand", sa.String(120)),
        sa.Column("category", sa.String(120)),
        sa.Column("unit", sa.String(20), nullable=False, server_default="PZA"),
        sa.Column("cost_usd", sa.Numeric(14, 4)),
        sa.Column("cost_mxn", sa.Numeric(14, 4)),
        sa.Column("list_price_usd", sa.Numeric(14, 4)),
        sa.Column("list_price_mxn", sa.Numeric(14, 4)),
        sa.Column("currency_default", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("bind_product_id", sa.String(100)),
        sa.Column("bind_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_brand", "products", ["brand"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_bind_product_id", "products", ["bind_product_id"])

    # ---- projects ----
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("customer_id", sa.Integer, sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("valid_until", sa.Date),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("exchange_rate", sa.Numeric(10, 4), nullable=False, server_default="19.00"),
        sa.Column("subtotal_cost", sa.Numeric(14, 2), server_default="0"),
        sa.Column("subtotal_sale", sa.Numeric(14, 2), server_default="0"),
        sa.Column("discount_pct", sa.Numeric(7, 4), server_default="0"),
        sa.Column("discount_amount", sa.Numeric(14, 2), server_default="0"),
        sa.Column("tax_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("grand_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("margin_pct", sa.Numeric(7, 4), server_default="0"),
        sa.Column("bind_quote_id", sa.String(100)),
        sa.Column("bind_folio", sa.String(80)),
        sa.Column("bind_status", sa.String(50)),
        sa.Column("bind_synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_projects_code", "projects", ["code"])
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_bind_quote_id", "projects", ["bind_quote_id"])
    op.create_index("ix_projects_bind_folio", "projects", ["bind_folio"])
    op.create_index("ix_projects_created_by_id", "projects", ["created_by_id"])

    # ---- quote_items ----
    op.create_table(
        "quote_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("position", sa.Integer, nullable=False, server_default="1"),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 4), server_default="0"),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("discount_pct", sa.Numeric(7, 4), server_default="0"),
        sa.Column("tax_pct", sa.Numeric(7, 4), server_default="16"),
        sa.Column("line_cost_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("line_sale_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("line_margin_pct", sa.Numeric(7, 4), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_quote_items_project_id", "quote_items", ["project_id"])
    op.create_index("ix_quote_items_product_id", "quote_items", ["product_id"])

    # ---- project_versions ----
    op.create_table(
        "project_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("snapshot_json", sa.JSON, nullable=False),
        sa.Column("change_note", sa.String(500)),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_project_versions_project_id", "project_versions", ["project_id"])

    # ---- bind_sync_logs ----
    op.create_table(
        "bind_sync_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("run_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("records_in", sa.Integer, server_default="0"),
        sa.Column("records_out", sa.Integer, server_default="0"),
        sa.Column("errors_count", sa.Integer, server_default="0"),
        sa.Column("message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bind_sync_logs_run_type", "bind_sync_logs", ["run_type"])
    op.create_index("ix_bind_sync_logs_status", "bind_sync_logs", ["status"])

    # ---- integration_events ----
    op.create_table(
        "integration_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payload_json", sa.JSON),
        sa.Column("result_json", sa.JSON),
        sa.Column("error_message", sa.Text),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_integration_events_provider", "integration_events", ["provider"])
    op.create_index("ix_integration_events_event_type", "integration_events", ["event_type"])
    op.create_index("ix_integration_events_status", "integration_events", ["status"])
    op.create_index("ix_integration_events_project_id", "integration_events", ["project_id"])


def downgrade() -> None:
    # Borrar en orden inverso para respetar FKs
    op.drop_table("integration_events")
    op.drop_table("bind_sync_logs")
    op.drop_table("project_versions")
    op.drop_table("quote_items")
    op.drop_table("projects")
    op.drop_table("products")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
