import enum
import json
from datetime import datetime, timezone

from flask import url_for
from sqlalchemy import Sequence
from sqlalchemy.orm import object_mapper

from elixir_dss import db
from elixir_dss.clients.daisy import get_elu_partners
from elixir_dss.clients.idservice import generate_id
from elixir_dss.controllers.utils import dict_list_lookup


class ContactType(db.Model):
    __tablename__ = "contact_types"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, unique=True, nullable=False)


class LegalBasisType(db.Model):
    __tablename__ = "legalbasis_type"
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"code": self.code, "label": self.label}


class ConsentStatus(db.Model):
    __tablename__ = "consent_status"
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {"code": self.code, "label": self.label}


class SubjectCategory(db.Model):
    __tablename__ = "subject_category"
    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class EmailNotification(db.Model):
    __tablename__ = "email_notification"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)
    recipients_json = db.Column(db.String, nullable=False)
    text_body = db.Column(db.String, nullable=False)
    html_body = db.Column(db.String, nullable=False)

    created_on = db.Column(db.Date, nullable=False)


class SubmissionAttachment(db.Model):
    __tablename__ = "submission_attachments"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )
    note = db.Column(db.String, nullable=False)
    folder_name = db.Column(db.String, nullable=False)
    file_names = db.Column(db.String, nullable=False)

    def files_urls(self):
        if self.file_names is not None:
            result = []
            names = self.file_names.strip(" \t\n\r").split(" ")
            for name in names:
                result.append(
                    (
                        url_for(
                            "download_submission_attachment",
                            attach_id=self.id,
                            filename=name,
                        ),
                        name,
                    )
                )
            return result
        else:
            return None


class SubmissionStatusEnum(enum.Enum):
    draft = "Initiation"
    metadata_submission = "Metadata Entry"
    metadata_approval = "Metadata Review"
    data_upload = "Data Upload"
    data_approval = "Data Verification"
    completed = "Complete"
    cancelled = "Cancelled"

    def next_state(self):
        return {
            self.draft: self.metadata_submission,
            self.metadata_submission: self.metadata_approval,
            self.metadata_approval: self.data_upload,
            self.data_upload: self.data_approval,
            self.data_approval: self.completed,
        }.get(self)

    def prev_state(self):
        return {
            self.completed: self.data_approval,
            self.data_approval: self.data_upload,
            self.data_upload: self.metadata_approval,
            self.metadata_approval: self.metadata_submission,
            self.metadata_submission: self.draft,
        }.get(self)

    def step_num(self):
        return {
            self.draft: 0,
            self.metadata_submission: 1,
            self.metadata_approval: 2,
            self.data_upload: 3,
            self.data_approval: 4,
            self.completed: 5,
            self.cancelled: -1,
        }.get(self)


