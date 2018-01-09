import os

from flask import Flask
from flask_assets import Environment
from flask_babel import Babel
from flask_mail import Mail
#from flask_security import SQLAlchemyUserDatastore, Security
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader
import elixir_dcp.assets as assets
import elixir_dcp.exceptions as exceptions
from flask_oidc import OpenIDConnect


__VERSION__ = "0.0.1-dev"


def configure_authentication_system():
    from .authentication.config_authentication import ConfigAuthentication
    from .authentication.aai_authentication import AAIAuthentication

    authentication_method = app.config.get('AUTHENTICATION_METHOD', 'CONFIG')
    if authentication_method == 'CONFIG':
        authentication = ConfigAuthentication(app.config.get('AUTHENTICATION_DICT', {}))
    elif authentication_method == 'AAI':
        authentication = AAIAuthentication()
    else:
        raise ValueError("Unsupported authentication method")
    app.config['authentication'] = authentication


def create_application():
    new_app = Flask(__name__)
    env = os.environ.get('ELIXIR_DCP_ENV', 'dev')  # will default to dev env if no var exported
    new_app.config.from_object('elixir_dcp.settings.%sConfig' % env.capitalize())
    new_app.config['ENV'] = env
    new_app.jinja_env.add_extension('jinja2.ext.i18n')
    return new_app


app = create_application()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "oidc_login"
login_manager.login_message_category = "error"

csrf = CSRFProtect()
csrf.init_app(app)

oidc = OpenIDConnect()
oidc.init_app(app)

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
configure_authentication_system()

# Setup Flask-Babel
#babel = Babel(app)

# Setup Flask-Mail
#mail = Mail(app)

# Setup Flask-Security
#from elixir_dcp.models import Role, User

#user_datastore = SQLAlchemyUserDatastore(db, User, Role)
#security = Security(app, user_datastore)


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

@app.template_filter('pluralize')
def _submission_view_mode(user_role, submission_status):
    app.logger.debug(number)
    if number == 1:
        return singular
    else:
        return plural

@app.context_processor
def inject_now():
    return {'version': __VERSION__}


from . import controllers

__all__ = [controllers, assets, app, db, exceptions, oidc]
# db.create_all()
if __name__ == '__main__':
    app.run()
