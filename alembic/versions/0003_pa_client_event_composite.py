"""composite unique on (game_id, client_event_id)

Revision ID: 0003_pa_client_event_composite
Revises: 0002_pa_idempotency
Create Date: 2025-08-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_pa_client_event_composite"
down_revision = "0002_pa_idempotency"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop old global-unique constraint
    op.drop_constraint("uq_pa_client_event_id", "plate_appearances", type_="unique")
    # Create composite unique
    op.create_unique_constraint(
        "uq_pa_game_client_event",
        "plate_appearances",
        ["game_id", "client_event_id"],
    )

def downgrade() -> None:
    op.drop_constraint("uq_pa_game_client_event", "plate_appearances", type_="unique")
    op.create_unique_constraint(
        "uq_pa_client_event_id",
        "plate_appearances",
        ["client_event_id"],
    )
