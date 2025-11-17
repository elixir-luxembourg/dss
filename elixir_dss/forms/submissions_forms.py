from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    FieldList,
    FormField,
    HiddenField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Regexp, NumberRange
from wtforms_components import SelectField, SelectMultipleField

from elixir_dss import app
from elixir_dss.controllers.api_controllers import get_elu_partners, get_elu_projects
from elixir_dss.models.services import get_active_users
from elixir_dss.models.submission import (
    ConsentStatus,
    Contact,
    ContactType,
    DeIdentificationType,
    LegalBasisType,
    SubjectCategory,
    SubmissionScope,
    SubmissionStudy,
)

from .validators import OptionalFieldValidator


class AttachmentForm(FlaskForm):
    """
    Form for creating or updating attachments in the form of uploaded files
    """

    id = HiddenField("Attachment_Id")
    note = StringField(
        "Attachment description",
        description="Please provide a brief description of the document you're uploading.",
        validators=[
            DataRequired(),
            Regexp(r"^[\w\s]+$", message="Note can only contain letters, ."),
            Length(min=2, max=40, message="Must be 2 to 40 characters long."),
        ],
    )
    submission_id = HiddenField("Submission_Id")
    file_attachments = StringField("File(s)")

    # wtf FileField does not support multiple uploads.
    # we use a hard-coded string field here
    # We keep it as dummy to attach validation errors

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if "sub_id" in kwargs:
            self.submission_id.data = kwargs["sub_id"]


class ContactForm(FlaskForm):
    """
    Form for creating or updating contacts
    """

    firstname = StringField(
        "Name",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s]+$", message="Can only contain letters, digits and underscore."
            ),
            Length(min=2, max=20, message="Must be 2 to 20 characters long."),
        ],
        render_kw={"placeholder": "Name"},
    )
    lastname = StringField(
        "Surname",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s]+$", message="Can only contain letters, digits and underscore."
            ),
            Length(min=2, max=20, message="Must be 2 to 20 characters long."),
        ],
        render_kw={"placeholder": "SURNAME"},
    )
    category_id = SelectField(
        "Type",
        validators=[DataRequired()],
        description="Please specify the role of the contact person, which could be the source study's PI, the data manager, legal rep or DPO of data submitting institution.",
        coerce=int,
    )
    email = EmailField(
        "Email",
        [DataRequired(), Email("This field requires an email address.")],
        render_kw={"placeholder": "Institutional e-mail"},
    )

    address = TextAreaField(
        "Division/Address",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]


class StudyForm(FlaskForm):
    """
    Form for creating or updating studies
    """

    id = HiddenField("study_id")
    submission_id = HiddenField("Submission_Id")

    name = StringField(
        "Title",
        description="Please specify the shortname or acronym for the study.",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s\-]+$",
                message="Name must contain only letters, digits, underscore or dash",
            ),
        ],
    )
    description = TextAreaField(
        "Description",
        description="Please provide a short textual summary of the study purpose, goals and method.",
        render_kw={"rows": 3},
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
    )
    website = StringField(
        "Website URL",
        description="Please provide a short description of the study.",
    )

    ethics_approval_exists = BooleanField(
        "Hereby it is confirmed that an ethics approval exists for the data collection as well as the data sharing for the purposes as foreseen in the agreement",
        default=False,
    )
    ethics_approval_no = StringField(
        "Ethics/IRB approval number",
        description="If know, please specify the reference number for the Ethics/IRB  approval.",
    )

    study_types = SelectMultipleField(
        "Study features(s)",
        validators=[DataRequired()],
        description="Please select the categories that best characterise the study within which the data has been collected. You can select multiple options.",
    )

    study_contacts = FieldList(
        FormField(ContactForm, default=lambda: Contact()),
        min_entries=1,
        description="Please provide contact person(s) for the study. You must provide at least one contact, which typically would be the study PI.",
        label="Study contacts",
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if "sub_id" in kwargs:
            self.submission_id.data = kwargs["sub_id"]
        self.study_types.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["study_types"]
        ]


