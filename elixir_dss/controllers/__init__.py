from functools import wraps

from flask import abort, render_template, request
from flask_login import current_user, login_required

from elixir_dss import db
from ..models.services import has_access
from ..models.submission import (
    Submission,
    SubmissionAttachment,
    SubmissionDataset,
    SubmissionStudy,
)

ACCESS_RULES = {
    "sub_id": (Submission, "id"),
    "submission_id": (Submission, "id"),
    "dataset_id": (SubmissionDataset, "submission_id"),
    "study_id": (SubmissionStudy, "submission_id"),
    "attach_id": (SubmissionAttachment, "submission_id"),
}


def protect(roles=None, states=None, public=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if public:
                return func(*args, **kwargs)

            entity_cls, attr, entity_id = _resolve_access(kwargs)
            submission = None

            if entity_cls:
                record = db.session.get(entity_cls, entity_id)
                if not record:
                    abort(404)

                submission_id = getattr(record, attr)
                submission = (
                    record
                    if entity_cls == Submission
                    else db.session.get(Submission, submission_id)
                )

                if not submission:
                    abort(404)

            if roles and not current_user.has_role_from(roles):
                return _forbidden("Error 403 - Unauthorised")

            if submission:
                is_steward = current_user.is_data_steward()

                if not is_steward and not has_access(
                    current_user.get_id(), submission.id
                ):
                    abort(404)

                if submission.is_cancelled() and request.method not in (
                    "GET",
                    "HEAD",
                    "OPTIONS",
                ):
                    return _forbidden(
                        "This submission has been cancelled. No further changes allowed."
                    )

                if states and not is_steward:
                    if submission.current_status not in states:
                        return _forbidden(
                            "You are not allowed to perform this action at this stage."
                        )

            return func(*args, **kwargs)

        if not public:
            wrapper = login_required(wrapper)

        wrapper._protected = True
        wrapper._public = public
        return wrapper

    return decorator


def _resolve_access(kwargs):
    for param, value in kwargs.items():
        if param in ACCESS_RULES:
            entity_cls, attr = ACCESS_RULES[param]
            return entity_cls, attr, value
    return None, None, None


def _forbidden(message):
    return (
        render_template("error.html", message=message, show_home_link=True),
        403,
    )


from . import errors, reporters, web_controllers, api_controllers  # noqa: E402

__author__ = "Valentin Grouès, Pinar Alper"

__all__ = [errors, web_controllers, reporters, api_controllers]
