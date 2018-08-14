import os
from flask_testing import TestCase
from elixir_dcp import db, app
from elixir_dcp.models.security import Role
from elixir_dcp.models.services import register_new_user, assign_role_to_user
from elixir_dcp.models.submission import SubmissionScope, ConsentStatus, DeIdentificationType, LegalBasisType
from elixir_dcp.models.security import User

__author__ = 'Pinar Alper'

class BaseTest(TestCase):
    def create_app(self):
        os.environ['ELIXIR_DCP_ENV'] = 'test'
        app.config.from_object('elixir_dcp.settings.TestConfig')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()
        initial_data = app.config.get('DATA_INIT')

        # for contact_type in initial_data['contact_types']:
        #     db.session.add(ContactType(name=contact_type))
        #
        for name_role in initial_data['names_roles']:
            db.session.add(Role(name=name_role))
        #
        # for category in initial_data['size_categories']:
        #     db.session.add(DataSizeCategory(code=category[0], label=category[1]))
        #
        # for code_triple in initial_data['ga4gh_codes']:
        #     db.session.add(GA4GHCodes(code=code_triple[0], name=code_triple[1], description = code_triple[2]))
        #
        #
        for deid_type in initial_data['deidentification_type']:
            db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

        for lb_type in initial_data['legal_basis']:
            db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

        for cons_status in initial_data['consent_status']:
            db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))
        #
        for sub_scope in initial_data['submission_scope']:
            db.session.add(SubmissionScope(code=sub_scope[0], label=sub_scope[1]))

        db.session.commit()


    def tearDown(self):
        db.session.remove()
        db.drop_all()





class BaseIntegrationTest(BaseTest):
    def setUp(self):
        super().setUp()
        # create users

        self.create_users()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=False)


    def create_users(self):
        u1 = User(first_name='P\u0131nar', last_name='Alper',
                  elixir_sub_id='DUMMY_ELX_ID', email='pinar.alper@uni.lu',
                  institution='University of Luxembourg',
                  phone_no='+352123456789')
        register_new_user(u1)
        assign_role_to_user(u1, 'admin')


        u2 = User(first_name='Kavita', last_name='Rege',
                       elixir_sub_id='ANOTHER_DUMMY_ELX_ID', email='kavita.rege@uni.lu',
                       institution='University of Luxembourg',
                       phone_no='+352123456789')
        register_new_user(u2)
        assign_role_to_user(u2, 'data_provider')



