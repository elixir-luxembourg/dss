# coding=utf-8
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user
import elixir_dcp.forms as forms
from elixir_dcp import login_manager
from elixir_dcp.models.security import User
from elixir_dcp.models.submission import Submission, SubmissionAttachment, SubmissionContact, SubmissionDish
import elixir_dcp.exceptions as exceptions
from sqlalchemy.exc import OperationalError
import os
import uuid
import shutil
from datetime import datetime
from elixir_dcp import app, db
from werkzeug.utils import secure_filename
from . import app_authorization

__author__ = 'Valentin Grouès, Pinar Alper'

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have logged out of ELIXIR DCP.', 'success')
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        elixir_reg_id = form.elixir_reg_id.data
        password = form.password.data
        try:
            authentication = app.config['authentication']
            if authentication.authenticate_user(elixir_reg_id, password):
                user = User.query.filter_by(elixir_reg_id=elixir_reg_id, active_user=True).one_or_none()
                if user is None:
                    form.username.errors.append('User not found!')
                else:
                    login_user(user, remember=False)
                    flash('Logged in successfully.', 'success')
                    return form.redirect()
            else:
                message = 'Wrong username / password combination!'
                form.elixir_reg_id.errors.append(message)
                form.password.errors.append(message)
        except exceptions.AuthenticationException as e:
            flash(e, 'error')

    return render_template('security/login_user.html', login_user_form=form)


@login_manager.user_loader
def load_user(user_id):
    app.logger.info('INFO: Load User with ID: %s', user_id)
    try:
        return User.query.get(int(user_id))
    except OperationalError as e:
        app.logger.error('Error: %s', e)
        return None


"""------------------------------------"""
"""Endpoints for managing  Submissions."""
"""------------------------------------"""


@app.route('/submission', methods=['GET'])
@app_authorization(allowed_roles=['steward', 'provider'])
def list_submissions():
    """
    List all submissions
    """
    submissions = Submission.query.all()
    return render_template('submission/submissionListing.html',
                           submissions=submissions, submsn_create_form=forms.SubmissionForm())

@app.route('/submission/create', methods=['POST'])
@app_authorization(allowed_roles=['steward'])
def create_submission():
    creation_form = forms.SubmissionForm(request.form)
    submission_rec = Submission()
    submission_rec.name = creation_form.name.data
    submission_rec.description = creation_form.description.data
    submission_rec.created_on = datetime.today()
    db.session.add(submission_rec)
    db.session.commit()
    flash('New submission created. Further information can be supplied through the editor.', 'info')
    return redirect(url_for('edit_submission', sub_id=submission_rec.id))

@app.route('/submission/edit/<int:sub_id>', methods=['GET', 'POST'])
def edit_submission(sub_id):

    app.logger.info('INFO: Edit submission SUB-ID: %s', sub_id)
    if request.method == 'GET':

        submission_rec = Submission.query.get_or_404(sub_id)
        sub_form = forms.SubmissionForm(obj=submission_rec)

        return render_template('submission/submissionEditor.html', submsn_form=sub_form, page_mode='edit')

    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        if form.validate_on_submit():
            submission_rec = Submission.query.filter_by(id=form.id.data).first()
            form.populate_obj(submission_rec)
            db.session.add(submission_rec)
            db.session.commit()
            flash('Submission updated successfully', 'info')

            return redirect(url_for('submission'))
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/submissionEditor.html', submsn_form=form, page_mode='edit')


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Contacts."""
"""----------------------------------------------------"""


@app.route('/submission_contacts/<int:sub_id>', methods=['GET'])
def list_submission_contacts(sub_id):
    if sub_id == 0:
        contacts = None
    else:
        contacts = SubmissionContact.query.filter_by(submission_id=sub_id)
    contct_form = forms.ContactForm()
    contct_form.submission_id.data = sub_id
    return render_template('submission/contactsInline.html', contacts=contacts, contct_form=contct_form)


@app.route('/submission_contact', methods=['POST'])
def add_submission_contact():
    form = forms.ContactForm(request.form)
    if form.validate_on_submit():
        contact = SubmissionContact()
        contact.name = form.name.data
        contact.is_primary = form.is_primary.data
        contact.category_id = form.category_id.data
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
    submission_contact = SubmissionContact.query.get_or_404(sub_contact_id)
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
        attachments = SubmissionAttachment.query.filter_by(submission_id=sub_id)
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
    file_validation = True
    form_validation = form.validate_on_submit()
    request_files = request.files.getlist(form.file_attachments.name)
    for file in request_files:
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            file_validation = False
            form.file_attachments.errors.append('No file(s) selected.')
        if not is_allowed_type(file.filename):
            file_validation = False
            form.file_attachments.errors.append('File {} is not of allowed type.'.format(file.filename))
    if (not file_validation) or (not form_validation ):
        flash("Please check the validity of your input in highlighted fields.", "error")
        attachments = SubmissionAttachment.query.filter_by(submission_id=form.submission_id.data)
        return render_template('submission/attachmentsInline.html', attachments=attachments,
                               attachment_form=form), 400
    else:
        attachments_folder = str(uuid.uuid4())
        path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachments_folder)
        os.makedirs(path_on_server)
        attachment = SubmissionAttachment()
        attachment.note = form.note.data
        attachment.submission_id = form.submission_id.data
        attachment.server_path = path_on_server
        attachment.file_names = ''
        for file in request_files:
            secured_file_name = secure_filename(file.filename)
            attachment.file_names += secured_file_name + ' '
            file.save(os.path.join(path_on_server, secured_file_name))
        db.session.add(attachment)
        db.session.commit()
        flash("Submission Attachment(s) added", "info")
        return "", 204


@app.route('/submission_attachment/<int:sub_attach_id>', methods=['DELETE'])
def delete_submission_attachment(sub_attach_id):
    submission_attachment = SubmissionAttachment.query.get_or_404(sub_attach_id)
    shutil.rmtree(submission_attachment.server_path)
    db.session.delete(submission_attachment)
    db.session.commit()
    flash("Submission Attachment deleted", "info")
    return "", 204