def uniqid():
    from time import time

    return hex(int(time() * 10000000))[2:]


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, Sequence("submission_id_seq"), primary_key=True)
    ref_name = db.Column(
        db.String(45), index=True, unique=True, nullable=False, default=uniqid()
    )
    created_on = db.Column(db.Date, nullable=False)
    finalised_on = db.Column(db.Date)
    current_status = db.Column(
        db.Enum(SubmissionStatusEnum),
        nullable=False,
        default=SubmissionStatusEnum.draft,
    )
    exported = db.Column(db.Boolean, nullable=False, default=False)
    institution_accession = db.Column(db.String)
    submission_contacts = db.relationship(
        "Contact", back_populates="submission", cascade="all, delete-orphan"
    )
    local_custodians_json = db.Column(db.String)
    local_project_name = db.Column(db.String)
    submission_accesses = db.relationship(
        "SubmissionAccess", cascade="all, delete-orphan"
    )
    notes = db.Column(db.String(250))

    studies = db.relationship("SubmissionStudy", cascade="all, delete-orphan")
    attachments = db.relationship("SubmissionAttachment", cascade="all, delete-orphan")
    datasets = db.relationship("SubmissionDataset", cascade="all, delete-orphan")
    messages = db.relationship("SubmissionMessage", cascade="all, delete-orphan")
    cancellation_reason = db.Column(db.String(500), nullable=True)
    cancelled_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_user_id])

    def is_deletable(self):
        return self.current_status == SubmissionStatusEnum.draft

    def is_in_progress(self):
        return self.current_status in (
            SubmissionStatusEnum.data_upload,
            SubmissionStatusEnum.metadata_submission,
            SubmissionStatusEnum.metadata_approval,
            SubmissionStatusEnum.data_approval,
        )

    def is_cancelled(self):
        return self.current_status == SubmissionStatusEnum.cancelled

    def is_cancellable(self):
        return self.current_status.value not in ["Completion", "Cancelled", "Draft"]

    def provider_user_ids(self):
        result = []
        for access in self.submission_accesses:
            result.append(access.user_id)
        return result

    def provider_user_names(self):
        result = []
        for access in self.submission_accesses:
            result.append(access.user.first_name + " " + access.user.last_name.upper())
        return result

    def provider_institute_name(self):
        if self.institution_accession:
            institutions = get_elu_partners()
            return dict_list_lookup(
                institutions, "external_id", self.institution_accession, "name"
            )
        else:
            return None

    def provider_institute_address(self):
        if self.institution_accession:
            institutions = get_elu_partners()
            return dict_list_lookup(
                institutions, "external_id", self.institution_accession, "address"
            )
        else:
            return None

    def local_custodians(self):
        if self.local_custodians_json:
            return json.loads(self.local_custodians_json)
        else:
            return []

    def has_providers(self):
        if not self.submission_accesses:
            return False
        else:
            return True

    def has_study(self):
        if not self.studies:
            return False
        else:
            return True

    def has_dataset(self):
        if not self.datasets:
            return False
        else:
            return True

    def is_overview_info_complete(self):
        return self.submission_contacts

    def is_detail_info_complete(self):
        return self.studies and self.datasets

    def to_dict(self):
        base_dict = {
            "id": self.id,
            "ref_name": self.ref_name,
            "submission_contacts": self.submission_contacts,
            "local_custodians_json": self.local_custodians_json,
            "local_project_name": self.local_project_name,
            "studies": self.studies,
        }
        return base_dict


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    institution = db.Column(db.String, nullable=True)
    is_main_contact = db.Column(db.Boolean, nullable=False, default=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("contact_types.id"), nullable=False
    )
    contact_category = db.relationship("ContactType")

    study_id = db.Column(db.Integer, db.ForeignKey("submission_study.id"))
    study = db.relationship("SubmissionStudy", back_populates="study_contacts")

    submission_id = db.Column(db.Integer, db.ForeignKey("submissions.id"))
    submission = db.relationship("Submission", back_populates="submission_contacts")

    send_invite = db.Column(db.Boolean, nullable=False, default=False)

    def fullname(self):
        return self.first_name + " " + self.last_name.upper()

    def to_dict(self):
        base_dict = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "institution": self.institution,
            "is_main_contact": self.is_main_contact,
            "category": self.contact_category.name if self.contact_category else None,
        }
        return base_dict

    def clone(self, **overrides):
        mapper = object_mapper(self)
        exclude = {"id", "submission_id", "study_id"}
        exclude.update({c.key for c in mapper.columns if c.unique})
        attrs = {
            c.key: getattr(self, c.key) for c in mapper.columns if c.key not in exclude
        }
        attrs.update(overrides)
        return self.__class__(**attrs)


class SubmissionMessage(db.Model):
    __tablename__ = "submission_message"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )
    submission = db.relationship("Submission", back_populates="messages")
    created_on = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    sender_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sender_user = db.relationship("User")
    message_text = db.Column(db.String, nullable=False)
    message_type = db.Column(db.String, nullable=True)
    # html_body = db.Column(db.String, nullable=)


