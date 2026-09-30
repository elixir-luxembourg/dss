from functools import wraps

from flask import Blueprint, abort, request, jsonify
from werkzeug.exceptions import HTTPException

from elixir_dss import app, db
from elixir_dss.models.submission import (
    Submission,
    SubmissionStatusEnum,
)

dss_api = Blueprint("dss_api", __name__)


ALLOWED_STATUSES = {
    SubmissionStatusEnum.data_approval,
    SubmissionStatusEnum.completed,
    SubmissionStatusEnum.cancelled,
}

if not app.config.get("SERVICE_API_KEY"):
    raise RuntimeError("SERVICE_API_KEY is not configured")


@dss_api.errorhandler(HTTPException)
@dss_api.errorhandler(404)
def handle_http_exception(error):
    return jsonify({"error": error.description}), error.code


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != app.config.get("SERVICE_API_KEY"):
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)

    decorated_function._public = True
    return decorated_function


def requested_statuses(statuses):
    if not statuses:
        return ALLOWED_STATUSES
    try:
        return {SubmissionStatusEnum[status] for status in statuses}
    except KeyError:
        allowed = ", ".join(status.name for status in SubmissionStatusEnum)
        abort(400, f"Unknown status. Allowed: {allowed}")


def serialize_submission(submission):
    summary = {
        "id": submission.id,
        "ref_name": submission.ref_name,
        "status": submission.current_status.value,
        "status_code": submission.current_status.name,
    }
    if submission.current_status not in ALLOWED_STATUSES:
        return summary
    return summary | {
        "local_project_name": submission.local_project_name,
        "local_custodians": submission.local_custodian_entries(),
        "access": [
            {
                "role": access.role,
                "first_name": access.user.first_name,
                "last_name": access.user.last_name,
                "email": access.user.email,
            }
            for access in submission.submission_accesses
        ],
        "attachments": [
            {
                "id": attachment.id,
                "note": attachment.note,
                "folder_name": attachment.folder_name,
                "file_names": attachment.file_names.split(),
            }
            for attachment in submission.attachments
        ],
    }


@dss_api.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok"})


healthz._public = True


@dss_api.route("/submissions", methods=["GET"])
@require_api_key
def list_submissions():
    """List submissions, at most API_PAGE_SIZE per call.

    status: repeatable, defaults to ALLOWED_STATUSES.
    after: id cursor, pass the last id received to get the next page.

    GET /submissions?status=data_approval&status=completed&after=10
    """
    if set(request.args) - {"status", "after"}:
        abort(400, "Unknown parameter. Allowed: status, after")
    statuses = requested_statuses(request.args.getlist("status"))
    after = request.args.get("after", 0, type=int)
    submissions = (
        Submission.query.filter(
            Submission.current_status.in_(statuses), Submission.id > after
        )
        .order_by(Submission.id)
        .limit(app.config["API_PAGE_SIZE"])
        .all()
    )
    submission_list = [serialize_submission(s) for s in submissions]
    return jsonify({"data": submission_list, "count": len(submission_list)})


@dss_api.route("/submissions/<int:submission_id>/datasets", methods=["GET"])
@require_api_key
def get_submission_datasets(submission_id):
    """Datasets of one submission, 409 unless its status is in ALLOWED_STATUSES."""
    submission = db.get_or_404(Submission, submission_id)
    if submission.current_status not in ALLOWED_STATUSES:
        abort(409, f"Submission is at {submission.current_status.value} status")
    dataset_list = [dataset.to_dict() for dataset in submission.datasets]
    return jsonify(
        {
            "data": dataset_list,
            "count": len(dataset_list),
            "submission": serialize_submission(submission),
        }
    )
