import os
os.environ['ELIXIR_DCP_ENV'] = 'test'

from flask_testing import TestCase
from elixir_dcp import db, app
from elixir_dcp.models.security import User, Role
from elixir_dcp.models.services import register_new_user, assign_role_to_user

class BaseTest(TestCase):
    def create_app(self):

        #app.config.from_object('elixir-dcp.settings.TestConfig')
        return app

    def setUp(self):
        db.drop_all()
        db.create_all()
        initial_data = app.config.get('DATA_INIT')


        for name_role in initial_data['names_roles']:
            db.session.add(Role(name=name_role))


        u1 = User(first_name='P\u0131nar', last_name='Alper',
                  elixir_sub_id='DUMMY_VALUE', email='pinar.alper@uni.lu',
                  institution='University of Luxembourg',
                  phone_no='+352123456789')
        register_new_user(u1)
        assign_role_to_user(u1, 'admin')



    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=False)

    def login_as_admin(self):
        return self.login("pinar.alper@uni.lu", "palper")



