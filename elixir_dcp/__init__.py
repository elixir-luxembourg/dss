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
import json
from flask_wkhtmltopdf import Wkhtmltopdf

__VERSION__ = "0.0.1"


def create_application():
    new_app = Flask(__name__)
    wkhtmltopdf = Wkhtmltopdf(new_app)
    new_app.config['WKHTMLTOPDF_USE_CELERY '] = True

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

csrf = CSRFProtect()
csrf.init_app(app)

assets_env = Environment(app)
assets_loader = PythonAssetsLoader(assets)
for name, bundle in assets_loader.load_bundles().items():
    assets_env.register(name, bundle)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class OidcCredentials(db.Model):
    __tablename__ = 'oidc_credentials'

    cred_key = db.Column(db.String, primary_key=True)
    cred_val = db.Column(db.String)


class CredentialsPersistentStore:
    def __init__(self, persist_db=None):
        self.cred_db = persist_db

    def __setitem__(self, key, val):
        item = OidcCredentials.query.filter_by(cred_key=key).one_or_none()
        if item:
            item.cred_val = json.dumps(val)
            self.cred_db.session.add(item)
            self.cred_db.session.commit()
        else:
            item = OidcCredentials()
            item.cred_key = key
            item.cred_val = json.dumps(val)
            self.cred_db.session.add(item)
            self.cred_db.session.commit()

    def __getitem__(self, key):
        credential = OidcCredentials.query.filter_by(cred_key=key).one_or_none()
        if credential:
            return json.loads(credential.cred_val)
        else:
            return None

    def __delitem__(self, key):
        credential = OidcCredentials.query.filter_by(cred_key=key).one_or_none()
        if credential:
            db.session.delete(credential)
            db.session.commit()
        return


credentials_store = CredentialsPersistentStore(persist_db=db)

oidc = OpenIDConnect(app=app, credentials_store=credentials_store)

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
    app.jinja_env.auto_reload = True
    app.run(debug=True, use_reloader=True)
