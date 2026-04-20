"""add_closed_at_to_triage_decision

Revision ID: c9f2a1b4e8d3
Revises: 770ceda6d5a8
Create Date: 2026-04-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9f2a1b4e8d3"
down_revision: Union[str, Sequence[str], None] = "770ceda6d5a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add closed_at to triage_decision for productivity tracking (DD-31)."""
    op.add_column("triage_decision", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove closed_at from triage_decision."""
    op.drop_column("triage_decision", "closed_at")
