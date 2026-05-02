"""Tabla app_settings (config runtime-editable)

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-01
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("bind_base_url", sa.String(255)),
        sa.Column("bind_api_token", sa.String(500)),
        sa.Column("bind_use_mock", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("bind_timeout_seconds", sa.Integer, nullable=False, server_default="30"),
        sa.Column("bind_max_retries", sa.Integer, nullable=False, server_default="3"),
        sa.Column("default_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column(
            "default_exchange_rate_usd_mxn",
            sa.Numeric(10, 4),
            nullable=False,
            server_default="19.00",
        ),
        sa.Column(
            "default_tax_pct",
            sa.Numeric(7, 4),
            nullable=False,
            server_default="16.00",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Seed singleton row (id=1) con defaults
    op.execute(
        """
        INSERT INTO app_settings (id, bind_use_mock, bind_timeout_seconds, bind_max_retries,
                                  default_currency, default_exchange_rate_usd_mxn, default_tax_pct)
        VALUES (1, TRUE, 30, 3, 'USD', 19.00, 16.00)
        """
    )


def downgrade() -> None:
    op.drop_table("app_settings")
