import factory
from datetime import date
from factory.alchemy import SQLAlchemyModelFactory

from elixir_dss import db
from elixir_dss.models.submission import (
    Submission,
    SubmissionDataset,
    SubmissionStatusEnum,
)


class ProjectFactory(factory.Factory):
    class Meta:
        model = dict

    external_id = factory.Sequence(lambda n: f"ELU_P_{n + 1}")
    name = factory.Faker("company")
    acronym = factory.LazyAttribute(lambda obj: obj.name[:3].upper())


class PartnerFactory(factory.Factory):
    class Meta:
        model = dict

    external_id = factory.Sequence(lambda n: f"ELU_I_{n + 1}")
    name = factory.Faker("company")
    acronym = factory.LazyAttribute(lambda obj: obj.name[:3].upper())


class SubmissionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Submission
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    title = factory.Faker("sentence", nb_words=4)
    institution_accession = "ELU_I_77"
    submission_scope_code = "e"
    current_status = SubmissionStatusEnum.draft
    created_on = factory.LazyFunction(date.today)


class SubmissionDatasetFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SubmissionDataset
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    title = factory.Faker("sentence", nb_words=3)
    gdpr_datatypes_json = '["genetic"]'
    sci_datatypes_json = '["genomics"]'
    de_identification_type_code = "p"
    legal_basis_collection_std_code = "61a"
    legal_basis_sharing_std_code = "61a"
    legal_basis_collection_spec_code = "61a"
    legal_basis_sharing_spec_code = "61a"
