#!/usr/bin/env python

from flask_assets import ManageAssets
from flask_migrate import MigrateCommand
from flask_script import Manager, Shell

from elixir_dcp import app, db
from datetime import datetime
from elixir_dcp.models import Submission

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def init_db():
    db.drop_all()
    db.create_all()

    sub1 = Submission(name='OncoTrack', description='Submission of Oncotrack data', created=datetime.today())
    sub2 = Submission(name='Predict-TB', description='Submission of Predict-TB preclinical data', created=datetime.today())

    db.session.add(sub1)
    db.session.add(sub2)
    db.session.commit()
    return


manager.add_command("shell", Shell(use_ipython=True, use_bpython=False))
# work-around bug in flask-assets
app.jinja_env.assets_environment.environment = app.jinja_env.assets_environment
manager.add_command("assets", ManageAssets(app.jinja_env.assets_environment))
manager.run()
