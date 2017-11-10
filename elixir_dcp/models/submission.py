from elixir_dcp import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)
    description = db.Column(db.String(250))
    created = db.Column(db.Date)
    contacts = db.relationship("SubmissionContact")

    def __repr__(self):
        return '<Submission: {}>'.format(self.name)


class SubmissionContact(db.Model):
    __tablename__ = 'submission_contacts'

    id = db.Column(db.Integer, primary_key=True)
    is_primary = db.Column(db.Boolean, nullable=False)
    name = db.Column(db.String, nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'))

    # TODO: there also needs to be a FK that points to ELIXIR DCP registered Users table
