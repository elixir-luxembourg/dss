#!/usr/bin/env python
import click
from flask.cli import FlaskGroup
from flask_migrate import Migrate

from elixir_dss import app, db
from elixir_dss.importer.importer_utils import schedule_submission_export
from elixir_dss.models.security import Role, User
from elixir_dss.models.services import assign_role_to_user, register_new_user
from elixir_dss.models.submission import (
    ConsentStatus,
    ContactType,
    DeIdentificationType,
    LegalBasisType,
    SubjectCategory,
    SubmissionScope,
)

migrate_instance = Migrate(app, db)

cli = FlaskGroup(app)


@cli.command()
def init_db():
    """Initialize the database with default data."""
    click.echo("Dropping all tables...")
    db.drop_all()
    click.echo("Creating all tables...")
    db.create_all()

    initial_data = app.config.get("DATA_INIT")

    click.echo("Adding initial data...")
    for contact_type in initial_data["contact_types"]:
        db.session.add(ContactType(name=contact_type))

    for name_role in initial_data["names_roles"]:
        db.session.add(Role(name=name_role))

    for sub_category in initial_data["subject_category"]:
        db.session.add(SubjectCategory(code=sub_category[0], label=sub_category[1]))

    for deid_type in initial_data["deidentification_type"]:
        db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

    for cons_status in initial_data["consent_status"]:
        db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))

    for lb_type in initial_data["legal_basis"]:
        db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

    for sub_scope in initial_data["submission_scope"]:
        db.session.add(SubmissionScope(code=sub_scope[0], label=sub_scope[1]))

    db.session.commit()
    click.echo("Database initialized successfully!")


@cli.command()
def load_demo_users():
    """Load demonstration users for testing."""
    click.echo("Loading demo users...")

    u1 = User(
        first_name="Steward",
        last_name="One",
        elixir_sub_id="steward1@uni.lu",
        email="steward1@uni.lu",
        institution_accession="ELU_I_77",
        phone_no="+352123456789",
    )
    register_new_user(u1)
    assign_role_to_user(u1, "data_steward")
    click.echo("Created data steward user: steward1@uni.lu")

    u2 = User(
        first_name="Submitter",
        last_name="One",
        elixir_sub_id="submitter1@some.edu",
        email="submitter1@some.edu",
        institution_accession="ELU_I_79",
        phone_no="+352123456789",
    )
    register_new_user(u2)
    assign_role_to_user(u2, "user")
    click.echo("Created data provider: submitter1@some.edu")

    u3 = User(
        first_name="Submitter",
        last_name="Two",
        elixir_sub_id="submitter2@some.edu",
        email="submitter2@some.edu",
        institution_accession="ELU_I_79",
        phone_no="+352123456789",
    )
    register_new_user(u3)
    assign_role_to_user(u3, "user")
    click.echo("Created data provider: submitter2@some.edu")

    u4 = User(
        first_name="Admin",
        last_name="One",
        elixir_sub_id="admin@uni.lu",
        email="admin@uni.lu",
        institution_accession="ELU_I_77",
        phone_no="+352123456789",
    )
    register_new_user(u4)
    assign_role_to_user(u4, "admin")
    click.echo("Created admin user: admin@uni.lu")

    click.echo("Demo users loaded successfully!")


@cli.command()
@click.argument("name")
@click.argument("surname")
@click.argument("email")
@click.argument("elixir_id")
@click.argument("institution")
def create_admin(name, surname, email, elixir_id, institution):
    """Create an admin user.

    Arguments:
        NAME: First name of the admin
        SURNAME: Last name of the admin
        EMAIL: Email address
        ELIXIR_ID: ELIXIR ID
        INSTITUTION: Institution accession code
    """
    u1 = User(
        first_name=name,
        last_name=surname,
        elixir_sub_id=elixir_id,
        email=email,
        institution_accession=institution,
    )
    register_new_user(u1)
    assign_role_to_user(u1, "admin")
    click.echo(f"Admin user created successfully: {email}")


@cli.command()
@click.option(
    "--destination",
    "-d",
    default=app.config.get("SUBMISSION_EXPORT_FOLDER"),
    help=f"Path to the destination folder. Default: {app.config.get('SUBMISSION_EXPORT_FOLDER')}",
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    help="Export also submissions which have been already exported in the past. This will overwrite existing JSON files.",
)
@click.option(
    "--submission-id",
    "-i",
    multiple=True,
    help="List of submission IDs to export (can be used multiple times)",
)
def export_submissions(destination, all, submission_id):
    """Export submissions into JSON files."""
    submissions_to_export = list(submission_id) if submission_id else []
    click.echo(f"Exporting submissions to: {destination}")
    if all:
        click.echo("Exporting all submissions (including previously exported)")
    if submissions_to_export:
        click.echo(f"Exporting specific submissions: {submissions_to_export}")

    schedule_submission_export(destination, all, submissions_to_export)
    click.echo("Export completed!")


@cli.command()
def shell():
    """Start an interactive Python shell with app context."""
    import code
    import readline

    # Enable tab completion
    readline.parse_and_bind("tab: complete")

    # Create context with useful imports
    context = {
        "app": app,
        "db": db,
        "User": User,
        "Role": Role,
    }

    # Start interactive shell
    code.interact(
        local=context,
        banner="""
Python Shell for Elixir-DSS
Available objects: app, db, User, Role
Use tab for autocompletion
""",
    )


@cli.command()
@click.argument("email")
def grant_data_steward_access(email):
    click.echo(f"Granting data steward access to: {email}")

    user = User.query.filter_by(email=email).first()
    if user:
        assign_role_to_user(user, "data_steward")
        click.echo(f"Granted data steward access to: {email}")
    else:
        click.echo(f"User not found: {email}")


if __name__ == "__main__":
    cli()
