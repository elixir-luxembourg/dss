import logging
from logging.handlers import RotatingFileHandler

from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_assets import Environment
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from webassets.loaders import PythonLoader as PythonAssetsLoader

from elixir_dss.clients.lft import LFTHandler
from elixir_dss.settings import ELIXIR_DSS_ENV
import elixir_dss.assets as assets
import elixir_dss.exceptions as exceptions


__VERSION__ = "0.4.0-dev"


def create_application():
    new_app = Flask(__name__)
    new_app.config.from_object(
        "elixir_dss.settings.%sConfig" % ELIXIR_DSS_ENV.capitalize()
    )
    new_app.config["ENV"] = ELIXIR_DSS_ENV
    new_app.jinja_env.add_extension("jinja2.ext.i18n")

    new_app.cache = Cache(new_app, config=new_app.config["CACHE_CONFIG"])
    new_app.cache.clear()

    handler = RotatingFileHandler("elixir_dss_app.log", maxBytes=10000, backupCount=1)
    handler.setLevel(logging.ERROR)
    new_app.logger.addHandler(handler)
    return new_app


app = create_application()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message_category = "error"

oauth = None
authentication_method = app.config.get("AUTHENTICATION_METHOD", "CONFIG")
if authentication_method == "CONFIG":
    login_manager.login_view = "login"
elif authentication_method == "AAI":
    login_manager.login_view = "oidc_login"

    oauth = OAuth(app)
    if app.config.get("OIDC_AUTHORITY"):
        metadata_url = (
            f"{app.config['OIDC_AUTHORITY']}/.well-known/openid-configuration"
        )
        oauth.register(
            name="keycloak",
            server_metadata_url=metadata_url,
            client_id=app.config["CLIENT_ID"],
            client_secret=app.config["CLIENT_SECRET"],
            client_kwargs={"scope": app.config["OIDC_SCOPES"]},
        )
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

# Setup Flask-Mail
mail = Mail(app)

lft = LFTHandler(app)

app.add_template_global(login_manager.login_view, "login_page")


@app.template_filter("dt")
def _jinja2_filter_datetime(date, fmt=None):
    if date is None:
        return None
    if fmt:
        return date.strftime(fmt)
    else:
        return date.strftime("%Y-%m-%d,  %H:%M")


@app.template_filter("date")
def _jinja2_filter_date(date, fmt=None):
    return _jinja2_filter_datetime(date, "%Y-%m-%d")


@app.context_processor
def inject_now():
    return {
        "version": __VERSION__,
        "SYSTEM_NAME": app.config.get("TITLE", "LCSB Data Submission System"),
    }


@app.before_request
def enforce_auth_by_default():
    from flask import request
    from flask_login import current_user

    if request.endpoint in ("static", None):
        return

    view_func = app.view_functions.get(request.endpoint)
    if not view_func:
        return

    if getattr(view_func, "_public", False) or getattr(view_func, "_protected", False):
        return

    if not current_user.is_authenticated:
        return login_manager.unauthorized()


def run_export_submission():
    models.services.schedule_submission_export()


# Import controllers and models after all other objects are created to avoid circular imports
from . import controllers, models  # noqa: E402

app.register_blueprint(controllers.api_controllers.dss_api, url_prefix="/api/v1")

__all__ = [controllers, assets, app, db, exceptions, oauth, mail, lft]

if __name__ == "__main__":
    app.run(use_reloader=False)
