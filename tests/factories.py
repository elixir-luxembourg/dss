import factory
from datetime import date
from factory.alchemy import SQLAlchemyModelFactory

from elixir_dss import db
from elixir_dss.models.security import User
from elixir_dss.models.services import register_new_user
from elixir_dss.models.submission import (
    Contact,
    ContactType,
    Submission,
    SubmissionAccess,
    SubmissionDataset,
    SubmissionStatusEnum,
    SubmissionStudy,
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
    ref_name = factory.Sequence(lambda n: f"submission-{n}")
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
    dataset_type_code = "use_case_1"
    creator_name = factory.Faker("name")
    creator_email = factory.Faker("email")
    creator_institution = factory.Faker("company")
    creator_role = "Principal Investigator"
    description = factory.Faker("text", max_nb_chars=200)
    gdpr_datatypes_json = '["genetic"]'
    sci_datatypes_json = '["genomics"]'
    de_identification_type_code = "p"
    legal_basis_collection_std_code = "61a"
    legal_basis_sharing_std_code = "61a"
    legal_basis_collection_spec_code = "61a"
    legal_basis_sharing_spec_code = "61a"


class SubmissionStudyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = SubmissionStudy
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("catch_phrase")
    description = factory.Faker("text", max_nb_chars=200)
    website = factory.Faker("url")
    ethics_approval_exists = True
    ethics_approval_no = factory.Sequence(lambda n: f"ETH-{n + 1:04d}")
    study_types_json = '["observational", "interventional"]'


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    elixir_sub_id = factory.LazyAttribute(lambda obj: obj.email)
    email = factory.Faker("email")
    institution_accession = factory.Sequence(lambda n: f"ELU_I_{n + 1}")
    active_user = True
    phone_no = factory.Faker("phone_number")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user_instance = super()._create(model_class, *args, **kwargs)
        return register_new_user(user_instance)


class ContactFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Contact
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    firstname = factory.Faker("first_name")
    lastname = factory.Faker("last_name")
    email = factory.Faker("email")
    address = factory.Faker("address")
    contact_category = factory.LazyFunction(lambda: ContactType.query.get_or_404(1))
    category_id = 1


class SubmissionAccessFactory(SQLAlchemyModelFactory):
    class Meta:
        model = SubmissionAccess
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    submission_id = factory.SubFactory(SubmissionFactory)
    user_id = factory.SubFactory(UserFactory)
    access_granted_on = factory.LazyFunction(date.today)
