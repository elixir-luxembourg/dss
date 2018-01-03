# coding=utf-8
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, login_required, logout_user
import elixir_dcp.forms as forms
from elixir_dcp import login_manager
from elixir_dcp.models.security import User
from elixir_dcp.models.submission import  create_sub, delete_sub, Submission, SubmissionAccess, SubmissionAttachment, \
    SubmissionContact, SubmissionStatusEnum, SubmissionStudyDish, SubmissionUseConditionGroup
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


@app_authorization(allowed_roles=['admin'])
@app.route('/api/submission/<int:sub_id>', methods=['POST', 'DELETE'])
def api_submission(sub_id):
    if request.method == 'DELETE':
        try:
            delete_submission(sub_id)
            app.logger.info('INFO: Deleted submission SUB-ID: %s', sub_id)
            flash("Submission deleted!", "info")
        except exceptions.RecordLifecycleException as e:
            app.logger.error('ERROR %s', e)
            flash("Unable to delete submission", 'error')
        redirect(url_for('list_submissions'))
    elif request.method == 'POST':
        app.logger.info('SOme custom command targeted for a submission')
        redirect(url_for('list_submissions'))



@app.route('/submissions', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_submissions():
    """
    List all submissions
    """
    submissions = Submission.query.all()
    return render_template('submission/submissions.html',
                           submissions=submissions, submsn_create_form=forms.SubmissionForm())


@app.route('/my_submissions', methods=['GET'])
@app_authorization(allowed_roles=['provider','admin'])
def list_my_submissions():
    """
    List the submissions that have been shared with the LOGGED IN  user
    """

    my_submissions = db.session.query(User).filter(User.id ==
                                                   current_user.elixir_reg_id).join(SubmissionAccess,
                                                                                    SubmissionAccess.user_id ==
                                                                                    User.id).join(Submission,
                                                                                                  Submission.id == SubmissionAccess.submission_id).filter(Submission.current_status == SubmissionStatusEnum.in_progress_metadata)

    return render_template('submission/my_submissions.html',
                           my_submissions=my_submissions)


@app.route('/submission/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'provider'])
def get_submission(sub_id):
    #
    # We need to check here whether the user in the provider role has access to this submission
    #
    submission_rec = Submission.query.get_or_404(sub_id)
    app.logger.info('INFO: Get submission SUB-ID: %s', sub_id)
    return render_template('submission/viewer.html', submission=submission_rec)


@app.route('/submission/create', methods=['POST'])
@app_authorization(allowed_roles=['admin'])
def create_submission():
    creation_form = forms.SubmissionForm(request.form)
    submission_rec = create_sub(creation_form.title.data)
    flash('New submission {} created'.format(submission_rec.ref_name), 'info')
    return redirect(url_for('list_submissions'))


@app.route('/submission/edit/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin'])
def edit_submission(sub_id):
    app.logger.info('INFO: Edit submission SUB-ID: %s', sub_id)
    if request.method == 'GET':
        submission_rec = Submission.query.get_or_404(sub_id)
        app.logger.info('Sub REC: %s', submission_rec)
        sub_form = forms.SubmissionForm(obj=submission_rec)
        return render_template('submission/submission.html', submsn_form=sub_form, submission=submission_rec)
    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        submission_rec = Submission.query.filter_by(id=form.id.data).first()
        if form.validate_on_submit():
            form.populate_obj(submission_rec)
            db.session.add(submission_rec)
            db.session.commit()
            flash('Submission updated successfully', 'info')
            return redirect(url_for('list_submissions'))
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/submission.html', submsn_form=form, submission=submission_rec)


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Contacts."""
"""----------------------------------------------------"""


@app.route('/submission_contacts/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_submission_contacts(sub_id):
    contacts = SubmissionContact.query.filter_by(submission_id=sub_id)
    return render_template('submission/_contact_columns.html', contacts=contacts)


@app.route('/submission_contact/<int:contact_id>', methods=['GET', 'POST'])
@app.route('/submission_contact', methods=['POST'])
@app_authorization(allowed_roles=['admin'])
def add_edit_submission_contact(contact_id=None):

    if contact_id is None:
        mode = 'create'
    else:
        mode = 'edit'
    if request.method == 'GET':
        contact_rec = SubmissionContact.query.get_or_404(contact_id)
        result_form = forms.ContactForm(obj=contact_rec)
        return render_template('submission/_contact_form.html', contact_form=result_form)
    elif request.method == 'POST':
        posted_form = forms.ContactForm(request.form)
        if posted_form.validate_on_submit():
            if mode == 'edit':
                contact_rec = SubmissionContact.query.get_or_404(contact_id)
                posted_form.populate_obj(contact_rec)
            else:
                contact_rec = SubmissionContact()
                posted_form.populate_obj(contact_rec)
                contact_rec.id = None
            db.session.add(contact_rec)
            db.session.commit()
            msg = "updated" if mode == 'create' else "added"
            flash("Submission Contact {}.".format(msg), "info")

            sid = posted_form.submission_id.data

            return render_template('submission/_contact_form.html', contact_form=forms.ContactForm(formdata=None,
                                                                                                   obj=None,
                                                                                                   sub_id=sid)), 200
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_contact_form.html', contact_form=posted_form), 400


@app.route('/submission_contact/<int:contact_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin'])
def delete_submission_contact(contact_id):
    submission_contact = SubmissionContact.query.get_or_404(contact_id)
    db.session.delete(submission_contact)
    db.session.commit()
    flash("Submission Contact deleted", "info")
    return "", 204


"""-------------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Attachments."""
"""-------------------------------------------------------"""


@app.route('/submission_attachments/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'provider'])
def list_submission_attachments(sub_id):
    attachments = SubmissionAttachment.query.filter_by(submission_id=sub_id)
    return render_template('submission/_attachment_columns.html', attachments=attachments)


def is_allowed_type(filename):
    allowed_extensions = set(['txt', 'pdf', 'png'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/submission_attachment', methods=['POST'])
@app_authorization(allowed_roles=['admin', 'provider'])
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
        return render_template('submission/_attachment_form.html', attachment_form=form), 400
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
        sid = form.submission_id.data
        return render_template('submission/_attachment_form.html', attachment_form=forms.AttachmentForm(formdata=None,
                                                                                        obj=None,
                                                                                        sub_id=sid)), 200


@app.route('/submission_attachment/<int:attach_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin'])
def delete_submission_attachment(attach_id):
    submission_attachment = SubmissionAttachment.query.get_or_404(attach_id)
    shutil.rmtree(submission_attachment.server_path)
    db.session.delete(submission_attachment)
    db.session.commit()
    flash("Submission Attachment deleted", "info")
    return "", 204


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's DISHs."""
"""----------------------------------------------------"""


@app.route('/submission_dishes/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_submission_dishes(sub_id):
    dishes = SubmissionStudyDish.query.filter_by(submission_id=sub_id)
    return render_template('submission/_dish_columns.html', dishes=dishes)


@app.route('/submission_dish/<int:dish_id>', methods=['GET', 'POST'])
@app.route('/submission_dish', methods=['POST'])
@app_authorization(allowed_roles=['admin'])
def add_edit_submission_dish(dish_id=None):
    if dish_id is None:
        mode = 'create'
    else:
        mode = 'edit'
    if request.method == 'GET':
        dish_rec = SubmissionStudyDish.query.get_or_404(dish_id)
        result_form = forms.StudyDishForm(obj=dish_rec)
        return render_template('submission/_dish_form.html', dish_form=result_form)
    elif request.method == 'POST':
        posted_form = forms.StudyDishForm(request.form)
        if posted_form.validate_on_submit():
            if mode == 'edit':
                dish_rec = SubmissionStudyDish.query.get_or_404(dish_id)
                posted_form.populate_obj(dish_rec)
            else:
                dish_rec = SubmissionStudyDish()
                posted_form.populate_obj(dish_rec)
                dish_rec.id = None
            db.session.add(dish_rec)
            db.session.commit()
            msg = "created" if mode == 'create' else "updated"
            flash("Study {}.".format(msg), "info")

            sid = posted_form.submission_id.data

            return render_template('submission/_dish_form.html', dish_form=forms.StudyDishForm(formdata=None,
                                                                                                   obj=None,
                                                                                                   sub_id=sid)), 200
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_dish_form.html', dish_form=posted_form), 400


@app.route('/submission_dish/<int:dish_id>', methods=['DELETE'])
def delete_submission_dish(dish_id):
    dish = SubmissionStudyDish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    flash("Study deleted", "info")
    return "", 204


"""--------------------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's DUC/Consent Groups."""
"""--------------------------------------------------------------"""


@app.route('/submission_ducs/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_submission_ducs(sub_id):
    ducs = SubmissionUseConditionGroup.query.filter_by(submission_id=sub_id)
    return render_template('submission/_duc_columns.html', ducs=ducs)


@app.route('/submission_duc/<int:duc_id>', methods=['GET', 'POST'])
@app.route('/submission_duc', methods=['POST'])
@app_authorization(allowed_roles=['admin'])
def add_edit_submission_duc(duc_id=None):
    mode = "create" if duc_id is None else "edit"
    if request.method == 'GET':
        duc_rec = SubmissionUseConditionGroup.query.get_or_404(duc_id)
        result_form = forms.UseConditionGroupForm(obj=duc_rec)
        return render_template('submission/_duc_form.html', duc_form=result_form)
    elif request.method == 'POST':
        posted_form = forms.UseConditionGroupForm(request.form)
        if posted_form.validate_on_submit():
            if mode == 'edit':
                duc_rec = SubmissionUseConditionGroup.query.get_or_404(duc_id)
                posted_form.populate_obj(duc_rec)
            else:
                duc_rec = SubmissionUseConditionGroup()
                posted_form.populate_obj(duc_rec)
                duc_rec.id = None
            db.session.add(duc_rec)
            db.session.commit()
            flash("Data Use Condition Group {}.".format("created" if mode == 'create' else "updated"), "info")

            sid = posted_form.submission_id.data

            return render_template('submission/_duc_form.html', duc_form=forms.UseConditionGroupForm(formdata=None,
                                                                                                     obj=None,
                                                                                                     sub_id=sid)), 200
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_duc_form.html', duc_form=posted_form), 400


@app.route('/submission_duc/<int:duc_id>', methods=['DELETE'])
def delete_submission_duc(duc_id):
    duc = SubmissionUseConditionGroup.query.get_or_404(duc_id)
    db.session.delete(duc)
    db.session.commit()
    flash("Use Condition Group deleted", "info")
    return "", 204
