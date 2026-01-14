from elixir_dss import db
from elixir_dss.models.security import Role
from elixir_dss.models.submission import (
    ConsentStatus,
    ContactType,
    DeIdentificationType,
    LegalBasisType,
    SubjectCategory,
)

INIT_DATA = {
    "names_roles": ["data_steward", "admin", "user"],
    "contact_types": [
        "Principal_Investigator",
        "Researcher",
        "Data_Manager",
        "Data_Protection_Officer",
        "Legal_Representative",
        "Other",
    ],
    "deidentification_type": [["p", "Pseudonymised"], ["a", "Anonymised"]],
    "subject_category": [
        ["ca", "Cases"],
        ["co", "Controls"],
        ["ca_co", "Cases_and_Controls"],
    ],
    "consent_status": [
        ["hm", "Homogeneous"],
        ["ht", "Heterogeneous"],
        ["dk", "Don't know"],
    ],
    "legal_basis": [
        ["61a", "Consent (6.1(a))"],
        [
            "61b",
            "Performance of a contract to which the data subject is party (6.1(b))",
        ],
        [
            "61c",
            "Compliance with a legal obligation to which the controller is subject (6.1(c))",
        ],
        ["61d", "Protection the vital interests of the data subject (6.1(d))"],
        ["61e", "Public interest (6.1(e))"],
        ["61f", "Legitimate interest (6.1(f))"],
    ],
}


def seed_init_data():
    if not db.session.query(ContactType).first():
        for contact_type in INIT_DATA["contact_types"]:
            db.session.add(ContactType(name=contact_type))

    if not db.session.query(Role).first():
        for name_role in INIT_DATA["names_roles"]:
            db.session.add(Role(name=name_role))

    if not db.session.query(DeIdentificationType).first():
        for deid_type in INIT_DATA["deidentification_type"]:
            db.session.add(DeIdentificationType(code=deid_type[0], label=deid_type[1]))

    if not db.session.query(SubjectCategory).first():
        for subj_cat in INIT_DATA["subject_category"]:
            db.session.add(SubjectCategory(code=subj_cat[0], label=subj_cat[1]))

    if not db.session.query(LegalBasisType).first():
        for lb_type in INIT_DATA["legal_basis"]:
            db.session.add(LegalBasisType(code=lb_type[0], label=lb_type[1]))

    if not db.session.query(ConsentStatus).first():
        for cons_status in INIT_DATA["consent_status"]:
            db.session.add(ConsentStatus(code=cons_status[0], label=cons_status[1]))

    db.session.commit()
