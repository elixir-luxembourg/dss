# coding=utf-8
from flask import flash, redirect, render_template, request, url_for,g
from flask_login import current_user, login_user, login_required, logout_user

import elixir_dcp.forms as forms
from elixir_dcp import login_manager
from elixir_dcp.models.security import User
from elixir_dcp.models.submission import create_sub, delete_sub, share_sub, Submission, SubmissionAttachment, \
    SubmissionContact, SubmissionStatusEnum, SubmissionStudyDish, SubmissionUseConditionGroup
import elixir_dcp.exceptions as exceptions
from sqlalchemy.exc import OperationalError
from sqlalchemy import and_, or_
import os
import uuid
import shutil
from elixir_dcp import app, db, oidc
from werkzeug.utils import secure_filename
from . import app_authorization



__author__ = 'Valentin Grouès, Pinar Alper'

@app.route('/', methods=['GET'])
@oidc.require_login
@login_required
def home():
    return render_template('home.html')


@app.route("/logout")
@login_required
def logout():
    #Flask Login Logout
    logout_user()

    # The below OIDC logout does not work!
    #TODO: Find a way to sign out of AAI
    oidc.logout()
    flash('You have logged out of ELIXIR DCP.', 'success')
    return render_template('home.html')


@app.route('/oidc_login', methods=['GET', 'POST'])
@oidc.require_login
def oidc_login():

    app.logger.info('Debug in oidc_login')
    app.logger.info(g.oidc_id_token)
    app.logger.info("User Info:" + oidc.user_getinfo(['name', 'email', 'sub', 'bona_fide_status']).__str__())
    # TODO  We need to figure out why attributes other than sub are None after the initial authentication
    # Such as:  elixir_oidc_email = oidc.user_getfield("email")

    if request.method == 'GET':
        existing_user_record = User.query.filter_by(elixir_sub_id=oidc.user_getfield("sub")).one_or_none()
        if (existing_user_record is not None) & current_user.is_anonymous:
            login_user(existing_user_record, remember=True)
            #next = flask.request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            #if not is_safe_url(next):
            #return flask.abort(400)

            return redirect(url_for('home'))
        else:
            empty_form = forms.SignupForm(elixir_sub_id=oidc.user_getfield("sub"))
            return render_template('security/signup.html', signup_form=empty_form)
    elif request.method == 'POST':
        posted_form = forms.SignupForm(request.form)
        if posted_form.validate_on_submit():
            new_user_record = User(elixir_sub_id=posted_form.elixir_sub_id.data,
                            first_name=posted_form.first_name.data,
                            last_name=posted_form.last_name.data,
                            email=posted_form.email.data,
                            active_user=True)
            db.session.add(new_user_record)
            db.session.commit()
            User.query.filter_by(elixir_sub_id=posted_form.elixir_sub_id.data).one_or_none().assign_role('data_provider')
            login_user(new_user_record, remember=True)
            flash('You have been signed up to the ELIXIR-LU Data Submission system.', 'info')
            return redirect(url_for('home'))
        else:
            flash("Please check the validity of your input in highlighted places", "error")
            return render_template('submission/submission.html', signup_form=posted_form)




#return render_template('/security/oidc.html',
#                       sub=oidc.user_getfield("sub"),
#                       preferred_username=oidc.user_getfield("preferred_username"),
#                       email=oidc.user_getfield("email"),
#                       bona_fide_status=oidc.user_getfield("bona_fide_status"),
#                       groupNames=oidc.user_getfield("groupNames"),
#                       token=None)

#return redirect(url_for('home'))


"""return oidc.redirect_to_auth_server(request.url)

info = oidc.user_getinfo(['preferred_username', 'email', 'sub', 'bona_fide_status'])
# We need to figure out why attributes other than sub are None after the initial authentication

app.logger.info(info)

#from oauth2client.client import OAuth2Credentials
#credentials = OAuth2Credentials.from_json(oidc.credentials_store[info.get('sub')])
#app.logger.info(credentials)



    return render_template('/security/oidc.html',
                       sub=oidc.user_getfield("sub"),
                       preferred_username=oidc.user_getfield("preferred_username"),
                       email=oidc.user_getfield("email"),
                       bona_fide_status=oidc.user_getfield("bona_fide_status",),
                       groupNames=oidc.user_getfield("groupNames"),
                       token=None)
"""




def get_names_from_oidc(oidc_name):
    result = ['', '']

    if oidc_name is not None:
        if " " in oidc_name:
            name_list = oidc_name.split(" ")
            result[0] = name_list[0]
            if len(name_list) > 1:
                result[1] = name_list[1]
    return result

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
@app.route('/share/submission/<int:sub_id>', methods=['GET','POST'])
def share_submission(sub_id):
    if request.method == 'GET':
        submission_rec = Submission.query.get_or_404(sub_id)
        access_form = forms.SubmissionAccessForm(obj=submission_rec)
        return render_template('submission/_submission_share.html', submsn_access_form=access_form)
    elif request.method == 'POST':
        posted_form = forms.SubmissionAccessForm(request.form)
        if posted_form.validate_on_submit():
            try:
                shared_sub = share_sub(posted_form.id.data, posted_form.provider_user_id.data)
                flash('Submission {} shared with {}'.format(shared_sub.ref_name, shared_sub.provider_user.display_name()), "success")
                return redirect(url_for('list_submissions'))
            except exceptions.RecordLifecycleException as e:
                app.logger.error('ERROR %s', e)
                flash("The submission is not shareable due to its status", "error")
                return redirect(url_for('list_submissions'))
        else:
            flash("Unable to share submission with the information provided", "error")
            return redirect(url_for('list_submissions'))


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
        return "",400


@app_authorization(allowed_roles=['admin'])
@app.route('/archive/submission/<int:sub_id>', methods=['GET'])
def archive_submission(sub_id):
    pass


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
@login_required
@app_authorization(allowed_roles=['data_provider'])
def list_my_submissions():
    """
    List the submissions that have been shared with the LOGGED IN  user (with the data provider role)
    """

    my_submissions = db.session.query(Submission).filter(and_(Submission.provider_user_id == current_user.id,
                                                              or_(Submission.current_status==SubmissionStatusEnum.in_progress_metadata,
                                                                  Submission.current_status==SubmissionStatusEnum.in_progress_data)))

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
            submission_rec.title = form.title.data
            #form.populate_obj(submission_rec)
            db.session.add(submission_rec)
            db.session.commit()
            flash('Submission updated', 'success')
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
            flash("Submission Contact {}.".format(msg), "success")

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
        flash("Submission Attachment(s) added", "success")
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
    flash("Submission Attachment deleted", "success")
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
            flash("Study {}.".format(msg), "success")

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
    flash("Study deleted", "success")
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
            flash("Data Use Condition Group {}.".format("created" if mode == 'create' else "updated"), "success")

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
    flash("Use Condition Group deleted", "success")
    return "", 204
