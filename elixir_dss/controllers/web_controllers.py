import json
import os
import shutil
import uuid
from datetime import datetime, UTC

from flask import (
    flash,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import OperationalError
from werkzeug.utils import secure_filename
from wtforms import FieldList, FormField

import elixir_dss.exceptions as exceptions
import elixir_dss.forms as forms
from elixir_dss import app, db, lft, login_manager, oauth
from elixir_dss.models.security import User
from elixir_dss.models.services import (
    assign_role_to_user,
    create_sub,
    delete_sub,
    get_in_progress_submissions_shared_with_user,
    register_new_user,
    revert_sub,
    send_email_asynch,
    send_new_message_notification,
    steer_sub,
    update_submission_basic_info,
    update_user_info,
    clone_sub,
)
from elixir_dss.models.submission import (
    Contact,
    EmailNotification,
    Submission,
    SubmissionAttachment,
    SubmissionDataset,
    SubmissionMessage,
    SubmissionStatusEnum,
    SubmissionStudy,
)

from . import app_authorization


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")


@app.route("/users", methods=["GET"])
@app_authorization(allowed_roles=["admin"])
def list_users():
    users = User.query.all()
    return render_template("security/users.html", users=users)


@app.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
@app_authorization(allowed_roles=["admin"])
def edit_user(user_id):
    if request.method == "GET":
        user_rec = User.query.get_or_404(int(user_id))
        usr_form = forms.UserForm(obj=user_rec)
        usr_form.assigned_role_ids.data = user_rec.assigned_role_ids()
        return render_template("security/user.html", user_form=usr_form)
    elif request.method == "POST":
        form = forms.UserForm(request.form)
        user_rec = User.query.get_or_404(form.id.data)
        if form.validate_on_submit():
            update_user_info(user_rec, **form.data)

            flash("User updated", "success")
            return redirect(url_for("list_users"))
        else:
            flash(
                "Please check the validity of your input in highlighted places", "error"
            )
            return render_template("security/user.html", user_form=form)


@app.route("/logout")
@login_required
def logout():
    method = app.config.get("AUTHENTICATION_METHOD", "CONFIG")
    id_token = session.get("oidc_id_token")
    session_cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")

    logout_user()
    session.clear()
    session.permanent = False

    if method == "CONFIG" or not id_token:
        redirect_url = url_for("home")
    else:
        redirect_url = _keycloak_logout_url(id_token)

    response = make_response(redirect(redirect_url))
    response.set_cookie(session_cookie_name, "", expires=0, path="/", httponly=True)
    response.set_cookie("remember_token", "", expires=0, path="/", httponly=True)

    flash("You have logged out of Submission System.", "success")
    return response


@app.after_request
def disable_caching(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/oidc_login")
def oidc_login():
    redirect_uri = url_for("auth_callback", _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = oauth.keycloak.authorize_access_token()
    _set_token_session(token)

    userinfo = oauth.keycloak.userinfo(token=token)
    if not userinfo:
        flash("Failed to retrieve user info from Keycloak.", "error")
        return redirect(url_for("home"))

    sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name", "")
    first_name, last_name = (name.split(" ", 1) + [""])[:2]

    user = User.query.filter_by(elixir_sub_id=sub).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            elixir_sub_id=sub,
            first_name=first_name,
            last_name=last_name,
            email=email,
            active_user=True,
            institution_accession="UNKNOWN",
        )
        user = register_new_user(user)
        try:
            assign_role_to_user(user, "user")
        except Exception as e:
            app.logger.warning(f"Could not assign default role: {e}")

    login_user(user)
    flash("Logged in successfully!", "success")
    return redirect(url_for("home"))


def refresh_token():
    refresh_value = session.get("oidc_refresh_token")
    if not refresh_value:
        flash("Session expired. Please log in again.", "warning")
        return _clear_session()

    try:
        app.logger.debug("[REFRESH] Attempting token refresh...")
        new_token = oauth.keycloak.fetch_access_token(
            grant_type="refresh_token",
            refresh_token=refresh_value,
        )
        _set_token_session(new_token)
        app.logger.debug("OIDC token successfully refreshed.")
    except Exception as e:
        app.logger.error(f"Failed to refresh token: {e}")
        flash("Session expired. Please log in again.", "warning")
        return _clear_session()


@app.before_request
def check_token_expiration():
    if request.endpoint in ("static", "home", "oidc_login", "auth_callback", "logout"):
        return
    if "oidc_access_token" in session:
        now = datetime.now(UTC)
        expires_at = session.get("oidc_expires_at", 0)
        if now.timestamp() > expires_at:
            return refresh_token()


def _set_token_session(token: dict):
    """Store Keycloak tokens and expiry info in session."""
    now = datetime.now(UTC)
    session["oidc_id_token"] = token.get("id_token")
    session["oidc_access_token"] = token.get("access_token")
    session["oidc_refresh_token"] = token.get("refresh_token")
    session["oidc_expires_at"] = now.timestamp() + token.get("expires_in", 0)


def _clear_session():
    """Clear user session and cookies."""
    session.clear()
    session.permanent = False

    logout_user()

    response = make_response(redirect(url_for("home")))

    session_cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
    response.set_cookie(session_cookie_name, "", expires=0, path="/", httponly=True)
    response.set_cookie("remember_token", "", expires=0, path="/", httponly=True)

    return response


def _keycloak_logout_url(id_token: str):
    """Construct Keycloak logout URL."""
    base = f"{app.config['OIDC_AUTHORITY']}/protocol/openid-connect/logout"
    redirect_uri = url_for("home", _external=True)
    return f"{base}?post_logout_redirect_uri={redirect_uri}&id_token_hint={id_token}"


def landing_page_for_user(usr):
    if usr.is_data_steward():
        return url_for("list_submissions")
    else:
        return url_for("list_my_submissions")


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """View and update user profile."""
    if request.method == "POST":
        posted_form = forms.MyProfileForm(request.form)
        if posted_form.validate_on_submit():
            update_user_info(current_user, **posted_form.data)
            flash("Your profile is updated.", "success")
            return redirect(landing_page_for_user(current_user))
        else:
            flash(
                "Please check the validity of your input in highlighted places.",
                "error",
            )
            return render_template("security/profile.html", profile_form=posted_form)
    else:  # GET
        profile_form = forms.MyProfileForm(obj=current_user)
        return render_template("security/profile.html", profile_form=profile_form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    # Redirect to profile if already logged in
    if current_user.is_authenticated:
        return redirect(url_for("profile"))

    form = forms.LoginForm()
    if form.validate_on_submit():
        email = form.username.data
        password = form.password.data

        expected_password = app.config.get("AUTHENTICATION_DICT").get(email)

        if expected_password is not None and expected_password == password:
            app.logger.debug("config authentication passed")
            user = User.query.filter_by(email=email, active_user=True).one_or_none()
            if user is None:
                form.username.errors.append("User not found")
            else:
                login_user(user, remember=form.remember.data)
                flash("User logged in successfully.", "success")
                return form.redirect()
        else:
            message = "Wrong username / password combination."
            form.username.errors.append(message)
            form.password.errors.append(message)

    return render_template("security/login_user.html", login_user_form=form)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except OperationalError as e:
        app.logger.error("Error: %s", e)
        return None


"""------------------------------------"""
"""Endpoints for managing  Submissions."""
"""------------------------------------"""


@app_authorization(allowed_roles=["data_steward"])
@app.route("/submission/<int:sub_id>", methods=["DELETE"])
def delete_submission(sub_id):
    try:
        delete_sub(sub_id)
        app.logger.info("INFO: Deleted submission SUB-ID: %s", sub_id)
        flash("Submission deleted!", "success")
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error("ERROR %s", e)
        flash("Unable to delete submission", "error")
        return "", 400


@app.route("/steer/submission/<int:sub_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def steer_submission(sub_id):
    try:
        sub_with_new_state = steer_sub(sub_id)
        flash(
            f"Submission moved to next state {sub_with_new_state.current_status.value}!",
            "success",
        )
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error("ERROR %s", e)
        flash("Unable to transition submission to the next state", "error")
        return "", 400


@app.route("/revert/submission/<int:sub_id>", methods=["GET"])
@app_authorization(allowed_roles=["data_steward"])
def revert_submission(sub_id):
    try:
        sub_with_new_state = revert_sub(sub_id)
        flash(
            f"Submission moved to previous state {sub_with_new_state.current_status.value}!",
            "success",
        )
        return "", 204
    except exceptions.RecordLifecycleException as e:
        app.logger.error("ERROR %s", e)
        flash("Unable to revert submission to the previous state", "error")
        return "", 400


@app.route("/submissions", methods=["GET"])
@app_authorization(allowed_roles=["data_steward"])
def list_submissions():
    """
    List all submissions
    """
    submissions = Submission.query.all()
    return render_template(
        "submission/submissions.html",
        submissions=submissions,
        submsn_create_form=forms.SubmissionForm(),
    )


@app.route("/my_submissions", methods=["GET"])
@app_authorization(allowed_roles=["user"])
def list_my_submissions():
    """
    List the submissions that have been shared with the LOGGED IN  user
    """

    my_submissions = get_in_progress_submissions_shared_with_user(current_user.id)

    return render_template(
        "submission/my_submissions.html", my_submissions=my_submissions
    )


@app.route("/submission/<int:sub_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def get_submission(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    app.logger.info("INFO: Get submission SUB-ID: %s", sub_id)
    return render_template("submission/viewer.html", submission=submission_rec)


@app.route("/submission/create", methods=["POST"])
@app_authorization(allowed_roles=["data_steward"])
def create_submission():
    creation_form = forms.SubmissionForm(request.form)
    submission_rec = create_sub(
        creation_form.title.data, creation_form.institution_accession.data
    )
    flash(f"New submission {submission_rec.ref_name} created", "success")
    return redirect(url_for("list_submissions"))


@app.route("/submission/view/<int:sub_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def view_submission(sub_id):
    submission_rec = Submission.query.get_or_404(sub_id)
    return render_template("submission/submission.html", submission=submission_rec)


@app.route("/submission/edit/<int:sub_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def edit_submission(sub_id):
    app.logger.info("INFO: Edit submission SUB-ID: %s", sub_id)
    if request.method == "GET":
        submission_rec = Submission.query.get_or_404(sub_id)
        app.logger.info("Sub REC: %s", submission_rec)

        if current_user.is_data_steward():

            class AdminSubmissionForm(forms.SubmissionForm):
                pass

            AdminSubmissionForm.submission_contacts = FieldList(
                FormField(forms.ContactForm, default=lambda: Contact()),
                min_entries=1,
                description="You must provide at least three contacts. (1) Main contact who is the signatory on the submission info sheet, another (2) Data protection officer of the submitting institution\
                                                                                                                      (3) Legal representative for the submitting institution",
                label="Submission contacts",
            )
            sub_form = AdminSubmissionForm(obj=submission_rec)
        else:
            sub_form = forms.SubmissionForm(obj=submission_rec)
        if submission_rec.local_custodians_json:
            sub_form.local_custodians.data = json.loads(
                submission_rec.local_custodians_json
            )
        sub_form.provider_user_ids.data = submission_rec.provider_user_ids()
        return render_template("submission/submission_form.html", submsn_form=sub_form)
    elif request.method == "POST":
        if current_user.is_data_steward():

            class AdminSubmissionForm(forms.SubmissionForm):
                pass

            AdminSubmissionForm.submission_contacts = FieldList(
                FormField(forms.ContactForm, default=lambda: Contact()),
                min_entries=1,
                description="You must provide at least three contacts. (1) Main contact who is the signatory on the submission info sheet, another (2) Data protection officer of the submitting institution\
                                                                                                                      (3) Legal representative for the submitting institution",
                label="Submission contacts",
            )
            form = AdminSubmissionForm(request.form)
        else:
            form = forms.SubmissionForm(request.form)
        submission_rec = Submission.query.get_or_404(form.id.data)
        if form.validate_on_submit():
            form.populate_obj(submission_rec)
            update_submission_basic_info(
                submission_rec,
                title=form.title.data,
                submission_scope_code=form.submission_scope_code.data,
                local_custodians_json=json.dumps(form.local_custodians.data),
                local_project_name=form.local_project_name.data,
                institution_accession=form.institution_accession.data,
                provider_user_ids=form.provider_user_ids.data
                if request.form.get("provider_user_ids")
                else None,
            )

            flash("Submission updated", "success")
            return redirect(url_for("view_submission", sub_id=submission_rec.id))
        else:
            return render_template(
                "submission/submission_form.html", submsn_form=form
            ), 400


@app.route("/submission/clone/<int:submission_id>")
@login_required
def clone_submission(submission_id):
    clone_studies = request.args.get("clone_studies", "true").lower() == "true"
    clone_datasets = request.args.get("clone_datasets", "true").lower() == "true"

    new_sub = clone_sub(
        submission_id,
        clone_studies=clone_studies,
        clone_datasets=clone_datasets,
    )

    flash(f"Submission {new_sub.ref_name} cloned successfully.", "success")
    return redirect(url_for("view_submission", sub_id=new_sub.id))


"""-------------------------------------------------------"""
"""AJAX Endpoints for managing a submission's attachments."""
"""-------------------------------------------------------"""

#
#
# @app.route('/submission_attachments/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'], record_authorization={'entity':'Submission', 'entity_id_key':'sub_id', 'entity_ac_attribute':'id'})
# def list_submission_attachments(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_attachment_columns.html', submission = submission_rec), 200


def is_allowed_type(filename):
    allowed_extensions = set(["txt", "pdf", "png"])
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@app.route("/submission_attachment_add/<int:sub_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def add_submission_attachment(sub_id):
    if request.method == "GET":
        return render_template(
            "submission/attachment_form.html",
            attachment_form=forms.AttachmentForm(
                formdata=None, obj=None, sub_id=sub_id
            ),
        ), 200
    elif request.method == "POST":
        form = forms.AttachmentForm(request.form)
        file_validation = True
        form_validation = form.validate_on_submit()
        request_files = request.files.getlist(form.file_attachments.name)
        for file in request_files:
            # if user does not select file, browser may
            # submit an empty part without filename.
            # we therefore check for that.
            if file.filename == "":
                file_validation = False
                form.file_attachments.errors.append("No file(s) selected.")
            elif not is_allowed_type(file.filename):
                file_validation = False
                form.file_attachments.errors.append(
                    f"File {file.filename} is not of allowed type. Only TXT, PDF and PNG files can be uploaded."
                )
        if (
            (not file_validation)
            or (not form_validation)
            or (sub_id != int(form.submission_id.data))
        ):
            return render_template(
                "submission/attachment_form.html", attachment_form=form
            ), 400
        else:
            attachments_folder = str(uuid.uuid4())
            path_on_server = os.path.join(
                app.config["UPLOAD_FOLDER"], attachments_folder
            )

            if not os.path.exists(path_on_server):
                os.makedirs(path_on_server)
            attachment = SubmissionAttachment()
            attachment.note = form.note.data
            attachment.submission_id = form.submission_id.data
            attachment.folder_name = attachments_folder
            attachment.file_names = ""
            for file in request_files:
                secured_file_name = secure_filename(file.filename)
                attachment.file_names += secured_file_name + " "
                file.save(os.path.join(path_on_server, secured_file_name))
            db.session.add(attachment)
            db.session.commit()
            flash("Attachment added", "success")
            return redirect(url_for("view_submission", sub_id=attachment.submission_id))


@app.route("/submission_attachment_delete/<int:attach_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "SubmissionAttachment",
        "entity_id_key": "attach_id",
        "entity_ac_attribute": "submission_id",
    },
)
def delete_submission_attachment(attach_id):
    submission_attachment = SubmissionAttachment.query.get_or_404(attach_id)
    path_on_server = os.path.join(
        app.config["UPLOAD_FOLDER"], submission_attachment.folder_name
    )
    shutil.rmtree(path_on_server)
    db.session.delete(submission_attachment)
    db.session.commit()
    flash("Attachment deleted", "success")
    return redirect(
        url_for("view_submission", sub_id=submission_attachment.submission_id)
    )


"""----------------------------------------------------"""
"""AJAX Endpoints for managing a Submission's datasets."""
"""----------------------------------------------------"""
#
#
# @app.route('/submission_datasets/<int:sub_id>', methods=['GET'])
# @app_authorization(allowed_roles=['admin', 'data_provider'],
#                    record_authorization={'entity': 'Submission', 'entity_id_key': 'sub_id',
#                                          'entity_ac_attribute': 'id'})
# def list_submission_datasets(sub_id):
#     submission_rec = Submission.query.get_or_404(sub_id)
#     return render_template('submission/_dataset_columns.html', submission=submission_rec)


@app.route("/submission_dataset_add/<int:sub_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def add_submission_dataset(sub_id):
    if request.method == "GET":
        return render_template(
            "submission/dataset_form.html",
            dataset_form=forms.DatasetForm(formdata=None, obj=None, sub_id=sub_id),
        ), 200
    elif request.method == "POST":
        posted_form = forms.DatasetForm(request.form)
        if (
            posted_form.validate_on_submit()
            and int(posted_form.submission_id.data) == sub_id
        ):
            dataset_rec = SubmissionDataset()
            posted_form.populate_obj(dataset_rec)
            dataset_rec.id = None
            if posted_form.sci_datatypes.data:
                dataset_rec.sci_datatypes_json = json.dumps(
                    posted_form.sci_datatypes.data
                )
            if posted_form.gdpr_datatypes.data:
                dataset_rec.gdpr_datatypes_json = json.dumps(
                    posted_form.gdpr_datatypes.data
                )
            db.session.add(dataset_rec)
            db.session.commit()
            flash("Dataset added", "success")
            return redirect(
                url_for("view_submission", sub_id=dataset_rec.submission_id)
            )
        else:
            return render_template(
                "submission/dataset_form.html", dataset_form=posted_form
            ), 400


@app.route("/submission_dataset/<int:dataset_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "SubmissionDataset",
        "entity_id_key": "dataset_id",
        "entity_ac_attribute": "submission_id",
    },
)
def edit_submission_dataset(dataset_id):
    if request.method == "GET":
        dataset_rec = SubmissionDataset.query.get_or_404(dataset_id)
        result_form = forms.DatasetForm(obj=dataset_rec)
        if dataset_rec.sci_datatypes_json:
            result_form.sci_datatypes.data = json.loads(dataset_rec.sci_datatypes_json)
        if dataset_rec.gdpr_datatypes_json:
            result_form.gdpr_datatypes.data = json.loads(
                dataset_rec.gdpr_datatypes_json
            )
        return render_template(
            "submission/dataset_form.html", dataset_form=result_form
        ), 200
    elif request.method == "POST":
        posted_form = forms.DatasetForm(request.form)
        if posted_form.validate_on_submit():
            dataset_rec = SubmissionDataset.query.get_or_404(dataset_id)
            posted_form.populate_obj(dataset_rec)

            if posted_form.sci_datatypes.data:
                dataset_rec.sci_datatypes_json = json.dumps(
                    posted_form.sci_datatypes.data
                )

            if posted_form.gdpr_datatypes.data:
                dataset_rec.gdpr_datatypes_json = json.dumps(
                    posted_form.gdpr_datatypes.data
                )

            db.session.add(dataset_rec)
            db.session.commit()
            flash("Dataset updated", "success")
            return redirect(
                url_for("view_submission", sub_id=dataset_rec.submission_id)
            )
        else:
            return render_template(
                "submission/dataset_form.html", dataset_form=posted_form
            ), 400


@app.route("/submission_dataset_delete/<int:dataset_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "SubmissionDataset",
        "entity_id_key": "dataset_id",
        "entity_ac_attribute": "submission_id",
    },
)
def delete_submission_dataset(dataset_id):
    dataset = SubmissionDataset.query.get_or_404(dataset_id)
    db.session.delete(dataset)
    db.session.commit()
    flash("Dataset deleted", "success")
    return redirect(url_for("view_submission", sub_id=dataset.submission_id))


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


@app.route("/submission_study_add/<int:sub_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def add_submission_study(sub_id):
    if request.method == "GET":
        return render_template(
            "submission/study_form.html",
            study_form=forms.StudyForm(formdata=None, obj=None, sub_id=sub_id),
        ), 200
    elif request.method == "POST":
        posted_form = forms.StudyForm(request.form)
        if posted_form.validate_on_submit() and (
            int(posted_form.submission_id.data) == sub_id
        ):
            study_rec = SubmissionStudy()
            posted_form.populate_obj(study_rec)
            study_rec.id = None
            if posted_form.study_types.data:
                study_rec.study_types_json = json.dumps(posted_form.study_types.data)
            db.session.add(study_rec)
            db.session.commit()
            flash("Study added", "success")
            return redirect(url_for("view_submission", sub_id=study_rec.submission_id))
        else:
            return render_template(
                "submission/study_form.html", study_form=posted_form
            ), 400


@app.route("/submission_study/<int:study_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "SubmissionStudy",
        "entity_id_key": "study_id",
        "entity_ac_attribute": "submission_id",
    },
)
def edit_submission_study(study_id):
    if request.method == "GET":
        study_rec = SubmissionStudy.query.get_or_404(study_id)
        result_form = forms.StudyForm(obj=study_rec)
        if study_rec.study_types_json:
            result_form.study_types.data = json.loads(study_rec.study_types_json)
        return render_template(
            "submission/study_form.html", study_form=result_form
        ), 200
    elif request.method == "POST":
        posted_form = forms.StudyForm(request.form)
        if posted_form.validate_on_submit():
            study_rec = SubmissionStudy.query.get_or_404(study_id)
            posted_form.populate_obj(study_rec)
            if posted_form.study_types.data:
                study_rec.study_types_json = json.dumps(posted_form.study_types.data)
            db.session.add(study_rec)
            db.session.commit()
            flash("Study updated", "success")
            return redirect(url_for("view_submission", sub_id=study_rec.submission_id))
        else:
            return render_template(
                "submission/study_form.html", study_form=posted_form
            ), 400


@app.route("/submission_study_delete/<int:study_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "SubmissionStudy",
        "entity_id_key": "study_id",
        "entity_ac_attribute": "submission_id",
    },
)
def delete_submission_study(study_id):
    study = SubmissionStudy.query.get_or_404(study_id)
    db.session.delete(study)
    db.session.commit()
    flash("Study deleted", "success")
    return redirect(url_for("view_submission", sub_id=study.submission_id))


"""----------------------------------------------------"""
""" Endpoints for managing a submission's messages."""
"""----------------------------------------------------"""


@app.route("/submission_message_add/<int:sub_id>", methods=["GET", "POST"])
@app_authorization(
    allowed_roles=["user", "data_steward"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def add_submission_message(sub_id):
    if request.method == "GET":
        return render_template(
            "submission/message_form.html",
            message_form=forms.MessageForm(formdata=None, obj=None, sub_id=sub_id),
        ), 200
    elif request.method == "POST":
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

            return redirect(
                url_for("view_submission", sub_id=message_rec.submission_id)
            )
        else:
            return render_template(
                "submission/message_form.html", message_form=posted_form
            ), 400


"""----------------------------------------------------"""
""" Miscellaneous endpoints                            """
"""----------------------------------------------------"""


# @app.route('/autocomplete_institutes', methods=['GET'])
# def autocomplete_institutes():
#     return Response(dumps(app.config.get('DATA_INIT')['collab_institutions']), mimetype='application/json')


@app.route("/notification/<int:notification_id>", methods=["GET"])
@app_authorization(allowed_roles=["data_steward"])
def send_notification(notification_id):
    try:
        notification_rec = EmailNotification.query.get_or_404(int(notification_id))
        send_email_asynch(notification_rec)
        app.logger.info("INFO: Re-Sent email notification with ID: %s", notification_id)
        flash("Notification email sent!", "success")
        return "", 204
    except Exception as e:
        app.logger.error("ERROR  while sending notification email %s", e)
        flash("An error occurred when sending the notification email", "error")
        return "", 400


@app.route("/notifications", methods=["GET"])
@app_authorization(allowed_roles=["data_steward"])
def list_notifications():
    notifications = EmailNotification.query.all()
    return render_template("email/notifications.html", notifications=notifications)


@app.route("/dataset_link/<int:dataset_id>", methods=["GET"])
@app_authorization(
    allowed_roles=["admin", "data_provider"],
    record_authorization={
        "entity": "Submission",
        "entity_id_key": "sub_id",
        "entity_ac_attribute": "id",
    },
)
def dataset_link(dataset_id):
    if not request.method == "GET":
        return "", 405

    if lft.client is None:
        app.logger.warning("LFT client is not initialized. Skipping LFT link creation.")
        return render_template("submission/_lft_link_content.html", link=None)

    dataset = SubmissionDataset.query.get_or_404(dataset_id)
    submission = Submission.query.get_or_404(dataset.submission_id)
    if submission.current_status != SubmissionStatusEnum.completed:
        app.logger.info(f"Submission {submission.id} is not in completed state.")
        return render_template("submission/_lft_link_content.html", link=None)

    try:
        link = lft.get_or_create_link(dataset=dataset, sub=submission.ref_name)
        app.logger.info(
            f"Created LFT link for dataset {dataset.id}: {link.absolute_url}"
        )
        return render_template("submission/_lft_link_content.html", link=link)
    except Exception as e:
        app.logger.error(
            f"Failed to create LFT link for dataset {dataset.id}: {str(e)}"
        )
        return render_template("submission/_lft_link_content.html", link=None)
