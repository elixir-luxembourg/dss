# coding=utf-8
from flask import abort, flash, redirect, render_template, request, url_for, g, get_flashed_messages, Response
from flask_login import current_user, login_user, login_required, logout_user

from json import dumps
import elixir_dcp.forms as forms
from elixir_dcp import login_manager
from elixir_dcp.models.security import User
from elixir_dcp.models.services import create_sub, delete_sub, steer_sub, revert_sub, \
    get_in_progress_submissions_shared_with_user, register_new_user, assign_role_to_user, update_submission_basic_info, \
    update_user_info
from elixir_dcp.models.submission import Submission, SubmissionAttachment, SubmissionContact, \
    SubmissionStudyDish, SubmissionUploadInfo
import elixir_dcp.exceptions as exceptions
from sqlalchemy.exc import OperationalError
import os
import uuid
import shutil
from elixir_dcp import app, db, oidc
from werkzeug.utils import secure_filename
from . import app_authorization
from .utils import get_names_from_oidc

__author__ = 'Pinar Alper'


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/test_metadata', methods=['GET'])
def test_metadata():
    return render_template('submission/_study_metadata.html')


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
            update_user_info(user_rec, first_name=form.first_name.data,
                             last_name=form.last_name.data,
                             institution=form.institution.data,
                             email=form.email.data,
                             addr_line1=form.addr_line1.data,
                             addr_line2=form.addr_line2.data,
                             phone_no=form.phone_no.data,
                             assigned_role_ids=form.assigned_role_ids.data)

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

    flash('You have logged out of ELIXIR DCP.', 'success')
    return render_template('home.html')


@app.route('/oidc_login', methods=['GET', 'POST'])
@oidc.require_login
def oidc_login():
    app.logger.info(g.oidc_id_token)
    app.logger.info(
        "User Info:" + oidc.user_getinfo(['openid', 'email', 'profile', 'bona_fide_status', 'groupNames']).__str__())

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'GET':
        existing_user_record = User.query.filter_by(elixir_sub_id=oidc.user_getfield("sub")).one_or_none()
        if existing_user_record is None:
            name = oidc.user_getfield("name")
            if name is not None:
                partially_filled_form = forms.SignupForm(elixir_sub_id=oidc.user_getfield("sub"),
                                              first_name=get_names_from_oidc(name)[0],
                                              last_name=get_names_from_oidc(name)[1], email=oidc.user_getfield("email"))
                return render_template('security/signup.html', signup_form=partially_filled_form)
            else:
                return render_template('error.html', message="Error 500 - {}".format(
                    "Insufficient information on the AAI User, cannot continue with signup.")), 500
        else:
            if not existing_user_record.is_active:
                render_template('error.html', message="Error 500 - {}".format(
                    "You are no longer an active user of this application.")), 500
            else:
                login_user(existing_user_record, remember=True)
                nextt = request.args.get('next')

                app.logger.info(get_flashed_messages())
                if not forms.is_safe_url(nextt):
                    return abort(404)
                else:
                    return redirect(nextt or url_for('home'))
    elif request.method == 'POST':
        posted_form = forms.SignupForm(request.form)
        if posted_form.validate_on_submit():
            new_user_record = User()
            posted_form.populate_obj(new_user_record)
            registered_user = register_new_user(new_user_record)
            assign_role_to_user(registered_user, 'data_provider')
            login_user(registered_user, remember=True)
            flash('You are now signed up to the ELIXIR-LU Data Submission System.', 'success')
            return redirect(url_for('home'))
        else:
            flash("Please check the validity of your input in highlighted places.", "error")
            return render_template('security/signup.html', signup_form=posted_form)


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


