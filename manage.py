#!/usr/bin/env python

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell, Server
from elixir_dcp import app, db
from elixir_dcp.models.submission import ContactType, DataSizeCategory, GA4GHCodes, DeIdentificationType, \
    LegalBasisType, ConsentStatus, SubmissionScope
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
        db.session.add(GA4GHCodes(code=code_triple[0], name=code_triple[1], description=code_triple[2]))

    for deid_type in initial_data['deidentification_type']:
        db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

    for lb_type in initial_data['legal_basis']:
        db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

    for cons_status in initial_data['consent_status']:
        db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))

    for sub_scope in initial_data['submission_scope']:
        db.session.add(SubmissionScope(code=sub_scope[0], label=sub_scope[1]))

    db.session.commit()

    # sub1 = Submission(ref_name='ELX_LU_SUB-1', title='Submission of Oncotrack data', created_on=datetime.today(),
    #                   current_status=SubmissionStatusEnum.draft)
    # sub2 = Submission(ref_name='ELX_LU_SUB-2', title='Submission of Predict-TB  data',
    #                   created_on=datetime.today(), current_status=SubmissionStatusEnum.draft)
    # study1 = SubmissionStudy(study_name='Etriks', study_description='Etriks Project is ....', study_types_json='["Observational", "Interventional"]')
    # sub1.studies.append(study1)
    # study2 = SubmissionStudy(study_name='OncoTrack', study_description='IMI Project....',
    #                          study_types_json='["Observational", "Interventional"]')
    # sub1.studies.append(study2)
    # contact1 = StudyContact(firstname='Kavita', surname='Rege', category_id=3, email="kavita.rege@uni.lu",
    #                              institution="University of Luxembourg")
    # study1.study_contacts.append(contact1)
    # contact2 = StudyContact(firstname='Pinar', surname='Alper', category_id=2, email="pinar.alper@uni.lu",
    #                              institution="University of Luxembourg")
    # study1.study_contacts.append(contact2)

    # db.session.add(sub1)
    # db.session.add(sub2)
    # db.session.commit()

    # u1 = User(first_name='Kavita', last_name='Rege',
    #           elixir_sub_id='0a5006e96e96c8b9481af9a16034aebe7dc7c9c5@elixir-europe.org', email='kavita.rege@uni.lu',
    #           institution='University of Luxembourg',
    #           phone_no='3524666449647')
    # register_new_user(u1)
    # assign_role_to_user(u1, 'admin')
    # assign_role_to_user(u1, 'data_provider')

    u1 = User(first_name='P\u0131nar', last_name='Alper',
              elixir_sub_id='5142d45eeece42e2108f6c3c146745b41db21e87@elixir-europe.org', email='pinar.alper@uni.lu',
              institution='University of Luxembourg',
              phone_no='+352123456789')
    register_new_user(u1)
    assign_role_to_user(u1, 'admin')

    return


# TODO I don't know what the below command does. FInd out.
manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))

# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
