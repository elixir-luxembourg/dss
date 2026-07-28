import json
from datetime import datetime, timezone
from threading import Thread

from flask import flash, render_template
from flask_mail import Message
from sqlalchemy import and_, select

from elixir_dss import app, db, mail, lft
from elixir_dss.exceptions import RecordLifecycleException, RecordNotExistsException
from elixir_dss.models.security import Role, User, UsersRoles, normalize_email
from elixir_dss.models.submission import (
    EmailNotification,
    Submission,
    SubmissionAccess,
    SubmissionMessage,
    SubmissionStatusEnum,
    Contact,
    SubmissionStudy,
    SubmissionDataset,
)

CANNOT_STEER_MSG = "Submission cannot be steered to the next state!"


def delete_sub(submission_id: str):
    submission = Submission.query.filter_by(id=submission_id).one_or_none()
    if submission.is_deletable():
        db.session.delete(submission)
        db.session.commit()
        return True
    else:
        raise RecordLifecycleException("Submission cannot be deleted")


def has_access(user_id: str, submission_id: str):
    access = SubmissionAccess.query.filter_by(
        submission_id=submission_id, user_id=user_id
    ).one_or_none()
    if access is not None:
        return True
    else:
        return False


def _validate_steer(submission, target_state):
    if target_state is None:
        raise RecordLifecycleException(CANNOT_STEER_MSG)

    if (
        submission.current_status == SubmissionStatusEnum.draft
        and not submission.has_providers()
    ):
        flash(
            "You need to specify a data provider user before initiating a submission",
            "error",
        )
        raise RecordLifecycleException(CANNOT_STEER_MSG)

    if submission.current_status == SubmissionStatusEnum.metadata_submission and (
        not submission.has_study() or not submission.has_dataset()
    ):
        flash(
            "You need to add at least one study and one dataset before proceeding to the next step.",
            "error",
        )
        raise RecordLifecycleException(CANNOT_STEER_MSG)


def _apply_steer_side_effects(submission, target_state):
    if target_state == SubmissionStatusEnum.metadata_submission:
        send_submission_steer_step1_notification(submission)

    elif target_state == SubmissionStatusEnum.metadata_approval:
        send_metadata_approval_request_notification(submission)

    elif target_state == SubmissionStatusEnum.data_upload:
        submission.finalised_on = datetime.today()
        send_submission_steer_step2_notification(submission)
        flash(
            "An upload link will be created once all information provided is checked and where required signatures are received.",
            "success",
        )

    elif target_state == SubmissionStatusEnum.data_approval:
        if lft.client:
            try:
                lft.invalidate_links_for_submission(submission.id, delete_share=False)
            except Exception as e:
                app.logger.error(f"LFT invalidate failed for ds {submission.id}: {e}")
        send_data_approval_request_notification(submission)

    elif target_state == SubmissionStatusEnum.completed:
        send_submission_steer_step3_notification(submission)


def steer_sub(submission_id: str):
    submission = db.get_or_404(Submission, submission_id)
    target_state = submission.current_status.next_state()

    _validate_steer(submission, target_state)
    _apply_steer_side_effects(submission, target_state)

    submission.current_status = target_state
    db.session.add(submission)
    db.session.commit()

    return submission


def revert_sub(submission_id: str):
    submission = db.get_or_404(Submission, submission_id)
    new_state = submission.current_status.prev_state()
    if new_state is not None:
        submission.current_status = new_state
        db.session.add(submission)
        db.session.commit()
        return submission
    else:
        raise RecordLifecycleException(
            "Submission cannot be reverted to its previous state!"
        )


def create_sub(institute_accession: str):
    new_submission = Submission()
    new_submission.institution_accession = institute_accession
    new_submission.created_on = datetime.today()
    db.session.add(new_submission)
    db.session.flush()
    new_submission.ref_name = f"ELX_LU_SUB-{new_submission.id}"
    db.session.commit()
    return new_submission


def get_in_progress_submissions_shared_with_user(user_id: str):
    submission_accesses = SubmissionAccess.query.filter_by(user_id=user_id)
    submission_ids = []
    for access in submission_accesses:
        submission_ids.append(access.submission_id)

    return Submission.query.filter(Submission.id.in_(submission_ids))


