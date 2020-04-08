#!/usr/bin/env python
import unittest
import sys
from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell, Server
from elixir_dcp import app, db
from elixir_dcp.models.submission import ContactType, DeIdentificationType, \
    LegalBasisType, ConsentStatus, SubmissionScope, SubjectCategory
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

    for sub_category in initial_data['subject_category']:
        db.session.add(SubjectCategory(code=sub_category[0], label=sub_category[1]))

    for deid_type in initial_data['deidentification_type']:
        db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

    for cons_status in initial_data['consent_status']:
        db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))

    for lb_type in initial_data['legal_basis']:
        db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

    for sub_scope in initial_data['submission_scope']:
        db.session.add(SubmissionScope(code=sub_scope[0], label=sub_scope[1]))

    db.session.commit()

@manager.command
def load_demo_users():

    u1 = User(first_name='Steward', last_name='One',
              elixir_sub_id='steward1@uni.lu', email='steward1@uni.lu',
              institution_accession='ELU_I_77',
              phone_no='+352123456789')
    register_new_user(u1)
    assign_role_to_user(u1, 'admin')



    u2 = User(first_name='Submitter', last_name='One',
              elixir_sub_id='submitter1@some.edu', email='submitter1@some.edu',
              institution_accession='ELU_I_79',
              phone_no='+352123456789')
    register_new_user(u2)
    assign_role_to_user(u2, 'data_provider')

    u3 = User(first_name='Submitter', last_name='Two',
              elixir_sub_id='submitter2@some.edu', email='submitter2@some.edu',
              institution_accession='ELU_I_79',
              phone_no='+352123456789')


    register_new_user(u3)
    assign_role_to_user(u3, 'data_provider')

    return

# TODO I don't know what the below command does. FInd out.
manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))

# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
