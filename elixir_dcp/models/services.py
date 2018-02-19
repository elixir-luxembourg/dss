from elixir_dcp.models.submission import Submission, SubmissionStatusEnum, SubmissionAccess
from elixir_dcp.models.security import User, Role, UsersRoles
from elixir_dcp.exceptions import RecordLifecycleException, RecordNotExistsException
from elixir_dcp import db, app
from datetime import datetime
from sqlalchemy import and_
import sys


def delete_sub(submission_id):
    submission = Submission.query.filter_by(submission_id=submission_id).one_or_none()
    if submission.is_deletable():
        db.session.delete(submission)
        db.session.commit()
        return True
    else:
        raise RecordLifecycleException("Submission cannot be deleted")


def has_access(user_id, submission_id):
    access = SubmissionAccess.query.filter_by(submission_id=submission_id, user_id=user_id).one_or_none()
    if access is not None:
        return True
    else:
        return False


def steer_sub(submission_id):
    try:
        submission = Submission.query.get_or_404(submission_id)
        submission.current_status.get_steer_handler()()
        new_state = submission.current_status.next_state()
        submission.current_status = new_state
        db.session.add(submission)
        db.session.commit()
        return submission
    except:
        app.logger.error(sys.exc_info()[0])
        #TODO Better handle the exception here!
        raise RecordLifecycleException("Submission cannot be transitioned to the next state!")


def revert_sub(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    new_state = submission.current_status.prev_state()
    if new_state is not None:
        submission.current_status = new_state
        db.session.add(submission)
        db.session.commit()
        return submission
    else:
        raise RecordLifecycleException("Submission cannot be reverted to its previous state!")


def create_sub(title):
    new_submission = Submission()
    new_submission.title = title
    new_submission.created_on = datetime.today()
    db.session.add(new_submission)
    db.session.flush()
    new_submission.ref_name = "ELX_LU_SUB-{}".format(new_submission.id)
    db.session.commit()
    return new_submission


def share_sub(submission_id, shared_user_ids):
    submission = Submission.query.filter_by(id=submission_id).one_or_none()
    if submission.is_shareable():
        for user_id in shared_user_ids:
            if not has_access(user_id, submission_id):
                new_access = SubmissionAccess()
                new_access.submission_id = submission_id
                new_access.user_id = user_id
                new_access.access_granted_on = datetime.now()
                db.session.add(new_access)
                ##SEND the email
        revoked_acesses = db.session.query(SubmissionAccess).filter(and_(SubmissionAccess.submission_id == submission_id,
                                                                         SubmissionAccess.user_id.notin_(shared_user_ids)))
        if revoked_acesses is not None:
            for rev_acc in revoked_acesses:
                db.session.delete(rev_acc)
        db.session.commit()
    else:
        raise RecordLifecycleException("Submission cannot be shared.")


def get_submissions_shared_with_user(user_id):

    submission_ids = SubmissionAccess.query(SubmissionAccess.submission_id).filter_by(user_id=user_id)
    return Submission.query.filter_by(Submission.id.in_(submission_ids), Submission.current_status.in_(
        [SubmissionStatusEnum.in_progress_metadata, SubmissionStatusEnum.in_progress_data]))


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


def register_new_user(user: User):

    user.active_user = True
    db.session.add(user)
    db.session.commit()
    return user






