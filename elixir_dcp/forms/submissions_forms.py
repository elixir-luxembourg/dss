from flask_wtf import FlaskForm, Form
from wtforms import StringField, HiddenField, BooleanField, TextAreaField, DateField, \
    FormField, FieldList, RadioField
from wtforms_components import SelectField, SelectMultipleField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Regexp, Length

from elixir_dcp.controllers.api_controllers import get_elu_partners, get_elu_cohorts
from .validators import OptionalFieldValidator
from elixir_dcp.models.submission import ContactType, GA4GHCodes, DUCCodeInstance, StudyContact, SubmissionStudy
from elixir_dcp import app
from elixir_dcp.models.services import get_active_users



class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """
    id = HiddenField('Attachment_Id')
    note = StringField('Attachment Note',
                       validators=[DataRequired(), Regexp('^[\w\s]+$', message="Note can only contain letters, ."),
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
    firstname = StringField('Name',
                            validators=[DataRequired(),
                                        Regexp('^[\w\s]+$', message="Can only contain letters, digits and underscore."),
                                        Length(min=2, max=20,
                                               message="Must be 2 to 20 characters long.")],
                            render_kw={"placeholder": "Name"})
    surname = StringField('Surname',
                          validators=[DataRequired(),
                                      Regexp('^[\w\s]+$', message="Can only contain letters, digits and underscore."),
                                      Length(min=2, max=20,
                                             message="Must be 2 to 20 characters long.")],
                          render_kw={"placeholder": "SURNAME"})
    category_id = SelectField('Type', validators=[DataRequired()],
                              description="Please specify the role of the contact person, which could be the source study's PI, the data manager, legal rep or DPO of data submitting institution.",
                              coerce=int)
    email = EmailField('Email', [DataRequired(), Email("This field requires an email address.")],
                       render_kw={"placeholder": "Institutional e-mail"})

    address = TextAreaField('Address/Notes', validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                                message="Can only contain letters, digits, dash, comma and dot.")])

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]


class StudyForm(FlaskForm):
    """
        Form for creating or updating studies
    """
    id = HiddenField('study_id')
    submission_id = HiddenField('Submission Id')

    study_name = StringField('Study Name', validators=[DataRequired(), Regexp('^[\w\s\-]+$',
                                                                              message="Name must contain only letters, digits, underscore or dash")])
    study_description = TextAreaField('Study Description',
                                      description="Please provide a short description of the study.",
                                      render_kw={'rows': 3},
                                      validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                         message="Can only contain letters, digits, dash, comma and dot.")])
    ethics_approval_exists = BooleanField('Confirmation that Ethics Approval Exists',
                                          description="Confirmation that an ethics approval exists for the data collection, sharing and the purposes for which the data is shared.",
                                          default=False)
    study_types = SelectMultipleField('Study Type(s)', validators=[DataRequired()],
                                      description="Please select the categories that would best characterise the study within which the data has been collected.")

    study_contacts = FieldList(FormField(ContactForm, default=lambda: StudyContact()), min_entries=1,
                               label='Contacts List')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']
        self.study_types.choices = [(c, c) for c in app.config.get('DATA_INIT')['study_types']]


class UploadInfoForm(FlaskForm):
    """
    Form for creating records containing name of uploaded files and their checksum at the client.
    This information is used by the data steward to check data integrity after receiving files.
    """
    id = HiddenField('SubmissionUploadInfo_Id')
    submission_id = HiddenField('Submission Id')
    file_name = StringField('Name', description="Please specify the name of the file that has been uploaded.",
                            validators=[DataRequired(), Regexp('^[\w\s\-.]+$',
                                                               message="Can only contain letters, digits and underscore."),
                                        Length(min=5, max=40,
                                               message="Must be 5 to 40 characters long.")],
                            render_kw={"placeholder": "Only the name of the file without folder information."})
    md5_checksum_at_provider = StringField('File Checksum',
                                           description="Please specify the md5 checksum at your side. This information will be used by us to verify that the file has been transmitted without errors.",
                                           validators=[DataRequired(), Regexp('^[\w]+$',
                                                                              message="Can only letters and digits.")],
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
    note = TextAreaField('Note', validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                    message="Can only contain letters, digits, dash, comma and dot.")])

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.ga4gh_code.choices = [(c.code, c.name) for c in GA4GHCodes.query.all()]


class SubmissionForm(FlaskForm):
    """
    Form for updating a submission's title and
     detail info found in related beans.
    """

    id = HiddenField('Submission_Id')

    title = StringField('Title', validators=[DataRequired(),
                                             Regexp('^[\w\s\-]+$',
                                                    message="Title must contain only letters, digits, underscore or dash"),
                                             Length(min=5, max=75,
                                                    message="Title must be between 5 & 75 characters")])

    upload_instructions = TextAreaField('Upload Instructions', render_kw={"rows": "", "columns": "50"})

    provider_user_ids = SelectMultipleField('Submitting Users', coerce=int)

    submission_scope_code = SelectField('Recipient', validators=[DataRequired()])

    local_custodians = SelectMultipleField('Recipient PI(s)', validators=[DataRequired()])

    local_project_name = StringField('Recipient Project', validators=[OptionalFieldValidator(regex_str='^[\w\s]+$',
                                                                                             message="Can only contain letters, digits and underscore.")])
    institution_accession = SelectField('Submitting Institution', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.provider_user_ids.choices = [(usr.id, usr.display_name()) for usr in get_active_users()]
        self.submission_scope_code.choices = [(c[0], c[1]) for c in app.config.get('DATA_INIT')['submission_scope']]
        self.local_custodians.choices = [(c, c) for c in app.config.get('DATA_INIT')['lcsb_pis']]
        self.institution_accession.choices = [(c["elu_accession"],
                                               c["name"] + ' - ' + c["acronym"] if 'acronym' in c else c[
                                                   "name"]) for c in
                                              get_elu_partners()]


class DatadecForm(FlaskForm):
    """
    Form for creating or updating a data declaration within a submission
    """
    id = HiddenField('dataset_Id')
    submission_id = HiddenField('Submission Id')

    title = StringField('Data Title', validators=[DataRequired(),
                                                  Regexp('^[\w\s\-]+$',
                                                         message="Title must contain only letters, digits, underscore or dash"),
                                                  Length(min=5, max=50,
                                                         message="Title must be between 5 & 50 characters")])

    study_id = SelectField('Study', coerce=int,
                           description="This field denotes a Study defined by you as part of the submission.")

    cohort_accession = SelectField('Cohort',
                                   description="This field denotes a Cohort from  LCSB's common cohorts list.")

    estimate_data_size_code = SelectField('Estimated Total Data Size',
                                          description="Please select the estimated size of the dataset that will be subnmitted for this study.",
                                          validators=[DataRequired()])

    data_types = SelectMultipleField('Data Type(s)',
                                     description="Please select the categories that would best characterise the types of data within this dataset.",
                                     validators=[DataRequired()])
    data_notes = TextAreaField('Notes/Comments', render_kw={'rows': 3},
                               validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                  message="Can only contain letters, digits, dash, comma and dot.")])

    metadata_exists = BooleanField('Is Metadata Provided',
                                   description="Confirmation of whether metadata will be uploaded alongside data. As a minimum we would expect a Data Dictionary to be supplied alongside data.",
                                   default=True)

    # Ethics & Data Protection

    legal_basis_collection_code = SelectField('Legal Basis of Data Collection', validators=[DataRequired()])
    legal_basis_sharing_code = SelectField('Legal Basis of Data Sharing', validators=[DataRequired()])
    subjects_minors = BooleanField('Subjects Minors', default=False)
    subjects_vulnerable = BooleanField('Subjects Those Unable to Consent', default=False)
    subjects_unable_to_consent = BooleanField('Other Vulnerable Subjects', default=False)
    subjects_notes = TextAreaField('Notes on Subjects', render_kw={'rows': 3},
                                   validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                      message="Can only contain letters, digits, dash, comma and dot.")])

    consent_status_code = SelectField('Consent Status', validators=[DataRequired()])
    consent_notes = TextAreaField('Notes on Consent', render_kw={'rows': 3},
                                  validators=[OptionalFieldValidator(regex_str='^[\w\s,\-.]+$',
                                                                     message="Can only contain letters, digits, dash, comma and dot.")])
    de_identification_type_code = SelectField('De-Identification Type', validators=[DataRequired()])

    duc_codes = FieldList \
        (FormField(UseConditionCodeForm, default=lambda: DUCCodeInstance()), min_entries=1,
         label='Data Use Restrictions')

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if 'sub_id' in kwargs:
            self.submission_id.data = kwargs['sub_id']

        if  self.submission_id.data is None:
            self.submission_id.data = -1

        self.estimate_data_size_code.choices = [(c[0], c[1]) for c in app.config.get('DATA_INIT')['size_categories']]
        self.legal_basis_sharing_code.choices = [(c[0], c[1]) for c in app.config.get('DATA_INIT')['legal_basis']]
        self.legal_basis_collection_code.choices = [(c[0], c[1]) for c in app.config.get('DATA_INIT')['legal_basis']]
        self.consent_status_code.choices = [(c[0], c[1]) for c in app.config.get('DATA_INIT')['consent_status']]
        self.de_identification_type_code.choices = [(c[0], c[1]) for c in
                                                    app.config.get('DATA_INIT')['deidentification_type']]
        self.data_types.choices = app.config.get('DATA_INIT')['data_types']
        self.study_id.choices = [(-1, '-')] + [(study.id, study.study_name) for study in
                                               SubmissionStudy.query.filter_by(submission_id=self.submission_id.data)]
        self.cohort_accession.choices = [('', '-')] + [(c["elu_accession"], c["title"]) for c in get_elu_cohorts()]

    def source_stati(self):
        empty_study = False
        if self.study_id.data == -1:
            empty_study = True
        empty_cohort = False
        if not self.cohort_accession.data:
            empty_cohort =  True
        return empty_study, empty_cohort


    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        empty_study, empty_cohort = self.source_stati()
        if empty_study and empty_cohort:
            self.study_id.errors.append('Missing input, provide either a study or cohort.')
            self.cohort_accession.errors.append('Missing input, provide either a study or cohort.')
            return False
        if empty_study:
            self.study_id.data = None
        if empty_cohort:
            self.study_id.cohort = None
        return True
