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
from wtforms.validators import DataRequired, Email, Length, Regexp
from wtforms_components import SelectField, SelectMultipleField

from elixir_dss import app
from elixir_dss.controllers.api_controllers import get_elu_partners, get_elu_projects
from elixir_dss.models.services import get_active_users
from elixir_dss.models.submission import Contact, ContactType, SubmissionScope

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
    send_invite = BooleanField(
        "Invite contact to become submitter for this submission",
        default=False,
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
