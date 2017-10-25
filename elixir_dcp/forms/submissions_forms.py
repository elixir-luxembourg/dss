from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, DateField
from wtforms.validators import DataRequired


class SubmissionForm(FlaskForm):
    """
    Form for creating or updating submissions
    """

    id = HiddenField('Id', validators=[DataRequired()], default=-1)
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    created = DateField('Created On', validators=[DataRequired()], format='%d/%m/%y')

