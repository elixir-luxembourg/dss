"""Add an ORCID iD to dataset creators.

Revision ID: 8c4e2b7d1a93
Revises: 5d2e8a91c4f0
Create Date: 2026-10-23

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8c4e2b7d1a93"
down_revision = "5d2e8a91c4f0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("submission_dataset_creator") as batch_op:
        batch_op.add_column(sa.Column("orcid", sa.String(length=19), nullable=True))


def downgrade():
    with op.batch_alter_table("submission_dataset_creator") as batch_op:
        batch_op.drop_column("orcid")
