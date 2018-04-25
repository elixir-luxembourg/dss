from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, SelectField, DateField, SelectMultipleField, \
    FormField, FieldList, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Regexp, Length

from .validators import OptionalFieldValidator
from elixir_dcp.models.submission import ConsentStatusEnum, ContactType, DataSizeCategory, DeIdentificationTypeEnum, \
    GA4GHCodes, DUCCodeInstance, SubmissionScopeEnum
from elixir_dcp.models.security import User
from elixir_dcp import app



class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """
    id = HiddenField('Attachment_Id')
    note = StringField('Attachment Note',
                       validators=[DataRequired(), Regexp('^[a-zA-Z\s]+$', message="Note can only contain letters."),
                                   Length(min=2, max=40,
                                          message="Must be 2 to 40 characters long.")])
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
    name = StringField('Name', description='This is the help text for name',
                       validators=[DataRequired(), Regexp('^[a-zA-Z\s]+$', message="Can only contain letters."),
                                   Length(min=2, max=20,
                                          message="Must be 2 to 20 characters long.")],
                       render_kw={"placeholder": "Name"})
    surname = StringField('Surname', description='This is the help text for surname',
                          validators=[DataRequired(), Regexp('^[a-zA-Z\s]+$', message="Can only contain letters."),
                                      Length(min=2, max=20,
                                             message="Must be 2 to 20 characters long.")],
                          render_kw={"placeholder": "SURNAME"})

    category_id = SelectField('Type', coerce=int)
    email = EmailField('Email', [DataRequired(), Email("This field requires an email address.")],
                       render_kw={"placeholder": "Institutional e-mail"})

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]


class UploadInfoForm(FlaskForm):
    """
    Form for creating records containing name of uploaded files and their checksum at the client.
    This information is used by the data steward to check data integrity after receiving files.
    """
    id = HiddenField('SubmissionUploadInfo_Id')
    submission_id = HiddenField('Submission Id')
    file_name = StringField('Name', validators=[DataRequired(), Regexp('^[a-zA-Z0-9-\s\.]+$',
                                                                       message="File name can contain letters, numbers and dash."),
                                                Length(min=5, max=40,
                                                       message="Must be 5 to 40 characters long.")],
                            render_kw={"placeholder": "Only the name of the file without folder information."})
    md5_checksum_at_provider = StringField('File Checksum', validators=[DataRequired(), Regexp('^[0-9]+$',
                                                                                               message="Can only contain numbers.")],
                                           render_kw={"placeholder": "32 Characters checksum."})

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
                                             Regexp('\w+',
                                                    message="Title must contain only letters numbers or underscore"),
                                             Length(min=15, max=75,
                                                    message="Title must be between 15 & 75 characters")])

    upload_instructions = TextAreaField('Upload Instructions', render_kw={"rows": "6", "columns": "50"})

    provider_user_ids = SelectMultipleField('Data Provider(s)', coerce=int)

    submission_scope = SelectField('Category', choices=SubmissionScopeEnum.choices(), validators=[DataRequired()])

    collab_local_custodian = StringField('Recipient PI', validators=[OptionalFieldValidator(regex_str='^[a-zA-Z\s,]+$',
                                                                                         message="Recipient name can contain only letters and colon.")])

    collab_project_name = StringField('Recipient Project', validators=[OptionalFieldValidator(regex_str='^[a-zA-Z0-9\s,]+$',
                                                                                    message="Can only contain letters, numbers and colon.")])

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.provider_user_ids.choices = [(usr.id, usr.display_name()) for usr in User.query.all()]


class StudyDishForm(FlaskForm):
    """
    Form for creating or updating DISH for each study within a submission
    """
    # Study
    id = HiddenField('DISH_Id')
    submission_id = HiddenField('Submission Id')
    study_name = StringField('Study Name', validators=[DataRequired()])
    study_description = TextAreaField('Study Description', render_kw={'rows': 3})
    study_types = SelectMultipleField('Study Type(s)', validators=[DataRequired()])

    # Data
    estimate_data_size = SelectField('Estimated Total Data Size', validators=[DataRequired()])
    data_types = SelectMultipleField('Data Type(s)', validators=[DataRequired()])
    metadata_exists = BooleanField('Metadata Provided', default=True)

    # Ethics & Data Protection
    ethics_approval_exists = BooleanField('Ethics Approval Exists', default=False)
    subjects_minors = BooleanField('Subjects Minors', default=False)
    subjects_vulnerable = BooleanField('Subjects Those Unable to Consent', default=False)
    subjects_unable_to_consent = BooleanField('Other Vulnerable Subjects', default=False)

    consent_status = SelectField('Consent Status', choices=ConsentStatusEnum.choices())
    consent_notes = TextAreaField('Notes on Consent', render_kw={'rows': 3})
    de_identification_type = SelectField('De-Identification Type', choices=DeIdentificationTypeEnum.choices())

    duc_codes = FieldList \
        (FormField(UseConditionCodeForm, default=lambda: DUCCodeInstance()), min_entries=1,
         label='Data Use Restrictions')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.estimate_data_size.choices = [(c.code, c.label) for c in DataSizeCategory.query.all()]
        self.data_types.choices = [(c, c) for c in app.config.get('DATA_INIT')['data_types']]
        self.study_types.choices = [(c, c) for c in app.config.get('DATA_INIT')['study_types']]
