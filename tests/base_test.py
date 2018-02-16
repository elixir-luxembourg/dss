
from flask_testing import TestCase
from elixir_dcp import db, app, configure_authentication_system


class BaseTest(TestCase):
    def create_app(self):
        app.config.from_object('elixir-dcp.settings.TestConfig')
        configure_authentication_system()
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=False)

    def login_as_admin(self):
        return self.login("valentin.groues@uni.lux", "password")

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

