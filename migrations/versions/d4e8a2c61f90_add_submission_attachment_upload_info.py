"""Add upload date and uploader to submission_attachments.

Revision ID: d4e8a2c61f90
Revises: 8c4e2b7d1a93
Create Date: 2026-10-22

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e8a2c61f90"
down_revision = "8c4e2b7d1a93"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("submission_attachments") as batch_op:
        batch_op.add_column(
            sa.Column("uploaded_on", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_submission_attachments_uploaded_by_user_id_users",
            "users",
            ["uploaded_by_user_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("submission_attachments") as batch_op:
        batch_op.drop_constraint(
            "fk_submission_attachments_uploaded_by_user_id_users", type_="foreignkey"
        )
        batch_op.drop_column("uploaded_by_user_id")
        batch_op.drop_column("uploaded_on")
