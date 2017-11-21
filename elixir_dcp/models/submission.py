from elixir_dcp import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)
    description = db.Column(db.String(250))
    created = db.Column(db.Date)
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


class ContactType(db.Model):
    __tablename__ = 'contact_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)


class SubmissionAttachment(db.Model):
    __tablename__ = 'submission_attachments'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String, nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))
    server_path = db.Column(db.String, nullable=False)
    file_names = db.Column(db.String, nullable=False)

