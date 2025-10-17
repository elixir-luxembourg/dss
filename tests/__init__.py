import os

from flask_testing import TestCase

from elixir_dss import app, db
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

__author__ = "Pinar Alper"


class BaseTest(TestCase):
    def create_app(self):
        os.environ["elixir_dss_ENV"] = "test"
        app.config.from_object("elixir_dss.settings.TestConfig")
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()
        initial_data = app.config.get("DATA_INIT")

        for contact_type in initial_data["contact_types"]:
            db.session.add(ContactType(name=contact_type))

        for name_role in initial_data["names_roles"]:
            db.session.add(Role(name=name_role))

        for deid_type in initial_data["deidentification_type"]:
            db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

        for subj_cat in initial_data["subject_category"]:
            db.session.add(SubjectCategory(code=subj_cat[0], label=subj_cat[1]))

        for lb_type in initial_data["legal_basis"]:
            db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

        for cons_status in initial_data["consent_status"]:
            db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))
        #
        for sub_scope in initial_data["submission_scope"]:
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
        return self.client.post(
            "/login",
            data=dict(username=username, password=password, remember=True),
            follow_redirects=False,
        )

    def create_users(self):
        u1 = User(
            first_name="Steward",
            last_name="One",
            elixir_sub_id="DUMMY_ELX_ID",
            email="steward1@uni.lu",
            institution_accession="ELU_I_77",
            phone_no="+352123456789",
        )
        register_new_user(u1)
        assign_role_to_user(u1, "admin")

        u2 = User(
            first_name="Submitter",
            last_name="One",
            elixir_sub_id="ANOTHER_DUMMY_ELX_ID",
            email="submitter1@some.edu",
            institution_accession="ELU_I_79",
            phone_no="+352123456789",
        )
        register_new_user(u2)
        assign_role_to_user(u2, "data_provider")

        u3 = User(
            first_name="Submitter",
            last_name="Two",
            elixir_sub_id="YET_ANOTHER_DUMMY_ELX_ID",
            email="submitter2@some.edu",
            institution_accession="ELU_I_79",
            phone_no="+352123456789",
        )
        register_new_user(u3)
        assign_role_to_user(u3, "data_provider")
