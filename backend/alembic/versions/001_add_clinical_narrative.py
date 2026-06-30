"""Add clinical_narrative to speakers

Revision ID: 001_clinical_narrative
Revises: 
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_clinical_narrative'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add clinical_narrative text column to speakers table."""
    op.add_column('speakers', sa.Column('clinical_narrative', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove clinical_narrative column from speakers table."""
    op.drop_column('speakers', 'clinical_narrative')
