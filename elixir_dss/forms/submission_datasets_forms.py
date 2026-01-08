from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    EmailField,
    HiddenField,
    IntegerField,
    StringField,
    TextAreaField,
    FieldList,
    FormField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Optional,
    Regexp,
    NumberRange,
    ValidationError,
)
from wtforms_components import SelectField, SelectMultipleField

from elixir_dss import app
from elixir_dss.models.submission import (
    ConsentStatus,
    DeIdentificationType,
    LegalBasisType,
    SubmissionStudy,
)

from .validators import OptionalFieldValidator


class DatasetCreatorForm(FlaskForm):
    first_name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
        render_kw={"placeholder": "Name"},
    )
    last_name = StringField(
        "Surname",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
        render_kw={"placeholder": "SURNAME"},
    )
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email("This field requires a valid email address."),
        ],
        render_kw={"placeholder": "Institutional e-mail"},
    )
    institution = StringField(
        "Institution",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
        render_kw={"placeholder": "University/Institution"},
        description="Main institutional affiliation",
    )
    role = StringField(
        "Role",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
        description="Please specify the role of the contact person (e.g., Principal Investigator, Researcher, Data Manager)",
    )


class DatasetForm(FlaskForm):
    id = HiddenField("dataset_Id")
    submission_id = HiddenField("Submission_Id")
    internal_id = StringField("Internal ID", render_kw={"readonly": True})
    creators = FieldList(
        FormField(DatasetCreatorForm),
        min_entries=1,
        description="At least one creator is required. Additional creators are optional.",
    )
    description = TextAreaField(
        "Dataset description",
        description="",
        render_kw={"rows": 4},
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
    )
    external_identifiers = StringField(
        "External Identifiers",
        description="If applicable, provide external identifier(s) for this dataset (e.g., accession numbers). Separate multiple identifiers with |.",
        render_kw={"placeholder": "EGAD00000000001"},
    )
    title = StringField(
        "Dataset title",
        description="Please provide a short descriptive title for the data.",
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
        "Study identifier",
        coerce=int,
        description="Please specify the source Study/Cohort that is the source of the data. This should refer to a study/cohort you defined in a Study sheet e.g. Study1",
        validators=[
            DataRequired(),
            NumberRange(min=1, message="You must select a valid study"),
        ],
    )

    # Data protection (GDPR)

    gdpr_datatypes = SelectMultipleField(
        "The data includes the following categories and types of personal data",
        description='These are definitions from the GDPR. In biomedical projects with pseudonymised cohort data, the options  would likely fall under  "Special category, i.e. sensitive, personal data" e.g. "Genetic data", "Data concerning health" and ""Other special categories of data". \nYou may get assistance from your institute\'s DPO or legal team in filling out this section.',
        validators=[DataRequired()],
    )
    gdpr_datatypes_notes = TextAreaField(
        "Personal data remarks",
        description='In case of "other special categories of data", please specify.',
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    is_special_category_data = BooleanField(
        "Is data classified as special category (sensitive) personal data according to Art 9.2 GDPR?",
        description="",
        default=False,
    )

    # GDPR Art 9.2 - Only shown when special category data is selected
    has_art92_derogation = BooleanField(
        "For the processing of special category (sensitive) personal data, do you have a  legitimation under Art. 9.2 GDPR that provides specific derogation from the general prohibition to process such data?",
        description="",
        default=False,
    )

    # Scope of data subjects

    sci_datatypes = SelectMultipleField(
        "Data types",
        description="Please select the categories that would best characterise the types of data within this dataset. You can select multiple options.",
        validators=[DataRequired()],
    )

    sci_datatypes_notes = TextAreaField(
        "Data types - Remarks",
        description="In case of 'Other' types of data, please specify.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    de_identification_type_code = SelectField(
        "Is the data anonymised or pseudonymised?",
        description="A dataset is considered anonymised if no stakeholder is holding a mapping from the Subject ID in the data to the identifying personal information e.g. name, surname, date of birth, address of the human subject supplying the data.\nA dataset is considered pseudonymised if there exists some cohort owner/coordinator holding the mapping from the Subject ID to the human subject identifying personal information.",
        validators=[DataRequired()],
    )

    # Data protection (GDPR)

    legal_basis_collection_std_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR for the collection of personal data?",
        description="These options come from GDPR Article 6. \nYou may get assistance from your institute's DPO or legal team in filling out this section.",
        validators=[DataRequired()],
    )
    legal_basis_sharing_std_code = SelectField(
        "What is the legal basis according to Art. 6.1 GDPR for the sharing and, where applicable, the subsequent processing of personal data?",
        description="These options come from GDPR Article 6. \nYou may get assistance from your institute's DPO or legal team in filling out this section.",
        validators=[DataRequired()],
    )

    # Scope of data subjects
    has_special_subjects = BooleanField(
        'Does the dataset contain data from "Special subjects"?',
        description='"Special subjects" refers to minors or subjects unable to give consent e.g. mentally impaired subjects.',
        default=False,
    )
    special_subjects_notes = TextAreaField(
        "Please provide a brief description of these Special Data Subjects.",
        description="",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    # Technical Metadata Section
    number_of_records = IntegerField(
        "Number of records",
        description="Please specify the approximate number of records/subjects in the dataset.",
        validators=[Optional()],
    )

    dataset_version = StringField(
        "Dataset version",
        description="Please specify the version of the dataset (e.g., v1.0, v2.1).",
        render_kw={"placeholder": "v1.0"},
        validators=[Optional()],
    )

    creation_date = DateField(
        "Creation date",
        description="This date is set automatically when the dataset is created.",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    last_update_date = DateField(
        "Last update date",
        description="This date is updated automatically when the dataset is saved.",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    data_standards = SelectMultipleField(
        "Data standards",
        description="Please select the data standards used in this dataset (e.g., CDISC, MINSEQE, NCIt, EDAM).",
        validators=[Optional()],
    )

    file_types = SelectMultipleField(
        "File types",
        description="Please select the file types/formats included in this dataset.",
        validators=[Optional()],
    )

    byte_size = StringField(
        "Byte size",
        description="Please provide an estimate of the total dataset size (e.g., '10 GB', '500 MB', '2 TB').",
        render_kw={"placeholder": "e.g., 10 GB"},
        validators=[Optional()],
    )

    sample_types = SelectMultipleField(
        "Types of samples collected",
        description="If biological samples are included, please specify the types (e.g., blood, tissue, DNA).",
        validators=[Optional()],
    )

    # Fields from former DatasetHostedForm (use_case_2)
    consent_status_code = SelectField(
        "Are the consents heterogeneous or homogeneous?",
        description="\nIf the consent form has changed throughout the course of the study in a way that changes the usage restrictions on data then this case is considered heterogeneous.\nIf the consent form has stayed the same over the course of the study but it has options so that different subjects can create different restrictions on their data, then this case is also considered heterogeneous.",
        validators=[DataRequired()],
    )
    consent_notes = TextAreaField(
        "If the consent is heterogeneous, please specify the data dictionary item (column) that specifies consent groups in data.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    # Consent and ethics

    restriction_rs = BooleanField(
        "Limited scope of research. \nIs data consented to be used only in specific research/disease areas?",
        description="",
        default=False,
    )
    restriction_rs_notes = TextAreaField(
        "Please describe research/disease areas restriction on data",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_gs = BooleanField(
        "Geographical restriction.\nDoes consent contain clauses that put geographical restrictions to the sharing of data?",
        description="",
        default=False,
    )
    restriction_gs_notes = TextAreaField(
        "Please describe geographical restrictions on data",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_user_specific = BooleanField(
        "Restricted type of recipients.\nDoes the consent limit the type of recipients?",
        description="",
        default=False,
    )
    restriction_user_specific_notes = TextAreaField(
        "Please describe the recipient restrictions on data.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_pub = BooleanField(
        "Are there any requirements in case of publications based on the data?",
        description="",
        default=False,
    )
    restriction_pub_notes = TextAreaField(
        "Please describe the publication requirements.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    restriction_ts = BooleanField(
        "Retention time.\nDoes the consent contain clauses that put time-limits on the use of data?",
        description="",
        default=False,
    )
    restriction_ts_notes = TextAreaField(
        "Please describe the time-limit restrictions on data.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    # Specific data use conditions

    use_restriction_project = BooleanField(
        "Is the use of data limited to the project named in the Submission sheet?",
        description="",
        default=False,
    )
    use_restriction_research_use = BooleanField(
        "Does the limitation to the RESEARCH PROJECT include the RESEARCH USE (as defined in the Consortium Agreement)?",
        description="",
        default=False,
    )

    restriction_ts_lcsb = BooleanField(
        "Is the data being sent to ELIXIR-LU/LCSB for a limited duration?",
        description="",
        default=False,
    )
    restriction_ts_lcsb_date = DateField(
        "Please state the agreed end date for data's residence at ELIXIR-LU/LCSB",
        description="",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    restriction_rtn = BooleanField(
        "Is there a requirement to return data or documents to the database/resource?",
        description="",
        default=False,
    )
    restriction_rtn_notes = TextAreaField(
        "Please describe the return requirements.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_us = BooleanField(
        "Is the use limited to approved users/groups/institutions?",
        description="",
        default=False,
    )
    restriction_us_notes = TextAreaField(
        "Please list the specific users/groups/institutions to which ELIXIR-LU/LCSB is instructed to give access to the data upon request.",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_ip = BooleanField(
        "Are there any conditions/restrictions regarding the Intellectual Property (IP) of the data?",
        description="",
        default=False,
    )
    restriction_ip_notes = TextAreaField(
        "Please describe the IP conditions/restrictions",
        render_kw={"rows": 3},
        description="",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    restriction_other_notes = TextAreaField(
        "If there are any other restrictions on data, please describe them here.",
        render_kw={"rows": 3},
        description="If applicable, in your description you may refer to GA4GH Data Use Category Codes, found at the below link.\nhttps://www.ga4gh.org/wp-content/uploads/DataUseBeacon_160209_tab_0.pdf",
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )
    access_form_required = BooleanField(
        "Will all researchers accessing the data need to sign an access request form?",
        description="If an access request form is needed, please make sure you provide the form template as a supporting document to the submission.",
        default=False,
    )
    dac_approval_required = BooleanField(
        "Will access require Data Access Committee (DAC) approval?",
        description="",
        default=False,
    )
    dac_approval_notes = TextAreaField(
        "If a DAC Approval is needed please describe the required procedure.",
        render_kw={"rows": 3},
        description="",
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
        self.data_standards.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["data_standards"]
        ]
        self.file_types.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["file_types"]
        ]
        self.sample_types.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["sample_types"]
        ]
        lb_lookup = [(c.code, c.label) for c in LegalBasisType.query.all()]
        self.legal_basis_sharing_std_code.choices = lb_lookup
        self.legal_basis_collection_std_code.choices = lb_lookup
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
        self.consent_status_code.choices = [
            (c.code, c.label) for c in ConsentStatus.query.all()
        ]

    def validate_last_update_date(self, field):
        if self.creation_date.data and field.data:
            if field.data < self.creation_date.data:
                raise ValidationError("Last update date must be after creation date.")

    def validate_creators(self, field):
        if not any(
            entry.first_name.data or entry.last_name.data or entry.email.data
            for entry in field.entries
        ):
            raise ValidationError("At least one creator is required.")

        for entry in field.entries:
            if not any(
                [
                    entry.first_name.data,
                    entry.last_name.data,
                    entry.email.data,
                    entry.institution.data,
                    entry.role.data,
                ]
            ):
                raise ValidationError("Creator entries cannot be empty.")
