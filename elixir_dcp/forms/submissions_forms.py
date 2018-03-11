from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, SelectField, DateField, SelectMultipleField, \
    FormField, FieldList, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email,  Regexp, Length
from elixir_dcp.models.submission import ConsentStatusEnum, ContactType, DataSizeCategory, DeIdentificationTypeEnum, \
     GA4GHCodes, DUCCodeInstance
from elixir_dcp.models.security import User


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
    email = EmailField('Email', [DataRequired(), Email("This field requires an email address.")], render_kw={"placeholder": "Institutional e-mail"})

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]


class UploadInfoForm(FlaskForm):
    """
    Form for creating records containing name of uplaoded files and their checksum at the client.
    This information is used by the data steward to check data integrity after receiving files.
    """
    id = HiddenField('SubmissionUploadInfo_Id')
    submission_id = HiddenField('Submission Id')
    file_name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Only the name of the file without folder information."})
    md5_checksum_at_provider = StringField('File Checksum', validators=[DataRequired()], render_kw={"placeholder": "32 Characters checksum."})

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']


class UseConditionCodeForm(FlaskForm):
    """
    Form for creating an instance of a Ga4GH code to be included in a DUC group
    """
    ga4gh_code = SelectField('GA4GH Code')
    note = TextAreaField('Note')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.ga4gh_code.choices = [(c.code, c.code + " - " + c.name) for c in GA4GHCodes.query.all()]


class SubmissionForm(FlaskForm):
    """
    Form for updating a submission's title and
     detail info found in releated beans.
    """

    id = HiddenField('Submission_Id')

    title = StringField('Title', validators=[DataRequired(),
                                             Regexp('\w+', message="Title must contain only letters numbers or underscore"),
                                             Length(min=15, max=75, message="Title must be between 5 & 25 characters")])

    upload_instructions = TextAreaField('Upload Instructions', render_kw={"placeholder": "Instructions will be displayed here once you complete Study Registration and we create an upload link for you.", "rows": "6", "columns": "50"})

    provider_user_ids = SelectMultipleField('Shared With', coerce=int)

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.provider_user_ids.choices = [(usr.id, usr.display_name()) for usr in User.query.all()]


class StudyDishForm(FlaskForm):

    """
    Form for creating or updating DISH for each study within a submission
    """
    id = HiddenField('DISH_Id')
    submission_id = HiddenField('Submission Id')
    study_name = StringField('Dataset Name', validators=[DataRequired()])

    joint_providers = BooleanField('Submitter is (Joint)Controller for Data', default=False)
    estimate_data_size = SelectField('Estimated Total Data Size', validators=[DataRequired()])

    ethics_approval_exists = BooleanField('Ethics Approval Exists', default=False)

    subjects_minors = BooleanField('Subjects Minors', default=False)
    subjects_vulnerable = BooleanField('Subjects those Unable To Consent', default=False)
    subjects_unable_to_consent = BooleanField('Has other vulnerable Subjects', default=False)

    consent_status = SelectField('Consent Status', choices=ConsentStatusEnum.choices())
    consent_notes = TextAreaField('Note on Heterogeneous Consents', render_kw={'rows': 3})
    de_identification_type = SelectField('De-Identification Type', choices=DeIdentificationTypeEnum.choices())

    storage_end_date = DateField('Store Until', validators=[DataRequired()], format='%d/%m/%Y', render_kw={"placeholder": "DD/MM/YYYY"})

    duc_codes = FieldList(FormField(UseConditionCodeForm, default=lambda: DUCCodeInstance()),  min_entries=1, label='Data Use Restrictions')

    def __init__(self, *args, **kwargs):
            FlaskForm.__init__(self, *args, **kwargs)
            if 'sub_id' in kwargs:
                self.submission_id.data = kwargs['sub_id']
            self.estimate_data_size.choices = [(c.code, c.label) for c in DataSizeCategory.query.all()]

