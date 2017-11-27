#!/usr/bin/env python
from datetime import datetime

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell
from elixir_dcp import app, db
from elixir_dcp.models.submission import ContactType, DataSizeCategory, Submission, SubmissionContact
from elixir_dcp.models import User, Role

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()

    names_contact_types = ['PI', 'Researcher', 'Data Manager', 'Data Protection Officer', 'Legal Representative', 'Other']
    for name_contact_type in names_contact_types:
        db.session.add(ContactType(name=name_contact_type))

    names_roles= ['admin', 'provider', 'consumer', 'steward']
    for name_role in names_roles:
        db.session.add(Role(name=name_role))

    db.session.add(DataSizeCategory(code='elx_s', label='Less than 10GB'))
    db.session.add(DataSizeCategory(code='elx_m', label='Between 10 and 100GB'))
    db.session.add(DataSizeCategory(code='elx_l', label='Greater than 100 GB'))
    db.session.commit()

    sub1 = Submission(name='OncoTrack', description='Submission of Oncotrack data', created_on=datetime.today(),
                      joint_providers=True)
    sub2 = Submission(name='Predict-TB', description='Submission of Predict-TB preclinical data',
                      created_on=datetime.today(), joint_providers=False)
    contact1 = SubmissionContact(name='Pinar Alper', category_id=3, is_primary=True)
    sub1.contacts.append(contact1)
    contact2 = SubmissionContact(name='Valentin Grouès', category_id=1,  is_primary=True)
    sub2.contacts.append(contact2)
    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()

    db.session.add(User(first_name='Pinar', last_name='Alper', elixir_reg_id='pinar.alper@uni.lu',
                                 phone_code='352', phone_no='123456789', active_user=True))
    db.session.add(User(first_name='Alice', last_name='White', elixir_reg_id='pi@some.uni',
                                 phone_code='44', phone_no='123456789', active_user=True))
    db.session.commit()

    return


manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))
# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
