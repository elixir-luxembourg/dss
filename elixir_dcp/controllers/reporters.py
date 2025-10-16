import io
import os

from docxtpl import DocxTemplate
from flask import (
    make_response,
    render_template,
    request,
    send_file,
)
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from elixir_dcp import app
from elixir_dcp.controllers import app_authorization
from elixir_dcp.importer.submission_exporter import SubmissionExporter
from elixir_dcp.models.submission import Submission


@app.route("/submission/generate_submission_pdf/<int:sub_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["admin", "data_provider"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def generate_submission_pdf(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    rendered = render_template(
        "submission/generate_submission_pdf.html",
        submission_rec=submission_rec,
        png_elx_lu=app.static_folder + "/public/images/" + "ELIXIR_LU_WB.png",
        png_lcsb=app.static_folder + "/public/images/" + "LCSB-logo.png",
        png_uni=app.static_folder + "/public/images/" + "Uni-LU.png",
    )

    font_config = FontConfiguration()
    bootstrap_css = CSS(
        filename=app.static_folder
        + "/vendor/node_modules/bootstrap/dist/css/bootstrap.css"
    )
    page_css = CSS(
        string="""
        @page {
            size: A4;
            margin: 1cm;
            @bottom-center {
                content: counter(page) " of " counter(pages);
                font-size: 9pt;
            }
        }
    """
    )
    html = HTML(string=rendered, base_url=request.url_root)
    pdf_bytes = html.write_pdf(
        stylesheets=[bootstrap_css, page_css], font_config=font_config
    )

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"inline; filename=submission_{submission_rec.ref_name}.pdf"
    )
    return response


@app.route("/submission/generate_submission_docx/<int:sub_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["admin", "data_provider"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def generate_submission_docx(sub_id):
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
