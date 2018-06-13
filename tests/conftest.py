import os
import pytest

from elixir_dcp import create_application, db as _db


TESTDB = 'test-elixir-dcp.db'
TESTDB_PATH = "/Users/kavita.rege/virtualenvs/elixir-dcp/elixir_dcp/{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def app(request):
    """Session wide test 'Flask' application."""
    settings_override = {
       'TESTING': True,
       'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,

   }

    app = create_application()

    #Establish an application context before running the tests
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='session')
def db(app, request):
    """Session-wide test database"""
    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)

    def teardown():
        _db.drop_all()
        os.unlink(TESTDB_PATH)

    _db.init_app(app)
    with app.app_context():
        _db.create_all()

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='function', autouse=True)
def session(app, db, request):
    """Creates a new database for a test.
    Returns function-scoped session"""

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        options = dict(bind=connection, binds={})
        session = db.create_scoped_session(options=options)

        db.session = session

        def teardown():
            transaction.rollback()
            connection.close()
            session.remove()

        request.addfinalizer(teardown)
        return session


