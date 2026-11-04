from werkzeug.datastructures import ImmutableMultiDict

from elixir_dss.forms import SignupForm
from elixir_dss.forms.submission_datasets_forms import DatasetCreatorForm
from elixir_dss.forms.submissions_forms import ContactForm, StudyForm
from tests import BaseTest

__author__ = "Pinar Alper"


class FormValidatorsTest(BaseTest):
    def test_signup_form(self):
        f1 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar",
            last_name="á è í ö â ñ ç ř α Š ",
            phone_no="125736 87--34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
        )

        self.assertTrue(f1.validate())

        f2 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar1 23 ",
            last_name="è í ö â ñ ç ř α Š",
            phone_no="125736 87--34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
        )
        self.assertTrue(f2.validate())

        f3 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar",
            last_name="Alper958945",
            phone_no="125736 87<tags></tags>34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
        )
        self.assertFalse(f3.validate())
        print(f3.errors)

        f4 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar",
            last_name="Alper",
            phone_no="125736 87-DROP TABLE;-34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
            addr_line1=None,
            addr_line2=None,
        )
        self.assertFalse(f4.validate())
        print(f4.errors)

        f5 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar<>",
            last_name="Alper",
            phone_no="125736 87--34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
        )
        self.assertFalse(f5.validate())
        print(f5.errors)

        f6 = SignupForm(
            elixir_sub_id="DUMMY ELIXIR SUB ID NOT VALIDATED",
            first_name="Pinar",
            last_name="Alper",
            phone_no="+44 125736 87--34 ",
            institution_accession="ELU_I_77",
            email="pinar.alper@uni.lu",
            addr_line1="2 Rue John Lennon",
            addr_line2="BELVAL-894375",
        )

        self.assertTrue(f6.validate())


class StudyFormTest(BaseTest):
    @staticmethod
    def _contact(idx=0, main=True):
        base = [
            (f"study_contacts-{idx}-first_name", "John"),
            (f"study_contacts-{idx}-last_name", "Doe"),
            (f"study_contacts-{idx}-email", f"contact{idx}@example.com"),
            (f"study_contacts-{idx}-institution", "Test University"),
            (f"study_contacts-{idx}-category_id", "1"),
        ]
        return base + [(f"study_contacts-{idx}-is_main_contact", "y")] if main else base

    def test_valid_minimal_study(self):
        with self.app.app_context():
            form = StudyForm(
                ImmutableMultiDict(
                    [
                        ("name", "Test Study"),
                        ("description", "Study description"),
                        ("study_types", "Observational"),
                        *self._contact(0, main=True),
                    ]
                )
            )
            self.assertTrue(form.validate(), f"Errors: {form.errors}")

    def test_requires_main_contact(self):
        with self.app.app_context():
            form = StudyForm(
                ImmutableMultiDict(
                    [
                        ("name", "Test Study"),
                        ("description", "Description"),
                        ("study_types", "Observational"),
                        *self._contact(0, main=False),
                    ]
                )
            )
            self.assertFalse(form.validate())
            self.assertIn("study_contacts", form.errors)

    def test_negative_number_of_subjects_rejected(self):
        with self.app.app_context():
            form = StudyForm(
                ImmutableMultiDict(
                    [
                        ("name", "Test Study"),
                        ("description", "Description"),
                        ("study_types", "Observational"),
                        ("number_of_subjects", "-10"),
                        *self._contact(0, main=True),
                    ]
                )
            )
            self.assertFalse(form.validate())
            self.assertIn("number_of_subjects", form.errors)


class ContactFormTest(BaseTest):
    def test_main_contact_requires_institution(self):
        """main contact must have institution"""
        with self.app.app_context():
            form = ContactForm(
                ImmutableMultiDict(
                    [
                        ("first_name", "John"),
                        ("last_name", "Doe"),
                        ("email", "john@example.com"),
                        ("category_id", "1"),
                        ("is_main_contact", "y"),
                    ]
                )
            )
            self.assertFalse(form.validate())
            self.assertIn("institution", form.errors)

    def test_invalid_email_rejected(self):
        """invalid format rejected"""
        with self.app.app_context():
            form = ContactForm(
                ImmutableMultiDict(
                    [
                        ("first_name", "Test"),
                        ("last_name", "User"),
                        ("email", "not-an-email"),
                        ("category_id", "1"),
                    ]
                )
            )
            self.assertFalse(form.validate())
            self.assertIn("email", form.errors)


class DatasetCreatorFormTest(BaseTest):
    def _form(self, orcid):
        return DatasetCreatorForm(
            ImmutableMultiDict(
                [
                    ("first_name", "Josiah"),
                    ("last_name", "Carberry"),
                    ("email", "josiah@example.com"),
                    ("institution", "Brown University"),
                    ("role", "PI"),
                    ("orcid", orcid),
                ]
            )
        )

    def test_orcid_optional(self):
        with self.app.app_context():
            form = self._form("")
            self.assertTrue(form.validate(), form.errors)

    def test_orcid_valid(self):
        with self.app.app_context():
            for value, expected in (
                ("0000-0001-9235-8496", "0000-0001-9235-8496"),
                (" https://orcid.org/0000-0001-9235-8496 ", "0000-0001-9235-8496"),
                ("orcid.org/0000-0002-1694-233x", "0000-0002-1694-233X"),
            ):
                form = self._form(value)
                self.assertTrue(form.validate(), (value, form.errors))
                self.assertEqual(form.orcid.data, expected)

    def test_orcid_invalid(self):
        with self.app.app_context():
            for value in (
                "0000-0002-1825-009",
                "0000000218250097",
                "0000-0002-1825-0098",  # wrong check digit
                "https://example.org/0000-0001-9235-8496",
            ):
                form = self._form(value)
                self.assertFalse(form.validate(), value)
                self.assertIn("orcid", form.errors)