class SubmissionStudy(db.Model):
    __tablename__ = "submission_study"
    # Study
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )
    name = db.Column(db.String, nullable=False)
    acronym = db.Column(db.String, nullable=True)
    description = db.Column(db.String, nullable=False)
    external_identifiers_json = db.Column(db.String, nullable=True)
    website = db.Column(db.String, nullable=True)
    ethics_approval_exists = db.Column(db.Boolean, nullable=False, default=False)
    ethics_approval_no = db.Column(db.String, nullable=True)
    study_types_json = db.Column(db.String, nullable=False)
    multi_center_study = db.Column(db.Boolean, nullable=False, default=False)
    study_characteristics = db.Column(db.Text, nullable=True)
    species_json = db.Column(db.String, nullable=True)
    diseases_json = db.Column(db.String, nullable=True)
    number_of_subjects = db.Column(db.Integer, nullable=True)
    sample_sources_json = db.Column(db.String, nullable=True)
    description_of_cohorts = db.Column(db.Text, nullable=True)
    informed_consent_given = db.Column(db.Boolean, nullable=True)
    age_range_of_subjects = db.Column(db.String, nullable=True)
    other_subject_characteristics_json = db.Column(db.String, nullable=True)
    contact_remarks = db.Column(db.Text, nullable=True)
    study_contacts = db.relationship(
        "Contact", back_populates="study", cascade="all, delete-orphan"
    )

    def _json_list(self, attr_name):
        """Safely decode a JSON list stored in the given attribute."""
        raw_value = getattr(self, attr_name, None)
        if not raw_value:
            return []
        try:
            parsed = json.loads(raw_value)
        except (json.JSONDecodeError, ValueError):
            return []
        return parsed if isinstance(parsed, list) else []

    @property
    def study_feature_names(self):
        """Return study types as a list."""
        return self._json_list("study_types_json")

    @property
    def external_identifiers(self):
        """Return external identifiers as a list."""
        return self._json_list("external_identifiers_json")

    @property
    def species_names(self):
        """Return species as a list (NCBITaxon ontology)."""
        return self._json_list("species_json")

    @property
    def diseases_names(self):
        """Return diseases as a list (MONDO ontology)."""
        return self._json_list("diseases_json")

    @property
    def sample_sources_names(self):
        """Return sample sources as a list (NCIt, EFO, UBERON ontologies)."""
        return self._json_list("sample_sources_json")

    @property
    def other_subject_characteristics_list(self):
        """Return other subject characteristics as a list."""
        return self._json_list("other_subject_characteristics_json")

    def clone(self, **overrides):
        mapper = object_mapper(self)
        exclude = {"id", "submission_id"}
        exclude.update({c.key for c in mapper.columns if c.unique})
        attrs = {
            c.key: getattr(self, c.key) for c in mapper.columns if c.key not in exclude
        }
        attrs.update(overrides)
        return self.__class__(**attrs)


