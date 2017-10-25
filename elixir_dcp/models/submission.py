from elixir_dcp import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), index=True, unique=True, nullable=False)
    description = db.Column(db.String(60))
    created = db.Column(db.Date)

    def __repr__(self):
        return '<Submission: {}>'.format(self.name)
