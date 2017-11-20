# coding=utf-8
import calendar

from flask import flash, redirect, render_template, request, url_for

import elixir_dcp.forms as forms
import elixir_dcp.models as models
import sys
import os
import uuid
from elixir_dcp import app, db
from werkzeug.utils import secure_filename

__author__ = 'Valentin Grouès, Pinar Alper'


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


"""------------------------------------"""
"""Endpoints for managing  Submissions."""
"""------------------------------------"""


@app.route('/submissions', methods=['GET'])
def list_submissions():
    """
    List all submissions
    """
    submissions = models.Submission.query.all()
    return render_template('submission/listing.html',
                           submissions=submissions, title="Data Submissions to ELIXIR DCP")


@app.route('/submissions/edit/<int:sub_id>', methods=['GET', 'POST'])
def add_edit_submission(sub_id):
    """
    I used the id -> 0 to differentiate between CREATE and EDIT mode
    """
    # TODO: Find a more elegant way to determine page mode both for templates and controllers

    if request.method == 'GET':

        if sub_id == 0:
            #  an empty form
            empty_sub_form = forms.SubmissionForm()
            return render_template('submission/editor.html', submsn_form=empty_sub_form)

        else:
            #  a form filled  with info from the db
            submission_rec = models.Submission.query.get_or_404(sub_id)
            sub_form = forms.SubmissionForm(obj=submission_rec)

        return render_template('submission/editor.html', submsn_form=sub_form)

    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        if form.validate_on_submit():
            if int(form.id.data) == 0:
                submission_rec = models.Submission()

                # We do not call form.populate_obj in this case because it sets the
                # id to 0 and this gets persisted. If id is not set SQLAlchemy auto assigns.
                # TODO: its ugly, fix it

                submission_rec.created = form.created.data
                submission_rec.name = form.name.data
                submission_rec.description = form.description.data

                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission created successfully', 'info')
            else:
                submission_rec = models.Submission.query.filter_by(id=form.id.data).first()
                form.populate_obj(submission_rec)
                db.session.add(submission_rec)
                db.session.commit()
                flash('Submission updated successfully', 'info')

            return redirect(url_for('list_submissions'))
        else:
            print(form.errors, file=sys.stderr)
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/editor.html', form=form)


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Contacts."""
"""----------------------------------------------------"""


@app.route('/submission_contacts/<int:sub_id>', methods=['GET'])
def list_submission_contacts(sub_id):
    if sub_id == 0:
        contacts = None
    else:
        contacts = models.SubmissionContact.query.filter_by(submission_id=sub_id)
    contct_form = forms.ContactForm()
    contct_form.submission_id.data = sub_id
    return render_template('submission/contactsInline.html', contacts=contacts, contct_form=contct_form)


@app.route('/submission_contact', methods=['POST'])
def add_submission_contact():
    form = forms.ContactForm(request.form)
    if form.validate_on_submit():
        contact = models.SubmissionContact()
        contact.name = form.name.data
        contact.is_primary = form.is_primary.data
        contact.submission_id = form.submission_id.data
        db.session.add(contact)
        db.session.commit()
        flash("Submission Contact added", "info")
        return "", 204
    else:
        flash("Please check the validity of your input in highlighted places", "error")
        return "", 400


@app.route('/submission_contact/<int:sub_contact_id>', methods=['DELETE'])
def delete_submission_contact(sub_contact_id):
    submission_contact = models.SubmissionContact.query.get_or_404(sub_contact_id)
    db.session.delete(submission_contact)
    db.session.commit()
    flash("Submission Contact deleted", "info")
    return "", 204


"""-------------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Attachments."""
"""-------------------------------------------------------"""


@app.route('/submission_attachments/<int:sub_id>', methods=['GET'])
def list_submission_attachments(sub_id):
    if sub_id == 0:
        attachments = None
    else:
        attachments = models.SubmissionAttachment.query.filter_by(submission_id=sub_id)
    attachment_form = forms.AttachmentForm()
    attachment_form.submission_id.data = sub_id
    return render_template('submission/attachmentsInline.html', attachments=attachments,
                           attachment_form=attachment_form)

def is_allowed_type(filename):
    allowed_extensions = set(['txt', 'pdf', 'png'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/submission_attachment', methods=['POST'])
def add_submission_attachment():
    form = forms.AttachmentForm(request.form)
    if form.validate_on_submit():
        if 'attachments[]' not in request.files:
            flash('No file part')
            return "", 400
        requestfiles = request.files.getlist('attachments[]')
        for file in requestfiles:
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return "", 400
            if not is_allowed_type(file.filename):
                flash("File is not of allowed type", "error")
                return "", 400
    else:
        flash("Please check the validity of your input in highlighted places", "error")
        return "", 400
    attachments_folder = str(uuid.uuid4())
    path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachments_folder)
    os.makedirs(path_on_server)
    attachment = models.SubmissionAttachment()
    attachment.note = form.note.data
    attachment.submission_id = form.submission_id.data
    attachment.server_path = path_on_server
    attachment.file_names = ''
    for file in requestfiles:
        secured_file_name = secure_filename(file.filename)
        attachment.file_names += secured_file_name + ' '
        file.save(os.path.join(path_on_server, secured_file_name))
    db.session.add(attachment)
    db.session.commit()
    flash("Submission Attachment(s) added", "info")
    return "", 204


@app.route('/submission_attachment/<int:sub_attach_id>', methods=['DELETE'])
def delete_submission_attachment(sub_attach_id):
    submission_attachment = models.SubmissionAttachment.query.get_or_404(sub_attach_id)
    db.session.delete(submission_attachment)
    db.session.commit()
    flash("Submission Attachment deleted", "info")
    return "", 204
