import os

from elixir_dss import app, db
from elixir_dss.importer.submission_exporter import SubmissionExporter
from elixir_dss.models.submission import Submission, SubmissionStatusEnum


def schedule_submission_export(
    path_to_json_directory=None,
    export_all_submissions=False,
    submissions_to_export=None,
):
    app.logger.info("export schedule started")
    submissions = get_submissions_to_export(
        export_all_submissions, submissions_to_export
    )
    app.logger.info("schedule_submission_export")
    if path_to_json_directory is None:
        path_to_json_directory = os.path.join(
            app.config.get("SUBMISSION_EXPORT_FOLDER")
        )
    if submissions.count() > 0:
        for submission in submissions:
            exporter = SubmissionExporter([submission])
            export_directory = os.path.join(path_to_json_directory, submission.ref_name)
            app.logger.info(export_directory)
            if not os.path.exists(export_directory):
                os.makedirs(export_directory)
            with open(
                os.path.join(export_directory, submission.ref_name + ".json"), "w"
            ) as jsonfile:
                exporter.export_to_file(jsonfile)

            submission.exported = True
            db.session.add(submission)
            db.session.commit()


def get_submissions_to_export(
    export_all_submissions: bool = False, submissions_to_export: list[str] = None
):
    if export_all_submissions:
        submissions = Submission.query.filter_by(
            current_status=SubmissionStatusEnum.completed
        )
    else:
        submissions = Submission.query.filter_by(
            current_status=SubmissionStatusEnum.completed, exported=False
        )

    if submissions_to_export:
        submissions_indexes = []
        for idx, submission in enumerate(submissions):
            if submission.ref_name in submissions_to_export:
                submissions_indexes.append(idx)
            else:
                app.logger.warnings(
                    f"Submission {submission.ref_name} not found. Skipping..."
                )
        submissions = submissions[submissions_indexes]  # check if this works
    return submissions
