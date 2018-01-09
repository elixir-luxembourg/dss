from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, SelectField, DateField, SelectMultipleField, \
    FormField, FieldList, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Optional, Regexp, Length
from wtforms.widgets import HiddenInput

from elixir_dcp.models.submission import ConsentStatusEnum, ContactType, DataSizeCategory, DeIdentificationTypeEnum, \
    SubmissionStatusEnum, GA4GHCodes, DUCCodeInstance


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
    name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Name"})
    surname = StringField('Surname', validators=[DataRequired()], render_kw={"placeholder": "SURNAME"})
    is_primary = BooleanField('Is Primary?', default=False)
    category_id = SelectField('Type', coerce=int)
    email = EmailField('Email', [DataRequired(), Email("This field requires an email address.")], render_kw={"placeholder": "Your institutional e-mail"})

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]




class UseConditionCodeForm(FlaskForm):
    """
    Form for creating an instance of a Ga4GH code to be included in a DUC group
    """
    ga4gh_code = SelectField('GA4GH Code')
    note = StringField('Note')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.ga4gh_code.choices = [(c.code, c.code + " - " + c.name) for c in GA4GHCodes.query.all()]


class UseConditionGroupForm(FlaskForm):
    """
    Form for creating or updating Data Use Condition (DUC) Groups
    """

    id = IntegerField('UseConditionGroup_Id', widget=HiddenInput(), validators=[Optional()])

    submission_id = HiddenField('Submission Id')
    group_name = StringField('Name', validators=[DataRequired()])
    duc_codes = FieldList(FormField(UseConditionCodeForm, default=lambda: DUCCodeInstance()),  min_entries=1, label='Data Use Conditions')
    #applies_to_studies = SelectMultipleField('Applies to Studies')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
            #self.applies_to_studies.choices = [('22', 'study 1'), ('23', 'study 2')]
            # TODO read from db using kwargs['sub_id']



class SubmissionForm(FlaskForm):
    """
    Form for updating submission header info
    """

    id = HiddenField('Submission_Id')
    ref_name = StringField('Reference No')
    title = StringField('Title', validators=[DataRequired(),
                                             Regexp('\w+', message="Title must contain only letters numbers or underscore"),
                                             Length(min=15, max=75, message="Title must be between 5 & 25 characters")])

    created_on = DateField('Created On', format='%d/%m/%Y')

    """
   We only have the Optional Validator here because in our submission editor we have the
   status select field disabled, this results in value None to be submitted
    """
    current_status = SelectField('Current Status', validators=[Optional()], choices=SubmissionStatusEnum.choices())


    def child_contact_form(self, *args, **kwargs):
        return ContactForm(formdata=None, obj=None, sub_id=self.id.data)


    def child_dish_form(self, *args, **kwargs):
        return StudyDishForm(formdata=None, obj=None, sub_id=self.id.data)

    def child_attachment_form(self, *args, **kwargs):
        return AttachmentForm(formdata=None, obj=None, sub_id=self.id.data)


    def child_duc_form(self, *args, **kwargs):
        return UseConditionGroupForm(formdata=None, obj=None, sub_id=self.id.data)


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

    subjects_minors = BooleanField('Subjects Minors', default=False)
    subjects_vulnerable = BooleanField('Subjects Those Unable To Consent', default=False)
    subjects_unable_to_consent = BooleanField('Vulnerable Subjects', default=False)

    consent_status = SelectField('Consent Status', choices=ConsentStatusEnum.choices())
    de_identification_type = SelectField('De-Identification Type', choices=DeIdentificationTypeEnum.choices())

    storage_end_date = DateField('Storage End', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})
    embargo_end_date = DateField('Embargo Until', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})


    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.estimate_data_size.choices = [(c.code, c.label) for c in DataSizeCategory.query.all()]
