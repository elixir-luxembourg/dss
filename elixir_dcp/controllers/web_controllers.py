# coding=utf-8
from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for, g, get_flashed_messages, make_response
from flask_login import current_user, login_user, login_required, logout_user

import elixir_dcp.forms as forms
from elixir_dcp import login_manager

from elixir_dcp.models.security import User
from elixir_dcp.models.services import create_sub, delete_sub, steer_sub, revert_sub, \
    get_in_progress_submissions_shared_with_user, register_new_user, assign_role_to_user, update_submission_basic_info, \
    update_user_info, send_email_asynch, send_new_message_notification
from elixir_dcp.models.submission import Submission, SubmissionDataDeclaration, SubmissionUploadInfo, SubmissionStudy, \
    EmailNotification, SubmissionAttachment, SubmissionMessage
import elixir_dcp.exceptions as exceptions
from sqlalchemy.exc import OperationalError
import os
import uuid
import shutil
from werkzeug.utils import secure_filename
import json
from elixir_dcp import app, db, oidc

from . import app_authorization
from .utils import get_names_from_oidc


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/users', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_users():
    users = User.query.all()
    return render_template('security/users.html',
                           users=users)


@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin'])
def edit_user(user_id):
    if request.method == 'GET':
        user_rec = User.query.get_or_404(int(user_id))
        usr_form = forms.UserForm(obj=user_rec)
        usr_form.assigned_role_ids.data = user_rec.assigned_role_ids()
        return render_template('security/user.html', user_form=usr_form)
    elif request.method == 'POST':
        form = forms.UserForm(request.form)
        user_rec = User.query.get_or_404(form.id.data)
        if form.validate_on_submit():
            update_user_info(user_rec, **form.data)

            flash('User updated', 'success')
            return redirect(url_for('list_users'))
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('security/user.html', user_form=form)


@app.route("/logout")
@login_required
def logout():
    # Flask Login's Logout
    logout_user()

    # OIDC's logout, does not work!
    # TODO: Find a way to sign out of AAI
    oidc.logout()

    flash('You have logged out of Submission System.', 'success')
    return render_template('home.html')


@app.after_request
def disable_caching(response):
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route('/oidc_login', methods=['GET', 'POST'])
@oidc.require_login
def oidc_login():
    app.logger.info(g.oidc_id_token)
    app.logger.info(
        "oidc_login  token info:" + oidc.user_getinfo(
            ['openid', 'email', 'profile']).__str__())

    existing_user_record = User.query.filter_by(elixir_sub_id=oidc.user_getfield("sub")).one_or_none()

    if request.method == 'GET':
        if existing_user_record is None:
            name = oidc.user_getfield("name")
            if name is not None:
                partially_filled_form = forms.SignupForm(elixir_sub_id=oidc.user_getfield("sub"),
                                                         first_name=get_names_from_oidc(name)[0],
                                                         last_name=get_names_from_oidc(name)[1],
                                                         email=oidc.user_getfield("email"))
                return render_template('security/signup.html', signup_form=partially_filled_form)
            else:
                return render_template('error.html', message="Error 500 - {}".format(
                    "Insufficient information on the AAI User, cannot continue with signup.")), 500
        else:
            if not existing_user_record.is_active:
                render_template('error.html', message="Error 500 - {}".format(
                    "You are no longer an active user of this application.")), 500
            else:
                if not current_user.is_authenticated:
                    login_user(existing_user_record, remember=True)
                    nextt = request.args.get('next')

                    app.logger.info(get_flashed_messages())
                    if not forms.is_safe_url(nextt):
                        return abort(404)
                    else:
                        return redirect(nextt or landing_page_for_user(existing_user_record))
                else:
                    existing_user_info_form = forms.MyProfileForm(obj=current_user)
                    return render_template('security/signup.html', signup_form=existing_user_info_form)
    elif request.method == 'POST':
        if existing_user_record is None:
            posted_form = forms.SignupForm(request.form)
            if posted_form.validate_on_submit():
                new_user_record = User()
                posted_form.populate_obj(new_user_record)
                registered_user = register_new_user(new_user_record)
                assign_role_to_user(registered_user, 'data_provider')
                login_user(registered_user, remember=True)
                flash('You are now signed up to the Submission System.', 'success')
                return redirect(landing_page_for_user(current_user))
            else:
                flash("Please check the validity of your input in highlighted places.", "error")
                return render_template('security/signup.html', signup_form=posted_form)
        elif current_user.is_authenticated:
            posted_form = forms.MyProfileForm(request.form)
            if posted_form.validate_on_submit():
                update_user_info(current_user, **posted_form.data)
                flash('Your profile is updated.', 'success')
                return redirect(landing_page_for_user(current_user))
            else:
                flash("Please check the validity of your input in highlighted places.", "error")
                return render_template('security/signup.html', signup_form=posted_form)


