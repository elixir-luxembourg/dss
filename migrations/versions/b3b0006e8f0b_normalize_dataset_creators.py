"""Normalize dataset creators

Revision ID: b3b0006e8f0b
Revises: 8873ba3e2997
Create Date: 2025-12-23 11:33:17.938318

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b3b0006e8f0b"
down_revision = "8873ba3e2997"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create creators table
    op.create_table(
        "submission_dataset_creator",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("institution", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["submission_dataset.id"],
            ondelete="CASCADE",
        ),
    )

    # 2. Backfill data from legacy columns
    op.execute("""
               INSERT INTO submission_dataset_creator
                   (dataset_id, first_name, last_name, email, institution, role)
               SELECT
                   id,
                   creator_name,
                   '',
                   creator_email,
                   creator_institution,
                   creator_role
               FROM submission_dataset
               WHERE creator_name IS NOT NULL
               """)

    # 3. Drop legacy columns (SQLite-safe)
    with op.batch_alter_table("submission_dataset") as batch_op:
        batch_op.drop_column("creator_name")
        batch_op.drop_column("creator_email")
        batch_op.drop_column("creator_institution")
        batch_op.drop_column("creator_role")


def downgrade():
    # 1. Recreate legacy columns
    with op.batch_alter_table("submission_dataset") as batch_op:
        batch_op.add_column(
            sa.Column("creator_name", sa.String(), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("creator_email", sa.String(), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column(
                "creator_institution", sa.String(), nullable=False, server_default=""
            )
        )
        batch_op.add_column(
            sa.Column("creator_role", sa.String(), nullable=False, server_default="")
        )

    # 2. Restore legacy data from first creator
    op.execute("""
               UPDATE submission_dataset
               SET
                   creator_name = (
                       SELECT first_name FROM submission_dataset_creator
                       WHERE dataset_id = submission_dataset.id
                   LIMIT 1
                   ),
                   creator_email = (
               SELECT email FROM submission_dataset_creator
               WHERE dataset_id = submission_dataset.id
                   LIMIT 1
                   ),
                   creator_institution = (
               SELECT institution FROM submission_dataset_creator
               WHERE dataset_id = submission_dataset.id
                   LIMIT 1
                   ),
                   creator_role = (
               SELECT role FROM submission_dataset_creator
               WHERE dataset_id = submission_dataset.id
                   LIMIT 1
                   )
               """)

    # 3. Drop creators table
    op.drop_table("submission_dataset_creator")
