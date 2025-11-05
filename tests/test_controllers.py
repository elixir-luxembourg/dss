from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from flask import url_for
from elixir_dss import db

from elixir_dss.models.security import User
from elixir_dss.models.services import create_sub
from elixir_dss.models.submission import (
    SubmissionDataset,
    SubmissionStatusEnum,
)
from elixir_dss.clients.lft import LFTLink
from tests import BaseIntegrationTest
from tests.factories import (
    SubmissionDatasetFactory,
    SubmissionFactory,
    SubmissionStudyFactory,
)

__author__ = "Pinar Alper"


class ControllersTest(BaseIntegrationTest):
    def test_get_submissions(self):
        users = User.query.all()
        self.assertEqual(4, len(users))

        self.login("steward1@uni.lu", "steward1")

        response = self.client.get(url_for("list_submissions"))

        self.assertIn(
            "No submissions have been added yet.", response.data.decode("utf-8")
        )

    def test_access_control2(self):
        self.login("steward1@uni.lu", "steward1")

        #
        # User with an admin  role cannot access the following end point
        #

        response = self.client.get(url_for("list_my_submissions"))
        self.assert403(response)

    def test_access_control1(self):
        self.login("submitter2@some.edu", "submitter2")

        #
        # User with a data provider role cannot access the following end points
        #

        response = self.client.get(url_for("list_submissions"))
        self.assert403(response)

        response = self.client.get(url_for("edit_user", user_id=0))
        self.assert403(response)

        response = self.client.get(url_for("revert_submission", sub_id=0))
        self.assert403(response)

        response = self.client.get(url_for("send_notification", notification_id=0))
        self.assert403(response)

        response = self.client.get(url_for("list_notifications"))
        self.assert403(response)

    def test_submission_create_submission(self):
        self.login("steward1@uni.lu", "steward1")

        create_submission_url = url_for("create_submission")
        response = self.client.post(
            create_submission_url,
            data={"title": "Test Submission 123", "institution_accession": "ELU_I_9"},
            follow_redirects=True,
        )
        data = response.data.decode("utf-8")
        self.assert200(response)
        self.assertIn("New submission", data)
        self.assertIn("created", data)

    def test_user_cannot_change_keycloak_managed_fields(self):
        self.login("submitter1@some.edu", "submitter1")
        user = User.query.filter_by(email="submitter1@some.edu").first()
        self.client.post(
            url_for("edit_user", user_id=user.id),
            data={
                "first_name": "Hacker",
                "last_name": "Changed",
                "email": "hacked@evil.com",
                "elixir_sub_id": "EVIL_ID",
                "phone_no": "+352111111111",
            },
            follow_redirects=True,
        )
        db.session.refresh(user)
        self.assertNotEqual(user.first_name, "Hacker")
        self.assertNotEqual(user.last_name, "Changed")
        self.assertNotEqual(user.email, "hacked@evil.com")
        self.assertNotEqual(user.elixir_sub_id, "EVIL_ID")

    def test_user_can_edit_only_their_profile(self):
        self.login("submitter1@some.edu", "submitter1")
        User.query.filter_by(email="submitter1@some.edu").first()
        response = self.client.post(
            url_for("profile"),
            data={"phone_no": "+352987654321"},
            follow_redirects=True,
        )
        self.assert200(response)

        other_user = User.query.filter_by(email="submitter2@some.edu").first()
        response = self.client.post(
            url_for("edit_user", user_id=other_user.id),
            data={"phone_no": "+352000000000"},
            follow_redirects=False,
        )
        self.assert403(response)

    def test_data_steward_can_create_submission(self):
        self.login("steward1@uni.lu", "steward1")
        response = self.client.post(
            url_for("create_submission"),
            data={"title": "Steward Submission", "institution_accession": "ELU_I_9"},
            follow_redirects=True,
        )
        self.assert200(response)
        self.assertIn("New submission", response.data.decode())

    def test_data_admin_cannot_create_submission(self):
        self.login("admin@uni.lu", "admin")
        response = self.client.post(
            url_for("create_submission"),
            data={"title": "Steward Submission", "institution_accession": "ELU_I_9"},
            follow_redirects=True,
        )
        self.assert403(response)

    def test_admin_can_edit_other_users(self):
        self.login("admin@uni.lu", "admin")
        user_to_edit = User.query.filter_by(email="submitter1@some.edu").first()
        response = self.client.post(
            url_for("edit_user", user_id=user_to_edit.id),
            data={"id": user_to_edit.id, "institution_accession": "ELU_I_EDITED"},
            follow_redirects=True,
        )
        self.assert200(response)

    def test_dataset_link(self):
        self.login("steward1@uni.lu", "steward1")

        submission = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        dataset = SubmissionDatasetFactory(submission_id=submission.id)
        mock_link = LFTLink(
            id="test_link_id",
            absolute_url="https://lft.example.com/links/test_link",
            expiration_date=datetime.now() + timedelta(days=1),
            password="test_password",
        )

        with patch("elixir_dss.controllers.web_controllers.lft") as mock_lft:
            mock_lft.client = MagicMock()
            mock_lft.get_or_create_link.return_value = mock_link

            response = self.client.get(
                url_for("dataset_link", dataset_id=dataset.id, sub_id=submission.id)
            )
            self.assert200(response)
            data = response.data.decode("utf-8")
            self.assertIn("test_link", data)

            mock_lft.get_or_create_link.assert_called_once_with(
                dataset=dataset, sub=submission.ref_name
            )

    def test_add_submission_dataset(self):
        self.login("steward1@uni.lu", "steward1")

        submission = create_sub("Test Submission", "ELU_I_9")
        study = SubmissionStudyFactory(submission_id=submission.id)

        get_response = self.client.get(
            url_for("add_submission_dataset", sub_id=submission.id)
        )
        self.assert200(get_response)

        response = self.client.post(
            url_for("add_submission_dataset", sub_id=submission.id),
            data={
                "submission_id": submission.id,
                "title": "Test_Dataset",
                "study_id": study.id,
                "gdpr_datatypes": ["genetic"],
                "sci_datatypes": ["Whole_genome_sequencing"],
                "de_identification_type_code": "p",
                "legal_basis_collection_std_code": "61a",
                "legal_basis_sharing_std_code": "61a",
                "legal_basis_collection_spec_code": "61a",
                "legal_basis_sharing_spec_code": "61a",
                "subject_category_code": "ca",
                "consent_status_code": "hm",
            },
            follow_redirects=True,
        )
        self.assert200(response)

        dataset = SubmissionDataset.query.filter_by(submission_id=submission.id).first()
        self.assertIsNotNone(dataset)
        self.assertIsNotNone(dataset.external_id)
        self.assertEqual("Test_Dataset", dataset.title)
