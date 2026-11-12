import io
import json
import os
import tempfile
from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock, call, patch

import docx
import pytest
from flask import url_for
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import OperationalError

from elixir_dss import app, db, lft
from elixir_dss.clients.idservice import IDServiceError
from elixir_dss.clients.lft import LFTLink
from elixir_dss.controllers.errors import csrf_error
from elixir_dss.controllers.utils import dict_list_lookup
from elixir_dss.controllers.web_controllers import load_user
from elixir_dss.exceptions import RecordLifecycleException
from elixir_dss.models.security import User
from elixir_dss.models.services import (
    create_sub,
    steer_sub,
    update_submission_basic_info,
)
from elixir_dss.models.submission import (
    EmailNotification,
    Submission,
    SubmissionAccess,
    SubmissionAttachment,
    SubmissionDataset,
    SubmissionMessage,
    SubmissionStatusEnum,
    SubmissionStudy,
)
from tests import BaseIntegrationTest
from tests.factories import (
    ContactFactory,
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

    def _dataset_dates_form(self, sub, study, **dates):
        return {
            "submission_id": sub.id,
            "title": "Dated_Dataset",
            "study_id": study.id,
            "description": "Description",
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
            **dates,
        }

    def _add_dataset_with_dates(self, ref_name, **dates):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub(ref_name)
        study = SubmissionStudyFactory(submission_id=sub.id)
        resp = self.client.post(
            url_for("add_submission_dataset", sub_id=sub.id),
            data=self._dataset_dates_form(sub, study, **dates),
            follow_redirects=True,
        )
        self.assert200(resp)
        return SubmissionDataset.query.filter_by(submission_id=sub.id).one()

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_add_dataset_dates_left_empty(self):
        dataset = self._add_dataset_with_dates("ELU_I_239")
        self.assertIsNone(dataset.creation_date)
        self.assertIsNone(dataset.last_update_date)

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_add_dataset_dates_kept_as_posted(self):
        dataset = self._add_dataset_with_dates(
            "ELU_I_239", creation_date="2020-01-02", last_update_date="2021-03-04"
        )
        self.assertEqual(dataset.creation_date.isoformat(), "2020-01-02")
        self.assertEqual(dataset.last_update_date.isoformat(), "2021-03-04")

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_edit_dataset_dates_kept_as_posted(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_240")
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()
        url = url_for("edit_submission_dataset", dataset_id=dataset.id)

        self.client.post(
            url,
            data=self._dataset_dates_form(sub, study, id=dataset.id),
            follow_redirects=True,
        )
        db.session.expire_all()
        dataset = db.session.get(SubmissionDataset, dataset.id)
        self.assertIsNone(dataset.creation_date)
        self.assertIsNone(dataset.last_update_date)

        self.client.post(
            url,
            data=self._dataset_dates_form(
                sub,
                study,
                id=dataset.id,
                creation_date="2020-01-02",
                last_update_date="2021-03-04",
            ),
            follow_redirects=True,
        )
        db.session.expire_all()
        dataset = db.session.get(SubmissionDataset, dataset.id)
        self.assertEqual(dataset.creation_date.isoformat(), "2020-01-02")
        self.assertEqual(dataset.last_update_date.isoformat(), "2021-03-04")

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

    def test_edit_submission_link_shown_only_to_data_stewards(self):
        submitter = User.query.filter_by(email="submitter1@some.edu").first()
        for status in (
            SubmissionStatusEnum.metadata_submission,
            SubmissionStatusEnum.data_upload,
        ):
            sub = SubmissionFactory(current_status=status)
            update_submission_basic_info(sub, provider_user_ids=[submitter.id])
            db.session.commit()
            edit_url = url_for("edit_submission", sub_id=sub.id)

            self.login("submitter1@some.edu", "submitter1")
            resp = self.client.get(url_for("view_submission", sub_id=sub.id))
            self.assert200(resp)
            self.assertNotIn(edit_url, resp.data.decode())
            self.logout()

            self.login("steward1@uni.lu", "steward1")
            resp = self.client.get(url_for("view_submission", sub_id=sub.id))
            self.assert200(resp)
            self.assertIn(edit_url, resp.data.decode())
            self.logout()

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
            created_on=datetime.now(UTC),
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

    @patch("elixir_dss.controllers.reporters.DocxTemplate")
    def test_generate_submission_docx_gdpr_labels(self, mock_docx_cls):
        """The DOCX shows the GDPR data types' labels, not their codes (#238)."""
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            gdpr_datatypes_json='["standard", "ethnic", "health"]',
        )
        mock_doc = MagicMock()
        mock_docx_cls.return_value = mock_doc

        resp = self.client.get(url_for("generate_submission_docx", sub_id=sub.id))
        self.assert200(resp)
        context = mock_doc.render.call_args[0][0]
        self.assertEqual(
            context["studies"][0]["datasets"][0]["gdpr_data_types"],
            "Standard personal data, Racial or ethnic origin, Data concerning health",
        )

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

    def test_create_submission_form_labels_point_to_form_controls(self):
        """Every label[for] must reference a labelable element (issue #189)."""
        from html.parser import HTMLParser

        labelable_tags = {
            "input",
            "select",
            "textarea",
            "button",
            "meter",
            "output",
            "progress",
        }

        class LabelCollector(HTMLParser):
            def __init__(self):
                super().__init__()
                self.label_targets = []
                self.tag_by_id = {}

            def handle_starttag(self, tag, attributes):
                attributes = dict(attributes)
                if attributes.get("id"):
                    self.tag_by_id[attributes["id"]] = tag
                if tag == "label" and attributes.get("for"):
                    self.label_targets.append(attributes["for"])

        self.login("steward1@uni.lu", "steward1")
        resp = self.client.get(url_for("create_submission"))
        self.assert200(resp)
        collector = LabelCollector()
        collector.feed(resp.data.decode())
        self.assertIn("institution_accession", collector.label_targets)
        for target in collector.label_targets:
            self.assertIn(
                collector.tag_by_id.get(target),
                labelable_tags,
                f"label for='{target}' does not point to a form control",
            )
        self.assertIn('aria-labelledby="contacts-fieldset-label"', resp.data.decode())
        self.assertIn('id="contacts-fieldset-label"', resp.data.decode())

    def test_view_submission(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)

    @patch("elixir_dss.models.submission.get_elu_projects")
    @patch("elixir_dss.models.submission.get_elu_partners")
    def test_view_submission_shows_entity_names(self, mock_partners, mock_projects):
        mock_partners.return_value = [{"external_id": "ELU_I_9", "name": "Test Uni"}]
        mock_projects.return_value = [
            {"external_id": "ELU_P_1", "name": "Test Project"}
        ]
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        update_submission_basic_info(sub, local_project_name="ELU_P_1")
        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)
        data = resp.data.decode()
        for label in (
            "Submitting institution",
            "Receiving project",
            "Submitters",
            "Recipients",
            "Status:",
            "Creation date:",
        ):
            self.assertIn(label, data)
        self.assertNotIn("Date of finalisation", data)
        self.assertIn(sub.current_status.value, data)
        self.assertNotIn("Receiving Project", data)
        self.assertIn(
            'Test Uni <span class="text-muted fw-normal">(ELU_I_9)</span>', data
        )
        self.assertIn(
            'Test Project <span class="text-muted fw-normal">(ELU_P_1)</span>', data
        )
        self.assertIn('title="Test Uni (ELU_I_9)"', data)
        self.assertIn('title="Test Project (ELU_P_1)"', data)

    @patch("elixir_dss.models.submission.get_elu_projects")
    @patch("elixir_dss.models.submission.get_elu_partners")
    def test_generate_submission_docx_shows_entity_names(
        self, mock_partners, mock_projects
    ):
        mock_partners.return_value = [{"external_id": "ELU_I_9", "name": "Test Uni"}]
        mock_projects.return_value = [
            {"external_id": "ELU_P_1", "name": "Test Project"}
        ]
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        update_submission_basic_info(sub, local_project_name="ELU_P_1")
        resp = self.client.get(url_for("generate_submission_docx", sub_id=sub.id))
        self.assert200(resp)
        document = docx.Document(io.BytesIO(resp.data))
        cells = [
            cell.text.strip()
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        ]
        self.assertIn("Test Uni (ELU_I_9)", cells)
        self.assertIn("Test Project (ELU_P_1)", cells)
        self.assertIn("Receiving project:", cells)
        self.assertNotIn("ELU_P_1", cells)

    def test_view_submission_shows_remarks(self):
        self.login("steward1@uni.lu", "steward1")
        submission = create_sub("ELU_I_9")
        submission.notes = "Cohort from the 2019 pilot\nSecond batch follows"
        db.session.commit()

        response = self.client.get(url_for("view_submission", sub_id=submission.id))

        self.assert200(response)
        page = response.data.decode()
        self.assertIn("Remarks", page)
        self.assertIn("Cohort from the 2019 pilot\nSecond batch follows", page)
        self.assertEqual(page.count("Cohort from the 2019 pilot"), 1)

    def test_view_submission_shows_remarks_in_summary_card_at_every_step(self):
        self.login("steward1@uni.lu", "steward1")
        for status in [
            SubmissionStatusEnum.draft,
            SubmissionStatusEnum.metadata_submission,
            SubmissionStatusEnum.data_upload,
            SubmissionStatusEnum.completed,
        ]:
            with self.subTest(status=status):
                submission = SubmissionFactory(current_status=status)
                submission.notes = f"Remarks at {status.value}"
                db.session.commit()

                response = self.client.get(
                    url_for("view_submission", sub_id=submission.id)
                )

                self.assert200(response)
                page = response.data.decode()
                self.assertEqual(page.count(f"Remarks at {status.value}"), 1)
                # The summary card at the top lists the remarks before its
                # "Submitting institution:" line.
                self.assertLess(
                    page.index(f"Remarks at {status.value}"),
                    page.index("Submitting institution:"),
                )

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

    def test_edit_submission_dataset_access_form_warning(self):
        # The reminder to upload the access request form only shows once it is required.
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        hidden = 'id="access-form-warning" class="bg-warning-subtle text-warning-emphasis border border-warning-subtle rounded p-3 d-flex align-items-start gap-2 mb-3 d-none"'
        shown = 'id="access-form-warning" class="bg-warning-subtle text-warning-emphasis border border-warning-subtle rounded p-3 d-flex align-items-start gap-2 mb-3"'
        for answer, expected in ((None, hidden), ("no", hidden), ("yes", shown)):
            dataset.access_form_required = answer
            db.session.commit()
            resp = self.client.get(
                url_for("edit_submission_dataset", dataset_id=dataset.id)
            )
            self.assert200(resp)
            self.assertIn(expected, resp.get_data(as_text=True), answer)

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

    def test_about_page_shows_version_and_commit(self):
        from elixir_dss import __VERSION__

        with patch.dict(app.config, {"COMMIT_ID": None}):
            page = self.client.get(url_for("about")).data.decode()
        self.assertIn(f"<strong>{__VERSION__}</strong>", page)
        self.assertIn(f"Version {__VERSION__}", page)
        self.assertNotIn("/commit/", page)

        with patch.dict(app.config, {"COMMIT_ID": "abc1234"}):
            page = self.client.get(url_for("about")).data.decode()
        self.assertIn(
            'href="https://github.com/elixir-luxembourg/dss/commit/abc1234"', page
        )
        self.assertIn("<code>abc1234</code></a>", page)
        self.assertIn(f"Version {__VERSION__} (abc1234)", page)

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

    @patch("elixir_dss.controllers.web_controllers.get_elu_lcsb_pis")
    def test_get_local_custodians(self, mock_get_elu_lcsb_pis):
        mock_get_elu_lcsb_pis.return_value = [
            {"name": "Jane Doe", "email": "jane.doe@uni.lu"},
            {"name": "John Roe", "email": None},
        ]
        self.login("steward1@uni.lu", "steward1")

        resp = self.client.get(url_for("get_local_custodians", external_id="ELU_P_1"))

        self.assert200(resp)
        self.assertEqual(resp.get_json(), ["Jane Doe <jane.doe@uni.lu>", "John Roe"])
        mock_get_elu_lcsb_pis.assert_called_once_with("ELU_P_1")

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
            steward = User.query.filter_by(email="steward1@uni.lu").first()
            self.assertIsNotNone(att.uploaded_on)
            self.assertEqual(att.uploaded_by_user_id, steward.id)
            page = resp.data.decode()
            self.assertIn(
                f'<time datetime="{att.uploaded_on.isoformat()}">'
                f"{att.uploaded_on.strftime('%b %d, %Y at %I:%M %p')}</time>",
                page,
            )
            self.assertIn(
                f'<div class="fw-semibold text-dark small attachment-uploader">'
                f"{steward.display_name()}</div>",
                page,
            )

    def test_view_submission_attachment_without_upload_info(self):
        """Attachments uploaded before the date was recorded show no date line."""
        self.login("steward1@uni.lu", "steward1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        attachment = SubmissionAttachment(
            submission_id=sub.id,
            note="Legacy attachment",
            folder_name="legacy-folder",
            file_names="legacy.txt",
        )
        db.session.add(attachment)
        db.session.commit()
        # the column default fills the date on insert: clear it as the migration leaves old rows
        attachment.uploaded_on = None
        db.session.commit()
        self.assertIsNone(attachment.uploaded_on)

        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)
        page = resp.data.decode()
        self.assertIn("Legacy attachment", page)
        self.assertNotIn("<time datetime=", page)

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
        original_internal_id = dataset.internal_id

        dataset_title = "Updated Title (v2.0) / final with very-very-very-very-very-very-very-very-very-very-very-very-very-very-long-title!"
        resp = self.client.post(
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            data={
                "id": dataset.id,
                "submission_id": sub.id,
                "title": dataset_title,
                "study_id": study.id,
                "description": "Updated dataset description: !@#$%^&*() [] {} / \\ ? + = : ; ' \" , . < > ~`|",
                "contains_personal_data": "y",
                "data_processing_type": "pseudonymised",
                "sci_datatypes": ["Whole_genome_sequencing"],
                "sci_datatypes_notes": "sci_datatypes_notes: a&b (c/d) 100%!",
                "gdpr_datatypes": ["genetic"],
                "gdpr_datatypes_notes": "gdpr_datatypes_notes: a&b (c/d) 100%!",
                "consent_notes": "consent_notes: a&b (c/d) 100%!",
                "restriction_rs_notes": "restriction_rs_notes: a&b (c/d) 100%!",
                "restriction_gs_notes": "restriction_gs_notes: a&b (c/d) 100%!",
                "restriction_user_specific_notes": "restriction_user_specific_notes: a&b (c/d) 100%!",
                "restriction_ts_notes": "restriction_ts_notes: a&b (c/d) 100%!",
                "restriction_pub_notes": "restriction_pub_notes: a&b (c/d) 100%!",
                "restriction_rtn_notes": "restriction_rtn_notes: a&b (c/d) 100%!",
                "restriction_us_notes": "restriction_us_notes: a&b (c/d) 100%!",
                "restriction_ip_notes": "restriction_ip_notes: a&b (c/d) 100%!",
                "restriction_other_notes": "restriction_other_notes: a&b (c/d) 100%!",
                "dac_approval_notes": "dac_approval_notes: a&b (c/d) 100%!",
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

        db.session.expire_all()
        updated_dataset = db.session.get(SubmissionDataset, dataset.id)
        self.assertEqual(updated_dataset.title, dataset_title)
        self.assertEqual(updated_dataset.internal_id, original_internal_id)
        self.assertEqual(
            updated_dataset.description,
            "Updated dataset description: !@#$%^&*() [] {} / \\ ? + = : ; ' \" , . < > ~`|",
        )
        for field in (
            "sci_datatypes_notes",
            "gdpr_datatypes_notes",
            "consent_notes",
            "restriction_rs_notes",
            "restriction_gs_notes",
            "restriction_user_specific_notes",
            "restriction_ts_notes",
            "restriction_pub_notes",
            "restriction_rtn_notes",
            "restriction_us_notes",
            "restriction_ip_notes",
            "restriction_other_notes",
            "dac_approval_notes",
        ):
            self.assertEqual(
                getattr(updated_dataset, field),
                f"{field}: a&b (c/d) 100%!",
            )

    def _post_dataset_use_conditions(self, use_conditions):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, restriction_ip="yes"
        )
        db.session.commit()
        resp = self.client.post(
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            data={
                "id": dataset.id,
                "submission_id": sub.id,
                "title": "Dataset",
                "study_id": study.id,
                "description": "Description",
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
                **use_conditions,
            },
            follow_redirects=True,
        )
        db.session.expire_all()
        return resp, db.session.get(SubmissionDataset, dataset.id)

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_edit_submission_dataset_use_conditions(self):
        resp, dataset = self._post_dataset_use_conditions(
            {
                "restriction_rs": "no",
                "restriction_rs_notes": "There is no restriction",
                "restriction_gs": "not_applicable",
                "restriction_us": "not_available",
                "use_restriction_project": "no",
                "use_restriction_project_notes": "Any project of the consortium",
                "use_restriction_research_use": "no",
                "use_restriction_research_use_notes": "Not limited",
                "restriction_ts_lcsb": "no",
                "restriction_ts_lcsb_notes": "Kept indefinitely",
                "access_form_required": "no",
                "access_form_notes": "Open to approved users",
                "restriction_ip": "",
            }
        )
        self.assert200(resp)
        self.assertEqual(dataset.restriction_rs, "no")
        self.assertEqual(dataset.restriction_rs_notes, "There is no restriction")
        self.assertEqual(dataset.restriction_gs, "not_applicable")
        self.assertEqual(dataset.restriction_us, "not_available")
        self.assertEqual(dataset.use_restriction_project, "no")
        self.assertEqual(
            dataset.use_restriction_project_notes, "Any project of the consortium"
        )
        self.assertEqual(dataset.use_restriction_research_use_notes, "Not limited")
        self.assertEqual(dataset.restriction_ts_lcsb_notes, "Kept indefinitely")
        self.assertEqual(dataset.access_form_notes, "Open to approved users")
        # "----" clears an answer; a condition left out of the post stays unset.
        self.assertIsNone(dataset.restriction_ip)
        self.assertIsNone(dataset.dac_approval_required)

    def test_edit_submission_dataset_creator_orcid(self):
        resp, dataset = self._post_dataset_use_conditions(
            {"creators-0-orcid": "https://orcid.org/0000-0001-9235-8496"}
        )
        self.assert200(resp)
        self.assertEqual(dataset.creators[0].orcid, "0000-0001-9235-8496")

    def test_edit_submission_dataset_creator_orcid_invalid(self):
        resp, dataset = self._post_dataset_use_conditions(
            {"creators-0-orcid": "0000-0002-1825-0098"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"Not a valid ORCID iD", resp.data)
        self.assertNotEqual(dataset.title, "Dataset")

    def test_edit_submission_dataset_use_condition_invalid(self):
        resp, dataset = self._post_dataset_use_conditions({"restriction_rs": "maybe"})
        self.assertEqual(resp.status_code, 400)
        self.assertIsNone(dataset.restriction_rs)

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
            created_on=datetime.now(UTC),
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

    def test_add_dataset_form_sample_types_in_overview(self):
        self.login("steward1@uni.lu", "steward1")
        sub = create_sub("ELU_I_9")
        resp = self.client.get(url_for("add_submission_dataset", sub_id=sub.id))
        self.assert200(resp)
        page = resp.data.decode()
        notes = page.index('id="sci_datatypes_notes"')
        sample_types = page.index('id="sample_types"')
        creators = page.index("Dataset Creators")
        self.assertLess(notes, sample_types)
        self.assertLess(sample_types, creators)

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
            _response, status_code = csrf_error(CSRFError("CSRF token missing"))
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


class RecipientAccessTest(BaseIntegrationTest):
    def _make_submission_with_recipient(
        self, status=SubmissionStatusEnum.metadata_submission
    ):
        sub = SubmissionFactory(current_status=status)
        recipient = User.query.filter_by(email="submitter2@some.edu").first()
        db.session.add(
            SubmissionAccess(
                submission_id=sub.id,
                user_id=recipient.id,
                role=SubmissionAccess.ROLE_RECIPIENT,
                access_granted_on=datetime.now(),
            )
        )
        db.session.commit()
        return sub

    def test_recipient_view_is_read_only(self):
        sub = self._make_submission_with_recipient()
        SubmissionStudyFactory(submission_id=sub.id)
        db.session.commit()
        self.login("submitter2@some.edu", "submitter2")

        resp = self.client.get(url_for("view_submission", sub_id=sub.id))
        self.assert200(resp)
        data = resp.data.decode("utf-8")
        write_urls = [
            url_for("edit_submission", sub_id=sub.id),
            url_for("add_submission_attachment", sub_id=sub.id),
        ]
        for write_url in write_urls:
            with self.subTest(write_url=write_url):
                self.assertNotIn(write_url, data)
        self.assertIn(url_for("add_submission_message", sub_id=sub.id), data)
        self.assertIn(url_for("generate_submission_docx", sub_id=sub.id), data)

    def test_recipient_can_use_read_routes(self):
        sub = self._make_submission_with_recipient()
        self.login("submitter2@some.edu", "submitter2")

        with (
            tempfile.TemporaryDirectory() as upload_dir,
            patch.dict(app.config, {"UPLOAD_FOLDER": upload_dir}),
        ):
            folder = "recipient-download"
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

            read_urls = [
                url_for("view_submission", sub_id=sub.id),
                url_for("generate_submission_docx", sub_id=sub.id),
                url_for(
                    "download_submission_attachment",
                    attach_id=att.id,
                    filename="test.txt",
                ),
            ]
            for read_url in read_urls:
                with self.subTest(read_url=read_url):
                    self.assert200(self.client.get(read_url))

    def test_recipient_can_add_message(self):
        sub = self._make_submission_with_recipient()
        self.login("submitter2@some.edu", "submitter2")

        resp = self.client.post(
            url_for("add_submission_message", sub_id=sub.id),
            data={"submission_id": sub.id, "message_text": "A recipient question"},
            follow_redirects=True,
        )
        self.assert200(resp)
        self.assertEqual(1, SubmissionMessage.query.count())

    def test_recipient_cannot_use_write_routes(self):
        sub = self._make_submission_with_recipient()
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        attachment = SubmissionAttachment(
            submission_id=sub.id,
            note="Protected",
            folder_name="unused",
            file_names="test.txt",
        )
        db.session.add(attachment)
        db.session.commit()
        self.login("submitter2@some.edu", "submitter2")

        blocked_urls = [
            url_for("add_submission_attachment", sub_id=sub.id),
            url_for("add_submission_dataset", sub_id=sub.id),
            url_for("add_submission_study", sub_id=sub.id),
            url_for("edit_submission_study", study_id=study.id),
            url_for("edit_submission_dataset", dataset_id=dataset.id),
            url_for("delete_submission_study", study_id=study.id),
            url_for("delete_submission_dataset", dataset_id=dataset.id),
            url_for("steer_submission", sub_id=sub.id),
            url_for("clone_submission", submission_id=sub.id),
            url_for("dataset_link", dataset_id=dataset.id),
            url_for("delete_submission_attachment", attach_id=attachment.id),
        ]
        for blocked_url in blocked_urls:
            with self.subTest(blocked_url=blocked_url):
                self.assert403(self.client.get(blocked_url))

        self.assert403(
            self.client.post(
                url_for("cancel_submission", sub_id=sub.id),
                data={"cancellation_reason": "Recipient tries to cancel"},
            )
        )

    def test_message_submission_id_must_match_url(self):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        submitter = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[submitter.id])
        other_sub = SubmissionFactory(
            current_status=SubmissionStatusEnum.metadata_submission
        )
        self.login("submitter1@some.edu", "submitter1")

        resp = self.client.post(
            url_for("add_submission_message", sub_id=sub.id),
            data={"submission_id": other_sub.id, "message_text": "Cross post"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(0, SubmissionMessage.query.count())

    @patch("elixir_dss.forms.submissions_forms.get_elu_lcsb_pis")
    def test_create_submission_assigns_recipient(self, mock_get_elu_lcsb_pis):
        mock_get_elu_lcsb_pis.return_value = [
            {"name": "Jane Doe", "email": "jane.doe@uni.lu"}
        ]
        self.login("steward1@uni.lu", "steward1")
        steward = User.query.filter_by(email="steward1@uni.lu").first()

        resp = self.client.post(
            url_for("create_submission"),
            data={
                "institution_accession": "ELU_I_9",
                "local_project_name": "ELU_P_1",
                "local_custodians": ["Jane Doe <jane.doe@uni.lu>"],
                "provider_user_ids": [steward.id],
                "submission_contacts-0-first_name": "John",
                "submission_contacts-0-last_name": "Doe",
                "submission_contacts-0-email": "john.doe@example.com",
                "submission_contacts-0-category_id": "1",
            },
            follow_redirects=True,
        )
        self.assert200(resp)

        sub = Submission.query.first()
        recipient = User.query.filter_by(email="jane.doe@uni.lu").one()
        access = SubmissionAccess.query.filter_by(
            submission_id=sub.id, user_id=recipient.id
        ).one()
        self.assertEqual(access.role, SubmissionAccess.ROLE_RECIPIENT)
        self.assertTrue(
            EmailNotification.query.filter(
                EmailNotification.subject.contains("assigned as Recipient")
            ).one_or_none()
        )


class ReadOnlyMetadataTest(BaseIntegrationTest):
    def _make_submission(self, status=SubmissionStatusEnum.metadata_approval):
        sub = SubmissionFactory(current_status=status)
        submitter = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[submitter.id])
        study = SubmissionStudyFactory(
            submission_id=sub.id,
            name="Read-only study",
            study_contacts=[ContactFactory()],
        )
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            title="Read-only dataset",
            sci_datatypes_json='["Whole_genome_sequencing"]',
        )
        db.session.commit()
        return sub, study, dataset

    def _assert_read_only_form(self, resp, title):
        self.assert200(resp)
        data = resp.data.decode("utf-8")
        self.assertIn(title, data)
        self.assertIn('data-read-only="true"', data)
        self.assertIn("<fieldset disabled>", data)
        self.assertNotIn('id="submit-btn"', data)
        self.assertNotIn('data-toggle="fieldset-add-row"', data)
        self.assertNotIn('data-toggle="fieldset-remove-row"', data)

    def test_steward_views_metadata_read_only_during_review(self):
        _sub, study, dataset = self._make_submission()
        self.login("steward1@uni.lu", "steward1")

        self._assert_read_only_form(
            self.client.get(url_for("view_submission_study", study_id=study.id)),
            "Read-only study",
        )
        self._assert_read_only_form(
            self.client.get(url_for("view_submission_dataset", dataset_id=dataset.id)),
            "Read-only dataset",
        )

    def test_submission_page_links_rows_to_read_only_views(self):
        sub, study, dataset = self._make_submission()
        self.login("steward1@uni.lu", "steward1")

        data = self.client.get(url_for("view_submission", sub_id=sub.id)).data.decode()
        self.assertIn(
            f'href="{url_for("view_submission_study", study_id=study.id)}"', data
        )
        self.assertIn(
            f'href="{url_for("view_submission_dataset", dataset_id=dataset.id)}"', data
        )
        self.assertNotIn(
            f'href="{url_for("edit_submission_study", study_id=study.id)}"', data
        )
        self.assertNotIn(
            f'href="{url_for("edit_submission_dataset", dataset_id=dataset.id)}"', data
        )

    def test_submission_page_keeps_edit_links_during_metadata_entry(self):
        sub, study, dataset = self._make_submission(
            SubmissionStatusEnum.metadata_submission
        )
        self.login("submitter1@some.edu", "submitter1")

        data = self.client.get(url_for("view_submission", sub_id=sub.id)).data.decode()
        self.assertIn(
            f'href="{url_for("edit_submission_study", study_id=study.id)}"', data
        )
        self.assertIn(
            f'href="{url_for("edit_submission_dataset", dataset_id=dataset.id)}"', data
        )
        self.assertNotIn(
            f'href="{url_for("view_submission_study", study_id=study.id)}"', data
        )

    def test_submitter_and_recipient_view_read_only_after_metadata_entry(self):
        sub, study, dataset = self._make_submission(SubmissionStatusEnum.completed)
        recipient = User.query.filter_by(email="submitter2@some.edu").first()
        db.session.add(
            SubmissionAccess(
                submission_id=sub.id,
                user_id=recipient.id,
                role=SubmissionAccess.ROLE_RECIPIENT,
                access_granted_on=datetime.now(),
            )
        )
        db.session.commit()

        for email, password in (
            ("submitter1@some.edu", "submitter1"),
            ("submitter2@some.edu", "submitter2"),
        ):
            with self.subTest(user=email):
                self.login(email, password)
                self._assert_read_only_form(
                    self.client.get(
                        url_for("view_submission_study", study_id=study.id)
                    ),
                    "Read-only study",
                )
                self._assert_read_only_form(
                    self.client.get(
                        url_for("view_submission_dataset", dataset_id=dataset.id)
                    ),
                    "Read-only dataset",
                )
                self.logout()

    def test_read_only_views_refuse_users_without_access_and_writes(self):
        _sub, study, dataset = self._make_submission()
        self.login("submitter2@some.edu", "submitter2")
        self.assert404(
            self.client.get(url_for("view_submission_study", study_id=study.id))
        )
        self.assert404(
            self.client.get(url_for("view_submission_dataset", dataset_id=dataset.id))
        )

        self.logout()
        self.login("steward1@uni.lu", "steward1")
        self.assert405(
            self.client.post(url_for("view_submission_study", study_id=study.id))
        )
        self.assert405(
            self.client.post(url_for("view_submission_dataset", dataset_id=dataset.id))
        )


class DuplicateStudyDatasetTest(BaseIntegrationTest):
    def _submitter_submission(self, status=SubmissionStatusEnum.metadata_submission):
        self.login("submitter1@some.edu", "submitter1")
        sub = SubmissionFactory(current_status=status)
        user = User.query.filter_by(email="submitter1@some.edu").first()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        return sub

    def test_duplicate_study_copies_it_with_its_contacts(self):
        sub = self._submitter_submission()
        study = SubmissionStudyFactory(
            submission_id=sub.id,
            name="Cohort A",
            study_contacts=[ContactFactory(first_name="Ada"), ContactFactory()],
        )
        db.session.commit()

        resp = self.client.post(
            url_for("duplicate_submission_study", study_id=study.id)
        )

        self.assertEqual(resp.status_code, 302)
        db.session.expire_all()
        studies = SubmissionStudy.query.filter_by(submission_id=sub.id).all()
        self.assertEqual(len(studies), 2)
        copy = next(s for s in studies if s.id != study.id)
        self.assertIn(url_for("edit_submission_study", study_id=copy.id), resp.location)
        self.assertEqual(copy.name, "Cohort A (copy)")
        self.assertEqual(copy.description, study.description)
        self.assertEqual(copy.species_json, study.species_json)
        self.assertEqual(
            sorted(c.first_name for c in copy.study_contacts),
            sorted(c.first_name for c in study.study_contacts),
        )
        self.assertEqual(
            len(db.session.get(SubmissionStudy, study.id).study_contacts), 2
        )
        self.assertEqual(db.session.get(SubmissionStudy, study.id).name, "Cohort A")

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_duplicate_dataset_copies_it_with_a_new_internal_id(self):
        sub = self._submitter_submission()
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            title="Genomes",
            internal_id="ORIGINAL_ID",
            use_restriction_project=True,
            restriction_pub=True,
            restriction_pub_notes="Acknowledge the cohort",
            creation_date=date(2024, 1, 2),
            last_update_date=date(2024, 3, 4),
        )
        creator_names = [c.first_name for c in dataset.creators]

        resp = self.client.post(
            url_for("duplicate_submission_dataset", dataset_id=dataset.id)
        )

        self.assertEqual(resp.status_code, 302)
        db.session.expire_all()
        datasets = SubmissionDataset.query.filter_by(submission_id=sub.id).all()
        self.assertEqual(len(datasets), 2)
        copy = next(d for d in datasets if d.id != dataset.id)
        self.assertIn(
            url_for("edit_submission_dataset", dataset_id=copy.id), resp.location
        )
        self.assertEqual(copy.title, "Genomes (copy)")
        with self.client.session_transaction() as session:
            self.assertIn(
                (
                    "success",
                    (
                        'Dataset duplicated and saved as "Genomes (copy)". '
                        "You can edit the copy below."
                    ),
                ),
                session["_flashes"],
            )
        self.assertEqual(copy.internal_id, "TEST_DATASET_ID_001")
        self.assertEqual(copy.study_id, study.id)
        self.assertTrue(copy.use_restriction_project)
        self.assertTrue(copy.restriction_pub)
        self.assertEqual(copy.restriction_pub_notes, "Acknowledge the cohort")
        self.assertEqual(copy.gdpr_datatypes_json, dataset.gdpr_datatypes_json)
        self.assertEqual([c.first_name for c in copy.creators], creator_names)
        self.assertEqual(copy.creation_date, dataset.creation_date)
        self.assertEqual(copy.last_update_date, dataset.last_update_date)
        original = db.session.get(SubmissionDataset, dataset.id)
        self.assertEqual(original.internal_id, "ORIGINAL_ID")
        self.assertEqual(len(original.creators), len(creator_names))

    @patch("elixir_dss.models.submission.generate_id")
    def test_duplicate_dataset_idservice_error(self, mock_gen):
        mock_gen.side_effect = IDServiceError("ID service down")
        sub = self._submitter_submission()
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        resp = self.client.post(
            url_for("duplicate_submission_dataset", dataset_id=dataset.id),
            follow_redirects=True,
        )

        self.assert200(resp)
        self.assertIn("ID generation service is unavailable", resp.data.decode())
        self.assertEqual(
            SubmissionDataset.query.filter_by(submission_id=sub.id).count(), 1
        )

    def test_duplicate_blocked_outside_metadata_submission(self):
        sub = self._submitter_submission(status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        self.assert403(
            self.client.post(url_for("duplicate_submission_study", study_id=study.id))
        )
        self.assert403(
            self.client.post(
                url_for("duplicate_submission_dataset", dataset_id=dataset.id)
            )
        )
        self.assertEqual(
            SubmissionStudy.query.filter_by(submission_id=sub.id).count(), 1
        )
        self.assertEqual(
            SubmissionDataset.query.filter_by(submission_id=sub.id).count(), 1
        )

    def test_duplicate_blocked_for_recipient(self):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        recipient = User.query.filter_by(email="submitter2@some.edu").first()
        db.session.add(
            SubmissionAccess(
                submission_id=sub.id,
                user_id=recipient.id,
                role=SubmissionAccess.ROLE_RECIPIENT,
                access_granted_on=datetime.now(),
            )
        )
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        self.login("submitter2@some.edu", "submitter2")

        self.assert403(
            self.client.post(url_for("duplicate_submission_study", study_id=study.id))
        )
        self.assert403(
            self.client.post(
                url_for("duplicate_submission_dataset", dataset_id=dataset.id)
            )
        )

    def test_duplicate_needs_post(self):
        sub = self._submitter_submission()
        study = SubmissionStudyFactory(submission_id=sub.id)
        self.assertEqual(
            self.client.get(
                url_for("duplicate_submission_study", study_id=study.id)
            ).status_code,
            405,
        )

    def test_view_submission_shows_duplicate_buttons(self):
        sub = self._submitter_submission()
        study = SubmissionStudyFactory(submission_id=sub.id)
        dataset = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        page = self.client.get(url_for("view_submission", sub_id=sub.id)).data.decode()

        self.assertIn(url_for("duplicate_submission_study", study_id=study.id), page)
        self.assertIn(
            url_for("duplicate_submission_dataset", dataset_id=dataset.id), page
        )

    @patch("elixir_dss.models.submission.generate_id")
    def test_duplicate_offered_and_allowed_exactly_where_add_is(self, mock_gen):
        mock_gen.side_effect = (f"COPY_{number}" for number in range(100))
        steward = ("steward1@uni.lu", "steward1")
        submitter = ("submitter1@some.edu", "submitter1")
        recipient = ("submitter2@some.edu", "submitter2")
        cases = [
            (who, status)
            for who in (steward, submitter, recipient)
            for status in (
                SubmissionStatusEnum.metadata_submission,
                SubmissionStatusEnum.metadata_approval,
                SubmissionStatusEnum.data_upload,
                SubmissionStatusEnum.cancelled,
            )
        ]
        for (email, password), status in cases:
            with self.subTest(user=email, status=status.name):
                sub = SubmissionFactory(current_status=status)
                provider = User.query.filter_by(email=submitter[0]).first()
                update_submission_basic_info(sub, provider_user_ids=[provider.id])
                db.session.add(
                    SubmissionAccess(
                        submission_id=sub.id,
                        user_id=User.query.filter_by(email=recipient[0]).first().id,
                        role=SubmissionAccess.ROLE_RECIPIENT,
                        access_granted_on=datetime.now(),
                    )
                )
                study = SubmissionStudyFactory(submission_id=sub.id)
                dataset = SubmissionDatasetFactory(
                    submission_id=sub.id, study_id=study.id
                )
                db.session.commit()
                self.client.get(url_for("logout"))
                self.login(email, password)

                page = self.client.get(
                    url_for("view_submission", sub_id=sub.id)
                ).data.decode()
                for add_endpoint, duplicate_url in (
                    (
                        "add_submission_study",
                        url_for("duplicate_submission_study", study_id=study.id),
                    ),
                    (
                        "add_submission_dataset",
                        url_for("duplicate_submission_dataset", dataset_id=dataset.id),
                    ),
                ):
                    add_url = url_for(add_endpoint, sub_id=sub.id)
                    self.assertEqual(duplicate_url in page, add_url in page)
                    add_allowed = (
                        self.client.post(
                            add_url, data={"submission_id": sub.id}
                        ).status_code
                        != 403
                    )
                    duplicate_allowed = (
                        self.client.post(duplicate_url).status_code != 403
                    )
                    self.assertEqual(duplicate_allowed, add_allowed)
