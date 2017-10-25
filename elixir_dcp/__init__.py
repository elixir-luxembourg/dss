import os

from flask import Flask
from flask_assets import Environment
from flask_babel import Babel
from flask_mail import Mail
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore, Security
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader

import elixir_dcp.assets as assets

__VERSION__ = "0.0.1-dev"


def create_application():
    new_app = Flask(__name__)
    env = os.environ.get('ELIXIR_DCP_ENV', 'dev')  # will default to dev env if no var exported
    new_app.config.from_object('elixir_dcp.settings.%sConfig' % env.capitalize())
    new_app.config['ENV'] = env
    new_app.jinja_env.add_extension('jinja2.ext.i18n')
    return new_app


app = create_application()

csrf = CSRFProtect()
csrf.init_app(app)

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Setup Flask-Babel

babel = Babel(app)

# Setup Flask-Mail
mail = Mail(app)

# Setup Flask-Security
from elixir_dcp.models import Role, User

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@app.template_filter('dt')
def _jinja2_filter_datetime(date, fmt=None):
    if date is None:
        return None
    if fmt:
        return date.strftime(fmt)
    else:
        return date.strftime('%Y-%m-%d,  %H:%M')


@app.template_filter('date')
def _jinja2_filter_date(date, fmt=None):
    return _jinja2_filter_datetime(date, '%Y-%m-%d')


@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    app.logger.debug(number)
    if number == 1:
        return singular
    else:
        return plural


@app.context_processor
def inject_now():
    return {'version': __VERSION__}


from . import controllers

__all__ = [controllers, assets, app]
# db.create_all()
if __name__ == '__main__':
    app.run()
