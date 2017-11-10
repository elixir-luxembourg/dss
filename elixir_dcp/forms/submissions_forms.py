from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, FormField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DateField


class ContactForm(FlaskForm):
    """
    Form for creating or updating submissions
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



