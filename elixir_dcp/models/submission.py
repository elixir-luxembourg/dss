from sqlalchemy import Sequence
from elixir_dcp import db, app
import enum
import os
import json


class ContactType(db.Model):
    __tablename__ = 'contact_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


class GA4GHCodes(db.Model):
    __tablename__ = 'ga4gh_codes'

    code = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String,  nullable=False)


class DataSizeCategory(db.Model):
    __tablename__ = 'data_size_category'

    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class EmailNotification(db.Model):
    __tablename__ = 'email_notification'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)
    recipients_json = db.Column(db.String, nullable=False)
    text_body = db.Column(db.String, nullable=False)
    html_body = db.Column(db.String, nullable=False)

    created_on = db.Column(db.Date, nullable=False)


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


class DeIdentificationType(db.Model):
    __tablename__ = 'deidentification_type'
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class LegalBasisType(db.Model):
    __tablename__ = 'legalbasis_type'
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class ConsentStatus(db.Model):
    __tablename__ = 'consent_status'
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


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


class SubmissionScope(db.Model):
    __tablename__ = 'submission_scope'
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)



def uniqid():
    from time import time
    return hex(int(time() * 10000000))[2:]


class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, Sequence('submission_id_seq'), primary_key=True)
    ref_name = db.Column(db.String(45), index=True, unique=True, nullable=False, default=uniqid())
    title = db.Column(db.String(75))
    created_on = db.Column(db.Date, nullable=False)
    dish_finalised_on = db.Column(db.Date)
    current_status = db.Column(db.Enum(SubmissionStatusEnum), nullable=False, default=SubmissionStatusEnum.draft)
    exported = db.Column(db.Boolean, nullable=False, default=False)
    upload_instructions = db.Column(db.String)

    submission_scope = db.relationship('SubmissionScope')
    submission_scope_code = db.Column(db.String, db.ForeignKey('submission_scope.code'), nullable=False, default='e')
    collab_local_custodian_json = db.Column(db.String)
    collab_project_name = db.Column(db.String)

    submission_accesses = db.relationship('SubmissionAccess', cascade="all, delete-orphan")

    studies = db.relationship("SubmissionStudy", cascade="all, delete-orphan")
    attachments = db.relationship("SubmissionAttachment", cascade="all, delete-orphan")
    datasets = db.relationship("SubmissionDataset", cascade="all, delete-orphan")
    uploadinfos = db.relationship("SubmissionUploadInfo", cascade="all, delete-orphan")

    def is_deletable(self):
        return self.current_status == SubmissionStatusEnum.draft

    def is_in_progress(self):
        return self.current_status == SubmissionStatusEnum.in_progress_data or self.current_status == SubmissionStatusEnum.in_progress_metadata

    def provider_user_ids(self):
        result = []
        for access in self.submission_accesses:
            result.append(access.user_id)
        return result

    def provider_user_names(self):
        result = []
        for access in self.submission_accesses:
            result.append(access.user.first_name + ' ' + access.user.last_name.upper())
        return result

    def uploads_instructions_lines(self):
        result = []
        if self.upload_instructions:
            for line in self.upload_instructions.split('\n'):
                result.append(line)
        return result

    def is_elixir(self):
        if self.submission_scope_code == 'e':
            return True
        else:
            return False

    def has_providers(self):
        if not self.submission_accesses:
            return False
        else:
            return True


class StudyContact(db.Model):
    __tablename__ = 'study_contacts'

    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    institution = db.Column(db.String, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('contact_types.id'), nullable=False)
    contact_category = db.relationship('ContactType')
    study_id = db.Column(db.Integer, db.ForeignKey('submission_study.id'), nullable=False)
    study = db.relationship("SubmissionStudy", back_populates="study_contacts")

    def fullname(self):
        return self.firstname + " " + self.surname.upper()


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
    dataset_id = db.Column(db.Integer, db.ForeignKey('submission_datasets.id'), nullable=False)
    dataset = db.relationship("SubmissionDataset", back_populates="duc_codes")

    def get_duc_codes_name(self, ga4gh_code):
        ga4gh_code_name =  GA4GHCodes.query.filter_by(code=ga4gh_code).one_or_none().name
        return ga4gh_code_name


