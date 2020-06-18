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


def export_submission(sub: Submission):
    sub_info = {}

    sub_info['elu_accession'] = sub.ref_name
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

    sub_info['datadecs'] = export_datadecs(sub)

    sub_info['attachments'] = export_attachment_info(sub)

    return sub_info


def export_datadecs(sub: Submission):
    datadec_list = []
    attrs_to_keep = [
        'title',
        'has_samples',
        'samples_notes',
        'restriction_rs',
        'restriction_rs_notes',
        'restriction_gs',
        'restriction_gs_notes',
        'restriction_us',
        'restriction_us_notes',
        'restriction_pub',
        'restriction_pub_notes',
        'restriction_rtn',
        'restriction_rtn_notes',
        'restriction_ip',
        'restriction_ip_notes',
        'restriction_ps',
        'restriction_ps_notes',
        "has_special_subjects",
        "special_subjects_notes",
        'restriction_other_notes',
        'access_form_required',
    ]

    for datadec in sub.datadecs:
        datadec_info = {}
        for attr in attrs_to_keep:
            datadec_info[attr] = getattr(datadec, attr)

        datadec_info['source_study'] = datadec.study.name
        datadec_info['legal_basis_data_collection_std'] = datadec.legal_basis_collection_std.label
        datadec_info['legal_basis_data_sharing_std'] = datadec.legal_basis_sharing_std.label
        datadec_info['legal_basis_data_collection_spec'] = datadec.legal_basis_collection_std.label
        datadec_info['legal_basis_data_sharing_spec'] = datadec.legal_basis_sharing_std.label
        datadec_info['legal_basis_notes'] = datadec.legal_basis_notes

        datadec_info['sci_datatypes'] = datadec.sci_data_type_names()
        datadec_info['gdpr_datatypes'] = datadec.gdpr_data_type_names()
        datadec_info['gdpr_datatypes_notes'] = datadec.gdpr_datatypes_notes

        if datadec.sci_datatypes_notes:
            datadec_info['sci_datatypes_notes'] = datadec.sci_datatypes_notes
        datadec_info[
            'has_special_subjects'] = datadec.has_special_subjects

        datadec_info['special_subject_notes'] = datadec.special_subjects_notes

        datadec_info['consent_status'] = datadec.consent_status.label.lower()
        if datadec.consent_notes: datadec_info['consent_notes'] = datadec.consent_notes
        datadec_info['de_identification'] = datadec.de_identification_type.label.lower()
        datadec_info['subject_categories'] = datadec.subject_category.label.lower()
        # use_restrictions = []
        # for duc_instance in datadec.duc_codes:
        #     use_restrictions.append({'ga4gh_code': duc_instance.ga4gh_code,
        #                              'note': duc_instance.note})
        # if use_restrictions:
        #     datadec_info['use_restrictions'] = use_restrictions
        datadec_list.append(datadec_info)
    return datadec_list


def export_attachment_info(sub: Submission):
    attachment_list = []
    for att in sub.attachments:
        att_info = {}
        att_info['description'] = att.note
        files_list = []
        names = att.file_names.strip(' \t\n\r').split(" ")
        for name in names:
            files_list.append({"$ref": os.path.join(att.folder_name, name)})
        att_info['files'] = files_list
        attachment_list.append(att_info)
    return attachment_list


def export_studies(sub: Submission):
    study_list = []
    for stdy in sub.studies:
        study_info = {}
        study_info['title'] = stdy.name
        study_info['description'] = stdy.description
        study_info['ethics_approval_no'] = stdy.ethics_approval_no
        study_info['ethics_approval_exists'] = stdy.ethics_approval_exists
        study_info['study_types'] = stdy.study_feature_names()
        contacts = []
        for contact in stdy.study_contacts:
            contact_info = {}
            contact_info['first_name'] = contact.firstname
            contact_info['last_name'] = contact.lastname
            contact_info['role'] = contact.contact_category.name
            contact_info['email'] = contact.email
            contact_info['address'] = contact.address
            contact_info['institution'] = sub.institution_accession
            contacts.append(contact_info)
        study_info['contacts'] = contacts
        study_list.append(study_info)
    return study_list


def schedule_submission_export():
    app.logger.info("export schedule started")
    all_submissions = Submission.query.filter_by(current_status=SubmissionStatusEnum.completed, exported=False)
    app.logger.info("schedule_submission_export")
    if all_submissions.count() > 0:
        for submission in all_submissions:
            export_directory = os.path.join(app.config.get('SUBMISSION_EXPORT_FOLDER'), submission.ref_name)
            app.logger.info(export_directory)
            if not os.path.exists(export_directory):
                os.makedirs(export_directory)
            submission_exportfile = open(os.path.join(export_directory, submission.ref_name + ".json"), "w")
            submission_exportfile.write(json.dumps([export_submission(submission)], indent=4))
            # submission_attachments = SubmissionAttachment.query.filter_by(submission_id=submission.id).all()
            # for attachment in submission_attachments:
            #
            #     try:
            #         path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], attachment.folder_name)
            #         attachment_folder_name = os.path.join(export_directory, attachment.folder_name)
            #         if not os.path.exists(attachment_folder_name):
            #             os.makedirs(attachment_folder_name)
            #         attachment_file = os.path.join(path_on_server, attachment.file_names)
            #         os.popen('cp ' + attachment_file + ' ' + attachment_folder_name)
            #
            #     except OSError as err:
            #         err.extend(err.args[0])

            # shutil.make_archive(export_directory, 'zip', export_directory)
            # app.logger.info("Created zip file")

            submission.exported = True
            db.session.add(submission)
            db.session.commit()


