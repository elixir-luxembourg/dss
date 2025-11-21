from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from flask import url_for
from elixir_dss import db, lft

from elixir_dss.models.security import User
from elixir_dss.models.services import (
    create_sub,
    update_submission_basic_info,
)
from elixir_dss.models.submission import (
    SubmissionDataset,
    SubmissionStatusEnum,
    Submission,
)
from elixir_dss.clients.lft import LFTLink
from tests import BaseIntegrationTest
from tests.factories import (
    SubmissionDatasetFactory,
    SubmissionFactory,
    SubmissionStudyFactory,
    ContactFactory,
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
        study = SubmissionStudyFactory(submission_id=submission.id)
        dataset = SubmissionDatasetFactory(
            submission_id=submission.id, study_id=study.id
        )
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

        submission = create_sub("ELU_I_9")
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
                "creator_name": "John Doe",
                "creator_email": "john.doe@example.com",
                "creator_institution": "Test University",
                "creator_role": "Principal Investigator",
                "description": "Test dataset description",
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
        self.assertIsNotNone(dataset.internal_id)
        self.assertEqual("Test_Dataset", dataset.title)

    def test_delete_submission(self):
        self.login("steward1@uni.lu", "steward1")

        submission = SubmissionFactory(current_status=SubmissionStatusEnum.draft)
        db.session.commit()
        delete_url = url_for("delete_submission", sub_id=submission.id)

        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, len(db.session.query(Submission).all()))

        submission_non_deletable = SubmissionFactory(
            current_status=SubmissionStatusEnum.completed
        )
        db.session.commit()
        non_deletable_url = url_for(
            "delete_submission", sub_id=submission_non_deletable.id
        )

        response_bad_request = self.client.delete(non_deletable_url)
        self.assertEqual(response_bad_request.status_code, 400)

    def test_provider_can_cancel_submission(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = create_sub("ELU_I_77")
        db.session.add(sub)
        db.session.commit()

        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": "integration test"},
            follow_redirects=True,
        )

        self.assert200(resp)
        sub = Submission.query.get(sub.id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.cancelled)

    def test_lft_links_deleted_on_submission_cancel(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = create_sub("ELU_I_100")
        db.session.add(sub)
        db.session.flush()

        study = SubmissionStudyFactory(submission_id=sub.id)
        db.session.add(study)
        db.session.flush()

        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        SubmissionDatasetFactory(
            submission_id=sub.id, internal_id="ds1", study_id=study.id
        )
        SubmissionDatasetFactory(
            submission_id=sub.id, internal_id="ds2", study_id=study.id
        )
        db.session.flush()

        original_client = lft.client
        try:
            mock_client = MagicMock()
            lft.client = mock_client
            lft.namespace_id = "ns"
            lft.username = "user"
            lft.password = "pass"

            link1 = MagicMock(hashid="link_ds1")
            link2 = MagicMock(hashid="link_ds2")

            mock_client.links_list.side_effect = [
                [link1],
                [link2],
            ]

            resp = self.client.post(
                url_for("cancel_submission", sub_id=sub.id),
                data={"cancellation_reason": "testing LFT cleanup"},
                follow_redirects=True,
            )
            self.assert200(resp)

            expected_calls_links_list = [
                call(namespace_id="ns", share_name="ds1", sub=None),
                call(namespace_id="ns", share_name="ds2", sub=None),
            ]
            mock_client.links_list.assert_has_calls(
                expected_calls_links_list, any_order=True
            )
            self.assertEqual(mock_client.links_list.call_count, 2)

            expected_calls_delete = [
                call(namespace_id="ns", share_name="ds1", link="link_ds1"),
                call(namespace_id="ns", share_name="ds2", link="link_ds2"),
            ]
            mock_client.delete_link.assert_has_calls(
                expected_calls_delete, any_order=True
            )
            self.assertEqual(mock_client.delete_link.call_count, 2)

        finally:
            lft.client = original_client

    def test_cannot_modify_cancelled_submission(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = create_sub("ELU_I_200")
        db.session.add(sub)
        db.session.commit()

        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        cancel_resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": "Testing modification block"},
            follow_redirects=True,
        )
        self.assert200(cancel_resp)

        sub = Submission.query.get(sub.id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.cancelled)

        response = self.client.post(
            url_for("add_submission_dataset", sub_id=sub.id),
            data={
                "submission_id": sub.id,
                "title": "Should_Not_Work",
                "gdpr_datatypes": ["genetic"],
                "sci_datatypes": ["Whole_genome_sequencing"],
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("cancelled", response.data.decode("utf-8"))

        dataset_count = SubmissionDataset.query.filter_by(submission_id=sub.id).count()
        self.assertEqual(dataset_count, 0)

    def test_require_can_steer_submission_user_blocked_in_forbidden_phases(self):
        self.login("submitter1@some.edu", "submitter1")

        forbidden_statuses = [
            SubmissionStatusEnum.draft,
            SubmissionStatusEnum.metadata_approval,
            SubmissionStatusEnum.data_approval,
        ]

        for status in forbidden_statuses:
            sub = SubmissionFactory(current_status=status)
            user = User.query.filter_by(email="submitter1@some.edu").first()
            update_submission_basic_info(sub, provider_user_ids=[user.id])
            db.session.commit()

            resp = self.client.get(url_for("steer_submission", sub_id=sub.id))
            self.assert403(resp)
            self.assertIn("not allowed to steer", resp.data.decode())

    def test_require_can_steer_submission_user_allowed_in_other_phases(self):
        self.login("submitter1@some.edu", "submitter1")

        allowed_statuses = [
            SubmissionStatusEnum.metadata_submission,
            SubmissionStatusEnum.data_upload,
        ]

        for status in allowed_statuses:
            sub = SubmissionFactory(current_status=status)
            user = User.query.filter_by(email="submitter1@some.edu").first()
            update_submission_basic_info(sub, provider_user_ids=[user.id])
            study_rec = SubmissionStudyFactory(
                submission_id=sub.id, study_contacts=[ContactFactory()]
            )
            SubmissionDatasetFactory(submission_id=sub.id, study_id=study_rec.id)
            db.session.commit()

            resp = self.client.get(url_for("steer_submission", sub_id=sub.id))
            self.assertIn(resp.status_code, (200, 204))

    def test_require_can_steer_submission_steward_always_allowed(self):
        self.login("steward1@uni.lu", "steward1")
        statuses = [
            SubmissionStatusEnum.draft,
            SubmissionStatusEnum.metadata_submission,
            SubmissionStatusEnum.metadata_approval,
            SubmissionStatusEnum.data_approval,
            SubmissionStatusEnum.data_upload,
        ]

        for status in statuses:
            sub = SubmissionFactory(current_status=status)
            db.session.commit()
            user = User.query.filter_by(email="steward1@uni.lu").first()
            update_submission_basic_info(sub, provider_user_ids=[user.id])
            study_rec = SubmissionStudyFactory(
                submission_id=sub.id, study_contacts=[ContactFactory()]
            )
            SubmissionDatasetFactory(submission_id=sub.id, study_id=study_rec.id)
            db.session.commit()

            resp = self.client.get(url_for("steer_submission", sub_id=sub.id))
            self.assertIn(resp.status_code, (200, 204))

    def test_require_metadata_access_blocks_user_outside_metadata_submission(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        study_rec = SubmissionStudyFactory(
            submission_id=sub.id, study_contacts=[ContactFactory()]
        )
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study_rec.id)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        resp = self.client.get(
            url_for("edit_submission_dataset", dataset_id=dataset.id)
        )
        self.assert403(resp)
        self.assertIn("no longer edit", resp.data.decode())

        resp = self.client.get(url_for("add_submission_dataset", sub_id=sub.id))
        self.assert403(resp)

    def test_require_metadata_access_allows_user_during_metadata_submission(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        study_rec = SubmissionStudyFactory(
            submission_id=sub.id, study_contacts=[ContactFactory()]
        )
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study_rec.id)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        resp = self.client.get(
            url_for("edit_submission_dataset", dataset_id=dataset.id)
        )
        self.assert200(resp)

    def test_require_metadata_access_for_study(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)

        resp = self.client.get(url_for("edit_submission_study", study_id=study.id))
        self.assert403(resp)
