from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import EmailField
from elixir_dcp.models.submission import ConsentStatusEnum, ContactType, DataSizeCategory, DeIdentificationTypeEnum, \
    SubmissionStatusEnum


class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """
    id = HiddenField('Attachment_Id')
    note = StringField('Attachment Note', validators=[DataRequired()])
    submission_id = HiddenField('Submission Id')
    file_attachments = StringField('File(s)')
    # wtf FileField does not support multiple uploads.
    # we use a hard-coded string field here
    # We keep it as dummy to attach validation errors

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']


class ContactForm(FlaskForm):
    """
    Form for creating or updating contacts
    """
    id = HiddenField('Contact_Id')
    submission_id = HiddenField('Submission Id')
    name = StringField('Contact', validators=[DataRequired()], render_kw={"placeholder": "Name SURNAME"})
    is_primary = BooleanField('Is Primary?', default=False)
    category_id = SelectField('Type', coerce=int)
    email = EmailField('Email', [DataRequired(), Email("This field requires an email address.")], render_kw={"placeholder": "email@uni.lu"})

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]


class SubmissionForm(FlaskForm):
    """
    Form for creating or updating submissions
    """

    id = HiddenField('Submission_Id')
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    created_on = DateField('Created On', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})
    current_status = SelectField('Current Status', choices=SubmissionStatusEnum.choices())



    def child_contact_form(self, *args, **kwargs):
        return ContactForm(formdata=None, obj=None, sub_id=self.id.data)


    def child_dish_form(self, *args, **kwargs):
        return StudyDishForm(formdata=None, obj=None, sub_id=self.id.data)

    def child_attachment_form(self, *args, **kwargs):
        return AttachmentForm(formdata=None, obj=None, sub_id=self.id.data)


class StudyDishForm(FlaskForm):

    """
    Form for creating or updating DISH for each study within a submission
    """
    id = HiddenField('DISH_Id')
    submission_id = HiddenField('Submission Id')
    study_name = StringField('Study Name', validators=[DataRequired()])
    joint_providers = BooleanField('Joint Providers', default=False)
    estimate_data_size = SelectField('Estimated Data Size', validators=[DataRequired()])

    ethics_approval_exists = BooleanField('Ethics Approval Exists', default=False)

    subjects_minors = BooleanField('Minors', default=False)
    subjects_vulnerable = BooleanField('Those Unable To Consent', default=False)
    subjects_unable_to_consent = BooleanField('Vulnerable', default=False)

    consent_status = SelectField('Consent Status', choices=ConsentStatusEnum.choices())
    de_identification_type = SelectField('Consent Status', choices=DeIdentificationTypeEnum.choices())

    storage_end_date = DateField('Storage End', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})
    embargo_end_date = DateField('Embargo Until', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})

    collaboration_required = BooleanField('Collaboration Required', default=False)
    irb_approval_required = BooleanField('IRB Approval Required', default=False)
    use_for_non_profit_only = BooleanField('Use for non-profit only', default=False)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.estimate_data_size.choices = [(c.code, c.label) for c in DataSizeCategory.query.all()]
