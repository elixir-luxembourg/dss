"""Use conditions answered Yes / No / Not applicable / Not available.

Turns the dataset use condition booleans into nullable strings. A true becomes
"yes"; a false becomes unset (NULL), since an untouched toggle cannot be told
from a deliberate No. Also adds a remark field to the use conditions that had
none.

Revision ID: 5d2e8a91c4f0
Revises: b3f1c9d47a21
Create Date: 2026-10-22

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5d2e8a91c4f0"
down_revision = "b3f1c9d47a21"
branch_labels = None
depends_on = None

TABLE = "submission_dataset"
COLUMNS = (
    "use_restriction_project",
    "use_restriction_research_use",
    "restriction_rs",
    "restriction_gs",
    "restriction_user_specific",
    "restriction_us",
    "restriction_pub",
    "restriction_ts",
    "restriction_ts_lcsb",
    "restriction_rtn",
    "access_form_required",
    "dac_approval_required",
    "restriction_ip",
)
NOTES_COLUMNS = (
    "use_restriction_project_notes",
    "use_restriction_research_use_notes",
    "restriction_ts_lcsb_notes",
    "access_form_notes",
)


def _swap(new_type, new_nullable, convert):
    """Replace each column with a <column>_new of new_type, filled by convert."""
    for column in COLUMNS:
        op.add_column(TABLE, sa.Column(f"{column}_new", new_type, nullable=True))
    convert()
    with op.batch_alter_table(TABLE) as batch_op:
        for column in COLUMNS:
            batch_op.drop_column(column)
    with op.batch_alter_table(TABLE) as batch_op:
        for column in COLUMNS:
            batch_op.alter_column(
                f"{column}_new",
                new_column_name=column,
                existing_type=new_type,
                nullable=new_nullable,
            )


def upgrade():
    table = sa.table(
        TABLE,
        *(sa.column(c, sa.Boolean()) for c in COLUMNS),
        *(sa.column(f"{c}_new", sa.String(20)) for c in COLUMNS),
    )

    def convert():
        for column in COLUMNS:
            op.execute(
                table.update()
                .where(table.c[column] == sa.true())
                .values({f"{column}_new": "yes"})
            )

    _swap(sa.String(length=20), True, convert)
    with op.batch_alter_table(TABLE) as batch_op:
        for column in NOTES_COLUMNS:
            batch_op.add_column(sa.Column(column, sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table(TABLE) as batch_op:
        for column in NOTES_COLUMNS:
            batch_op.drop_column(column)

    table = sa.table(
        TABLE,
        *(sa.column(c, sa.String(20)) for c in COLUMNS),
        *(sa.column(f"{c}_new", sa.Boolean()) for c in COLUMNS),
    )

    def convert():
        for column in COLUMNS:
            op.execute(
                table.update().values(
                    {
                        f"{column}_new": sa.case(
                            (table.c[column] == "yes", sa.true()), else_=sa.false()
                        )
                    }
                )
            )

    _swap(sa.Boolean(), False, convert)
