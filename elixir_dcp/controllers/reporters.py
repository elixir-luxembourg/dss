from docxtpl import DocxTemplate
from flask import abort, flash, redirect, render_template, request, url_for, g, get_flashed_messages, make_response

from elixir_dcp.models.submission import Submission

from elixir_dcp import app
from elixir_dcp.controllers import app_authorization
import os
import io
from flask import send_file
from elixir_dcp.importer.submission_exporter import SubmissionExporter
import pdfkit

@app.route('/submission/generate_submission_pdf/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def generate_submission_pdf(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    rendered = render_template('submission/generate_submission_pdf.html',
                               submission_rec=submission_rec,
                               png_elx_lu=app.static_folder + '/public/images/' + 'ELIXIR_LU_WB.png',
                               png_lcsb=app.static_folder + '/public/images/' + 'LCSB-logo.png',
                               png_uni=app.static_folder + '/public/images/' + 'Uni-LU.png')
    options = {
        'page-size': 'A4',
        'footer-center': '[page] of [topage]',
        'footer-font-size': '9',
        'dpi': 400
    }

    pdf = pdfkit.from_string(rendered, False,
                             css=app.static_folder + '/vendor/node_modules/bootstrap/dist/css/bootstrap.css',
                             options=options)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'
    return response


@app.route('/submission/generate_submission_docx/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def generate_submission_docx(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    template_path = os.path.join(app.root_path, 'templates', 'submission', 'generate_submission_docx.docx')
    doc = DocxTemplate(template_path)
    exporter = SubmissionExporter()
    context = exporter.export_submission(sub)
    try:
        doc.render(context, app.jinja_env)
    except:
        raise ValueError('Rendering of the DOCX report failed. Are you sure all required values are filled in?')
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return send_file(doc_io, mimetype=".docx", as_attachment=True, attachment_filename=f'Submission_{sub.ref_name}.docx')

@app.template_filter('pluralize')
def pluralize(arg, singular='', plural='s'):
    if len(arg) == 1:
        return singular
    else:
        return plural


