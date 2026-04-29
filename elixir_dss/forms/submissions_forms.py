from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    FieldList,
    FormField,
    HiddenField,
    IntegerField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
)
from wtforms_components import SelectField, SelectMultipleField

from elixir_dss import app
from elixir_dss.clients.daisy import get_elu_partners, get_elu_projects
from elixir_dss.models.services import get_active_users
from elixir_dss.models.submission import Contact, ContactType

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

    first_name = StringField(
        "Name",
        validators=[DataRequired()],
        render_kw={"placeholder": "Name"},
    )
    last_name = StringField(
        "Surname",
        validators=[DataRequired()],
        render_kw={"placeholder": "SURNAME"},
    )
    email = EmailField(
        "Email",
        [DataRequired(), Email("This field requires an email address.")],
        render_kw={"placeholder": "Institutional e-mail"},
    )

    institution = StringField(
        "Institution",
        render_kw={"placeholder": "University/Institution"},
        description="Main institutional affiliation (required for main contact)",
    )

    category_id = SelectField(
        "Role",
        validators=[DataRequired()],
        description="Please specify the role of the contact person (e.g., Principal Investigator, Researcher, Data Manager)",
        coerce=int,
    )

    is_main_contact = BooleanField(
        "Main contact",
        default=False,
        description="Designate as main study contact",
    )
    send_invite = BooleanField(
        "Invite contact to become submitter for this submission",
        default=False,
    )

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in ContactType.query.all()]

    def validate(self, extra_validators=None):
        """institution required if is_main_contact is True."""
        if not super(ContactForm, self).validate(extra_validators):
            return False

        # If main contact, institution is required
        if self.is_main_contact.data:
            if not self.institution.data or not self.institution.data.strip():
                self.institution.errors = (
                    list(self.institution.errors) if self.institution.errors else []
                )
                self.institution.errors.append(
                    "Institution is required for main contact"
                )
                return False

        return True


class StudyForm(FlaskForm):
    """
    Form for creating or updating studies
    """

    id = HiddenField("study_id")
    submission_id = HiddenField("Submission_Id")

    name = StringField(
        "Study name",
        validators=[DataRequired()],
        description="Study name or title",
    )

    acronym = StringField(
        "Study acronym",
        description="Short name for the study",
    )

    description = TextAreaField(
        "Study description",
        validators=[DataRequired()],
        description="Brief textual description of the study purpose (required for GDPR documentation)",
        render_kw={"rows": 3},
    )

    external_identifiers = StringField(
        "External identifiers",
        description="External database identifiers (e.g., EGAS00000000009). Separate multiple values with semicolons.",
    )

    website = StringField(
        "Website URL",
    )

    ethics_approval_exists = BooleanField(
        "Ethics approval confirmation",
        description="Does ethics approval exist for this study?",
        default=False,
    )

    ethics_approval_no = StringField(
        "Ethics/IRB approval number",
    )

    study_types = SelectMultipleField(
        "Study type(s)",
        validators=[DataRequired()],
        description="Please select the categories that best characterise the study",
        render_kw={"class": "elx-multi-select"},
    )

    multi_center_study = BooleanField(
        "Multi-centre study?",
        description="Is this a multi-centre study?",
        default=False,
    )

    study_characteristics = TextAreaField(
        "Study characteristics",
        description="Specify study characteristics using gene, disease, phenotype terms and study types",
        render_kw={"rows": 3},
    )

    number_of_subjects = IntegerField(
        "Number of subjects",
        validators=[Optional(), NumberRange(min=0)],
        description="Number of subjects recruited",
    )

    age_range_of_subjects = StringField(
        "Age range of subjects",
        description="Age range of subjects (e.g., 18-99 years)",
    )

    species = StringField(
        "Species",
        description="Species studied. Separate multiple values with semicolons. Ontology terms optional (e.g., Homo sapiens (NCBITaxon:9606))",
    )

    diseases = StringField(
        "Diseases/conditions",
        description="Diseases or conditions studied. Separate multiple values with semicolons. Ontology terms optional (e.g., Parkinson's disease (MONDO:0005180))",
    )

    sample_sources = StringField(
        "Sample sources",
        description="Sample sources studied. Separate multiple values with semicolons. Ontology terms optional (e.g., tissue sample; Blood (UBERON:0000178))",
    )

    description_of_cohorts = TextAreaField(
        "Description of Data Subjects",
        description="Detailed cohort description (e.g., 250 patients (132 male, 118 female) with type II diabetes)",
        render_kw={"rows": 3},
    )

    informed_consent_given = BooleanField(
        "Informed consent given?",
        default=False,
        description="Has informed consent been given?",
    )

    other_subject_characteristics = StringField(
        "Other subject characteristics",
        description="Other subject characteristics. Separate multiple values with semicolons (e.g., sex: 57 male, 85 female)",
    )

    study_contacts = FieldList(
        FormField(ContactForm, default=lambda: Contact()),
        min_entries=1,
        description="At least one study contact is required (typically the Study PI). You may add additional contacts if needed.",
    )

    contact_remarks = TextAreaField(
        "Contact remarks",
        description="General remarks or notes about study contacts",
        render_kw={"rows": 2},
    )

    def __init__(self, *args, **kwargs):
        sub_id = kwargs.pop("sub_id", None)
        super(StudyForm, self).__init__(*args, **kwargs)

        self.study_types.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["study_types"]
        ]

        if sub_id is not None:
            self.submission_id.data = sub_id

    def validate(self, extra_validators=None):
        """ensure at least one contact is designated as main contact."""
        if not super(StudyForm, self).validate(extra_validators):
            return False

        has_main_contact = any(
            contact.is_main_contact.data
            for contact in self.study_contacts
            if contact.is_main_contact.data
        )

        if not has_main_contact:
            if (
                not hasattr(self.study_contacts, "errors")
                or self.study_contacts.errors is None
            ):
                self.study_contacts.errors = []
            self.study_contacts.errors.append(
                "At least one contact must be designated as the main contact (typically the Study PI)"
            )
            return False

        return True


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
    Form for creating or updating a Submission.
    """

    id = HiddenField("Submission_Id")

    provider_user_ids = SelectMultipleField(
        "Submitting users",
        description="Please select the list of users who will be able to view and update the submission.",
        coerce=int,
    )

    local_custodians = SelectMultipleField(
        "Recipient",
        description="If known please specify the Principal Investigator/Researcher that is the recipient of data.",
    )

    local_project_name = SelectField(
        "Receiving project",
        description="If you are making this submission in the context of a  collaboration/project, please specif its name here.",
        coerce=str,
    )

    institution_accession = SelectField(
        "Submitting institution",
        description="Please select institute that is making the submission.",
        validators=[DataRequired()],
    )

    submission_contacts = FieldList(
        FormField(ContactForm, default=lambda: Contact()),
        min_entries=1,
        description="Please provide at least one main contact (the submitter). Additional contacts can be added as needed.",
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
        self.local_custodians.choices = [("", "")] + [
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
        self.local_project_name.choices = [("", "")] + [
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