def assign_role_to_user(user: User, role_name: str):
    role = Role.query.filter_by(name=role_name).one_or_none()
    if role:
        if not user.has_role_from([role_name]):
            new_role_assignment = UsersRoles()
            new_role_assignment.user_id = user.id
            new_role_assignment.role_id = role.id
            new_role_assignment.assigned_on = datetime.now()
            db.session.add(new_role_assignment)
            db.session.commit()
    else:
        raise RecordNotExistsException("Role with specified name does not exist.")


def get_active_users():
    return User.query.filter_by(active_user=True)


def deactivate_user(user: User):
    user.active_user = False
    db.session.add(user)
    db.session.commit()
    return user


def register_new_user(user: User) -> User:
    user.active_user = True
    db.session.add(user)
    db.session.commit()
    return user


def send_submission_steer_step1_notification(submission: Submission):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    persist_and_send_notification(
        "Submission [%s] initiated" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template("email/submission_steer1.txt", submission=submission),
        render_template("email/submission_steer1.html", submission=submission),
    )


def send_submission_steer_step2_notification(submission: Submission):
    persist_and_send_notification(
        "Submission [%s] steered to Data Upload, needs Upload Instructions"
        % submission.ref_name,
        "noreply@uni.lu",
        app.config.get("DATA_STEWARDS_MAILS"),
        render_template("email/submission_steer2.txt", submission=submission),
        render_template("email/submission_steer2.html", submission=submission),
    )


def send_submission_steer_step3_notification(submission: Submission):
    persist_and_send_notification(
        "Submission [%s] steered to Completion, needs Verification"
        % submission.ref_name,
        "noreply@uni.lu",
        app.config.get("DATA_STEWARDS_MAILS"),
        render_template("email/submission_steer3.txt", submission=submission),
        render_template("email/submission_steer3.html", submission=submission),
    )


def send_new_message_notification(submission_message: SubmissionMessage):
    recipients = []
    for access in submission_message.submission.submission_accesses:
        recipients.append(access.user.email)
    recipients = recipients + app.config.get("DATA_STEWARDS_MAILS")

    persist_and_send_notification(
        "Submission [%s] has new message" % submission_message.submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_new_message.txt", submission=submission_message.submission
        ),
        render_template(
            "email/submission_new_message.html",
            submission=submission_message.submission,
        ),
    )


def send_metadata_approval_request_notification(submission: Submission):
    persist_and_send_notification(
        "Submission [%s] ready for metadata approval" % submission.ref_name,
        "noreply@uni.lu",
        app.config.get("DATA_STEWARDS_MAILS"),
        render_template(
            "email/submission_metadata_approval_request.txt", submission=submission
        ),
        render_template(
            "email/submission_metadata_approval_request.html", submission=submission
        ),
    )


def send_metadata_approved_notification(submission: Submission, feedback=None):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    persist_and_send_notification(
        "Submission [%s] metadata approved" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_metadata_approved.txt",
            submission=submission,
            feedback=feedback,
        ),
        render_template(
            "email/submission_metadata_approved.html",
            submission=submission,
            feedback=feedback,
        ),
    )


def send_metadata_rejected_notification(submission: Submission, feedback):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    persist_and_send_notification(
        "Submission [%s] metadata requires changes" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_metadata_rejected.txt",
            submission=submission,
            feedback=feedback,
        ),
        render_template(
            "email/submission_metadata_rejected.html",
            submission=submission,
            feedback=feedback,
        ),
    )


def send_data_approval_request_notification(submission: Submission):
    persist_and_send_notification(
        "Submission [%s] ready for data approval" % submission.ref_name,
        "noreply@uni.lu",
        app.config.get("DATA_STEWARDS_MAILS"),
        render_template(
            "email/submission_data_approval_request.txt", submission=submission
        ),
        render_template(
            "email/submission_data_approval_request.html", submission=submission
        ),
    )


def send_data_approved_notification(submission: Submission, feedback=None):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    persist_and_send_notification(
        "Submission [%s] data upload approved" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_data_approved.txt",
            submission=submission,
            feedback=feedback,
        ),
        render_template(
            "email/submission_data_approved.html",
            submission=submission,
            feedback=feedback,
        ),
    )