class SubmissionStudy(db.Model):
    __tablename__ = 'submission_study'
    # Study
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    study_name = db.Column(db.String, nullable=False)
    study_description = db.Column(db.String, nullable=False)
    ethics_approval_exists = db.Column(db.Boolean, nullable=False, default=False)
    study_types_json = db.Column(db.String, nullable=False)
    study_contacts = db.relationship("StudyContact", back_populates='study',cascade="all, delete-orphan" )

    def study_type_names(self):

        if self.study_types_json is not None:
            return json.loads(self.study_types_json)

        else:
            return []

    def study_contacts_names(self, study_id):
        contact_fullname = []
        contacts = StudyContact.query.filter(StudyContact.study_id==study_id).all()
        if contacts is not None:
            for contact in contacts:
                contact_fullname.append(contact.fullname())
            return contact_fullname
        else:
            return []


class SubmissionDataset(db.Model):
    __tablename__ = 'submission_datasets'

    # Data
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    study_id = db.Column(db.Integer, db.ForeignKey('submission_study.id'), nullable=False)
    study = db.relationship("SubmissionStudy", foreign_keys=[study_id])

    estimate_data_size_code = db.Column(db.String, db.ForeignKey('data_size_category.code'), nullable=False, default='s')
    data_types_json = db.Column(db.String, nullable=False)
    data_notes = db.Column(db.String, nullable=True)
    metadata_exists = db.Column(db.Boolean, nullable=False, default=True)

    # Ethics & Data Protection
    legal_basis_sharing_code = db.Column(db.String, db.ForeignKey('legalbasis_type.code'), nullable=False, default='c')
    legal_basis_sharing = db.relationship('LegalBasisType', foreign_keys=[legal_basis_sharing_code])

    legal_basis_collection_code = db.Column(db.String, db.ForeignKey('legalbasis_type.code'), nullable=False, default='c')
    legal_basis_collection = db.relationship('LegalBasisType',  foreign_keys=[legal_basis_collection_code])

    subjects_minors = db.Column(db.Boolean, nullable=False, default=False)
    subjects_vulnerable = db.Column(db.Boolean, nullable=False, default=False)
    subjects_unable_to_consent = db.Column(db.Boolean, nullable=False, default=False)
    subjects_notes = db.Column(db.String, nullable=True)

    consent_status_code = db.Column(db.String, db.ForeignKey('consent_status.code'), nullable=False, default='m')
    consent_status = db.relationship('ConsentStatus', foreign_keys=[consent_status_code])

    consent_notes = db.Column(db.String, nullable=True)

    de_identification_type_code = db.Column(db.String, db.ForeignKey('deidentification_type.code'), nullable=False, default='p')
    de_identification_type = db.relationship('DeIdentificationType')

    duc_codes = db.relationship("DUCCodeInstance", back_populates="dataset", cascade="all, delete-orphan")




    def data_type_names(self):
        if self.data_types_json is not None:

            return json.loads(self.data_types_json)
        else:
            return []

    def duc_codes_names(self):
        result = []
        if self.duc_codes is not None:

            for duc_code_instance in self.duc_codes:
                result.append((duc_code_instance.ga4gh_code,
                               GA4GHCodes.query.filter_by(code=duc_code_instance.ga4gh_code).one_or_none().name))
        return result

    def special_subjects_status_display(self):
        if self.subjects_unable_to_consent or self.subjects_vulnerable or self.subjects_minors:
            return "Yes"
        else:
            return "No"


class SubmissionAccess(db.Model):
    __tablename__ = 'submission_access'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    access_granted_on = db.Column(db.DateTime, nullable=False)
    user = db.relationship("User")