class MessageForm(FlaskForm):
    """
    Form for creating messages under a submission.
    Messages facilitate communication between data submitter and data stewards.
    """

    id = HiddenField("SubmissionUploadInfo_Id")
    submission_id = HiddenField("Submission_Id")
    message_text = TextAreaField(
        "Message Text",
        description="Please type your message here.",
        render_kw={"rows": 3},
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if "sub_id" in kwargs:
            self.submission_id.data = kwargs["sub_id"]


class ReviewFeedbackForm(FlaskForm):
    feedback = TextAreaField(
        "Feedback",
        description="Provide feedback about this review (required when rejecting)",
        render_kw={"rows": 5, "maxlength": 2000},
    )


class SubmissionForm(FlaskForm):
    """
    Form for updating a submission's title and
     detail info found in related beans.
    """

    id = HiddenField("Submission_Id")

    title = StringField(
        "Title",
        description="Please provide a short descriptive title for the submission. ELIXIR LU data stewards  may refer this title when communicating with you.",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s\-]+$",
                message="Title must contain only letters, digits, underscore or dash",
            ),
            Length(min=5, max=75, message="Title must be between 5 & 75 characters"),
        ],
    )

    provider_user_ids = SelectMultipleField(
        "Submitting users",
        description="Please select the list of users who will be able to view and update the submission.",
        coerce=int,
    )

    submission_scope_code = SelectField(
        "Recipient lab",
        description="Please select either an LCSB research lab or ELIXIR-Luxembourg.",
        validators=[DataRequired()],
    )

    local_custodians = SelectMultipleField(
        "Recipient PI(s)",
        description="If known please specify the Principal Investigator/Researcher that is the recipient of data.",
    )

    local_project_name = SelectField(
        "Recipient project",
        description="If you are making this submission in the context of a  collaboration/project, please specif its name here.",
        validators=[DataRequired()],
    )

    institution_accession = SelectField(
        "Submitting institution",
        description="Please select institute that is making the submission.",
        validators=[DataRequired()],
    )

    submission_contacts = FieldList(
        FormField(ContactForm, default=lambda: Contact()),
        min_entries=3,
        description="You must provide at least three contacts. (1) Main contact who is the signatory on the submission info sheet, another (2) Data protection officer of the submitting institution\
                                                                                                                  (3) Legal representative for the submitting institution",
        label="Submission contacts",
    )

    notes = TextAreaField(
        "Remarks",
        description="If there is any information about the study you were unable to provide through the form you may specify it here.",
        render_kw={"rows": 2},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.provider_user_ids.choices = [
            (usr.id, usr.display_name()) for usr in get_active_users()
        ]
        self.submission_scope_code.choices = [
            (c.code, c.label) for c in SubmissionScope.query.all()
        ]
        self.local_custodians.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["lcsb_pis"]
        ]
        self.institution_accession.choices = [
            (
                c["external_id"],
                (
                    f"{c['name']} - {c['acronym']}"
                    if "acronym" in c and c["acronym"] is not None and "name" in c
                    else c["name"]
                    if "name" in c
                    else "-"
                ),
            )
            for c in get_elu_partners()
        ]
        self.local_project_name.choices = [
            (
                c["external_id"],
                (
                    f"{c['name']} - {c['acronym']}"
                    if "acronym" in c and c["acronym"] is not None and "name" in c
                    else c["name"]
                    if "name" in c
                    else "-"
                ),
            )
            for c in get_elu_projects()
        ]