@app_authorization(allowed_roles=['admin', 'data_provider'])
@app.route('/steer/submission/<int:sub_id>', methods=['GET'])
def steer_submission(sub_id):
    try:
        sub_with_new_state = steer_sub(sub_id)
        flash("Submission moved to next state {}!".format(sub_with_new_state.current_status.value), "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error('ERROR %s', e)
        flash("Unable to transition submission to the next state", 'error')
        return "", 400


@app_authorization(allowed_roles=['admin'])
@app.route('/revert/submission/<int:sub_id>', methods=['GET'])
def revert_submission(sub_id):
    try:
        sub_with_new_state = revert_sub(sub_id)
        flash("Submission moved to previous state {}!".format(sub_with_new_state.current_status.value), "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error('ERROR %s', e)
        flash("Unable to revert submission to the previous state", 'error')
        return "", 400


"""------------------------------------"""
"""------------------------------------"""
"""------------------------------------"""


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
@app_authorization(allowed_roles=['admin', 'data_provider'])
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
    flash('New submission {} created'.format(submission_rec.ref_name), 'success')
    return redirect(url_for('list_submissions'))


@app.route('/submission/edit/<int:sub_id>', methods=['GET', 'POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def edit_submission(sub_id):
    app.logger.info('INFO: Edit submission SUB-ID: %s', sub_id)
    if request.method == 'GET':
        submission_rec = Submission.query.get_or_404(sub_id)
        app.logger.info('Sub REC: %s', submission_rec)
        sub_form = forms.SubmissionForm(obj=submission_rec)
        sub_form.provider_user_ids.data = submission_rec.provider_user_ids()
        return render_template('submission/submission.html', submsn_form=sub_form, submission=submission_rec)
    elif request.method == 'POST':
        form = forms.SubmissionForm(request.form)
        submission_rec = Submission.query.get_or_404(form.id.data)
        if form.validate_on_submit():
            update_submission_basic_info(submission_rec, title=form.title.data,
                                         upload_instructions=form.upload_instructions.data,
                                         provider_user_ids=form.provider_user_ids.data)
            flash('Submission updated', 'success')
            return redirect(url_for('list_submissions'))
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/submission.html', submsn_form=form, submission=submission_rec)


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Contacts."""
"""----------------------------------------------------"""


@app.route('/submission_contacts_inline/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def inline_submission_contacts(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template('submission/_contacts.html', submission=submission_rec,
                           contact_form=forms.ContactForm(formdata=None,
                                                          obj=None,
                                                          sub_id=submission_rec.id))


@app.route('/submission_contacts/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def list_submission_contacts(sub_id):
    contacts = SubmissionContact.query.filter_by(submission_id=sub_id)
    return render_template('submission/_contact_columns.html', contacts=contacts)


@app.route('/submission_contact/<int:contact_id>', methods=['GET', 'POST'])
@app.route('/submission_contact', methods=['POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
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
            # msg = "updated" if mode == 'create' else "added"
            # flash("Submission Contact {}.".format(msg), "success")

            sid = posted_form.submission_id.data

            return render_template('submission/_contact_form.html', contact_form=forms.ContactForm(formdata=None,
                                                                                                   obj=None,
                                                                                                   sub_id=sid)), 200
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_contact_form.html', contact_form=posted_form), 400


@app.route('/submission_contact/<int:contact_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def delete_submission_contact(contact_id):
    submission_contact = SubmissionContact.query.get_or_404(contact_id)
    db.session.delete(submission_contact)
    db.session.commit()
    # flash("Submission Contact deleted", "info")
    return "", 204


"""-------------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Attachments."""
"""-------------------------------------------------------"""

@app.route('/submission_attachments_inline/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def inline_submission_attachments(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template('submission/_attachments.html', submission=submission_rec,
                           attachment_form=forms.AttachmentForm(formdata=None,
                                                          obj=None,
                                                          sub_id=submission_rec.id))

@app.route('/submission_attachments/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def list_submission_attachments(sub_id):
    attachments = SubmissionAttachment.query.filter_by(submission_id=sub_id)
    return render_template('submission/_attachment_columns.html', attachments=attachments)


def is_allowed_type(filename):
    allowed_extensions = set(['txt', 'pdf', 'png'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/submission_attachment', methods=['POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def add_submission_attachment():
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
        if not is_allowed_type(file.filename):
            file_validation = False
            form.file_attachments.errors.append(
                'File {} is not of allowed type. Only TXT, PDF and PNG files can be uploaded.'.format(file.filename))
    if (not file_validation) or (not form_validation):
        # flash("Please check the validity of your input in highlighted fields.", "error")
        return render_template('submission/_attachment_form.html', attachment_form=form), 400
    else:
        attachments_folder = str(uuid.uuid4())
        path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachments_folder)
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
        # flash("Submission Attachment(s) added", "success")
        sid = form.submission_id.data
        return render_template('submission/_attachment_form.html', attachment_form=forms.AttachmentForm(formdata=None,
                                                                                                        obj=None,
                                                                                                        sub_id=sid)), 200


@app.route('/submission_attachment/<int:attach_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def delete_submission_attachment(attach_id):
    submission_attachment = SubmissionAttachment.query.get_or_404(attach_id)
    path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], submission_attachment.folder_name)
    shutil.rmtree(path_on_server)
    db.session.delete(submission_attachment)
    db.session.commit()
    # flash("Submission Attachment deleted", "success")
    return "", 204


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's DISHs."""
"""----------------------------------------------------"""



@app.route('/submission_dishes_inline/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def inline_submission_dishes(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template('submission/_dishes.html', submission=submission_rec,
                           dish_form=forms.StudyDishForm(formdata=None,
                                                                obj=None,
                                                                sub_id=submission_rec.id))
@app.route('/submission_dishes/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def list_submission_dishes(sub_id):
    dishes = SubmissionStudyDish.query.filter_by(submission_id=sub_id)
    return render_template('submission/_dish_columns.html', dishes=dishes)


@app.route('/submission_dish/<int:dish_id>', methods=['GET', 'POST'])
@app.route('/submission_dish', methods=['POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
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
            # msg = "created" if mode == 'create' else "updated"
            # flash("Study {}.".format(msg), "success")

            sid = posted_form.submission_id.data

            return render_template('submission/_dish_form.html', dish_form=forms.StudyDishForm(formdata=None,
                                                                                               obj=None,
                                                                                               sub_id=sid)), 200
        else:
            # flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_dish_form.html', dish_form=posted_form), 400


@app.route('/submission_dish/<int:dish_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def delete_submission_dish(dish_id):
    dish = SubmissionStudyDish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    # flash("Study deleted", "success")
    return "", 204


@app.route('/submission_dish/<int:dish_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def get_dish_metadata(dish_id):
    dish = SubmissionStudyDish.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    # flash("Study deleted", "success")
    return "", 204


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's Upload Info Records."""
"""----------------------------------------------------"""


@app.route('/submission_uploadinfos_inline/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def inline_submission_uploadinfos(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template('submission/_uploadinfos.html', submission=submission_rec,
                           uploadinfo_form=forms.UploadInfoForm(formdata=None,
                                                         obj=None,
                                                         sub_id=submission_rec.id))

@app.route('/submission_uploadinfos/<int:sub_id>', methods=['GET'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def list_submission_uploadinfos(sub_id):
    uploadinfos = SubmissionUploadInfo.query.filter_by(submission_id=sub_id)
    return render_template('submission/_uploadinfo_columns.html', uploadinfos=uploadinfos)


@app.route('/submission_uploadinfo/<int:uploadinfo_id>', methods=['GET', 'POST'])
@app.route('/submission_uploadinfo', methods=['POST'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def add_edit_submission_uploadinfo(uploadinfo_id=None):
    if uploadinfo_id is None:
        mode = 'create'
    else:
        mode = 'edit'
    if request.method == 'GET':
        uploadinfo_rec = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
        result_form = forms.UploadInfoForm(obj=uploadinfo_rec)
        return render_template('submission/_uploadinfo_form.html', uploadinfo_form=result_form)
    elif request.method == 'POST':
        posted_form = forms.UploadInfoForm(request.form)
        if posted_form.validate_on_submit():
            if mode == 'edit':
                uploadinfo_rec = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
                posted_form.populate_obj(uploadinfo_rec)
            else:
                uploadinfo_rec = SubmissionUploadInfo()
                posted_form.populate_obj(uploadinfo_rec)
                uploadinfo_rec.id = None
            db.session.add(uploadinfo_rec)
            db.session.commit()
            # flash("Submission Upload Info {}.".format("created" if mode == 'create' else "updated"), "success")
            sid = posted_form.submission_id.data

            return render_template('submission/_uploadinfo_form.html',
                                   uploadinfo_form=forms.UploadInfoForm(formdata=None,
                                                                        obj=None,
                                                                        sub_id=sid)), 200
        else:
            # flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/_uploadinfo_form.html', uploadinfo_form=posted_form), 400


@app.route('/submission_uploadinfo/<int:uploadinfo_id>', methods=['DELETE'])
@app_authorization(allowed_roles=['admin', 'data_provider'])
def delete_submission_uploadinfo(uploadinfo_id):
    submission_uploadinfo = SubmissionUploadInfo.query.get_or_404(uploadinfo_id)
    db.session.delete(submission_uploadinfo)
    db.session.commit()
    # flash("Submission Upload Info deleted", "success")
    return "", 204


"""----------------------------------------------------"""
"""AJAX Endpoints for autocomplete fields in various forms"""
"""----------------------------------------------------"""


@app.route('/autocomplete_institutes', methods=['GET'])
def autocomplete_institutes():
    return Response(dumps(app.config.get('DATA_INIT')['collab_institutions']), mimetype='application/json')
