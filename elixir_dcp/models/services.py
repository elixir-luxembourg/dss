import os

from elixir_dcp.models.submission import Submission, SubmissionStatusEnum, SubmissionAccess, \
    EmailNotification, SubmissionMessage
from elixir_dcp.models.security import User, Role, UsersRoles
from elixir_dcp.exceptions import RecordLifecycleException, RecordNotExistsException
from elixir_dcp import db, app, mail
from datetime import datetime
from flask import flash, render_template
from flask_login import current_user
from sqlalchemy import and_
from threading import Thread
from flask_mail import Message
import json



def delete_sub(submission_id: str):
    submission = Submission.query.filter_by(id=submission_id).one_or_none()
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
            submission.finalised_on = datetime.today()
            send_submission_steer_step2_notification(submission)
            flash(
                'An upload link will be created once all information provided is checked and where required signatures are received.',
                'success')
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


def create_sub(title: str, institute_accession:str):
    new_submission = Submission()
    new_submission.title = title
    new_submission.institution_accession = institute_accession
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
    persist_and_send_notification("Submission [%s] initiated" % submission.ref_name,
                                  'noreply@uni.lu',
                                  recipients,
                                  render_template("email/submission_steer1.txt", submission=submission),
                                  render_template("email/submission_steer1.html", submission=submission))


def send_submission_steer_step2_notification(submission: Submission):
    persist_and_send_notification(
        "Submission [%s] steered to Data Upload, needs Upload Instructions" % submission.ref_name,
        'noreply@uni.lu',
        app.config.get('DATA_STEWARDS_MAILS'),
        render_template("email/submission_steer2.txt", submission=submission),
        render_template("email/submission_steer2.html", submission=submission))


def send_submission_steer_step3_notification(submission: Submission):
    persist_and_send_notification("Submission [%s] steered to Completion, needs Verification" % submission.ref_name,
                                  'noreply@uni.lu',
                                  app.config.get('DATA_STEWARDS_MAILS'),
                                  render_template("email/submission_steer3.txt", submission=submission),
                                  render_template("email/submission_steer3.html", submission=submission))


def send_new_message_notification(submission_message: SubmissionMessage):
    recipients = []
    for access in submission_message.submission.submission_accesses:
        recipients.append(access.user.email)
    recipients = recipients + app.config.get('DATA_STEWARDS_MAILS')

    persist_and_send_notification("Submission [%s] has new message" % submission_message.submission.ref_name,
                                  'noreply@uni.lu',
                                  recipients,
                                  render_template("email/submission_new_message.txt", submission=submission_message.submission),
                                  render_template("email/submission_new_message.html", submission=submission_message.submission))


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
    msg = Message(notification.subject, sender=notification.sender, recipients=json.loads(notification.recipients_json))
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

    if 'title' in kwargs:
        submission.title = kwargs.pop('title')

    if 'submission_scope_code' in kwargs:
        submission.submission_scope_code = kwargs.pop('submission_scope_code')

    if 'institution_accession' in kwargs:
        submission.institution_accession = kwargs.pop('institution_accession')

    if 'local_custodians_json' in kwargs:
        submission.local_custodians_json = kwargs.pop('local_custodians_json')

    if 'local_project_name' in kwargs:
        submission.local_project_name = kwargs.pop('local_project_name')

    db.session.add(submission)
    db.session.commit()

    if 'provider_user_ids' in kwargs:
        new_shared_user_ids = kwargs.get('provider_user_ids')
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
                        flash('Submission shared with %s' % usr.display_name(), 'info')

            revoked_acesses = db.session.query(SubmissionAccess).filter(
                and_(SubmissionAccess.submission_id == submission.id,
                     SubmissionAccess.user_id.notin_(
                         new_shared_user_ids)))
            if revoked_acesses is not None:
                for rev_acc in revoked_acesses:
                    db.session.delete(rev_acc)
                    db.session.commit()



def update_user_info(usr: User, **kwargs):
    if 'first_name' in kwargs:
        usr.first_name = kwargs.pop('first_name')
    if 'last_name' in kwargs:
        usr.last_name = kwargs.pop('last_name')
    if 'institution' in kwargs:
        usr.institution_accession = kwargs.pop('institution')
    if 'institution_division' in kwargs:
        usr.institution_division = kwargs.pop('institution_division')
    if 'email' in kwargs:
        usr.email = kwargs.pop('email')
    if 'addr_line1' in kwargs:
        usr.addr_line1 = kwargs.pop('addr_line1')
    if 'addr_line2' in kwargs:
        usr.addr_line2 = kwargs.pop('addr_line2')
    if 'phone_no' in kwargs:
        usr.phone_no = kwargs.pop('phone_no')

    if 'assigned_role_ids' in kwargs:
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

'''
def export_submission(sub: Submission):
    sub_info = {}

    #sub_info['elu_accession'] = sub.ref_name
    sub_info['source'] = 'https://elixir-dcp.lcsb.uni.lu/'
    sub_info['name'] = sub.ref_name
    sub_info['title'] = sub.title
    sub_info['submission_scope_code'] = sub.submission_scope_code
    sub_info['submitting_institution_accession'] = sub.institution_accession
    sub_info['submitting_institution_name'] = sub.provider_institute_name()
    sub_info['submitting_institution_address'] = sub.provider_institute_address()

    sub_info['created_on'] = sub.created_on.strftime("%Y-%m-%d")
    if sub.finalised_on:
        sub_info['finalised_on'] = sub.finalised_on.strftime("%Y-%m-%d")
    sub_info['submission_scope_code'] = sub.submission_scope.code
    sub_info['submission_scope_label'] = sub.submission_scope.label
    if sub.local_custodians_json:
        sub_info['local_custodians'] = json.loads(sub.local_custodians_json)
    if sub.local_project_name:
        sub_info['local_project'] = sub.local_project_name

    submitters = []
    for access in sub.submission_accesses:
        provider_info = {}
        provider_info['institution'] = access.user.institution_accession
        provider_info['email'] = access.user.email
        provider_info['first_name'] = access.user.first_name
        provider_info['last_name'] = access.user.last_name
        provider_info['phone_no'] = access.user.phone_no

        if access.user.addr_line1 or access.user.addr_line2:
            provider_info['address'] = (access.user.addr_line1 or '') + ' ' + (access.user.addr_line2 or '')

        provider_info['role'] = 'Data_Manager'
        submitters.append(provider_info)

    sub_info['data_providers'] = submitters

    sub_info['studies'] = export_studies(sub)

    sub_info['data_declarations'] = export_datadecs(sub)

    sub_info['attachments'] = export_attachment_info(sub)

    return sub_info
'''
