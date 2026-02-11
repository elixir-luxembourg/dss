import io
import os

from flask import (
    send_file,
)

from elixir_dss import app
from elixir_dss.controllers import protect
from elixir_dss.importer.submission_exporter import SubmissionExporter
from elixir_dss.models.submission import Submission


@app.route("/submission/generate_submission_docx/<int:sub_id>", methods=["GET"])
@protect(roles=["user", "data_steward"])
def generate_submission_docx(sub_id):
    from docxtpl import DocxTemplate

    sub = Submission.query.get_or_404(sub_id)
    template_path = os.path.join(
        app.root_path, "templates", "submission", "generate_submission_docx.docx"
    )
    doc = DocxTemplate(template_path)
    exporter = SubmissionExporter()
    context = exporter.export_submission(sub)
    try:
        doc.render(context, app.jinja_env)
    except Exception:
        raise ValueError(
            "Rendering of the DOCX report failed. Are you sure all required values are filled in?"
        )
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return send_file(
        doc_io,
        mimetype=".docx",
        as_attachment=True,
        download_name=f"Submission_{sub.ref_name}.docx",
    )


@app.template_filter("pluralize")
def pluralize(arg, singular="", plural="s"):
    if len(arg) == 1:
        return singular
    else:
        return plural
