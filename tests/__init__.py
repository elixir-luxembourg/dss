import os

from flask_testing import TestCase

os.environ["ELIXIR_DSS_ENV"] = "test"

from elixir_dss import app, db
from elixir_dss.models.security import User
from elixir_dss.models.services import assign_role_to_user, register_new_user
from elixir_dss.models.seed_data import seed_init_data

__author__ = "Pinar Alper"


class BaseTest(TestCase):
    def create_app(self):
        app.config.from_object("elixir_dss.settings.TestConfig")
        return app

    def setUp(self):
        if os.environ.get("ELIXIR_DSS_ENV", "") != "test":
            raise ValueError(
                "ELIXIR_DSS_ENV environment variable should be set to test for unittests"
            )
        db.drop_all()
        db.create_all()
        seed_init_data()

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
        assign_role_to_user(u1, "data_steward")

        u2 = User(
            first_name="Submitter",
            last_name="One",
            elixir_sub_id="ANOTHER_DUMMY_ELX_ID",
            email="submitter1@some.edu",
            institution_accession="ELU_I_79",
            phone_no="+352123456789",
        )
        register_new_user(u2)
        assign_role_to_user(u2, "user")

        u3 = User(
            first_name="Submitter",
            last_name="Two",
            elixir_sub_id="YET_ANOTHER_DUMMY_ELX_ID",
            email="submitter2@some.edu",
            institution_accession="ELU_I_79",
            phone_no="+352123456789",
        )
        register_new_user(u3)
        assign_role_to_user(u3, "user")

        u4 = User(
            first_name="admin",
            last_name="One",
            elixir_sub_id="ADMIN_ELX_ID",
            email="admin@uni.lu",
            institution_accession="ELU_I_77",
            phone_no="+352123456789",
        )
        register_new_user(u4)
        assign_role_to_user(u4, "admin")

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)
