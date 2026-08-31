from functools import wraps

from flask import Blueprint, request, jsonify

from elixir_dss import app, db
from elixir_dss.models.submission import (
    Submission,
    SubmissionStatusEnum,
)

dss_api = Blueprint("dss_api", __name__)


# The two stages an external consumer acts on: it inspects the data during
# Data Verification, and places it once the submission is Complete.
ALLOWED_STATUSES = {
    "data_approval": SubmissionStatusEnum.data_approval,
    "completed": SubmissionStatusEnum.completed,
}
# Unchanged default, so existing callers keep seeing completed submissions only.
DEFAULT_STATUSES = {SubmissionStatusEnum.completed}

if not app.config.get("SERVICE_API_KEY"):
    raise RuntimeError("SERVICE_API_KEY is not configured")


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@dss_api.errorhandler(ApiError)
def handle_api_error(error):
    return jsonify({"error": error.message}), error.status


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not app.config.get("SERVICE_API_KEY"):
            return jsonify({"error": "DSS API is not configured"}), 503
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != app.config.get("SERVICE_API_KEY"):
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)

    decorated_function._public = True
    return decorated_function


def _statuses():
    """The statuses named by ?status=a,b, or completed only when absent."""
    raw = request.args.get("status")
    if not raw:
        return DEFAULT_STATUSES
    try:
        return {ALLOWED_STATUSES[name.strip()] for name in raw.split(",")}
    except KeyError:
        raise ApiError(
            "Unknown status, allowed: " + ", ".join(sorted(ALLOWED_STATUSES))
        )


def _summary(submission):
    return {
        "id": submission.id,
        "ref_name": submission.ref_name,
        "status": submission.current_status.value,
        "status_code": submission.current_status.name,
    }


def _details(submission):
    """What a consumer needs to place a submission. All of it already stored."""
    return dict(
        _summary(submission),
        local_project_name=submission.local_project_name,
        local_custodians=submission.local_custodian_entries(),
        access=[
            {
                "role": access.role,
                "first_name": access.user.first_name,
                "last_name": access.user.last_name,
                "email": access.user.email,
            }
            for access in submission.submission_accesses
            if access.user
        ],
        attachments=[
            {
                "id": attachment.id,
                "note": attachment.note,
                "folder_name": attachment.folder_name,
                "file_names": attachment.file_names.split(),
            }
            for attachment in submission.attachments
        ],
    )


@dss_api.route("/healthz", methods=["GET"])
@require_api_key
def healthz():
    return jsonify({"status": "ok"})


@dss_api.route("/submissions", methods=["GET"])
@require_api_key
def list_submissions():
    submissions = Submission.query.filter(
        Submission.current_status.in_(_statuses())
    ).all()
    return jsonify(
        {"data": [_summary(s) for s in submissions], "count": len(submissions)}
    )


@dss_api.route("/submissions/<int:submission_id>", methods=["GET"])
@require_api_key
def get_submission(submission_id):
    """Readable at any status.

    A submission that has been staged can be rejected back to Data Upload or
    cancelled, and a filtered listing cannot express that: it simply
    disappears, leaving the caller holding data it cannot account for.
    """
    return jsonify({"data": _details(db.get_or_404(Submission, submission_id))})


@dss_api.route("/submissions/<int:submission_id>/datasets", methods=["GET"])
@require_api_key
def get_submission_datasets(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    if submission.current_status not in ALLOWED_STATUSES.values():
        raise ApiError("Submission is not found", 404)
    datasets = [dataset.to_dict() for dataset in submission.datasets]
    return jsonify(
        {
            "data": datasets,
            "count": len(datasets),
            "submission": _details(submission),
        }
    )
