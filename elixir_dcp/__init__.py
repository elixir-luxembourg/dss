import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_assets import Environment
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader
import elixir_dcp.assets as assets
import elixir_dcp.exceptions as exceptions
from flask_oidc import OpenIDConnect

__VERSION__ = "0.0.1-dev"


def create_application():
    new_app = Flask(__name__)
    env = os.environ.get('ELIXIR_DCP_ENV', 'dev')  # will default to dev env if no var exported
    new_app.config.from_object('elixir_dcp.settings.%sConfig' % env.capitalize())
    new_app.config['ENV'] = env
    new_app.jinja_env.add_extension('jinja2.ext.i18n')

    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.ERROR)
    new_app.logger.addHandler(handler)
    return new_app


app = create_application()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message_category = "error"

authentication_method = app.config.get('AUTHENTICATION_METHOD', 'CONFIG')
if authentication_method == 'CONFIG':
    login_manager.login_view = "login"
elif authentication_method == 'AAI':
    login_manager.login_view = "oidc_login"
else:
    raise ValueError("Unsupported authentication method")

oidc = OpenIDConnect()
oidc.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Setup Flask-Mail
mail = Mail(app)


app.add_template_global(login_manager.login_view, 'login_page')

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


@app.context_processor
def inject_now():
    return {'version': __VERSION__}


from . import controllers

__all__ = [controllers, assets, app, db, exceptions, oidc, mail]

if __name__ == '__main__':
    app.run()
