"""add client_event_id to plate_appearances

Revision ID: 0002_pa_idempotency
Revises: 0001_core
Create Date: 2025-08-31
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_pa_idempotency"
down_revision = "0001_core"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "plate_appearances",
        sa.Column("client_event_id", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_pa_client_event_id",
        "plate_appearances",
        ["client_event_id"],
    )

def downgrade() -> None:
    op.drop_constraint("uq_pa_client_event_id", "plate_appearances", type_="unique")
    op.drop_column("plate_appearances", "client_event_id")
