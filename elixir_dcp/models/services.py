from elixir_dcp.models.submission import Submission, SubmissionStatusEnum, SubmissionAccess, GA4GHCodes
from elixir_dcp.models.security import User, Role, UsersRoles
from elixir_dcp.controllers.utils import equal_long_strings
from elixir_dcp.exceptions import RecordLifecycleException, RecordNotExistsException
from elixir_dcp import db, app, mail
from datetime import datetime
from flask import flash, render_template
from sqlalchemy import and_
from threading import Thread
from flask_mail import Message


def delete_sub(submission_id: str):
    submission = Submission.query.filter_by(submission_id=submission_id).one_or_none()
    if submission.is_deletable():
        db.session.delete(submission)
        db.session.commit()
        return True
    else:
        raise RecordLifecycleException("Submission cannot be deleted")


def has_access(user_id: str, submission_id: str):
    access = SubmissionAccess.query.filter_by(submission_id=submission_id, user_id=user_id).one_or_none()
    if access is not None:
        return True
    else:
        return False


def steer_sub(submission_id: str):
    submission = Submission.query.get_or_404(submission_id)
    target_state = submission.current_status.next_state()
    if target_state is None:
        raise RecordLifecycleException("Submission cannot be steered to the next state!")
    elif target_state == SubmissionStatusEnum.in_progress_metadata and not submission.has_providers():
        flash('You need to specify a data provider user before initiating a submission', 'error')
        raise RecordLifecycleException("Submission cannot be steered to the next state!")
    else:
        if target_state == SubmissionStatusEnum.in_progress_metadata:
            send_submission_steer_step1_notification(submission)
        elif target_state == SubmissionStatusEnum.in_progress_data:
            send_submission_steer_step2_notification(submission)
        elif target_state == SubmissionStatusEnum.completed:
            send_submission_steer_step3_notification(submission)
        submission.current_status = target_state
        db.session.add(submission)
        db.session.commit()
    return submission


def revert_sub(submission_id: str):
    submission = Submission.query.get_or_404(submission_id)
    new_state = submission.current_status.prev_state()
    if new_state is not None:
        submission.current_status = new_state
        db.session.add(submission)
        db.session.commit()
        return submission
    else:
        raise RecordLifecycleException("Submission cannot be reverted to its previous state!")


def create_sub(title: str):
    new_submission = Submission()
    new_submission.title = title
    new_submission.created_on = datetime.today()
    db.session.add(new_submission)
    db.session.flush()
    new_submission.ref_name = "ELX_LU_SUB-{}".format(new_submission.id)
    db.session.commit()
    return new_submission


def get_in_progress_submissions_shared_with_user(user_id: str):
    submission_accesses = SubmissionAccess.query.filter_by(user_id=user_id)
    submission_ids = []
    for access in submission_accesses:
        submission_ids.append(access.submission_id)

    return Submission.query.filter(and_(Submission.id.in_(submission_ids), Submission.current_status.in_(
        [SubmissionStatusEnum.in_progress_metadata, SubmissionStatusEnum.in_progress_data])))


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


def register_new_user(user: User) -> User:
    user.active_user = True
    db.session.add(user)
    db.session.commit()
    return user


def send_submission_steer_step1_notification(submission: Submission):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    send_email("Submission [%s] initiated" % submission.ref_name,
               'noreply@elixir-luxembourg.org',
               recipients,
               render_template("email/submission_steer1.txt", submission=submission),
               render_template("email/submission_steer1.html", submission=submission))


def send_submission_steer_step2_notification(submission: Submission):
    send_email("Submission [%s] steered to Data Upload, needs Upload Instructions" % submission.ref_name,
               'noreply@elixir-luxembourg.org',
               app.config.get('DATA_STEWARDS_MAILS'),
               render_template("email/submission_steer2.txt", submission=submission),
               render_template("email/submission_steer2.html", submission=submission))


def send_submission_steer_step3_notification(submission: Submission):
    send_email("Submission [%s] steered to Completion, needs Verification" % submission.ref_name,
               'noreply@elixir-luxembourg.org',
               app.config.get('DATA_STEWARDS_MAILS'),
               render_template("email/submission_steer3.txt", submission=submission),
               render_template("email/submission_steer3.html", submission=submission))


def send_upload_instruction_notification(submission: Submission):
    recipients = []
    for access in submission.submission_accesses:
        recipients.append(access.user.email)
    send_email("Submission [%s] has new upload instructions" % submission.ref_name,
               'noreply@elixir-luxembourg.org',
               recipients,
               render_template("email/upload_instructions.txt", submission=submission),
               render_template("email/upload_instructions.html", submission=submission))


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def update_submission_basic_info(submission: Submission, **kwargs):
    new_instructions = kwargs.pop('upload_instructions')
    new_title = kwargs.pop('title')
    new_shared_user_ids = kwargs.pop('provider_user_ids')

    any_instruction_changes = not equal_long_strings(submission.upload_instructions, new_instructions)

    submission.title = new_title
    submission.upload_instructions = new_instructions
    db.session.add(submission)
    db.session.commit()

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
                flash('Submission shared with %s' % usr.display_name(), 'info')

    revoked_acesses = db.session.query(SubmissionAccess).filter(and_(SubmissionAccess.submission_id == submission.id,
                                                                     SubmissionAccess.user_id.notin_(
                                                                         new_shared_user_ids)))
    if revoked_acesses is not None:
        for rev_acc in revoked_acesses:
            db.session.delete(rev_acc)
            db.session.commit()

    if any_instruction_changes and submission.is_in_progress():
        send_upload_instruction_notification(submission)
        flash('Data Providers are notified of upload instructions', 'info')


def update_user_info(usr: User, **kwargs):

    usr.first_name = kwargs.pop('first_name')
    usr.last_name = kwargs.pop('last_name')
    usr.institution = kwargs.pop('institution')
    usr.email = kwargs.pop('email')
    usr.addr_line1 = kwargs.pop('addr_line1')
    usr.addr_line2 = kwargs.pop('addr_line2')
    usr.phone_no = kwargs.pop('phone_no')

    new_assigned_role_ids = set(kwargs.pop('assigned_role_ids'))
    old_assigned_role_ids = set(usr.assigned_role_ids())
    to_be_added = new_assigned_role_ids - old_assigned_role_ids
    to_be_removed = old_assigned_role_ids - new_assigned_role_ids

    for role_id in to_be_added:
        usr.assigned_roles.append(Role.query.get_or_404(role_id))

    for role_id in to_be_removed:
        usr.assigned_roles.remove(Role.query.get_or_404(role_id))

    db.session.add(usr)
    db.session.commit()
