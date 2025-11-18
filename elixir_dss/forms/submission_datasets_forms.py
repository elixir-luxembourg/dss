from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    EmailField,
    HiddenField,
    IntegerField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, Regexp, NumberRange
from wtforms_components import SelectField, SelectMultipleField

from elixir_dss import app
from elixir_dss.models.submission import (
    ConsentStatus,
    DeIdentificationType,
    LegalBasisType,
    SubjectCategory,
    SubmissionStudy,
)

from .validators import OptionalFieldValidator


class DatasetForm(FlaskForm):
    id = HiddenField("dataset_Id")
    submission_id = HiddenField("Submission_Id")
    internal_id = StringField("Internal ID", render_kw={"readonly": True})

    creator_name = StringField(
        "Creator(s) - Full Name",
        description="Please provide the full name(s) of the dataset creator(s).",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
    )
    creator_email = EmailField(
        "Creator(s) - Email",
        description="Please provide the email address(es) of the dataset creator(s).",
        validators=[
            DataRequired(),
            Email("This field requires a valid email address."),
        ],
    )
    creator_institution = StringField(
        "Creator(s) - Institution",
        description="Please provide the institution(s) of the dataset creator(s).",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            ),
        ],
    )
    creator_role = StringField(
        "Creator(s) - Role",
        description="Please specify the role(s) of the dataset creator(s) (e.g., Principal Investigator, Researcher).",
        validators=[
            DataRequired(),
            Regexp(
                r"^[\w\s,\-_]+$",
                message="Can only contain letters, digits, dash, underscore and spaces.",
            ),
        ],
    )
    description = TextAreaField(
        "Dataset Description",
        description="Please provide a detailed description of the dataset.",
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

    gdpr_datatypes = SelectMultipleField(
        "GDPR Personal data categories in the dataset",
        description="These are overarching categories of personal data as defined in GDPR Art. 9.1 and Art. 10. You may get assistance from your institute’s DPO or legal team in filling out this field. \
                                                    You can select multiple options.",
        validators=[DataRequired()],
    )
    gdpr_datatypes_notes = TextAreaField(
        "Personal data - Remarks",
        description="In case of 'other special categories of data', please specify.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

    # GDPR Art 9.2 - Only shown when special category data is selected
    has_art92_derogation = BooleanField(
        "For the processing of special category (sensitive) personal data, do you have a legitimation under Art. 9.2 GDPR that provides specific derogation from the general prohibition to process such data?",
        description="This question only applies if you have selected special category data above. You may get assistance from your institute's DPO or legal team.",
        default=False,
    )

    art92_derogation_notes = TextAreaField(
        "Art. 9.2 Legitimation - Remarks",
        description="If applicable, please provide details about the Art. 9.2 legitimation.",
        render_kw={"rows": 3},
        validators=[
            OptionalFieldValidator(
                regex_str=r"^[\w\s,\-.]+$",
                message="Can only contain letters, digits, dash, comma and dot.",
            )
        ],
    )

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
        "What is the legal basis according to Art. 6.1 GDPR for the sharing and, where applicable, the subsequent processing of standard (non-sensitive) personal data?",
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

    # Technical Metadata Section
    number_of_records = IntegerField(
        "Number of records",
        description="Please specify the approximate number of records/subjects in the dataset.",
    )

    dataset_version = StringField(
        "Dataset version",
        description="Please specify the version of the dataset (e.g., v1.0, v2.1).",
        render_kw={"placeholder": "v1.0"},
    )

    creation_date = DateField(
        "Creation date",
        description="This date is set automatically when the dataset is created.",
        format="%Y-%m-%d",
        render_kw={"readonly": True},
    )

    last_update_date = DateField(
        "Last update date",
        description="This date is updated automatically when the dataset is saved.",
        format="%Y-%m-%d",
        render_kw={"readonly": True},
    )

    data_standards = SelectMultipleField(
        "Data standards",
        description="Please select the data standards used in this dataset (e.g., CDISC, MINSEQE, NCIt, EDAM).",
    )

    file_types = SelectMultipleField(
        "File types",
        description="Please select the file types/formats included in this dataset.",
    )

    byte_size = StringField(
        "Byte size",
        description="Please provide an estimate of the total dataset size (e.g., '10 GB', '500 MB', '2 TB').",
        render_kw={"placeholder": "e.g., 10 GB"},
    )

    sample_types = SelectMultipleField(
        "Types of samples collected",
        description="If biological samples are included, please specify the types (e.g., blood, tissue, DNA).",
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
        self.legal_basis_sharing_spec_code.choices = lb_lookup
        self.legal_basis_collection_spec_code.choices = lb_lookup
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


class DatasetHostedForm(DatasetForm):
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
    use_restriction_project = BooleanField(
        "Use of DATA is limited to the RESEARCH PROJECT. Is the use of data limited to the project named in the Submission sheet?",
        default=False,
    )
    use_restriction_research_use = BooleanField(
        "Does the limitation to the RESEARCH PROJECT include the RESEARCH USE (as defined in the Consortium Agreement)?",
        default=False,
    )
    data_type_bg_or_result = SelectMultipleField(
        "Is the data Background or Results as defined in the Consortium Agreement?",
        description="Select all that apply.",
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consent_status_code.choices = [
            (c.code, c.label) for c in ConsentStatus.query.all()
        ]
        self.data_type_bg_or_result.choices = [
            (c, c) for c in app.config.get("DATA_INIT")["data_bg_or_result_types"]
        ]