class DatasetForm(FlaskForm):
    """
    Form for creating or updating a data set within a submission
    """

    id = HiddenField("dataset_Id")
    submission_id = HiddenField("Submission_Id")
    external_id = StringField("External ID", render_kw={"readonly": True})

    title = StringField(
        "Title",
        description="Please provide a short descriptive title for the  dataset. ELIXIR LU data stewards  may refer this title when communicating with you.",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s\-]+$",
                message="Title must contain only letters, digits, underscore or dash",
            ),
            Length(min=5, max=50, message="Title must be between 5 & 50 characters"),
        ],
    )

    study_id = SelectField(
        "Source study",
        coerce=int,
        description="Please specify the study/cohort that is the source of the dataset. To make a selection here, you must first define an entry in the Study tab on the Submission page.",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="You must select a valid study"),
        ],
    )

    # cohort_accession = SelectField('Cohort',
    #                                description="This field denotes a Cohort from  LCSB's common cohorts list.")

    gdpr_datatypes = SelectMultipleField(
        "GDPR Personal data categories in the dataset",
        description="These are overarching categories of personal data as defined in GDPR Art. 9.1 and Art. 10. You may get assistance from your institute’s DPO or legal team in filling out this field. \
                                                    You can select multiple options.",
        validators=[DataRequired()],
    )

    gdpr_datatypes_notes = TextAreaField(
        "Remarks on GDPR personal data categories in the dataset",
        description="If your have remarks  - e.g. to explain 'other personal data' - please provide it here.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    sci_datatypes = SelectMultipleField(
        "Scientific datatypes in the dataset",
        description="Please select the categories that would best characterise the types of data within this dataset. You can select multiple options.",
        validators=[DataRequired()],
    )

    sci_datatypes_notes = TextAreaField(
        "Remarks on scientific datatypes in the dataset",
        description="If your have other remarks about the data types - e.g. to explain 'Other' data - please provide it here.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    de_identification_type_code = SelectField(
        "Is the DATA anonymised or pseudonymised?",
        description="A dataset is considered anonymised if no stakeholder is holding a mapping from the Subject ID in the data to the \
                                              identifying personal information e.g. name, surname, date of birth, address of the human subject supplying the data.\
                                              A dataset is considered pseudonymised if there exists some cohort owner/coordinator holding the mapping from the \
                                              Subject ID to the human subject identifying personal information.",
        validators=[DataRequired()],
    )
    has_samples = BooleanField(
        "Includes Samples",
        description="Will you be submitting bio-samples to ELIXIR-LU/LCSB or to any other partner in the research project?",
        default=False,
    )
    samples_notes = StringField(
        "Notes on samples",
        description=" Please describe the nature of bio-samples (e.g. DNA, blood sample).",
    )

    # Lawful basis of processing

    legal_basis_collection_std_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR for the collection of standard (non-sensitive) personal data?",
        description="You may get assistance from your institute’s DPO or legal team in filling out this field.",
        validators=[DataRequired()],
    )
    legal_basis_sharing_std_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR for the  sharing and subsequent processing of standard (non-sensitive) personal data?",
        description="You may get assistance from your institute’s DPO or legal team in filling out this field.",
        validators=[DataRequired()],
    )
    legal_basis_collection_spec_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR  for the collection of special category (sensitive) personal data?",
        description="You may get assistance from your institute’s DPO or legal team in filling out this field.",
        validators=[DataRequired()],
    )
    legal_basis_sharing_spec_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR  for the  sharing and subsequent processing of special category (sensitive) personal data?",
        description="You may get assistance from your institute’s DPO or legal team in filling out this field.",
        validators=[DataRequired()],
    )
    legal_basis_notes = StringField(
        "Remarks on legal basis.",
        description="If the legal basis for special categories of data affect only a subset of sensitive data, please specify these here e.g. refers only to genetic but not to health data.",
    )

    subject_category_code = SelectField(
        "The dataset is related to the following categories of data subjects",
        description="Please denote the category of human subjects to which the data relates.",
        validators=[DataRequired()],
    )
    has_special_subjects = BooleanField(
        "Does the dataset contain data of 'Special Subjects'?",
        description="'Special Subjects' refers to minors or subjects unable to give consent e.g. mentally impaired subjects.",
        default=False,
    )
    special_subjects_notes = TextAreaField(
        "Notes on 'Special Subjects'",
        description="Please provide a brief description of these 'Special Subjects'.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    # Use restrictions originating from consent or elsewhere.

    consent_status_code = SelectField(
        "Are the consents heterogeneous or homogeneous?",
        description="If the consent form has changed throughout the course of the study in a way that changes the usage restrictions on data then this case is considered heterogeneous.\
    If the consent form has stayed the same over the course of the study but it has options so that different subjects can create different restrictions on their data, then this case is also considered heterogeneous",
        validators=[DataRequired()],
    )
    consent_notes = TextAreaField(
        "Notes on consent",
        render_kw={"rows": 3},
        description="If the consent is Heterogeneous, please specify the data dictionary item (column) that specifies consent groups in data.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_rs = BooleanField(
        "Limited scope of research: is data consented to be used only in specific research/disease areas? E.g.  use only in Biomedical Research or Parkinson's Research etc.",
        default=False,
    )
    restriction_rs_notes = TextAreaField(
        "Notes on limited scope of research",
        render_kw={"rows": 3},
        description="Please describe research/disease areas restriction on data.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_gs = BooleanField(
        "Geographic restriction: Does consent contain clauses that put geographic restrictions to the sharing of data? E.g. not to be shared outside Country A, B, or EU.",
        default=False,
    )
    restriction_gs_notes = TextAreaField(
        "Notes on geographic restriction",
        render_kw={"rows": 3},
        description="Please describe geographic restrictions on data.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_us = BooleanField(
        "Restricted type of recipients: Does consent limit the type of recipient? E.g. data can be sent only to public institutions.",
        default=False,
    )
    restriction_us_notes = TextAreaField(
        "Notes on restricted type of recipients",
        render_kw={"rows": 3},
        description="Please describe the recipient restrictions on data.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_pub = BooleanField(
        "Publication requirements: Are there any requirements in case of publications based on the DATA? E.g. papers should cite the cohort study?",
        default=False,
    )
    restriction_pub_notes = TextAreaField(
        "Notes on publication requirements",
        render_kw={"rows": 3},
        description="Please describe the publication requirements.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_ts = BooleanField(
        "Retention time: Does consent contain clauses that put time-limits on the use of data?",
        default=False,
    )
    restriction_ts_notes = TextAreaField(
        "Notes on retention time.",
        render_kw={"rows": 3},
        description="Please describe the time-limit restrictions on data.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_ps = BooleanField(
        "Project restriction: Is the use of data limited to the recipient project?",
        default=False,
    )
    restriction_ps_notes = TextAreaField(
        "Notes on project restriction",
        render_kw={"rows": 3},
        description="Please describe data restrictions related to their use in different project.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_ts_lcsb = BooleanField(
        "Time limit of storage at LCSB: Is the data being sent to ELIXIR-LU/LCSB for a limited duration?",
        default=False,
    )
    restriction_ts_lcsb_notes = TextAreaField(
        "Notes on storage duration at ELIXIR-LU/LCSB",
        render_kw={"rows": 3},
        description="Please state the agreed end date for data's residence at ELIXIR-LU/LCSB.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_rtn = BooleanField(
        "Data return requirements: Is there a requirement to return data or documents to the database/resource?",
        default=False,
    )
    restriction_rtn_notes = TextAreaField(
        "Notes on data return requirements",
        render_kw={"rows": 3},
        description="Is there a requirement to return data or documents to the database/resource?",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_other_notes = TextAreaField(
        "Other restrictions",
        render_kw={"rows": 3},
        description="If there are any other restrictions on  DATA, please describe them here.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    access_form_required = BooleanField(
        "Will all researchers accessing the DATA need to sign an access request form?",
        default=False,
    )
    dac_approval_required = BooleanField(
        "Will access require Data Access Committee (DAC) approval?", default=False
    )
    dac_approval_notes = TextAreaField(
        "Notes on DAC approval procedure",
        render_kw={"rows": 3},
        description="If a DAC Approval is needed please describe the required procedure.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_ip = BooleanField(
        "Are there any Intellectual Property (IP) retrictions/requirements when using the data?",
        default=False,
    )
    restriction_ip_notes = TextAreaField(
        "Notes on IP restrictions",
        render_kw={"rows": 3},
        description="If there are IP requirements please decribe them here.",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if "sub_id" in kwargs:
            self.submission_id.data = kwargs["sub_id"]

        if self.submission_id.data is None:
            self.submission_id.data = -1
        lb_lookup = [(c.code, c.label) for c in LegalBasisType.query.all()]
        self.legal_basis_sharing_std_code.choices = lb_lookup
        self.legal_basis_collection_std_code.choices = lb_lookup
        self.legal_basis_sharing_spec_code.choices = lb_lookup
        self.legal_basis_collection_spec_code.choices = lb_lookup
        self.consent_status_code.choices = [
            (c.code, c.label) for c in ConsentStatus.query.all()
        ]
        self.subject_category_code.choices = [
            (c.code, c.label) for c in SubjectCategory.query.all()
        ]
        self.de_identification_type_code.choices = [
            (c.code, c.label) for c in DeIdentificationType.query.all()
        ]
        self.sci_datatypes.choices = app.config.get("DATA_INIT")["sci_datatypes"]
        self.gdpr_datatypes.choices = app.config.get("DATA_INIT")["gdpr_datatypes"]
        self.study_id.choices = [(-1, "-")] + [
            (study.id, study.name)
            for study in SubmissionStudy.query.filter_by(
                submission_id=self.submission_id.data
            )
        ]
