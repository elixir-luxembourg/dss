import importlib
from functools import wraps

from flask import current_app, render_template, request
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS

from elixir_dss import db
from ..models.services import has_access
from ..models.submission import (
    Submission,
    SubmissionStatusEnum,
)

submission_models_module = importlib.import_module("elixir_dss.models.submission")


def app_authorization(**options):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if request.method in EXEMPT_METHODS:
                return func(*args, **kwargs)

            if current_app.config.get("LOGIN_DISABLED"):
                return func(*args, **kwargs)

            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()

            # Role check
            if not current_user.has_role_from(options.get("allowed_roles")):
                return _deny("Error 403 - Unauthorized")

            submission = None

            # --------------------------
            # Resolve submission from record_authorization
            # --------------------------
            record_auth = options.get("record_authorization")
            if record_auth:
                params = record_auth
                entity_cls = getattr(submission_models_module, params["entity"])
                entity_id = kwargs[params["entity_id_key"]]

                entity = db.session.get(entity_cls, entity_id)
                submission_id = getattr(entity, params["entity_ac_attribute"])

                if not current_user.is_data_steward():
                    if not has_access(current_user.get_id(), submission_id):
                        return _deny("Error 403 - Unauthorized")

                if params["entity"] == "Submission":
                    submission = entity
                else:
                    submission = db.session.get(Submission, submission_id)

                if (
                    submission
                    and submission.is_cancelled()
                    and request.method not in ("GET", "HEAD", "OPTIONS")
                ):
                    return _deny(
                        "This submission has been cancelled. No further changes allowed."
                    )

            # --------------------------
            # submission_action logic
            # --------------------------
            action = options.get("submission_action")
            if action and submission:
                if not current_user.is_data_steward():
                    if action == "edit_metadata":
                        if (
                            submission.current_status
                            != SubmissionStatusEnum.metadata_submission
                        ):
                            return _deny(
                                "You can no longer edit the submitted metadata!"
                            )

                    # 2. steer
                    if action == "steer":
                        forbidden = {
                            SubmissionStatusEnum.draft,
                            SubmissionStatusEnum.metadata_approval,
                            SubmissionStatusEnum.data_approval,
                        }
                        if submission.current_status in forbidden:
                            return _deny(
                                "You are not allowed to steer this submission at this stage."
                            )

            return func(*args, **kwargs)

        return decorated_view

    return wrapper


def _deny(message):
    return (
        render_template("error.html", message=message, show_home_link=True),
        403,
    )


from . import errors, reporters, web_controllers  # noqa: E402

__author__ = "Valentin Grouès, Pinar Alper"

__all__ = [errors, web_controllers, reporters]
