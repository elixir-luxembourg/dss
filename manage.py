#!/usr/bin/env python
from datetime import datetime

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell

from elixir_dcp import app, db
from elixir_dcp.models import ContactType, Submission, SubmissionContact

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()

    names_contact_types = ['PI', 'Researcher', 'Data Manager', 'Legal Representative', 'Other']
    for name_contact_type in names_contact_types:
        db.session.add(ContactType(name=name_contact_type))
    db.session.commit()
    sub1 = Submission(name='OncoTrack', description='Submission of Oncotrack data', created=datetime.today())
    sub2 = Submission(name='Predict-TB', description='Submission of Predict-TB preclinical data',
                      created=datetime.today())
    contact1 = SubmissionContact(name='Pinar Alper', category_id=3, is_primary=True)
    sub1.contacts.append(contact1)
    contact2 = SubmissionContact(name='Valentin Grouès', category_id=1, is_primary=True)
    sub2.contacts.append(contact2)
    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()
    return


manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))
# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
