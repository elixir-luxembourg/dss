from elixir_dcp import db
from elixir_dcp.exceptions import RecordLifecycleException
import enum
from datetime import datetime


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


class SubmissionStatusEnum(enum.Enum):
    draft = 'draft'
    in_progress = 'in_progress'
    completed = 'completed'
    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)
    description = db.Column(db.String(650))
    created_on = db.Column(db.Date, nullable=False)
    current_status = db.Column(db.Enum(SubmissionStatusEnum), nullable=False, default=SubmissionStatusEnum.draft)
    contacts = db.relationship("SubmissionContact", cascade="all, delete-orphan")
    attachments = db.relationship("SubmissionAttachment", cascade="all, delete-orphan")
    dishes = db.relationship("SubmissionStudyDish", cascade="all, delete-orphan")
    use_conditions = db.relationship("SubmissionUseConditionGroup", cascade="all, delete-orphan")

    def deleteable(self):
        return self.current_status == SubmissionStatusEnum.draft

    def shareable(self):
        return self.current_status is not SubmissionStatusEnum.completed


class SubmissionContact(db.Model):
    __tablename__ = 'submission_contacts'

    id = db.Column(db.Integer, primary_key=True)
    is_primary = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('contact_types.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'),  nullable=False)
    contact_category = db.relationship('ContactType')

    def fullname(self):
        return self.name + " " + self.surname.upper()


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

    def special_subjects_status(self):
        if self.subjects_unable_to_consent or self.subjects_vulnerable or self.subjects_minors:
            return "YES"
        else:
            return "NO"


class SubmissionAccess(db.Model):

    __tablename__ = 'submission_access'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    access_granted_on = db.Column(db.DateTime, nullable=False)


def delete_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    if submission.deleteable():
        db.session.delete(submission)
        db.session.commit()
        return True
    else:
        raise RecordLifecycleException("Submission cannot be deleted")


def share_submission(submission_id, user_id):
    submission = Submission.query.get_or_404(submission_id)

    if submission.shareable():

        existing_share = SubmissionAccess.query.filter_by(submission_id=submission_id, user_id=user_id).\
            one_or_none()

        if existing_share is not None:
            existing_share.user_id = user_id
            existing_share.access_granted_on = datetime.now()
            db.session.add(existing_share)
            db.session.commit()
        else:
            submission.current_status = SubmissionStatusEnum.in_progress
            db.session.add(submission)

            share = SubmissionAccess()
            share.submission_id = submission_id
            share.user_id = user_id
            share.access_granted_on = datetime.now()
            db.session.add(share)
            db.session.commit()

    else:
        raise RecordLifecycleException("Submission cannot be shared")