def landing_page_for_user(usr):
    if usr.is_admin():
        return url_for('list_submissions')
    else:
        return url_for('list_my_submissions')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.username.data
        password = form.password.data

        expected_password = app.config.get('AUTHENTICATION_DICT').get(email)

        if expected_password is not None and expected_password == password:
            app.logger.debug('config authentication passed')
            user = User.query.filter_by(email=email, active_user=True).one_or_none()
            if user is None:
                form.username.errors.append('User not found')
            else:
                login_user(user, remember=form.remember.data)
                flash('User logged in successfully.', 'success')
                return form.redirect()
        else:
            message = 'Wrong username / password combination.'
            form.username.errors.append(message)
            form.password.errors.append(message)

    return render_template('security/login_user.html', login_user_form=form)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except OperationalError as e:
        app.logger.error('Error: %s', e)
        return None


"""------------------------------------"""
"""Endpoints for managing  Submissions."""
"""------------------------------------"""


@app_authorization(allowed_roles=['admin'])
@app.route('/submission/<int:sub_id>', methods=['DELETE'])
def delete_submission(sub_id):
    try:
        delete_sub(sub_id)
        app.logger.info('INFO: Deleted submission SUB-ID: %s', sub_id)
        flash("Submission deleted!", "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error('ERROR %s', e)
        flash("Unable to delete submission", 'error')
        return "", 400


@app.route('/steer/submission/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def steer_submission(sub_id):
    try:
        sub_with_new_state = steer_sub(sub_id)
        flash("Submission moved to next state {}!".format(sub_with_new_state.current_status.value), "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error('ERROR %s', e)
        flash("Unable to transition submission to the next state", 'error')
        return "", 400


@app.route('/revert/submission/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def revert_submission(sub_id):
    try:
        sub_with_new_state = revert_sub(sub_id)
        flash("Submission moved to previous state {}!".format(sub_with_new_state.current_status.value), "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error('ERROR %s', e)
        flash("Unable to revert submission to the previous state", 'error')
        return "", 400


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
@app_authorization(allowed_roles=['data_provider'])
def list_my_submissions():
    """
    List the submissions that have been shared with the LOGGED IN  user
    """

    my_submissions = get_in_progress_submissions_shared_with_user(current_user.id)

    return render_template('submission/my_submissions.html',
                           my_submissions=my_submissions)


@app.route('/submission/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def get_submission(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    app.logger.info('INFO: Get submission SUB-ID: %s', sub_id)
    return render_template('submission/viewer.html', submission=submission_rec)


@app.route('/submission/create', methods=['POST'])
@app_authorization(allowed_roles=['admin'])
def create_submission():
    creation_form = forms.SubmissionForm(request.form)
    submission_rec = create_sub(creation_form.title.data, creation_form.institution_accession.data)
    flash('New submission {} created'.format(submission_rec.ref_name), 'success')
    return redirect(url_for('list_submissions'))


@app.route('/submission/view/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def view_submission(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template('submission/submission.html', submission=submission_rec)


@app.route('/submission/edit/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def edit_submission(sub_id):
    app.logger.info('INFO: Edit submission SUB-ID: %s', sub_id)
    if request.method == 'GET':
        submission_rec = Submission.query.get_or_404(sub_id)
        app.logger.info('Sub REC: %s', submission_rec)
        sub_form = forms.SubmissionForm(obj=submission_rec)
        if submission_rec.local_custodians_json:
            sub_form.local_custodians.data = json.loads(submission_rec.local_custodians_json)
        sub_form.provider_user_ids.data = submission_rec.provider_user_ids()
        return render_template('submission/submission_form.html', submsn_form=sub_form)
    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        submission_rec = Submission.query.get_or_404(form.id.data)
        if form.validate_on_submit():
            form.populate_obj(submission_rec)
            update_submission_basic_info(submission_rec, title=form.title.data,
                                         submission_scope_code=form.submission_scope_code.data,
                                         local_custodians_json=json.dumps(form.local_custodians.data),
                                         local_project_name=form.local_project_name.data,
                                         institution_accession=form.institution_accession.data,
                                         provider_user_ids=form.provider_user_ids.data if request.form.get(
                                             'provider_user_ids') else None)

            flash('Submission updated', 'success')
            return redirect(url_for('view_submission', sub_id=submission_rec.id))
        else:
            return render_template('submission/submission_form.html', submsn_form=form), 400


"""-------------------------------------------------------"""
"""AJAX Endpoints for managing a submission's sttachments."""
"""-------------------------------------------------------"""

#
#
# @app.route('/submission_attachments/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'], record_authorization={'entity':'Submission', 'entity_id_key':'sub_id', 'entity_ac_attribute':'id'})
# def list_submission_attachments(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_attachment_columns.html', submission = submission_rec), 200


def is_allowed_type(filename):
    allowed_extensions = set(['txt', 'pdf', 'png'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/submission_attachment_add/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'], record_authorization={'entity':'Submission', 'entity_id_key':'sub_id', 'entity_ac_attribute':'id'})
def add_submission_attachment(sub_id):
    if request.method == 'GET':
        return render_template('submission/attachment_form.html', attachment_form=forms.AttachmentForm(formdata=None,
                                                                                                        obj=None,
                                                                                                        sub_id=sub_id)), 200
    elif request.method == 'POST':
        form = forms.AttachmentForm(request.form)
        file_validation = True
        form_validation = form.validate_on_submit()
        request_files = request.files.getlist(form.file_attachments.name)
        for file in request_files:
            # if user does not select file, browser may
            # submit an empty part without filename.
            # we therefore check for that.
            if file.filename == '':
                file_validation = False
                form.file_attachments.errors.append('No file(s) selected.')
            elif not is_allowed_type(file.filename):
                file_validation = False
                form.file_attachments.errors.append(
                    'File {} is not of allowed type. Only TXT, PDF and PNG files can be uploaded.'.format(file.filename))
        if (not file_validation) or (not form_validation) or (sub_id != int(form.submission_id.data)):
            return render_template('submission/attachment_form.html', attachment_form=form), 400
        else:
            attachments_folder = str(uuid.uuid4())
            path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachments_folder)

            if not os.path.exists(path_on_server):
                os.makedirs(path_on_server)
            attachment = SubmissionAttachment()
            attachment.note = form.note.data
            attachment.submission_id = form.submission_id.data
            attachment.folder_name = attachments_folder
            attachment.file_names = ''
            for file in request_files:
                secured_file_name = secure_filename(file.filename)
                attachment.file_names += secured_file_name + ' '
                file.save(os.path.join(path_on_server, secured_file_name))
            db.session.add(attachment)
            db.session.commit()
            flash("Attachment added", "success")
            return redirect(url_for('view_submission', sub_id=attachment.submission_id))

@app.route('/submission_attachment_delete/<int:attach_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'], record_authorization={'entity':'SubmissionAttachment', 'entity_id_key':'attach_id', 'entity_ac_attribute':'submission_id'})
def delete_submission_attachment(attach_id):
    submission_attachment = SubmissionAttachment.query.get_or_404(attach_id)
    path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], submission_attachment.folder_name)
    shutil.rmtree(path_on_server)
    db.session.delete(submission_attachment)
    db.session.commit()
    flash("Attachment deleted", "success")
    return redirect(url_for('view_submission', sub_id=submission_attachment.submission_id))


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's datadecs."""
"""----------------------------------------------------"""
#
#
# @app.route('/submission_datadecs/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'],
#                    record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
#                                          'entity_ac_attribute': 'id'})
# def list_submission_datadecs(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_datadec_columns.html', submission=submission_rec)


@app.route('/submission_datadec_add/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def add_submission_datadec(sub_id):
    if request.method == 'GET':
        return render_template('submission/datadec_form.html', datadec_form=forms.DatadecForm(formdata=None,
                                                                                               obj=None,
                                                                                               sub_id=sub_id)), 200
    elif request.method == 'POST':
        posted_form = forms.DatadecForm(request.form)
        if posted_form.validate_on_submit() and int(posted_form.submission_id.data) == sub_id:
            datadec_rec = SubmissionDataDeclaration()
            posted_form.populate_obj(datadec_rec)
            datadec_rec.id = None
            if posted_form.sci_datatypes.data:
                datadec_rec.sci_datatypes_json = json.dumps(posted_form.sci_datatypes.data)
            if posted_form.gdpr_datatypes.data:
                datadec_rec.gdpr_datatypes_json = json.dumps(posted_form.gdpr_datatypes.data)
            db.session.add(datadec_rec)
            db.session.commit()
            flash("Data declaration added", "success")
            return redirect(url_for('view_submission', sub_id=datadec_rec.submission_id))
        else:
            return render_template('submission/datadec_form.html', datadec_form=posted_form), 400


@app.route('/submission_datadec/<int:datadec_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionDataDeclaration', 'entity_id_key': 'datadec_id',
                                         'entity_ac_attribute': 'submission_id'})
def edit_submission_datadec(datadec_id):
    if request.method == 'GET':
        datadec_rec = SubmissionDataDeclaration.query.get_or_404(datadec_id)
        result_form = forms.DatadecForm(obj=datadec_rec)
        if datadec_rec.sci_datatypes_json:
                result_form.sci_datatypes.data = json.loads(datadec_rec.sci_datatypes_json)
        if datadec_rec.gdpr_datatypes_json:
            result_form.gdpr_datatypes.data = json.loads(datadec_rec.gdpr_datatypes_json)
        return render_template('submission/datadec_form.html', datadec_form=result_form), 200
    elif request.method == 'POST':
        posted_form = forms.DatadecForm(request.form)
        if posted_form.validate_on_submit():

            datadec_rec = SubmissionDataDeclaration.query.get_or_404(datadec_id)
            posted_form.populate_obj(datadec_rec)

            if posted_form.sci_datatypes.data:
                datadec_rec.sci_datatypes_json = json.dumps(posted_form.sci_datatypes.data)

            if posted_form.gdpr_datatypes.data:
                datadec_rec.gdpr_datatypes_json = json.dumps(posted_form.gdpr_datatypes.data)

            db.session.add(datadec_rec)
            db.session.commit()
            flash("Data declaration updated", "success")
            return redirect(url_for('view_submission', sub_id=datadec_rec.submission_id))
        else:
            return render_template('submission/datadec_form.html', datadec_form=posted_form), 400


@app.route('/submission_datadec_delete/<int:datadec_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionDataDeclaration', 'entity_id_key': 'datadec_id',
                                         'entity_ac_attribute': 'submission_id'})
def delete_submission_datadec(datadec_id):
    datadec = SubmissionDataDeclaration.query.get_or_404(datadec_id)
    db.session.delete(datadec)
    db.session.commit()
    flash("Data declaration deleted", "success")
    return redirect(url_for('view_submission', sub_id=datadec.submission_id))


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Studies."""
"""----------------------------------------------------"""

# @app.route('/submission_studies/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'],
#                    record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
#                                          'entity_ac_attribute': 'id'})
# def list_submission_studies(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_study_columns.html', submission=submission_rec), 200


@app.route('/submission_study_add/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def add_submission_study(sub_id):
    if request.method == 'GET':
        return render_template('submission/study_form.html', study_form=forms.StudyForm(formdata=None,
                                                                                         obj=None,
                                                                                         sub_id=sub_id)), 200
    elif request.method == 'POST':
        posted_form = forms.StudyForm(request.form)
        if posted_form.validate_on_submit() and (int(posted_form.submission_id.data) == sub_id):
            study_rec = SubmissionStudy()
            posted_form.populate_obj(study_rec)
            study_rec.id = None
            if posted_form.study_types.data:
                study_rec.study_types_json = json.dumps(posted_form.study_types.data)
            db.session.add(study_rec)
            db.session.commit()
            flash("Study added", "success")
            return redirect(url_for('view_submission', sub_id=study_rec.submission_id))
        else:
            return render_template('submission/study_form.html', study_form=posted_form), 400


@app.route('/submission_study/<int:study_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionStudy', 'entity_id_key': 'study_id',
                                         'entity_ac_attribute': 'submission_id'})
def edit_submission_study(study_id):
    if request.method == 'GET':
        study_rec = SubmissionStudy.query.get_or_404(study_id)
        result_form = forms.StudyForm(obj=study_rec)
        if study_rec.study_types_json:
            result_form.study_types.data = json.loads(study_rec.study_types_json)
        return render_template('submission/study_form.html', study_form=result_form), 200
    elif request.method == 'POST':
        posted_form = forms.StudyForm(request.form)
        if posted_form.validate_on_submit():
            study_rec = SubmissionStudy.query.get_or_404(study_id)
            posted_form.populate_obj(study_rec)
            if posted_form.study_types.data:
                study_rec.study_types_json = json.dumps(posted_form.study_types.data)
            db.session.add(study_rec)
            db.session.commit()
            flash("Study updated", "success")
            return redirect(url_for('view_submission', sub_id=study_rec.submission_id))
        else:
            return render_template('submission/study_form.html', study_form=posted_form), 400


@app.route('/submission_study_delete/<int:study_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionStudy', 'entity_id_key': 'study_id',
                                         'entity_ac_attribute': 'submission_id'})
def delete_submission_study(study_id):
    study = SubmissionStudy.query.get_or_404(study_id)
    db.session.delete(study)
    db.session.commit()
    flash("Study deleted", "success")
    return redirect(url_for('view_submission', sub_id=study.submission_id))


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Upload Info Records."""
"""----------------------------------------------------"""

#
#
# @app.route('/submission_uploadinfos/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'],
#                    record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
#                                          'entity_ac_attribute': 'id'})
# def list_submission_uploadinfos(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_uploadinfo_columns.html', submission=submission_rec)


@app.route('/submission_uploadinfo_add/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def add_submission_uploadinfo(sub_id):
    if request.method == 'GET':
        return render_template('submission/uploadinfo_form.html',
                               uploadinfo_form=forms.UploadInfoForm(formdata=None,
                                                                    obj=None,
                                                                    sub_id=sub_id)), 200
    elif request.method == 'POST':
        posted_form = forms.UploadInfoForm(request.form)
        if posted_form.validate_on_submit():
            uploadinfo_rec = SubmissionUploadInfo()
            posted_form.populate_obj(uploadinfo_rec)
            uploadinfo_rec.id = None
            db.session.add(uploadinfo_rec)
            db.session.commit()
            flash("Checksum added", "success")
            return redirect(url_for('view_submission', sub_id=uploadinfo_rec.submission_id))
        else:
            return render_template('submission/uploadinfo_form.html', uploadinfo_form=posted_form), 400


@app.route('/submission_uploadinfo/<int:uploadinfo_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionUploadInfo', 'entity_id_key': 'uploadinfo_id',
                                         'entity_ac_attribute': 'submission_id'})
def edit_submission_uploadinfo(uploadinfo_id):
    if request.method == 'GET':
        uploadinfo_rec = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
        result_form = forms.UploadInfoForm(obj=uploadinfo_rec)
        return render_template('submission/uploadinfo_form.html', uploadinfo_form=result_form), 200
    elif request.method == 'POST':
        posted_form = forms.UploadInfoForm(request.form)
        if posted_form.validate_on_submit():

            uploadinfo_rec = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
            posted_form.populate_obj(uploadinfo_rec)

            db.session.add(uploadinfo_rec)
            db.session.commit()
            flash("Checksum updated", "success")
            return redirect(url_for('view_submission', sub_id=uploadinfo_rec.submission_id))
        else:
            return render_template('submission/uploadinfo_form.html', uploadinfo_form=posted_form), 400


@app.route('/submission_uploadinfo_delete/<int:uploadinfo_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'SubmissionUploadInfo', 'entity_id_key': 'uploadinfo_id',
                                         'entity_ac_attribute': 'submission_id'})
def delete_submission_uploadinfo(uploadinfo_id):
    submission_uploadinfo = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
    db.session.delete(submission_uploadinfo)
    db.session.commit()
    flash("Checksum deleted", "success")
    return redirect(url_for('view_submission', sub_id=submission_uploadinfo.submission_id))


"""----------------------------------------------------"""
""" Endpoints for managing a submission's messages."""
"""----------------------------------------------------"""



@app.route('/submission_message_add/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'],
                   record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
                                         'entity_ac_attribute': 'id'})
def add_submission_message(sub_id):
    if request.method == 'GET':
        return render_template('submission/message_form.html',
                               message_form=forms.MessageForm(formdata=None,
                                                                    obj=None,
                                                                    sub_id=sub_id)), 200
    elif request.method == 'POST':
        posted_form = forms.MessageForm(request.form)
        if posted_form.validate_on_submit():
            message_rec = SubmissionMessage()
            posted_form.populate_obj(message_rec)
            message_rec.id = None
            message_rec.sender_user = current_user
            message_rec.created_on = datetime.now()
            db.session.add(message_rec)
            db.session.commit()
            if message_rec.submission.is_in_progress():
                send_new_message_notification(message_rec)
            flash("Message added", "success")

            return redirect(url_for('view_submission', sub_id=message_rec.submission_id))
        else:
            return render_template('submission/message_form.html', message_form=posted_form), 400


"""----------------------------------------------------"""
""" Miscellaneous endpoints                            """
"""----------------------------------------------------"""


# @app.route('/autocomplete_institutes', methods=['GET'])
# def autocomplete_institutes():
#     return Response(dumps(app.config.get('DATA_INIT')['collab_institutions']), mimetype='application/json')



@app.route('/notification/<int:notification_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def send_notification(notification_id):
    try:
        notification_rec = EmailNotification.query.get_or_404(int(notification_id))
        send_email_asynch(notification_rec)
        app.logger.info('INFO: Re-Sent email notification with ID: %s', notification_id)
        flash("Notification email sent!", "success")
        return "", 204
    except Exception as e:
        app.logger.error('ERROR  while sending notification email %s', e)
        flash("An error occurred when sending the notification email", 'error')
        return "", 400


@app.route('/notifications', methods=['GET'])
@app_authorization(allowed_roles=['admin'])
def list_notifications():
    notifications = EmailNotification.query.all()
    return render_template('email/notifications.html',
                           notifications=notifications)
