from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SubmissionForm(FlaskForm):
    """
    Form for admin to add or edit a department
    """
    #id
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])

    submit = SubmitField('Submit')

