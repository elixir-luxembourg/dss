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

            """
            submission_exportfile = open(os.path.join(export_directory, submission.ref_name + ".json"), "w")
            submission_exportfile.write(json.dumps([export_submission(submission)], indent=4))
            """
            # submission_attachments = SubmissionAttachment.query.filter_by(submission_id=submission.id).all()
            # for attachment in submission_attachments:
            #
            #     try:
            #         path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachment.folder_name)
            #         attachment_folder_name = os.path.join(export_directory, attachment.folder_name)
            #         if not os.path.exists(attachment_folder_name):
            #             os.makedirs(attachment_folder_name)
            #         attachment_file = os.path.join(path_on_server, attachment.file_names)
            #         os.popen('cp ' + attachment_file + ' ' + attachment_folder_name)
            #
            #     except OSError as err:
            #         err.extend(err.args[0])

            # shutil.make_archive(export_directory, 'zip', export_directory)
            # app.logger.info("Created zip file")

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
