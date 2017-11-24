from elixir_dcp import db
import enum


class ContactType(db.Model):
    __tablename__ = 'contact_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


class DataSizeCategory(db.Model):
    __tablename__ = 'data_size_category'

    code = db.Column(db.String, unique=True, nullable=False, primary_key=True)
    label = db.Column(db.String, nullable=False)


class SubmissionAttachment(db.Model):
    __tablename__ = 'submission_attachments'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String, nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    server_path = db.Column(db.String, nullable=False)
    file_names = db.Column(db.String, nullable=False)


class DeIdentificationTypeEnum(enum.Enum):
    a = 'anonymized'
    p = 'pseudonymized'


class ConsentStatusEnum(enum.Enum):
    htr = 'heterogeneous'
    hmg = 'homogeneous'

class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)
    description = db.Column(db.String(650))
    created_on = db.Column(db.Date, nullable=False)
    joint_providers = db.Column(db.Boolean, nullable=False)

    contacts = db.relationship("SubmissionContact")
    attachments = db.relationship("SubmissionAttachment")

    def __repr__(self):
        return '<Submission: {}>'.format(self.name)


class SubmissionContact(db.Model):
    __tablename__ = 'submission_contacts'

    id = db.Column(db.Integer, primary_key=True)
    is_primary = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('contact_types.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    contact_category = db.relationship('ContactType')
    # TODO: there also needs to be a FK that points to ELIXIR DCP registered Users table


class SubmissionDish(db.Model):
    __tablename__ = 'submission_dishes'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    study_name = db.Column(db.String, nullable=False)
    estimate_data_size = db.Column(db.Integer, db.ForeignKey('data_size_category.code'), nullable=False)
    ethics_approval_exists = db.Column(db.Boolean, nullable=False, default=False)
    special_subjects_exists = db.Column(db.Boolean, nullable=False, default=False)
    special_subjects_desc = db.Column(db.String)
    consent_status = db.Column(db.Enum(ConsentStatusEnum), nullable=False, default=ConsentStatusEnum.hmg)
    # heterogeneous/homogeneous
    # if heterogeneous we would need to keep all consent group descriptions for this study.

    de_identification_type = db.Column(db.Enum(DeIdentificationTypeEnum), nullable=False,
                                       default=DeIdentificationTypeEnum.p)

    storage_end_date = db.Column(db.Date, nullable=True)
    embargo_end_date = db.Column(db.Date, nullable=True)

    collaboration_required = db.Column(db.Boolean, nullable=False, default=False)
    irb_approval_required = db.Column(db.Boolean, nullable=False, default=False)
    use_for_non_profit_only = db.Column(db.Boolean, nullable=False, default=False)


