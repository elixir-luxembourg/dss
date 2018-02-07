from sqlalchemy import Sequence

from elixir_dcp import db, app
from elixir_dcp.exceptions import RecordLifecycleException
import enum
from datetime import datetime

import sys

class ContactType(db.Model):
    __tablename__ = 'contact_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


class GA4GHCodes(db.Model):
    __tablename__ = 'ga4gh_codes'

    code = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, unique=True, nullable=False)


class DataSizeCategory(db.Model):
    __tablename__ = 'data_size_category'

    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class SubmissionAttachment(db.Model):
    __tablename__ = 'submission_attachments'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String, nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    server_path = db.Column(db.String, nullable=False)
    file_names = db.Column(db.String, nullable=False)


class DeIdentificationTypeEnum(enum.Enum):
    a = 'anonymized'
    p = 'pseudonymized'
    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class ConsentStatusEnum(enum.Enum):
    htr = 'heterogeneous'
    hmg = 'homogeneous'
    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]





def transition_0_to_1():
    app.logger.info(" Debug in P1")

def transition_1_to_2():
    app.logger.info(" Debug in P2")

def transition_2_to_3():
    app.logger.info(" Debug in P3")

def transition_3_to_4():
    app.logger.info(" Debug in P4")


class SubmissionStatusEnum(enum.Enum):
    draft = 'Draft'
    in_progress_metadata = 'Study Registration'
    in_progress_data = 'Upload'
    completed = 'Completed'
    archived = 'Archived'

    def next_state(self):
        return {SubmissionStatusEnum.draft:SubmissionStatusEnum.in_progress_metadata,
                SubmissionStatusEnum.in_progress_metadata:SubmissionStatusEnum.in_progress_data,
                SubmissionStatusEnum.in_progress_data:SubmissionStatusEnum.completed,
                SubmissionStatusEnum.completed:SubmissionStatusEnum.archived}.get(self)

    def prev_state(self):
        return {SubmissionStatusEnum.completed:SubmissionStatusEnum.in_progress_data,
                SubmissionStatusEnum.in_progress_data:SubmissionStatusEnum.in_progress_metadata,
                SubmissionStatusEnum.in_progress_metadata:SubmissionStatusEnum.draft}.get(self)

    def step_num(self):
        return {SubmissionStatusEnum.draft:0,
                SubmissionStatusEnum.in_progress_metadata:1,
                SubmissionStatusEnum.in_progress_data:2,
                SubmissionStatusEnum.completed:3,
                SubmissionStatusEnum.archived:4}.get(self)



    def get_transition_handler(self):
        return {SubmissionStatusEnum.draft:transition_0_to_1,
                SubmissionStatusEnum.in_progress_metadata:transition_1_to_2,
                SubmissionStatusEnum.in_progress_data:transition_2_to_3,
                SubmissionStatusEnum.completed:transition_3_to_4}.get(self)


def uniqid():
    from time import time
    return hex(int(time()*10000000))[2:]


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, Sequence('submission_id_seq'), primary_key=True)
    ref_name = db.Column(db.String(45), index=True, unique=True, nullable=False, default=uniqid())
    title = db.Column(db.String(75))
    created_on = db.Column(db.Date, nullable=False)
    provider_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    provider_user = db.relationship('User')
    current_status = db.Column(db.Enum(SubmissionStatusEnum), nullable=False, default=SubmissionStatusEnum.draft)
    contacts = db.relationship("SubmissionContact", cascade="all, delete-orphan")
    attachments = db.relationship("SubmissionAttachment", cascade="all, delete-orphan")
    dishes = db.relationship("SubmissionStudyDish", cascade="all, delete-orphan")
    use_conditions = db.relationship("SubmissionUseConditionGroup", cascade="all, delete-orphan")
    uploadinfos = db.relationship("SubmissionUploadInfo", cascade="all, delete-orphan")

    def is_shareable(self):
        return ((self.current_status is not SubmissionStatusEnum.completed)
                & (self.current_status is not SubmissionStatusEnum.archived))


