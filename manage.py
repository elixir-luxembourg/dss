#!/usr/bin/env python
from datetime import datetime

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell
from elixir_dcp import app, db
from elixir_dcp.models.submission import ContactType, DataSizeCategory, Submission, SubmissionContact, \
    SubmissionStatusEnum, GA4GHCodes, SubmissionUseConditionGroup
from elixir_dcp.models.security import User, Role

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()

    names_contact_types = ['PI', 'Researcher', 'Data Manager', 'Data Protection Officer', 'Legal Representative',
                           'Other']
    for name_contact_type in names_contact_types:
        db.session.add(ContactType(name=name_contact_type))

    names_roles = ['data_provider', 'admin']
    for name_role in names_roles:
        db.session.add(Role(name=name_role))

    size_categories = [['elx_s', 'Less than 10GB'],
                       ['elx_m', 'Between 10 and 100GB'],
                       ['elx_l', 'Greater than 100 GB']]
    for category in size_categories:
        db.session.add(DataSizeCategory(code=category[0], label=category[1]))
    db.session.commit()

    ga4gh_codes = [['NRES', 'no restrictions', 'No restrictions on data use.'],
                   ['GRU(CC)', 'general research use and clinical care',
                    'For health/medical/biomedical purposes and other biological research, including the study of population origins or ancestry.'],
                   ['HMB(CC)', 'health/medical/biomedical research and clinical care',
                    'Use of the data is limited to health/medical/biomedical purposes, does not include the study of population origins or ancestry.'],
                   ['DS-[XX](CC)', 'disease-specific research and clinical care.',
                    'Use of the data must be related to [disease].'],
                   ['POA', 'population origins/ancestry research',
                    'Use of the data is limited to the study of population origins or ancestry.'],
                   ['RS-[XX]', 'other research-specific restrictions',
                    'Use of the data is limited to studies of [research type] (e.g., pediatric research).'],
                   ['RUO', 'research use only',
                    'Use of data is limited to research purposes (e.g., does not include its use in clinical care).'], ['NMDS', 'no \"general methods\" research',
                    'Use of the data includes methods development research (e.g., development of software or algorithms) ONLY within the bounds of other data use limitations.'],
                   ['GSO', 'genetic studies only',
                    'Use of the data is limited to genetic studies only (i.e., no research using only the phenotype data).'],
                   ['NPU', 'not-for-profit use only', 'Use of the data is limited to not-for-profit organizations.'],
                   ['PUB', 'publication required',
                    'Requestor agrees to make results of studies using the data available to the larger scientific community.'],
                   ['COL-[XX]', 'collaboration required',
                    'Requestor must agree to collaboration with the primary study investigator(s).'],
                   ['RTN', 'return data to database/resource',
                    'Requestor must return derived/enriched data to the database/resource.'],
                   ['IRB', 'ethics approval required',
                    'Requestor must provide documentation of local IRB/REC approval.'],
                   ['GS-[XX]', 'geographical restrictions',
                    'Use of the data is limited to within [geographic region].'],
                   ['MOR-[XX]', 'publication moratorium/embargo',
                    'Requestor agrees not to publish results of studies until [date].'],
                   ['TS-[XX]', 'time limits on use', 'Use of data is approved for [x months].'],
                   ['US', 'user-specific restrictions', 'Use of data is limited to use by approved users.'],
                   ['PS', 'project-specific restrictions', 'Use of data is limited to use within an approved project.'],
                   ['IS', 'institution-specific restrictions',
                    'Use of data is limited to use within an approved institution.']]

    for code_triple in ga4gh_codes:
        db.session.add(GA4GHCodes(code=code_triple[0], name=code_triple[1], description=code_triple[2]))
    db.session.commit()

    sub1 = Submission(name='OncoTrack', description='Submission of Oncotrack data', created_on=datetime.today(),
                      current_status=SubmissionStatusEnum.draft)
    sub2 = Submission(name='Predict-TB', description='Submission of Predict-TB preclinical data',
                      created_on=datetime.today(), current_status=SubmissionStatusEnum.draft)
    contact1 = SubmissionContact(name='P\u0131nar', surname='Alper', category_id=3, is_primary=True)
    sub1.contacts.append(contact1)
    contact2 = SubmissionContact(name='Valentin', surname='Grou\u00E8s', category_id=1, is_primary=True)
    sub2.contacts.append(contact2)
    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()

    db.session.add(User(first_name='P\u0131nar', last_name='Alper', elixir_reg_id='pinar.alper@uni.lu',
                        phone_code='352', phone_no='123456789', active_user=True))
    db.session.add(User(first_name='Alice', last_name='White', elixir_reg_id='alice@kcl.ac.uk',
                        phone_code='44', phone_no='123456789', active_user=True))
    db.session.commit()

    User.query.filter_by(elixir_reg_id='pinar.alper@uni.lu').one_or_none().assign_role('admin')
    User.query.filter_by(elixir_reg_id='alice@kcl.ac.uk').one_or_none().assign_role('data_provider')
    db.session.commit()

    return

@manager.command
def get_all_DUC_groups():
    groups = SubmissionUseConditionGroup.query.all()
    for group in groups:
        app.logger.info(group)
    return


manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))
# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()



