from sqlalchemy import Sequence
from elixir_dcp import db, app
import enum
import os


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
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    note = db.Column(db.String, nullable=False)
    folder_name = db.Column(db.String, nullable=False)
    file_names = db.Column(db.String, nullable=False)

    def files_urls(self):
        if self.file_names is not None:
            result = []
            names = self.file_names.strip(' \t\n\r').split(" ")
            for name in names:
                result.append(
                    (os.path.join(os.path.join(app.config.get('UPLOADS_SERVER_PATH'), self.folder_name), name), name))
                return result
        else:
            return None


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
    draft = 'Draft'
    in_progress_metadata = 'Study Registration'
    in_progress_data = 'Data Upload'
    completed = 'Completion'

    def next_state(self):
        return {self.draft: self.in_progress_metadata,
                self.in_progress_metadata: self.in_progress_data,
                self.in_progress_data: self.completed}.get(self)

    def prev_state(self):
        return {self.completed: self.in_progress_data,
                self.in_progress_data: self.in_progress_metadata,
                self.in_progress_metadata: self.draft}.get(self)

    def step_num(self):
        return {self.draft: 0,
                self.in_progress_metadata: 1,
                self.in_progress_data: 2,
                self.completed: 3}.get(self)


def uniqid():
    from time import time
    return hex(int(time() * 10000000))[2:]


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, Sequence('submission_id_seq'), primary_key=True)
    ref_name = db.Column(db.String(45), index=True, unique=True, nullable=False, default=uniqid())
    title = db.Column(db.String(75))
    created_on = db.Column(db.Date, nullable=False)
    current_status = db.Column(db.Enum(SubmissionStatusEnum), nullable=False, default=SubmissionStatusEnum.draft)
    upload_instructions = db.Column(db.String)

    submission_accesses = db.relationship('SubmissionAccess', cascade="all, delete-orphan")
    contacts = db.relationship("SubmissionContact", cascade="all, delete-orphan")
    attachments = db.relationship("SubmissionAttachment", cascade="all, delete-orphan")
    dishes = db.relationship("SubmissionStudyDish", cascade="all, delete-orphan")
    uploadinfos = db.relationship("SubmissionUploadInfo", cascade="all, delete-orphan")

    def is_deletable(self):
        return self.current_status == SubmissionStatusEnum.draft

    def is_in_progress(self):
        return self.current_status == SubmissionStatusEnum.in_progress_data or self.current_status == SubmissionStatusEnum.in_progress_metadata

    def is_assigned(self):
        if self.provider_users is not None:
            return True
        else:
            return False

    def provider_user_ids(self):
        result = []
        for access in self.submission_accesses:
            result.append(access.user_id)
            # += ("" if index == 0 else ", ")+ access.user.first_name + " " +access.user.last_name
        return result

    def provider_users_display(self):
        result = ""
        index = 0
        for access in self.submission_accesses:
            result += ("" if index == 0 else ", ") + access.user.first_name + " " + access.user.last_name
            index += 1
        return result

    def has_providers(self):
        if self.submission_accesses is None:
            return False
        elif len(self.submission_accesses) == 0:
            return False
        else:
            return True

class SubmissionContact(db.Model):
    __tablename__ = 'submission_contacts'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    is_primary = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String)
    institution = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey('contact_types.id'), nullable=False)
    contact_category = db.relationship('ContactType')

    def fullname(self):
        return self.name + " " + self.surname.upper()


class SubmissionUploadInfo(db.Model):
    __tablename__ = 'submission_upload_info'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    file_name = db.Column(db.String(45), nullable=False)
    md5_checksum_at_provider = db.Column(db.String(32), nullable=False)


class DUCCodeInstance(db.Model):
    __tablename__ = 'duc_code_instances'

    id = db.Column(db.Integer, primary_key=True)
    ga4gh_code = db.Column(db.String, db.ForeignKey('ga4gh_codes.code'), nullable=False)
    note = db.Column(db.String(250))
    study_id = db.Column(db.Integer, db.ForeignKey('submission_dishes.id'), nullable=False)
    study = db.relationship("SubmissionStudyDish", back_populates="duc_codes")


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
    consent_notes = db.Column(db.String, nullable=False)
    de_identification_type = db.Column(db.Enum(DeIdentificationTypeEnum), nullable=False,
                                       default=DeIdentificationTypeEnum.p)
    storage_end_date = db.Column(db.Date, nullable=True)

    duc_codes = db.relationship("DUCCodeInstance", back_populates="study", cascade="all, delete-orphan")

    def duc_codes_names(self):
        result = []
        if self.duc_codes is not None:

            for duc_code_instance in self.duc_codes:
                result.append((duc_code_instance.ga4gh_code,
                               GA4GHCodes.query.filter_by(code=duc_code_instance.ga4gh_code).one_or_none().name))
        return result

    def special_subjects_status_display(self):
        if self.subjects_unable_to_consent or self.subjects_vulnerable or self.subjects_minors:
            return "Y"
        else:
            return "N"


class SubmissionAccess(db.Model):
    __tablename__ = 'submission_access'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    access_granted_on = db.Column(db.DateTime, nullable=False)
    user = db.relationship("User")