def send_data_rejected_notification(submission: Submission, feedback):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    persist_and_send_notification(
        "Submission [%s] data upload requires changes" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_data_rejected.txt",
            submission=submission,
            feedback=feedback,
        ),
        render_template(
            "email/submission_data_rejected.html",
            submission=submission,
            feedback=feedback,
        ),
    )


def send_invitations(submission: Submission, users: list[User]):
    recipients = []
    for user in users:
        recipients.append(user.email)
    recipients = recipients + app.config.get("DATA_STEWARDS_MAILS")
    invitation_url = (
        f"{app.config['BASE_URL'].rstrip('/')}/submission/view/{submission.id}"
    )

    persist_and_send_notification(
        "Invitation to collaborate on Submission [%s]" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_invitation.txt",
            submission=submission,
            invitation_url=invitation_url,
        ),
        render_template(
            "email/submission_invitation.html",
            submission=submission,
            invitation_url=invitation_url,
        ),
    )


def approve_metadata(submission_id, reviewer_id, feedback=None):
    submission = db.get_or_404(Submission, submission_id)
    submission.current_status = SubmissionStatusEnum.data_upload
    db.session.add(submission)

    if feedback:
        message_text = f"Metadata approved.<br>{feedback.strip()}"
    else:
        message_text = "Metadata approved."

    message = SubmissionMessage(
        submission_id=submission_id,
        sender_user_id=reviewer_id,
        message_text=message_text,
        message_type="metadata_approval",
        created_on=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()

    send_metadata_approved_notification(submission, feedback)
    return submission


def reject_metadata(submission_id, reviewer_id, feedback):
    submission = db.get_or_404(Submission, submission_id)
    submission.current_status = SubmissionStatusEnum.metadata_submission
    db.session.add(submission)

    message_text = f"Metadata rejected.<br>{feedback.strip()}"

    message = SubmissionMessage(
        submission_id=submission_id,
        sender_user_id=reviewer_id,
        message_text=message_text,
        message_type="metadata_rejection",
        created_on=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()

    send_metadata_rejected_notification(submission, feedback)
    return submission


def approve_data(submission_id, reviewer_id, feedback=None):
    submission = db.get_or_404(Submission, submission_id)
    submission.current_status = SubmissionStatusEnum.completed
    db.session.add(submission)

    if feedback:
        message_text = f"Data approved.<br>{feedback.strip()}"
    else:
        message_text = "Data approved."

    message = SubmissionMessage(
        submission_id=submission_id,
        sender_user_id=reviewer_id,
        message_text=message_text,
        message_type="data_approval",
        created_on=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()

    send_data_approved_notification(submission, feedback)
    return submission


def reject_data(submission_id, reviewer_id, feedback):
    submission = db.get_or_404(Submission, submission_id)
    submission.current_status = SubmissionStatusEnum.data_upload
    db.session.add(submission)

    message_text = f"Data rejected.<br>{feedback.strip()}"

    message = SubmissionMessage(
        submission_id=submission_id,
        sender_user_id=reviewer_id,
        message_text=message_text,
        message_type="data_rejection",
        created_on=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()

    send_data_rejected_notification(submission, feedback)
    return submission


def persist_and_send_notification(subject, sender, recipients, text_body, html_body):
    notification = EmailNotification()
    notification.subject = subject
    notification.sender = sender
    notification.recipients_json = json.dumps(recipients)
    notification.text_body = text_body
    notification.html_body = html_body
    notification.created_on = datetime.today()
    db.session.add(notification)
    db.session.commit()
    send_email_asynch(notification)


def send_email_asynch(notification: EmailNotification):
    msg = Message(
        notification.subject,
        sender=notification.sender,
        recipients=json.loads(notification.recipients_json),
    )
    msg.body = notification.text_body
    msg.html = notification.html_body
    # if mode == 'asynch':
    thr = Thread(target=send_async_email_target, args=[app, msg])
    thr.start()
    # else:
    #     with app.app_context():
    #         mail.send(msg)


def send_async_email_target(app, msg):
    with app.app_context():
        mail.send(msg)


def update_submission_basic_info(submission: Submission, **kwargs):
    if "institution_accession" in kwargs:
        submission.institution_accession = kwargs.pop("institution_accession")

    if "local_custodians_json" in kwargs:
        submission.local_custodians_json = kwargs.pop("local_custodians_json")

    if "local_project_name" in kwargs:
        submission.local_project_name = kwargs.pop("local_project_name")

    if "submission_contacts" in kwargs:
        contacts_data = kwargs.pop("submission_contacts")
        submission.submission_contacts = []
        for contact_data in contacts_data:
            contact = Contact()
            for key, value in contact_data.items():
                setattr(contact, key, value)
            submission.submission_contacts.append(contact)

    db.session.add(submission)
    db.session.commit()

    if "provider_user_ids" in kwargs:
        new_shared_user_ids = kwargs.get("provider_user_ids")
        if new_shared_user_ids is not None:
            for user_id in new_shared_user_ids:
                if not has_access(user_id, submission.id):
                    new_access = SubmissionAccess()
                    new_access.submission_id = submission.id
                    new_access.user_id = user_id
                    new_access.access_granted_on = datetime.now()
                    db.session.add(new_access)
                    db.session.commit()

                    if submission.is_in_progress():
                        send_submission_steer_step1_notification(submission)
                        usr = User.query.filter_by(id=user_id).one_or_none()
                        flash("Submission shared with %s" % usr.display_name(), "info")

            stmt = select(SubmissionAccess).filter(
                and_(
                    SubmissionAccess.submission_id == submission.id,
                    SubmissionAccess.user_id.notin_(new_shared_user_ids),
                )
            )
            revoked_acesses = db.session.execute(stmt).scalars().all()
            if revoked_acesses is not None:
                for rev_acc in revoked_acesses:
                    db.session.delete(rev_acc)
                    db.session.commit()


def update_user_info(usr: User, **kwargs):
    if "first_name" in kwargs:
        usr.first_name = kwargs.pop("first_name")
    if "last_name" in kwargs:
        usr.last_name = kwargs.pop("last_name")
    if "institution_accession" in kwargs:
        usr.institution_accession = kwargs.pop("institution_accession")
    if "institution_division" in kwargs:
        usr.institution_division = kwargs.pop("institution_division")
    if "email" in kwargs:
        usr.email = normalize_email(kwargs.pop("email"))
    if "addr_line1" in kwargs:
        usr.addr_line1 = kwargs.pop("addr_line1")
    if "addr_line2" in kwargs:
        usr.addr_line2 = kwargs.pop("addr_line2")
    if "phone_no" in kwargs:
        usr.phone_no = kwargs.pop("phone_no")

    if "assigned_role_ids" in kwargs:
        new_assigned_role_ids = set(kwargs.pop("assigned_role_ids"))
        old_assigned_role_ids = set(usr.assigned_role_ids())
        to_be_added = new_assigned_role_ids - old_assigned_role_ids
        to_be_removed = old_assigned_role_ids - new_assigned_role_ids

        for role_id in to_be_added:
            usr.assigned_roles.append(db.get_or_404(Role, role_id))

        for role_id in to_be_removed:
            usr.assigned_roles.remove(db.get_or_404(Role, role_id))

    db.session.add(usr)
    db.session.commit()


def clone_sub(
    original_submission_id: int,
    clone_studies=True,
    clone_datasets=True,
) -> Submission:
    """
    Deep-clone a submission's metadata into a new submission.
    - new submission is set to in_progress_metadata (form-filling phase).
    - studies and data declarations are duplicated if user chooses to.
    - submission_access (users) and submission_contacts are duplicated.
    - attachments are ignored
    """
    try:
        old_sub = db.get_or_404(Submission, original_submission_id)
        new_status = SubmissionStatusEnum.metadata_submission
        if old_sub.current_status == SubmissionStatusEnum.draft:
            new_status = SubmissionStatusEnum.draft

        new_sub = Submission(
            institution_accession=old_sub.institution_accession,
            created_on=datetime.now(),
            local_custodians_json=old_sub.local_custodians_json,
            local_project_name=old_sub.local_project_name,
            current_status=new_status,
        )
        db.session.add(new_sub)
        db.session.flush()

        new_sub.ref_name = f"ELX_LU_SUB-{new_sub.id}"

        # clone contacts
        for c in old_sub.submission_contacts:
            db.session.add(
                Contact(
                    first_name=c.first_name,
                    last_name=c.last_name,
                    email=c.email,
                    institution=c.institution,
                    category_id=c.category_id,
                    is_main_contact=c.is_main_contact,
                    submission_id=new_sub.id,
                )
            )

        # clone studies if selected
        study_id_map = {}
        if clone_studies:
            old_studies = SubmissionStudy.query.filter_by(
                submission_id=old_sub.id
            ).all()
            for s in old_studies:
                new_s = s.clone(submission_id=new_sub.id)
                db.session.add(new_s)
                db.session.flush()
                study_id_map[s.id] = new_s.id

                # study contacts
                for sc in s.study_contacts:
                    db.session.add(
                        sc.clone(submission_id=new_sub.id, study_id=new_s.id)
                    )

        # clone datasets if selected
        if clone_datasets:
            old_datasets = SubmissionDataset.query.filter_by(
                submission_id=old_sub.id
            ).all()
            for d in old_datasets:
                db.session.add(
                    d.clone(
                        submission_id=new_sub.id,
                        study_id=study_id_map.get(d.study_id) if d.study_id else None,
                    )
                )

        # clone access (users)
        for access in old_sub.submission_accesses:
            if not has_access(access.user_id, new_sub.id):
                db.session.add(
                    SubmissionAccess(
                        submission_id=new_sub.id,
                        user_id=access.user_id,
                        access_granted_on=datetime.now(),
                    )
                )

        db.session.commit()

        app.logger.info(
            f"Cloned submission {old_sub.ref_name} -> {new_sub.ref_name} by user clone_sub()"
        )
        return new_sub

    except Exception as e:
        db.session.rollback()
        app.logger.error(
            f"Failed to clone submission {original_submission_id}: {str(e)}"
        )
        raise


def send_submission_cancellation_notification(
    submission: Submission, cancelled_by_user: User
):
    recipients = []

    for access in submission.submission_accesses:
        recipients.append(access.user.email)

    recipients = recipients + app.config.get("DATA_STEWARDS_MAILS", [])

    persist_and_send_notification(
        "Submission [%s] has been CANCELLED" % submission.ref_name,
        "noreply@uni.lu",
        recipients,
        render_template(
            "email/submission_cancelled.txt",
            submission=submission,
            cancelled_by_user=cancelled_by_user,
        ),
        render_template(
            "email/submission_cancelled.html",
            submission=submission,
            cancelled_by_user=cancelled_by_user,
        ),
    )


def cancel_sub(submission: Submission, reason: str, cancelled_by_user: User):
    submission.current_status = SubmissionStatusEnum.cancelled
    submission.cancellation_reason = reason
    submission.cancelled_by_user_id = cancelled_by_user.id
    submission.finalised_on = datetime.now(timezone.utc)

    # invalidate lft
    if lft.client:
        try:
            lft.invalidate_links_for_submission(submission.id, delete_share=True)
        except Exception as e:
            app.logger.error(f"LFT invalidate failed for ds {submission.id}: {e}")

    db.session.add(submission)

    message_text = f"Submission Cancelled.<br>This submission was cancelled by {cancelled_by_user.display_name()}.<br>Cancellation comment: {reason}."
    message = SubmissionMessage(
        submission_id=submission.id,
        sender_user_id=cancelled_by_user.id,
        message_text=message_text,
        message_type="submission_cancellation",
        created_on=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()

    send_submission_cancellation_notification(submission, cancelled_by_user)

    return submission


def invite_submitters(submission: Submission, contacts: list[Contact]):
    users_for_invitation = []

    for contact in contacts:
        if contact.send_invite is False:
            continue
        contact_email = normalize_email(contact.email)
        user = User.query.filter_by(email=contact_email).first()
        if not user:
            user = User(
                first_name=contact.first_name,
                last_name=contact.last_name,
                email=contact_email,
                elixir_sub_id=contact_email,
                active_user=True,
            )
            db.session.add(user)
            db.session.flush()
            assign_role_to_user(user, "user")
            access = SubmissionAccess(
                submission_id=submission.id,
                user_id=user.id,
                access_granted_on=datetime.now(),
            )
            db.session.add(access)
            users_for_invitation.append(user)

    db.session.commit()
    if users_for_invitation:
        send_invitations(submission, users_for_invitation)
