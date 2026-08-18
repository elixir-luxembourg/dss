"""Add role to submission_access and unique constraint.

Revision ID: b3f1c9d47a21
Revises: cff59b0aa417
Create Date: 2026-08-11

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3f1c9d47a21"
down_revision = "cff59b0aa417"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("submission_access") as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(length=20),
                nullable=False,
                server_default="submitter",
            )
        )
        batch_op.create_unique_constraint(
            "uq_submission_access_submission_user", ["submission_id", "user_id"]
        )


def downgrade():
    with op.batch_alter_table("submission_access") as batch_op:
        batch_op.drop_constraint("uq_submission_access_submission_user", type_="unique")
        batch_op.drop_column("role")
