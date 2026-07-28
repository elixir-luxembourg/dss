import io
import json
import os
import tempfile
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from flask import url_for
import pytest
from elixir_dss import app, db, lft

from elixir_dss.models.security import User
from elixir_dss.models.services import (
    create_sub,
    steer_sub,
    update_submission_basic_info,
)
from elixir_dss.models.submission import (
    EmailNotification,
    SubmissionAttachment,
    SubmissionDataset,
    SubmissionMessage,
    SubmissionStatusEnum,
    SubmissionStudy,
    Submission,
)
from elixir_dss.clients.lft import LFTLink
from elixir_dss.clients.idservice import IDServiceError
from elixir_dss.exceptions import RecordLifecycleException
from elixir_dss.controllers.errors import csrf_error
from elixir_dss.controllers.utils import dict_list_lookup
from elixir_dss.controllers.web_controllers import load_user
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import OperationalError
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
        self.assert404(response)

        response = self.client.get(url_for("send_notification", notification_id=0))
        self.assert403(response)

        response = self.client.get(url_for("list_notifications"))
        self.assert403(response)

    def test_submission_create_submission(self):
        self.login("steward1@uni.lu", "steward1")
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        create_submission_url = url_for("create_submission")
        response = self.client.post(
            create_submission_url,
            data={
                "institution_accession": "ELU_I_9",
                "provider_user_ids": [steward.id],
                "submission_contacts-0-first_name": "John",
                "submission_contacts-0-last_name": "Doe",
                "submission_contacts-0-email": "john.doe@example.com",
                "submission_contacts-0-category_id": "1",
            },
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
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        response = self.client.post(
            url_for("create_submission"),
            data={
                "institution_accession": "ELU_I_9",
                "provider_user_ids": [steward.id],
                "submission_contacts-0-first_name": "Jane",
                "submission_contacts-0-last_name": "Smith",
                "submission_contacts-0-email": "jane.smith@example.com",
                "submission_contacts-0-category_id": "1",
            },
            follow_redirects=True,
        )
        self.assert200(response)
        self.assertIn("New submission", response.data.decode())

    def test_data_admin_cannot_create_submission(self):
        self.login("admin@uni.lu", "admin")
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        response = self.client.post(
            url_for("create_submission"),
            data={
                "institution_accession": "ELU_I_9",
                "provider_user_ids": [steward.id],
                "submission_contacts-0-first_name": "Jane",
                "submission_contacts-0-last_name": "Smith",
                "submission_contacts-0-email": "jane.smith@example.com",
                "submission_contacts-0-category_id": "1",
            },
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

    @pytest.mark.usefixtures("mock_idservice_requests_post")
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
                "creators-0-first_name": "John",
                "creators-0-last_name": "Doe",
                "creators-0-email": "john.doe@example.com",
                "creators-0-institution": "Test University",
                "creators-0-role": "Principal Investigator",
                "description": "Test dataset description",
                "contains_personal_data": "y",
                "data_processing_type": "pseudonymised",
                "gdpr_datatypes": ["genetic"],
                "sci_datatypes": ["Whole_genome_sequencing"],
                "data_standards": ["CDISC"],
                "file_types": ["CSV (format:3752)"],
                "sample_types": ["blood"],
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
        self.assertEqual(dataset.internal_id, "TEST_DATASET_ID_001")
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
        sub = db.session.get(Submission, sub.id)
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

            resp = self.client.post(
                url_for("cancel_submission", sub_id=sub.id),
                data={"cancellation_reason": "testing LFT cleanup"},
                follow_redirects=True,
            )
            self.assert200(resp)

            expected_calls_delete = [
                call(namespace_id="ns", share_name="ds1"),
                call(namespace_id="ns", share_name="ds2"),
            ]
            mock_client.delete_share.assert_has_calls(
                expected_calls_delete, any_order=True
            )
            self.assertEqual(mock_client.delete_share.call_count, 2)

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

        sub = db.session.get(Submission, sub.id)
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
            self.assertIn("not allowed to perform this action", resp.data.decode())

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
        self.assertIn("not allowed to perform this action", resp.data.decode())

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

    def test_public_routes_accessible_without_auth(self):
        resp = self.client.get(url_for("home"))
        self.assert200(resp)

        resp = self.client.get(url_for("login"))
        self.assert200(resp)

    def test_protected_routes_require_auth(self):
        resp = self.client.get(url_for("list_submissions"))
        self.assertIn(resp.status_code, (302, 401))

    def test_user_without_access_blocked(self):
        self.login("submitter2@some.edu", "submitter2")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user1 = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user1.id])

        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert404(resp)

    def test_steward_can_access_any_submission(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)

    def test_nonexistent_entity_returns_404(self):
        self.login("steward1@uni.lu", "steward1")

        resp = self.client.get(url_for("view_submission", sub_id=99999))
        self.assert404(resp)

        resp = self.client.get(url_for("edit_submission_dataset", dataset_id=99999))
        self.assert404(resp)

    def test_delete_dataset_blocked_outside_metadata_submission(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        resp = self.client.get(
            url_for("delete_submission_dataset", dataset_id=dataset.id)
        )
        self.assert403(resp)

    def test_delete_study_blocked_outside_metadata_submission(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)

        resp = self.client.get(url_for("delete_submission_study", study_id=study.id))
        self.assert403(resp)

    @patch("elixir_dss.controllers.web_controllers._keycloak_logout_url")
    def test_logout_keycloak(self, mock_logout_url):
        self.login("submitter1@some.edu", "submitter1")

        mock_logout_url.return_value = "/kc/logout"
        self.app.config["AUTHENTICATION_METHOD"] = "IA"

        with self.client.session_transaction() as sess:
            sess["oidc_id_token"] = "fake-token"
        resp = self.client.get(url_for("logout"))

        self.assertEqual(resp.status_code, 302)
        self.assertIn("/kc/logout", resp.location)

    @patch("elixir_dss.controllers.web_controllers.reject_data")
    def test_reject_data(self, mock_reject):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory()
        db.session.commit()
        resp = self.client.post(
            url_for("reject_data_endpoint", sub_id=sub.id),
            data={"feedback": ""},
            follow_redirects=True,
        )
        self.assertIn("feedback is required", resp.data.decode().lower())

        resp = self.client.post(
            url_for("reject_data_endpoint", sub_id=sub.id),
            data={"feedback": "Not OK"},
        )

        mock_reject.assert_called_once()
        self.assertEqual(resp.status_code, 302)

    def test_delete_study_success(self):
        self.login("submitter1@some.edu", "submitter1")

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        db.session.commit()

        resp = self.client.get(url_for("delete_submission_study", study_id=study.id))
        self.assertEqual(resp.status_code, 302)

    @patch("elixir_dss.controllers.web_controllers.send_email_asynch")
    def test_send_notification(self, mock_send):
        self.login("steward1@uni.lu", "steward1")
        notif = EmailNotification(
            subject="Test Notification Subject",
            sender="noreply@uni.lu",
            recipients_json=json.dumps(["test@example.com"]),
            text_body="body",
            html_body="<p>body</p>",
            created_on=datetime.today(),
        )
        db.session.add(notif)
        db.session.commit()

        resp = self.client.get(url_for("list_notifications"))
        self.assert200(resp)
        self.assertIn("Test Notification Subject", resp.data.decode("utf-8"))

        resp = self.client.get(url_for("send_notification", notification_id=notif.id))
        self.assertEqual(resp.status_code, 204)
        mock_send.assert_called_once()

    @patch("elixir_dss.controllers.web_controllers.send_new_message_notification")
    def test_add_submission_message(self, mock_notif):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")

        resp = self.client.get(url_for("add_submission_message", sub_id=sub.id))
        self.assert200(resp)

        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        steer_sub(sub.id)

        resp = self.client.post(
            url_for("add_submission_message", sub_id=sub.id),
            data={
                "submission_id": sub.id,
                "message_text": "Test message content",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.message_text, "Test message content")
        mock_notif.assert_called_once()

    @patch("elixir_dss.controllers.reporters.DocxTemplate")
    def test_generate_submission_docx_render_failure(self, mock_docx_cls):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        mock_doc = MagicMock()
        mock_doc.render.side_effect = Exception("template error")
        mock_docx_cls.return_value = mock_doc

        with self.assertRaises(ValueError):
            self.client.get(url_for("generate_submission_docx", sub_id=sub.id))

    def test_edit_submission(self):
        self.login("steward1@uni.lu", "steward1")
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        sub = create_sub("ELU_I_9")
        update_submission_basic_info(sub, provider_user_ids=[steward.id])

        resp = self.client.get(url_for("edit_submission", sub_id=sub.id))
        self.assert200(resp)

        resp = self.client.post(
            url_for("edit_submission", sub_id=sub.id),
            data={
                "id": sub.id,
                "institution_accession": "ELU_I_9",
                "provider_user_ids": [steward.id],
                "submission_contacts-0-first_name": "John",
                "submission_contacts-0-last_name": "Doe",
                "submission_contacts-0-email": "john.doe@example.com",
                "submission_contacts-0-category_id": "1",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        db.session.expire_all()
        updated = db.session.get(Submission, sub.id)
        self.assertEqual(len(updated.submission_contacts), 1)
        self.assertEqual(updated.submission_contacts[0].first_name, "John")

    @patch("elixir_dss.controllers.reporters.DocxTemplate")
    def test_generate_submission_docx(self, mock_docx_cls):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        mock_doc = MagicMock()
        mock_docx_cls.return_value = mock_doc

        resp = self.client.get(url_for("generate_submission_docx", sub_id=sub.id))
        self.assert200(resp)
        mock_doc.render.assert_called_once()
        mock_doc.save.assert_called_once()

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_clone_submission(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        study = SubmissionStudyFactory(
            submission_id=sub.id, study_contacts=[ContactFactory()]
        )
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.get(url_for("clone_submission", submission_id=sub.id))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Submission.query.count(), 2)

    def test_cancel_submission_empty_reason(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": ""},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("Reason is required", resp.data.decode())

    def test_create_submission_get(self):
        self.login("steward1@uni.lu", "steward1")
        resp = self.client.get(url_for("create_submission"))
        self.assert200(resp)

    def test_view_submission(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)

    def test_edit_submission_dataset_get(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            sci_datatypes_json='["Whole_genome_sequencing"]',
            gdpr_datatypes_json='["genetic"]',
            data_standards_json='["CRAM"]',
            file_types_json='["fastq"]',
            sample_types_json='["tissue"]',
        )
        resp = self.client.get(
            url_for("edit_submission_dataset", dataset_id=dataset.id)
        )
        self.assert200(resp)

    @patch("elixir_dss.models.services.send_metadata_approved_notification")
    def test_approve_metadata(self, _mock_notif):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        SubmissionStudyFactory(submission_id=sub.id, study_contacts=[ContactFactory()])
        db.session.commit()

        resp = self.client.post(
            url_for("approve_metadata_endpoint", sub_id=sub.id),
            data={"feedback": "Looks good"},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        db.session.expire_all()
        updated = db.session.get(Submission, sub.id)
        self.assertEqual(updated.current_status, SubmissionStatusEnum.data_upload)

    @patch("elixir_dss.models.services.send_data_approved_notification")
    def test_approve_data(self, _mock_notif):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_approval)
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        db.session.commit()

        resp = self.client.post(
            url_for("approve_data_endpoint", sub_id=sub.id),
            data={"feedback": ""},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        db.session.expire_all()
        updated = db.session.get(Submission, sub.id)
        self.assertEqual(updated.current_status, SubmissionStatusEnum.completed)

    def test_revert_submission(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        db.session.commit()

        resp = self.client.get(url_for("revert_submission", sub_id=sub.id))
        self.assertEqual(resp.status_code, 204)

        db.session.expire_all()
        updated = db.session.get(Submission, sub.id)
        self.assertEqual(
            updated.current_status, SubmissionStatusEnum.metadata_submission
        )

    def test_add_submission_study_get(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        resp = self.client.get(url_for("add_submission_study", sub_id=sub.id))
        self.assert200(resp)

    def test_edit_submission_study_get(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        resp = self.client.get(url_for("edit_submission_study", study_id=study.id))
        self.assert200(resp)

    @patch("elixir_dss.models.services.send_metadata_rejected_notification")
    def test_reject_metadata_with_feedback(self, mock_notif):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        steward = User.query.filter_by(email="steward1@uni.lu").first()
        update_submission_basic_info(sub, provider_user_ids=[steward.id])
        db.session.commit()

        resp = self.client.post(
            url_for("reject_metadata_endpoint", sub_id=sub.id),
            data={"feedback": "Needs revision"},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        mock_notif.assert_called_once()

    def test_steer_submission_confirmed(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(
            submission_id=sub.id, study_contacts=[ContactFactory()]
        )
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.post(
            url_for("steer_submission_confirmed", sub_id=sub.id),
            data={"responsibility_ack": "on"},
            follow_redirects=True,
        )
        self.assert200(resp)

        db.session.expire_all()
        updated = db.session.get(Submission, sub.id)
        self.assertEqual(updated.current_status, SubmissionStatusEnum.metadata_approval)

    def test_steer_submission_confirmed_no_ack(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        resp = self.client.post(
            url_for("steer_submission_confirmed", sub_id=sub.id),
            data={},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("acknowledge", resp.data.decode())

    def test_about_page(self):
        resp = self.client.get(url_for("about"))
        self.assert200(resp)

    def test_list_users(self):
        self.login("admin@uni.lu", "admin")
        resp = self.client.get(url_for("list_users"))
        self.assert200(resp)

    def test_data_steward_can_list_user_accesses(self):
        submission = create_sub("ELU_I_77")
        submitter = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(submission, provider_user_ids=[submitter.id])

        self.login("steward1@uni.lu", "steward1")
        resp = self.client.get(url_for("list_user_accesses"))

        self.assert200(resp)
        response_text = resp.data.decode("utf-8")
        self.assertIn(submitter.email, response_text)
        self.assertIn(submission.ref_name, response_text)

        self.logout()
        self.login("submitter1@some.edu", "submitter1")
        resp = self.client.get(url_for("list_user_accesses"))
        self.assert403(resp)

    def test_edit_user_get(self):
        self.login("admin@uni.lu", "admin")
        user = User.query.filter_by(email="submitter1@some.edu").first()
        resp = self.client.get(url_for("edit_user", user_id=user.id))
        self.assert200(resp)

    def test_edit_user_post_success(self):
        self.login("admin@uni.lu", "admin")
        user = User.query.filter_by(email="submitter1@some.edu").first()
        resp = self.client.post(
            url_for("edit_user", user_id=user.id),
            data={
                "id": user.id,
                "first_name": "Updated",
                "last_name": "Name",
                "email": user.email,
                "institution_accession": "ELU_I_77",
                "elixir_sub_id": user.elixir_sub_id,
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        db.session.expire_all()
        updated = db.session.get(User, user.id)
        self.assertEqual(updated.first_name, "Updated")
        self.assertEqual(updated.last_name, "Name")

    def test_profile_get(self):
        self.login("submitter1@some.edu", "submitter1")
        resp = self.client.get(url_for("profile"))
        self.assert200(resp)

    def test_profile_post_success(self):
        self.login("submitter1@some.edu", "submitter1")
        user = User.query.filter_by(email="submitter1@some.edu").first()
        resp = self.client.post(
            url_for("profile"),
            data={
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "institution_accession": user.institution_accession,
                "elixir_sub_id": user.elixir_sub_id,
                "phone_no": "+352111222333",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        db.session.expire_all()
        updated = db.session.get(User, user.id)
        self.assertEqual(updated.phone_no, "+352111222333")

    def test_login_wrong_password(self):
        resp = self.client.post(
            url_for("login"),
            data={
                "username": "steward1@uni.lu",
                "password": "wrongpassword",
                "remember": "y",
            },
        )
        self.assert200(resp)
        self.assertIn("Wrong username", resp.data.decode())

    def test_login_user_not_found_in_db(self):
        user = User.query.filter_by(email="submitter1@some.edu").first()
        user.active_user = False
        db.session.commit()

        resp = self.client.post(
            url_for("login"),
            data={
                "username": "submitter1@some.edu",
                "password": "submitter1",
                "remember": "y",
            },
        )
        self.assert200(resp)
        self.assertIn("User not found", resp.data.decode())

    def test_login_redirect_if_authenticated(self):
        self.login("submitter1@some.edu", "submitter1")
        resp = self.client.get(url_for("login"))
        self.assertEqual(resp.status_code, 302)

    def test_reject_metadata_empty_feedback(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        db.session.commit()
        resp = self.client.post(
            url_for("reject_metadata_endpoint", sub_id=sub.id),
            data={"feedback": ""},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("Feedback is required", resp.data.decode())

    @patch("elixir_dss.controllers.web_controllers.steer_sub")
    def test_steer_submission_lifecycle_error(self, mock_steer):
        mock_steer.side_effect = RecordLifecycleException("Cannot transition")
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        db.session.commit()
        resp = self.client.get(url_for("steer_submission", sub_id=sub.id))
        self.assertEqual(resp.status_code, 400)

    @patch("elixir_dss.controllers.web_controllers.steer_sub")
    def test_steer_submission_confirmed_lifecycle_error(self, mock_steer):
        mock_steer.side_effect = RecordLifecycleException("Cannot transition")
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()
        resp = self.client.post(
            url_for("steer_submission_confirmed", sub_id=sub.id),
            data={"responsibility_ack": "on"},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("Unable to transition", resp.data.decode())

    @patch("elixir_dss.controllers.web_controllers.revert_sub")
    def test_revert_submission_lifecycle_error(self, mock_revert):
        mock_revert.side_effect = RecordLifecycleException("Cannot revert")
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.draft)
        db.session.commit()
        resp = self.client.get(url_for("revert_submission", sub_id=sub.id))
        self.assertEqual(resp.status_code, 400)

    def test_create_submission_post_invalid(self):
        self.login("steward1@uni.lu", "steward1")
        resp = self.client.post(
            url_for("create_submission"),
            data={},
        )
        self.assertEqual(resp.status_code, 400)

    def test_edit_submission_post_invalid(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.post(
            url_for("edit_submission", sub_id=sub.id),
            data={"id": sub.id},
        )
        self.assertEqual(resp.status_code, 400)

    def test_edit_submission_with_local_custodians(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        sub.local_custodians_json = json.dumps(["custodian1"])
        db.session.commit()
        resp = self.client.get(url_for("edit_submission", sub_id=sub.id))
        self.assert200(resp)

    @patch("elixir_dss.controllers.web_controllers.clone_sub")
    def test_clone_submission_error(self, mock_clone):
        mock_clone.side_effect = Exception("Clone failed")
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.get(
            url_for("clone_submission", submission_id=sub.id),
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("Unable to clone", resp.data.decode())

    def test_cancel_submission_non_steward_empty_reason(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = create_sub("ELU_I_77")
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": ""},
            follow_redirects=True,
        )
        self.assert200(resp)

    def test_cancel_submission_unauthorized_user(self):
        self.login("submitter2@some.edu", "submitter2")
        sub = create_sub("ELU_I_77")
        user1 = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user1.id])
        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": "testing"},
        )
        self.assert404(resp)

    def test_cancel_submission_already_cancelled(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.cancelled)
        db.session.commit()
        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": "testing"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertIn("cancelled", resp.data.decode())

    @patch("elixir_dss.controllers.web_controllers.cancel_sub")
    def test_cancel_submission_exception(self, mock_cancel):
        mock_cancel.side_effect = Exception("DB error")
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.post(
            url_for("cancel_submission", sub_id=sub.id),
            data={"cancellation_reason": "testing"},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIn("Internal error", resp.data.decode())

    def test_add_attachment_get(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()
        resp = self.client.get(url_for("add_submission_attachment", sub_id=sub.id))
        self.assert200(resp)

    def test_add_attachment_post_success(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        with (
            tempfile.TemporaryDirectory() as upload_dir,
            patch.dict(app.config, {"UPLOAD_FOLDER": upload_dir}),
        ):
            data = {
                "note": "Test attachment",
                "submission_id": str(sub.id),
                "file_attachments": (io.BytesIO(b"test content"), "test.txt"),
            }
            resp = self.client.post(
                url_for("add_submission_attachment", sub_id=sub.id),
                data=data,
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            self.assert200(resp)

            att = SubmissionAttachment.query.filter_by(submission_id=sub.id).first()
            self.assertIsNotNone(att)

    def test_add_attachment_post_bad_type(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        data = {
            "note": "Test attachment",
            "submission_id": str(sub.id),
            "file_attachments": (io.BytesIO(b"test"), "malware.exe"),
        }
        resp = self.client.post(
            url_for("add_submission_attachment", sub_id=sub.id),
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)

    def test_delete_attachment(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        with (
            tempfile.TemporaryDirectory() as upload_dir,
            patch.dict(app.config, {"UPLOAD_FOLDER": upload_dir}),
        ):
            folder = "test-folder-delete"
            att_path = os.path.join(upload_dir, folder)
            os.makedirs(att_path, exist_ok=True)

            att = SubmissionAttachment(
                submission_id=sub.id,
                note="To delete",
                folder_name=folder,
                file_names="test.txt",
            )
            db.session.add(att)
            db.session.commit()

            resp = self.client.get(
                url_for("delete_submission_attachment", attach_id=att.id),
                follow_redirects=True,
            )
            self.assert200(resp)
            self.assertFalse(os.path.exists(att_path))

    def test_download_attachment(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        with (
            tempfile.TemporaryDirectory() as upload_dir,
            patch.dict(app.config, {"UPLOAD_FOLDER": upload_dir}),
        ):
            folder = "test-folder-download"
            att_path = os.path.join(upload_dir, folder)
            os.makedirs(att_path, exist_ok=True)

            with open(os.path.join(att_path, "test.txt"), "w") as f:
                f.write("test content")

            att = SubmissionAttachment(
                submission_id=sub.id,
                note="To download",
                folder_name=folder,
                file_names="test.txt",
            )
            db.session.add(att)
            db.session.commit()

            resp = self.client.get(
                url_for(
                    "download_submission_attachment",
                    attach_id=att.id,
                    filename="test.txt",
                )
            )
            self.assert200(resp)
            self.assertEqual(resp.data, b"test content")
            resp.close()

            resp_404 = self.client.get(
                url_for(
                    "download_submission_attachment",
                    attach_id=att.id,
                    filename="nonexistent.txt",
                )
            )
            self.assertEqual(resp_404.status_code, 404)

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_edit_submission_dataset_post(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, title="Test Dataset Edit"
        )
        db.session.commit()

        resp = self.client.post(
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            data={
                "id": dataset.id,
                "submission_id": sub.id,
                "title": "Updated Dataset Title",
                "study_id": study.id,
                "description": "Updated dataset description: !@#$%^&*() [] {} / \\ ? + = : ; ' \" , . < > ~`|",
                "contains_personal_data": "y",
                "data_processing_type": "pseudonymised",
                "sci_datatypes": ["Whole_genome_sequencing"],
                "gdpr_datatypes": ["genetic"],
                "data_standards": ["CDISC"],
                "file_types": ["CSV (format:3752)"],
                "sample_types": ["blood"],
                "legal_basis_collection_std_code": "61a",
                "legal_basis_sharing_std_code": "61a",
                "consent_status_code": "hm",
                "creators-0-first_name": "John",
                "creators-0-last_name": "Doe",
                "creators-0-email": "john@example.com",
                "creators-0-institution": "Test Uni",
                "creators-0-role": "Principal Investigator",
            },
            follow_redirects=True,
        )
        self.assert200(resp)

        updated_dataset = db.session.get(SubmissionDataset, dataset.id)
        self.assertEqual(updated_dataset.title, "Updated Dataset Title")
        self.assertEqual(updated_dataset.internal_id, dataset.internal_id)
        self.assertEqual(
            updated_dataset.description,
            "Updated dataset description: !@#$%^&*() [] {} / \\ ? + = : ; ' \" , . < > ~`|",
        )

    def test_edit_submission_dataset_post_invalid(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.post(
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            data={},
        )
        self.assertEqual(resp.status_code, 400)

    def test_delete_submission_dataset(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.get(
            url_for("delete_submission_dataset", dataset_id=dataset.id),
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertIsNone(db.session.get(SubmissionDataset, dataset.id))

    def test_add_submission_study_post(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        resp = self.client.post(
            url_for("add_submission_study", sub_id=sub.id),
            data={
                "submission_id": sub.id,
                "name": "Test Study",
                "description": "A study description",
                "study_types": ["Observational"],
                "species": "Homo sapiens; Mus musculus",
                "external_identifiers": "EGAS001; EGAS002",
                "diseases": "PD",
                "sample_sources": "Blood",
                "other_subject_characteristics": "sex: 50 male",
                "study_contacts-0-first_name": "Jane",
                "study_contacts-0-last_name": "Doe",
                "study_contacts-0-email": "jane@example.com",
                "study_contacts-0-institution": "Test Uni",
                "study_contacts-0-category_id": "1",
                "study_contacts-0-is_main_contact": "y",
            },
            follow_redirects=True,
        )
        self.assert200(resp)
        study = SubmissionStudy.query.filter_by(submission_id=sub.id).first()
        self.assertIsNotNone(study)
        self.assertEqual(study.name, "Test Study")

    def test_add_submission_study_post_invalid(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        resp = self.client.post(
            url_for("add_submission_study", sub_id=sub.id),
            data={"submission_id": sub.id},
        )
        self.assertEqual(resp.status_code, 400)

    def test_edit_submission_study_post(self):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        db.session.commit()

        resp = self.client.post(
            url_for("edit_submission_study", study_id=study.id),
            data={
                "id": study.id,
                "submission_id": sub.id,
                "name": "Updated Study",
                "description": "Updated description",
                "study_types": ["Interventional"],
                "study_contacts-0-first_name": "Jane",
                "study_contacts-0-last_name": "Doe",
                "study_contacts-0-email": "jane@example.com",
                "study_contacts-0-institution": "Test Uni",
                "study_contacts-0-category_id": "1",
                "study_contacts-0-is_main_contact": "y",
            },
            follow_redirects=True,
        )
        self.assert200(resp)

    def test_edit_submission_study_post_invalid(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        study = SubmissionStudyFactory(submission_id=sub.id)
        db.session.commit()

        resp = self.client.post(
            url_for("edit_submission_study", study_id=study.id),
            data={"id": study.id, "submission_id": sub.id},
        )
        self.assertEqual(resp.status_code, 400)

    @patch("elixir_dss.controllers.web_controllers.send_new_message_notification")
    def test_add_submission_message_not_in_progress(self, mock_notify):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.post(
            url_for("add_submission_message", sub_id=sub.id),
            data={
                "submission_id": sub.id,
                "message_text": "Draft message",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

        # Message must still be persisted even when the submission is not
        # in progress — only the notification should be skipped.
        persisted = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.message_text, "Draft message")
        mock_notify.assert_not_called()

    @patch("elixir_dss.controllers.web_controllers.send_email_asynch")
    def test_send_notification_error(self, mock_send):
        mock_send.side_effect = Exception("SMTP error")
        self.login("steward1@uni.lu", "steward1")
        notif = EmailNotification(
            subject="Test",
            sender="noreply@uni.lu",
            recipients_json=json.dumps(["test@example.com"]),
            text_body="body",
            html_body="<p>body</p>",
            created_on=datetime.today(),
        )
        db.session.add(notif)
        db.session.commit()
        resp = self.client.get(url_for("send_notification", notification_id=notif.id))
        self.assertEqual(resp.status_code, 400)

    @patch.object(lft, "get_or_create_link")
    @patch.object(lft, "client", None)
    def test_dataset_link_no_lft_client(self, mock_get_or_create):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.get(url_for("dataset_link", dataset_id=dataset.id))
        self.assert200(resp)
        self.assertIn(b"Upload link not available", resp.data)
        mock_get_or_create.assert_not_called()

    @patch.object(lft, "get_or_create_link")
    @patch.object(lft, "password", "pass", create=True)
    @patch.object(lft, "username", "user", create=True)
    @patch.object(lft, "namespace_id", "ns")
    @patch.object(lft, "client", new_callable=MagicMock)
    def test_dataset_link_wrong_status(self, _mock_client, mock_get_or_create):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.draft)
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        resp = self.client.get(url_for("dataset_link", dataset_id=dataset.id))
        self.assert200(resp)
        self.assertIn(b"Upload link not available", resp.data)
        mock_get_or_create.assert_not_called()

    @patch.object(lft, "password", "pass", create=True)
    @patch.object(lft, "username", "user", create=True)
    @patch.object(lft, "namespace_id", "ns")
    @patch.object(lft, "client", new_callable=MagicMock)
    def test_dataset_link_exception(self, _mock_client):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        with patch.object(
            lft, "get_or_create_link", side_effect=Exception("LFT error")
        ) as mock_get_or_create:
            resp = self.client.get(url_for("dataset_link", dataset_id=dataset.id))
            self.assert200(resp)
            self.assertIn(b"Upload link not available", resp.data)
            mock_get_or_create.assert_called_once()

    @patch("elixir_dss.controllers.web_controllers.generate_id")
    def test_add_dataset_idservice_error(self, mock_gen):
        mock_gen.side_effect = IDServiceError("ID service down")
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        study = SubmissionStudyFactory(submission_id=sub.id)
        db.session.commit()

        resp = self.client.post(
            url_for("add_submission_dataset", sub_id=sub.id),
            data={
                "submission_id": sub.id,
                "title": "Test Dataset",
                "study_id": study.id,
                "description": "Test dataset description",
                "contains_personal_data": "y",
                "data_processing_type": "pseudonymised",
                "sci_datatypes": ["Whole_genome_sequencing"],
                "gdpr_datatypes": ["genetic"],
                "legal_basis_collection_std_code": "61a",
                "legal_basis_sharing_std_code": "61a",
                "consent_status_code": "hm",
                "creators-0-first_name": "John",
                "creators-0-last_name": "Doe",
                "creators-0-email": "john@example.com",
                "creators-0-institution": "Test Uni",
                "creators-0-role": "PI",
            },
        )
        self.assertEqual(resp.status_code, 503)

    def test_add_dataset_post_invalid(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.post(
            url_for("add_submission_dataset", sub_id=sub.id),
            data={"submission_id": sub.id},
        )
        self.assertEqual(resp.status_code, 400)

    def test_profile_post_steward(self):
        self.login("steward1@uni.lu", "steward1")
        user = User.query.filter_by(email="steward1@uni.lu").first()
        resp = self.client.post(
            url_for("profile"),
            data={
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "institution_accession": user.institution_accession,
                "elixir_sub_id": user.elixir_sub_id,
                "phone_no": "+352999888777",
            },
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)

    def test_add_attachment_empty_file(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        data = {
            "note": "Test attachment",
            "submission_id": str(sub.id),
            "file_attachments": (io.BytesIO(b""), ""),
        }
        resp = self.client.post(
            url_for("add_submission_attachment", sub_id=sub.id),
            data=data,
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)

    def test_download_attachment_file_missing_on_disk(self):
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        db.session.commit()

        with (
            tempfile.TemporaryDirectory() as upload_dir,
            patch.dict(app.config, {"UPLOAD_FOLDER": upload_dir}),
        ):
            folder = "test-folder-missing"
            att_path = os.path.join(upload_dir, folder)
            os.makedirs(att_path, exist_ok=True)

            att = SubmissionAttachment(
                submission_id=sub.id,
                note="Missing file",
                folder_name=folder,
                file_names="exists.txt missing.txt",
            )
            db.session.add(att)
            db.session.commit()

            with open(os.path.join(att_path, "exists.txt"), "w") as f:
                f.write("content")

            resp = self.client.get(
                url_for(
                    "download_submission_attachment",
                    attach_id=att.id,
                    filename="missing.txt",
                )
            )
            self.assertEqual(resp.status_code, 404)

    @patch("elixir_dss.controllers.web_controllers.generate_id")
    def test_edit_dataset_idservice_error(self, mock_gen):
        mock_gen.side_effect = IDServiceError("ID service down")
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            title="Test Dataset NoID",
            internal_id=None,
        )
        db.session.commit()

        resp = self.client.post(
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            data={
                "id": dataset.id,
                "submission_id": sub.id,
                "title": "Test Dataset NoID",
                "study_id": study.id,
                "description": "Some description here",
                "contains_personal_data": "y",
                "data_processing_type": "pseudonymised",
                "sci_datatypes": ["Whole_genome_sequencing"],
                "gdpr_datatypes": ["genetic"],
                "legal_basis_collection_std_code": "61a",
                "legal_basis_sharing_std_code": "61a",
                "consent_status_code": "hm",
                "creators-0-first_name": "John",
                "creators-0-last_name": "Doe",
                "creators-0-email": "john@example.com",
                "creators-0-institution": "Test Uni",
                "creators-0-role": "Principal Investigator",
            },
        )
        self.assertEqual(resp.status_code, 503)

    def test_pluralize_filter(self):
        """Cover reporters.py pluralize template filter."""
        pluralize = app.jinja_env.filters["pluralize"]
        self.assertEqual(pluralize(["a"]), "")
        self.assertEqual(pluralize(["a"], "item", "items"), "item")
        self.assertEqual(pluralize(["a", "b"]), "s")
        self.assertEqual(pluralize(["a", "b"], "item", "items"), "items")

    def test_csrf_error_handler(self):
        """Cover errors.py csrf_error handler."""
        with app.test_request_context():
            response, status_code = csrf_error(CSRFError("CSRF token missing"))
            self.assertEqual(status_code, 400)

    def test_enforce_auth_unauthenticated(self):
        """Cover enforce_auth_by_default unauthenticated path."""
        resp = self.client.get(url_for("list_submissions"))
        # Should redirect to login page (302)
        self.assertEqual(resp.status_code, 302)

    def test_dict_list_lookup_not_found(self):
        """Cover utils.py dict_list_lookup return None."""
        result = dict_list_lookup([{"a": 1, "b": 2}], "a", "nonexistent", "b")
        self.assertIsNone(result)

    def test_load_user(self):
        """Cover load_user function."""
        user = User.query.filter_by(email="steward1@uni.lu").first()
        # Normal path
        loaded = load_user(user.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.email, "steward1@uni.lu")

    def test_load_user_db_error(self):
        """Cover load_user OperationalError path."""
        with patch(
            "elixir_dss.controllers.web_controllers.db.session.get",
            side_effect=OperationalError("", {}, Exception("db error")),
        ):
            result = load_user(1)
            self.assertIsNone(result)