class SubmissionDataset(db.Model):
    __tablename__ = "submission_dataset"

    id = db.Column(db.Integer, primary_key=True)
    internal_id = db.Column(db.String(20), unique=True, nullable=True)
    title = db.Column(db.String, nullable=False)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )
    study_id = db.Column(
        db.Integer, db.ForeignKey("submission_study.id"), nullable=False
    )
    study = db.relationship("SubmissionStudy", foreign_keys=[study_id])

    creators = db.relationship(
        "SubmissionDatasetCreator",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="SubmissionDatasetCreator.id",
    )

    description = db.Column(db.String, nullable=False)
    external_identifiers = db.Column(db.String, nullable=True)

    gdpr_datatypes_json = db.Column(db.String, nullable=False)
    gdpr_datatypes_notes = db.Column(db.String, nullable=True)

    sci_datatypes_json = db.Column(db.String, nullable=False)
    sci_datatypes_notes = db.Column(db.String, nullable=True)

    contains_personal_data = db.Column(db.Boolean, nullable=True, default=True)
    data_processing_type = db.Column(db.String, nullable=True)

    legal_basis_collection_std_code = db.Column(
        db.String, db.ForeignKey("legalbasis_type.code"), nullable=False, default="61a"
    )
    legal_basis_collection_std = db.relationship(
        "LegalBasisType", foreign_keys=[legal_basis_collection_std_code]
    )

    legal_basis_sharing_std_code = db.Column(
        db.String, db.ForeignKey("legalbasis_type.code"), nullable=False, default="61a"
    )
    legal_basis_sharing_std = db.relationship(
        "LegalBasisType", foreign_keys=[legal_basis_sharing_std_code]
    )

    is_special_category_data = db.Column(db.Boolean, nullable=False, default=False)

    has_special_subjects = db.Column(db.Boolean, nullable=False, default=False)
    special_subjects_notes = db.Column(db.String, nullable=True)

    consent_status_code = db.Column(
        db.String, db.ForeignKey("consent_status.code"), nullable=False, default="hm"
    )
    consent_status = db.relationship(
        "ConsentStatus", foreign_keys=[consent_status_code]
    )
    consent_notes = db.Column(db.String, nullable=True)

    # GDPR Art 9.2 legitimation
    has_art92_derogation = db.Column(db.Boolean, nullable=False, default=False)

    use_restriction_project = db.Column(db.Boolean, nullable=False, default=False)
    use_restriction_research_use = db.Column(db.Boolean, nullable=False, default=False)

    restriction_rs = db.Column(db.Boolean, nullable=False, default=False)
    restriction_rs_notes = db.Column(db.String, nullable=True)
    restriction_gs = db.Column(db.Boolean, nullable=False, default=False)
    restriction_gs_notes = db.Column(db.String, nullable=True)
    restriction_user_specific = db.Column(db.Boolean, nullable=False, default=False)
    restriction_user_specific_notes = db.Column(db.String, nullable=True)
    restriction_us = db.Column(db.Boolean, nullable=False, default=False)
    restriction_us_notes = db.Column(db.String, nullable=True)
    restriction_pub = db.Column(db.Boolean, nullable=False, default=False)
    restriction_pub_notes = db.Column(db.String, nullable=True)
    restriction_ts = db.Column(db.Boolean, nullable=False, default=False)
    restriction_ts_notes = db.Column(db.String, nullable=True)

    restriction_ts_lcsb = db.Column(db.Boolean, nullable=False, default=False)
    restriction_ts_lcsb_date = db.Column(db.Date, nullable=True)

    restriction_rtn = db.Column(db.Boolean, nullable=False, default=False)
    restriction_rtn_notes = db.Column(db.String, nullable=True)
    restriction_other_notes = db.Column(db.String, nullable=True)
    access_form_required = db.Column(db.Boolean, nullable=False, default=False)
    dac_approval_required = db.Column(db.Boolean, nullable=False, default=False)
    dac_approval_notes = db.Column(db.String, nullable=True)
    restriction_ip = db.Column(db.Boolean, nullable=False, default=False)
    restriction_ip_notes = db.Column(db.String, nullable=True)

    # Technical metadata
    number_of_records = db.Column(db.Integer, nullable=True)
    dataset_version = db.Column(db.String, nullable=True)
    creation_date = db.Column(db.Date, nullable=True)
    last_update_date = db.Column(db.Date, nullable=True)
    data_standards_json = db.Column(db.String, nullable=True)
    file_types_json = db.Column(db.String, nullable=True)
    byte_size = db.Column(db.String, nullable=True)
    sample_types_json = db.Column(db.String, nullable=True)

    def sci_data_type_names(self):
        if self.sci_datatypes_json is not None:
            return json.loads(self.sci_datatypes_json)
        else:
            return []

    def gdpr_data_type_names(self):
        if self.gdpr_datatypes_json is not None:
            return json.loads(self.gdpr_datatypes_json)
        else:
            return []

    def data_standard_names(self):
        if self.data_standards_json is not None:
            return json.loads(self.data_standards_json)
        else:
            return []

    def file_type_names(self):
        if self.file_types_json is not None:
            return json.loads(self.file_types_json)
        else:
            return []

    def sample_type_names(self):
        if self.sample_types_json is not None:
            return json.loads(self.sample_types_json)
        else:
            return []

    def has_special_category_data(self):
        if self.gdpr_datatypes_json is not None:
            gdpr_types = json.loads(self.gdpr_datatypes_json)
            special_categories = [
                "ethnic",
                "genetic",
                "biometric",
                "health",
                "sex",
                "criminal",
                "other",
            ]
            return any(cat in str(gdpr_types).lower() for cat in special_categories)
        return False

    def has_special_subjects_display(self):
        if self.has_special_subjects:
            return "Yes"
        else:
            return "No"

    def to_dict(self):
        base_dict = {
            "title": self.title,
            "creators": [creator.to_dict() for creator in self.creators],
            "description": self.description,
            "external_identifiers": self.external_identifiers,
            "gdpr_datatypes_json": self.gdpr_datatypes_json,
            "gdpr_datatypes_notes": self.gdpr_datatypes_notes,
            "sci_datatypes_json": self.sci_datatypes_json,
            "sci_datatypes_notes": self.sci_datatypes_notes,
            "contains_personal_data": self.contains_personal_data,
            "data_processing_type": self.data_processing_type,
            "legal_basis_collection_std_code": self.legal_basis_collection_std_code,
            "legal_basis_collection_std": (
                self.legal_basis_collection_std.to_dict()
                if self.legal_basis_collection_std
                else None
            ),
            "legal_basis_sharing_std_code": self.legal_basis_sharing_std_code,
            "legal_basis_sharing_std": (
                self.legal_basis_sharing_std.to_dict()
                if self.legal_basis_sharing_std
                else None
            ),
            "is_special_category_data": self.is_special_category_data,
            "has_special_subjects": self.has_special_subjects,
            "special_subjects_notes": self.special_subjects_notes,
            "consent_status_code": self.consent_status_code,
            "consent_status": (
                self.consent_status.to_dict() if self.consent_status else None
            ),
            "consent_notes": self.consent_notes,
            "has_art92_derogation": self.has_art92_derogation,
            "use_restriction_project": self.use_restriction_project,
            "use_restriction_research_use": self.use_restriction_research_use,
            "number_of_records": self.number_of_records,
            "dataset_version": self.dataset_version,
            "creation_date": (
                self.creation_date.isoformat() if self.creation_date else None
            ),
            "last_update_date": (
                self.last_update_date.isoformat() if self.last_update_date else None
            ),
            "data_standards_json": self.data_standards_json,
            "file_types_json": self.file_types_json,
            "byte_size": self.byte_size,
            "sample_types_json": self.sample_types_json,
        }
        return base_dict

    def clone(self, **overrides):
        mapper = object_mapper(self)
        exclude = {"id"}
        exclude.update({c.key for c in mapper.columns if c.unique})
        attrs = {
            c.key: getattr(self, c.key) for c in mapper.columns if c.key not in exclude
        }
        attrs.update(overrides)
        cloned = SubmissionDataset(**attrs)

        cloned.creators = [creator.clone() for creator in self.creators]
        cloned.internal_id = generate_id(cloned.title)
        return cloned


class SubmissionAccess(db.Model):
    __tablename__ = "submission_access"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer, db.ForeignKey("submissions.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    access_granted_on = db.Column(db.DateTime, nullable=False)
    user = db.relationship("User")


class SubmissionDatasetCreator(db.Model):
    __tablename__ = "submission_dataset_creator"

    id = db.Column(db.Integer, primary_key=True)

    dataset_id = db.Column(
        db.Integer, db.ForeignKey("submission_dataset.id"), nullable=False
    )

    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    institution = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    dataset = db.relationship("SubmissionDataset", back_populates="creators")

    def fullname(self):
        return f"{self.first_name} {self.last_name.upper()}"

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "institution": self.institution,
            "role": self.role,
        }

    def clone(self, **overrides):
        return SubmissionDatasetCreator(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            institution=self.institution,
            role=self.role,
            **overrides,
        )
