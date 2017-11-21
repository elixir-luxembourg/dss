#!/usr/bin/env python

from datetime import datetime

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell

from elixir_dcp import app, db
from elixir_dcp.models import Submission, SubmissionContact, ContactType

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()

    contact_type1 = ContactType(name='PI')
    contact_type2 = ContactType(name='Researcher')
    contact_type3 = ContactType(name='Data Manager')
    contact_type4 = ContactType(name='Legal Representative')
    contact_type5 = ContactType(name='Other')

    db.session.add(contact_type1)
    db.session.add(contact_type2)
    db.session.add(contact_type3)
    db.session.add(contact_type4)
    db.session.add(contact_type5)
    db.session.commit()
    sub1 = Submission(name='OncoTrack', description='Submission of Oncotrack data', created=datetime.today())
    sub2 = Submission(name='Predict-TB', description='Submission of Predict-TB preclinical data',
                      created=datetime.today())
    contact1 = SubmissionContact(name='Pinar Alper', category_id = 3, is_primary=True)
    sub1.contacts.append(contact1)
    contact2 = SubmissionContact(name='Valentin Grouès', category_id = 1,  is_primary=True)
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
