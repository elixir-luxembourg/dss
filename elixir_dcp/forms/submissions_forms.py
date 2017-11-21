from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from elixir_dcp.models import ContactType

class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """
    id = HiddenField('Id', default='0')
    note = StringField('Attachment Note', validators=[DataRequired()])
    submission_id = HiddenField('Submission Id')
    file_attachments = StringField('File(s)')
    # wtf FileField does not support multiple uploads.
    # we use a hard-coded string field here
    # We keep it as dummy to attach validation errors

class ContactForm(FlaskForm):
    """
    Form for creating or updating contacts
    """
    id = HiddenField('Id', default='0')
    submission_id = HiddenField('Submission Id')
    name = StringField('Contact Name')
    is_primary = BooleanField('Is Primary?', default=False)
    category_id = SelectField('Contact Type', choices=[(c.id, c.name) for c in ContactType.query.all()], coerce=int)


class SubmissionForm(FlaskForm):
    """
    Form for creating or updating submissions
    """

    id = HiddenField('Id',  default='0')
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    created = DateField('Created On', validators=[DataRequired()], format='%d/%m/%Y')