class SubmissionContact(db.Model):
    __tablename__ = 'submission_contacts'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'),  nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('contact_types.id'), nullable=False)
    contact_category = db.relationship('ContactType')

    def fullname(self):
        return self.name + " " + self.surname.upper()


class SubmissionUploadInfo(db.Model):
    __tablename__ = 'submission_upload_info'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'),  nullable=False)
    file_name = db.Column(db.String(45), nullable=False)
    md5_checksum_at_provider = db.Column(db.String(32), nullable=False)


class DUCCodeInstance(db.Model):

    __tablename__ = 'duc_code_instances'

    id = db.Column(db.Integer, primary_key=True)
    ga4gh_code = db.Column(db.String, db.ForeignKey('ga4gh_codes.code'), nullable=False)
    note = db.Column(db.String(150))
    duc_group_id = db.Column(db.Integer, db.ForeignKey('consent_groups.id'), nullable=False)
    duc_group = db.relationship("SubmissionUseConditionGroup", back_populates="duc_codes")


class SubmissionUseConditionGroup(db.Model):

    __tablename__ = 'consent_groups'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    group_name = db.Column(db.String, nullable=False)
    duc_codes = db.relationship("DUCCodeInstance", back_populates="duc_group",  cascade="all, delete-orphan")

    def duc_codes_display(self):
        result = ""
        index = 0
        for duc_code in self.duc_codes:
            result += ("" if index == 0 else ", ")+duc_code.ga4gh_code
            index += 1

        return result

class SubmissionStudyDish(db.Model):
    __tablename__ = 'submission_dishes'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    study_name = db.Column(db.String, nullable=False)
    joint_providers = db.Column(db.Boolean, default=False, nullable=False)
    estimate_data_size = db.Column(db.Integer, db.ForeignKey('data_size_category.code'), nullable=False)

    # Ethics
    ethics_approval_exists = db.Column(db.Boolean, nullable=False, default=False)
    subjects_minors = db.Column(db.Boolean, nullable=False, default=False)
    subjects_vulnerable = db.Column(db.Boolean, nullable=False, default=False)
    subjects_unable_to_consent = db.Column(db.Boolean, nullable=False, default=False)

    # Data Protection
    consent_status = db.Column(db.Enum(ConsentStatusEnum), nullable=False, default=ConsentStatusEnum.hmg)
    de_identification_type = db.Column(db.Enum(DeIdentificationTypeEnum), nullable=False,
                                       default=DeIdentificationTypeEnum.p)
    storage_end_date = db.Column(db.Date, nullable=True)
    embargo_end_date = db.Column(db.Date, nullable=True)

    def special_subjects_status_display(self):
        if self.subjects_unable_to_consent or self.subjects_vulnerable or self.subjects_minors:
            return "YES"
        else:
            return "NO"


def delete_sub(submission_id):
    submission = Submission.query.one_or_none()
    if (submission is not None) & (submission.current_status == SubmissionStatusEnum.draft):
        db.session.delete(submission)
        db.session.commit()
        return True
    else:
        raise RecordLifecycleException("Submission cannot be deleted")


def share_sub(submission, provider_user):
    if ((submission is not None) & submission.is_shareable()):

        submission.provider_user_id = provider_user.id
        db.session.add(submission)
        db.session.commit()

        if submission.current_status is SubmissionStatusEnum.draft:
            return steer_sub(submission)
        else:
            return submission

    else:
        raise RecordLifecycleException("Submission cannot be shared")




def steer_sub(submission):
    try:
        submission.current_status.get_transition_handler()()
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

    else:
        raise RecordLifecycleException("Submission status cannot be changed")


def create_sub(title):
    new_submission = Submission()
    new_submission.title = title
    new_submission.created_on = datetime.today()
    db.session.add(new_submission)
    db.session.flush()
    new_submission.ref_name =  "ELX_LU_SUB-{}".format(new_submission.id)
    db.session.commit()
    return new_submission

