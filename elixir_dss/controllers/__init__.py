import importlib
from functools import wraps

from flask import current_app, render_template, request
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS

from elixir_dss import db
from ..models.services import has_access

submission_models_module = importlib.import_module("elixir_dss.models.submission")


def app_authorization(**options):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)
            elif current_app.config.get("LOGIN_DISABLED"):
                return func(*args, **kwargs)
            elif not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            else:
                if not current_user.has_role_from(options.get("allowed_roles")):
                    return (
                        render_template(
                            "error.html",
                            message="Error 403 - Unauthorized",
                            show_home_link=True,
                        ),
                        403,
                    )
                if (not current_user.is_data_steward()) and options.get(
                    "record_authorization"
                ):
                    params = options.get("record_authorization")
                    my_entity_name = getattr(submission_models_module, params["entity"])
                    my_entity_id = kwargs[params["entity_id_key"]]
                    # SQLAlchemy 2.0 style - use session.get() for primary key lookups
                    my_entity = db.session.get(my_entity_name, my_entity_id)
                    my_attribute = getattr(my_entity, params["entity_ac_attribute"])
                    if not has_access(current_user.get_id(), my_attribute):
                        return (
                            render_template(
                                "error.html",
                                message="Error 403 - Unauthorized",
                                show_home_link=True,
                            ),
                            403,
                        )
            return func(*args, **kwargs)

        return decorated_view

    return wrapper


from . import errors, reporters, web_controllers  # noqa: E402

__author__ = "Valentin Grouès, Pinar Alper"

__all__ = [errors, web_controllers, reporters]
