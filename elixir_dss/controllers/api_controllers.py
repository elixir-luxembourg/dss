from functools import wraps
import os

from flask import Blueprint, request, jsonify

from elixir_dss.models.submission import Submission
from elixir_dss.models.submission import SubmissionStatusEnum


dss_api = Blueprint("dss_api", __name__)

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "secret-api-key")

ALLOWED_STATUSES = {
    "completed": SubmissionStatusEnum.completed,
}


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != SERVICE_API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)

    decorated_function._public = True
    return decorated_function


@dss_api.route("/healthz", methods=["GET"])
@require_api_key
def healthz():
    return jsonify({"status": "ok"})


@dss_api.route("/submissions", methods=["GET"])
@require_api_key
def list_submissions():
    submissions = Submission.query.filter(
        Submission.current_status.in_(ALLOWED_STATUSES.values())
    ).all()
    submission_list = []
    for submission in submissions:
        submission_list.append(
            {
                "id": submission.id,
                "ref_name": submission.ref_name,
                "status": submission.current_status.value,
            }
        )
    return jsonify({"data": submission_list, "count": len(submission_list)})


@dss_api.route("/submissions/<int:submission_id>/datasets", methods=["GET"])
@require_api_key
def get_submission_datasets(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    dataset_list = []
    for dataset in submission.datasets:
        dataset_list.append(dataset.to_dict())
    return jsonify(
        {
            "data": dataset_list,
            "count": len(dataset_list),
            "submission": {
                "id": submission.id,
                "ref_name": submission.ref_name,
                "status": submission.current_status.value,
            },
        }
    )
