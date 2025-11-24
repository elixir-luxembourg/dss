import importlib
from functools import wraps

from flask import current_app, render_template, request
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS

from elixir_dss import db
from ..models.services import has_access
from ..models.submission import Submission

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
                if options.get("record_authorization"):
                    params = options.get("record_authorization")
                    my_entity_class = getattr(
                        submission_models_module, params["entity"]
                    )
                    my_entity_id = kwargs[params["entity_id_key"]]
                    # SQLAlchemy 2.0 style - use session.get() for primary key lookups
                    my_entity = db.session.get(my_entity_class, my_entity_id)
                    submission_id = getattr(my_entity, params["entity_ac_attribute"])
                    if not current_user.is_data_steward():
                        if not has_access(
                            user_id=current_user.get_id(), submission_id=submission_id
                        ):
                            return (
                                render_template(
                                    "error.html",
                                    message="Error 403 - Unauthorized",
                                    show_home_link=True,
                                ),
                                403,
                            )
                    if params["entity"] == "Submission":
                        submission = my_entity
                    else:
                        submission = db.session.get(Submission, submission_id)

                    if (
                        submission
                        and submission.is_cancelled()
                        and request.method not in ("GET", "HEAD", "OPTIONS")
                    ):
                        return (
                            render_template(
                                "error.html",
                                message="Error 403 - This submission has been cancelled. No further changes are allowed.",
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
