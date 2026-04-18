"""fix_repo_config_repo_id_not_autoincrement

Revision ID: 770ceda6d5a8
Revises: e60ad1eb0a30
Create Date: 2026-04-18 08:36:56.920478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '770ceda6d5a8'
down_revision: Union[str, Sequence[str], None] = 'e60ad1eb0a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE repo_config ALTER COLUMN repo_id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS repo_config_repo_id_seq")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("CREATE SEQUENCE IF NOT EXISTS repo_config_repo_id_seq")
    op.execute("ALTER TABLE repo_config ALTER COLUMN repo_id SET DEFAULT nextval('repo_config_repo_id_seq'::regclass)")
