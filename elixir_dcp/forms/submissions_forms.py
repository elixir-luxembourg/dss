from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField
from flask_wtf.file import FileField, FileRequired

class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """
    id = HiddenField('Id', default='0')
    note = StringField('Attachment Note', validators=[DataRequired()])
    submission_id = HiddenField('Submission Id')
    file_attachments = StringField('File(s)')
    # wtf FileField does not support multiple uploads.
    # we have a hard-coded field in own
    # We keep it as dummy to attach validation errors

class ContactForm(FlaskForm):
    """
    Form for creating or updating contacts
    """
    id = HiddenField('Id', default='0')
    submission_id = HiddenField('Submission Id')
    name = StringField('Contact Name')
    is_primary = BooleanField('Is Primary?', default=False)


class SubmissionForm(FlaskForm):
    """
    Form for creating or updating submissions
    """

    id = HiddenField('Id',  default='0')
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    created = DateField('Created On', validators=[DataRequired()], format='%d/%m/%Y')



