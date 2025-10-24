import factory


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
