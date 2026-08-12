from functools import wraps

from flask import abort, render_template, request
from flask_login import current_user, login_required

from elixir_dss import db
from ..models.services import get_access
from ..models.submission import (
    Submission,
    SubmissionAccess,
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


def _resolve_submission(kwargs):
    entity_cls, attr, entity_id = _resolve_access(kwargs)
    if not entity_cls:
        return None

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

    return submission


def _check_roles(roles):
    if roles and not current_user.has_role_from(roles):
        return _forbidden("Error 403 - Unauthorised")
    return None


def _check_submission_access(submission):
    is_steward = current_user.is_data_steward()
    if is_steward:
        return is_steward, None
    access = get_access(current_user.get_id(), submission.id)
    if access is None:
        abort(404)
    return is_steward, access.role


def _check_submission_state(submission, states, is_steward):
    if submission.is_cancelled() and request.method not in ("GET", "HEAD", "OPTIONS"):
        return _forbidden(
            "This submission has been cancelled. No further changes allowed."
        )

    if states and not is_steward and submission.current_status not in states:
        return _forbidden("You are not allowed to perform this action at this stage.")

    return None


def protect(roles=None, states=None, public=False, recipient_allowed=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if public:
                return func(*args, **kwargs)

            submission = _resolve_submission(kwargs)

            error = _check_roles(roles)
            if error:
                return error

            if submission:
                is_steward, access_role = _check_submission_access(submission)
                if (
                    access_role == SubmissionAccess.ROLE_RECIPIENT
                    and not recipient_allowed
                ):
                    return _forbidden("You have read-only access to this submission.")
                error = _check_submission_state(submission, states, is_steward)
                if error:
                    return error

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
