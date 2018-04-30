#!/usr/bin/env python
from datetime import datetime
from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell, Server
from elixir_dcp import app, db, mail
from elixir_dcp.models.submission import ContactType, DataSizeCategory, Submission, SubmissionContact, \
    SubmissionStatusEnum, GA4GHCodes
from elixir_dcp.models.security import User, Role
from elixir_dcp.models.services import assign_role_to_user, register_new_user

manager = Manager(app)
manager.add_command("runserver", Server(host="127.0.0.1", port=5000))

manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()
    initial_data = app.config.get('DATA_INIT')

    for contact_type in initial_data['contact_types']:
        db.session.add(ContactType(name=contact_type))

    for name_role in initial_data['names_roles']:
        db.session.add(Role(name=name_role))

    for category in initial_data['size_categories']:
        db.session.add(DataSizeCategory(code=category[0], label=category[1]))

    for code_triple in initial_data['ga4gh_codes']:
        db.session.add(GA4GHCodes(code=code_triple[0], name=code_triple[1], description = code_triple[2]))
    db.session.commit()

    sub1 = Submission(ref_name='ELX_LU_SUB-1', title='Submission of Oncotrack data', created_on=datetime.today(),
                      current_status=SubmissionStatusEnum.draft)
    sub2 = Submission(ref_name='ELX_LU_SUB-2', title='Submission of Predict-TB  data',
                      created_on=datetime.today(), current_status=SubmissionStatusEnum.draft)
    contact1 = SubmissionContact(name='P\u0131nar', surname='Alper', category_id=3, email="pinar.alper@uni.lu",
                                 institution="University of Luxembourg")
    sub1.contacts.append(contact1)
    contact2 = SubmissionContact(name='Valentin', surname='Grou\u00E8s', category_id=1, email="pinar.alper@uni.lu",
                                 institution="University of Luxembourg")
    sub2.contacts.append(contact2)
    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()

    u1 = User(first_name='P\u0131nar', last_name='Alper',
              elixir_sub_id='5142d45eeece42e2108f6c3c146745b41db21e87@elixir-europe.org', email='pinar.alper@uni.lu',
              institution='University of Luxembourg',
              phone_no='+352123456789')
    register_new_user(u1)
    assign_role_to_user(u1, 'admin')

    # u2 = User(first_name='Pinar2', last_name='Alper2',
    #           elixir_sub_id='a2ba8f4043649f46c91b895e8568d8b96d985284@elixir-europe.org',
    #           email='pinarpink@googlemail.com', institution='University of Manchester',
    #           phone_no='+44123456789')
    # register_new_user(u2)
    # assign_role_to_user(u2, 'data_provider')

    return


# TODO I don't know what the below command does. FInd out.
manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))

# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
