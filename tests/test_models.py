import json
from unittest.mock import patch

import pytest

from elixir_dss import db
from elixir_dss.exceptions import RecordLifecycleException
from elixir_dss.importer.submission_exporter import SubmissionExporter
from elixir_dss.models.security import User
from elixir_dss.models.services import (
    assign_role_to_user,
    create_sub,
    deactivate_user,
    delete_sub,
    register_new_user,
    update_submission_basic_info,
    clone_sub,
    revert_sub,
    steer_sub,
    cancel_sub,
    invite_submitters,
)
from elixir_dss.models.submission import (
    ContactType,
    Submission,
    SubmissionAccess,
    SubmissionStatusEnum,
    SubmissionDatasetCreator,
)
from tests import BaseTest
from tests.factories import (
    SubmissionAttachmentFactory,
    SubmissionStudyFactory,
    SubmissionDatasetFactory,
    UserFactory,
    SubmissionFactory,
    ContactFactory,
)

__author__ = "Pinar Alper"


class ModelPersistenceTest(BaseTest):
    def test_users_roles(self):
        u1 = User(
            first_name="P\u0131nar",
            last_name="Alper",
            elixir_sub_id="DUMMY_ELX_ID",
            email="pinar.alper@uni.lu",
            institution_accession="ELU_I_77",
            phone_no="+352123456789",
        )
        register_new_user(u1)
        assign_role_to_user(u1, "admin")

        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]

        self.assertEqual("P\u0131nar", pinar.first_name)
        self.assertEqual("Alper", pinar.last_name)
        self.assertEqual("DUMMY_ELX_ID", pinar.elixir_sub_id)
        self.assertEqual("pinar.alper@uni.lu", pinar.email)
        self.assertEqual("+352123456789", pinar.phone_no)
        self.assertEqual("ELU_I_77", pinar.institution_accession)

        self.assertEqual(1, len(pinar.assigned_roles))
        self.assertTrue(pinar.is_active)
        self.assertTrue(pinar.is_admin())

        assign_role_to_user(pinar, "data_steward")
        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]
        self.assertEqual(2, len(pinar.assigned_roles))
        self.assertTrue(pinar.is_data_steward())

        deactivate_user(pinar)
        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]
        self.assertFalse(pinar.is_active)

    def test_create_submission(self):
        submission_rec = create_sub("ELU_I_77")

        self.assertEqual(1, len(Submission.query.all()))
        sub = Submission.query.get_or_404(submission_rec.id)
        sub_id = sub.id
        self.assertEqual(sub.ref_name, "ELX_LU_SUB-1")
        self.assertEqual(sub.current_status, SubmissionStatusEnum.draft)
        self.assertIsNotNone(sub.created_on)

        self.assertTrue(sub.is_deletable())
        self.assertFalse(sub.is_in_progress())
        self.assertEqual(0, len(sub.submission_accesses))
        self.assertEqual(0, len(sub.studies))
        self.assertEqual(0, len(sub.datasets))
        self.assertEqual(0, len(sub.provider_user_names()))
        self.assertFalse(sub.has_providers())

        u1 = User(
            first_name="Kavita",
            last_name="Rege",
            elixir_sub_id="SOME_ELX_ID",
            email="kavita.rege@uni.lu",
            institution_accession="ELU_I_77",
            phone_no="+352123456789",
        )
        usr = register_new_user(u1)
        update_submission_basic_info(sub, provider_user_ids=[usr.id])

        self.assertEqual(
            1, len(Submission.query.get_or_404(sub_id).submission_accesses)
        )

        delete_sub(sub_id)
        self.assertEqual(0, len(Submission.query.all()))

        # Testing delete-orphan annotations on the relations of Submission
        self.assertEqual(0, len(SubmissionAccess.query.all()))

    def test_steer_submission(self):
        # Setup initial DRAFT submission using the factory
        submission_rec = SubmissionFactory()
        sub_id = submission_rec.id

        # Steer fails without Data Provider
        self._assert_steer_fails(
            sub_id, "Steering should fail because provider is missing."
        )

        # Add Data Provider
        usr = UserFactory(
            first_name="Kavita", last_name="Rege", institution_accession="ELU_I_2"
        )
        sub = Submission.query.get_or_404(sub_id)
        update_submission_basic_info(sub, provider_user_ids=[usr.id])

        self.assertEqual(1, len(SubmissionAccess.query.all()))
        self.assertEqual(1, len(sub.submission_accesses))

        # Steer to METADATA_SUBMISSION
        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_submission)

        # Steer fails without Study/Dataset
        self._assert_steer_fails(sub_id)

        # Add metadata
        study_rec = SubmissionStudyFactory(
            submission_id=sub_id, study_contacts=[ContactFactory()]
        )
        SubmissionDatasetFactory(submission_id=sub_id, study_id=study_rec.id)
        db.session.commit()

        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_approval)

        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_upload)

        revert_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_approval)

        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_upload)

        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_approval)

        steer_sub(sub_id)
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.completed)

        # Steer fails when COMPLETED
        self._assert_steer_fails(
            sub_id, "Steering should fail because submission is complete."
        )

    def test_new_6_step_workflow_state_transitions(self):
        """Test the new 6-step workflow with approval states"""
        # Test step_num mapping for all 6 states
        self.assertEqual(SubmissionStatusEnum.draft.step_num(), 0)
        self.assertEqual(SubmissionStatusEnum.metadata_submission.step_num(), 1)
        self.assertEqual(SubmissionStatusEnum.metadata_approval.step_num(), 2)
        self.assertEqual(SubmissionStatusEnum.data_upload.step_num(), 3)
        self.assertEqual(SubmissionStatusEnum.data_approval.step_num(), 4)
        self.assertEqual(SubmissionStatusEnum.completed.step_num(), 5)

        # Test next_state transitions
        self.assertEqual(
            SubmissionStatusEnum.draft.next_state(),
            SubmissionStatusEnum.metadata_submission,
        )
        self.assertEqual(
            SubmissionStatusEnum.metadata_submission.next_state(),
            SubmissionStatusEnum.metadata_approval,
        )
        self.assertEqual(
            SubmissionStatusEnum.metadata_approval.next_state(),
            SubmissionStatusEnum.data_upload,
        )
        self.assertEqual(
            SubmissionStatusEnum.data_upload.next_state(),
            SubmissionStatusEnum.data_approval,
        )
        self.assertEqual(
            SubmissionStatusEnum.data_approval.next_state(),
            SubmissionStatusEnum.completed,
        )
        self.assertIsNone(SubmissionStatusEnum.completed.next_state())

        # Test prev_state transitions
        self.assertIsNone(SubmissionStatusEnum.draft.prev_state())
        self.assertEqual(
            SubmissionStatusEnum.metadata_submission.prev_state(),
            SubmissionStatusEnum.draft,
        )
        self.assertEqual(
            SubmissionStatusEnum.metadata_approval.prev_state(),
            SubmissionStatusEnum.metadata_submission,
        )
        self.assertEqual(
            SubmissionStatusEnum.data_upload.prev_state(),
            SubmissionStatusEnum.metadata_approval,
        )
        self.assertEqual(
            SubmissionStatusEnum.data_approval.prev_state(),
            SubmissionStatusEnum.data_upload,
        )
        self.assertEqual(
            SubmissionStatusEnum.completed.prev_state(),
            SubmissionStatusEnum.data_approval,
        )

        # Test is_in_progress includes approval states
        submission = create_sub("ELU_I_77")
        submission.current_status = SubmissionStatusEnum.metadata_submission
        self.assertTrue(submission.is_in_progress())
        submission.current_status = SubmissionStatusEnum.metadata_approval
        self.assertTrue(submission.is_in_progress())
        submission.current_status = SubmissionStatusEnum.data_upload
        self.assertTrue(submission.is_in_progress())
        submission.current_status = SubmissionStatusEnum.data_approval
        self.assertTrue(submission.is_in_progress())
        submission.current_status = SubmissionStatusEnum.draft
        self.assertFalse(submission.is_in_progress())
        submission.current_status = SubmissionStatusEnum.completed
        self.assertFalse(submission.is_in_progress())

    def test_export_submission(self):
        submission_rec = create_sub("ELU_I_5")

        u1 = UserFactory()
        usr = register_new_user(u1)

        update_submission_basic_info(
            submission_rec,
            institution_accession="ELU_I_5",
            provider_user_ids=[usr.id],
            local_project_name="Submitting to NCER PD Diagnosis project",
            local_custodians_json=json.dumps(["Enrico Glaab", "Rudi Balling"]),
        )

        study_rec = SubmissionStudyFactory(submission_id=submission_rec.id)
        c1 = ContactFactory()
        c1.contact_category = ContactType.query.get_or_404(1)
        study_rec.study_contacts = [c1]

        SubmissionDatasetFactory(
            submission_id=submission_rec.id,
            study_id=study_rec.id,
            sci_datatypes_json=json.dumps(["Genomics_variant_array", "RNASeq"]),
            gdpr_datatypes_json=json.dumps(["standard", "ethnic"]),
            has_special_subjects=True,
            special_subjects_notes="mothers and babies",
            consent_notes="Consent is consistent among all subjects",
        )
        SubmissionDatasetFactory(
            submission_id=submission_rec.id,
            study_id=study_rec.id,
            sci_datatypes_json=json.dumps(["Transcriptome_array", "RNASeq"]),
            gdpr_datatypes_json=json.dumps(["standard", "ethnic"]),
            consent_status_code="ht",
            consent_notes="There are three primary consent groups",
        )

        SubmissionAttachmentFactory(submission_id=submission_rec.id)
        SubmissionAttachmentFactory(submission_id=submission_rec.id)

        submission_rec = Submission.query.get_or_404(submission_rec.id)
        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)

        self.assertEqual(exp["ref_name"], submission_rec.ref_name)
        self.assertEqual(len(exp["data_declarations"]), 2)
        print(json.dumps(exp, indent=4))

    def test_clone_submission_basic(self):
        original = create_sub("ELU_I_11")

        clone = clone_sub(original.id)

        # Assert new object is distinct
        self.assertNotEqual(original.id, clone.id)
        self.assertTrue(clone.ref_name.startswith("ELX_LU_SUB-"))

        self.assertEqual(clone.current_status, SubmissionStatusEnum.draft)

        self.assertEqual(len(clone.submission_contacts), 0)
        self.assertEqual(len(clone.datasets), 0)
        self.assertEqual(len(clone.studies), 0)
        self.assertFalse(clone.exported)

        # Db contains two submissions
        subs = Submission.query.all()
        self.assertEqual(2, len(subs))

    @pytest.mark.usefixtures("mock_idservice_requests_post")
    def test_clone_with_studies_and_datasets(self):
        sub = create_sub("ELU_I_77")

        # Add study + dataset
        study = SubmissionStudyFactory(
            submission_id=sub.id,
            name="Study 1",
            description="Genomics cohort",
            ethics_approval_exists=True,
            study_types_json=json.dumps(["Observational"]),
        )
        dataset = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            title="Dataset 1",
            creators=[
                SubmissionDatasetCreator(
                    first_name="John",
                    last_name="Doe",
                    email="john@example.com",
                    institution="Uni",
                    role="PI",
                )
            ],
            description="Sample dataset description",
            gdpr_datatypes_json=json.dumps(["personal"]),
            sci_datatypes_json=json.dumps(["RNASeq"]),
        )

        clone = clone_sub(sub.id, clone_studies=True, clone_datasets=True)

        self.assertEqual(len(clone.studies), 1)
        self.assertEqual(len(clone.datasets), 1)
        self.assertEqual(clone.datasets[0].title, "Dataset 1")
        self.assertEqual(clone.datasets[0].internal_id, "TEST_DATASET_ID_001")
        self.assertNotEqual(clone.datasets[0].id, dataset.id)
        self.assertNotEqual(clone.studies[0].id, study.id)

    def _assert_steer_fails(self, sub_id, reason="Expected failure"):
        """Assert that steering fails with the expected exception and message."""
        with self.assertRaises(RecordLifecycleException, msg=reason):
            steer_sub(sub_id)

    def test_clone_submission_rollback_on_error(self):
        from unittest.mock import patch
        from tests.factories import (
            SubmissionFactory,
            SubmissionStudyFactory,
            SubmissionDatasetFactory,
        )

        original = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=original.id)
        SubmissionDatasetFactory(submission_id=original.id, study_id=study.id)

        submissions_before = Submission.query.count()

        with patch.object(db.session, "commit", side_effect=Exception("DB error")):
            with self.assertRaises(Exception):
                clone_sub(original.id, clone_studies=True, clone_datasets=True)

        self.assertEqual(submissions_before, Submission.query.count())
        self.assertIsNotNone(Submission.query.get(original.id))

    @patch("elixir_dss.models.services.send_invitations")
    def test_invite_submitters(self, mock_send_invitations):
        submission = create_sub("ELU_I_77")

        existing_user = UserFactory()
        contact_existing = ContactFactory(
            first_name=existing_user.first_name,
            last_name=existing_user.last_name,
            email=existing_user.email,
            category_id=1,
            submission_id=submission.id,
        )

        contact_new = ContactFactory(submission_id=submission.id, send_invite=True)

        contact_without_invite = ContactFactory(
            submission_id=submission.id, send_invite=False
        )

        invite_submitters(submission, [contact_existing, contact_new])

        self.assertEqual(User.query.count(), 2)
        self.assertEqual(SubmissionAccess.query.count(), 1)

        self.assertIsNone(SubmissionAccess.query.filter_by(user=existing_user).first())

        self.assertIsNone(
            User.query.filter_by(email=contact_without_invite.email).first()
        )

        mock_send_invitations.assert_called_once()
        invited_users = mock_send_invitations.call_args[0][1]
        self.assertEqual(len(invited_users), 1)
        self.assertEqual(invited_users[0].email, contact_new.email)

    @patch("elixir_dss.models.services.send_invitations")
    def test_invite_submitters_empty_list(self, mock_send_invitations):
        submission = create_sub("ELU_I_77")

        invite_submitters(submission, [])

        self.assertEqual(User.query.count(), 0)
        self.assertEqual(SubmissionAccess.query.count(), 0)

        mock_send_invitations.assert_not_called()

    def test_study_json_helper_methods(self):
        """Test _json_list helper handles JSON parsing and None/invalid values"""
        submission = SubmissionFactory()

        # Test JSON parsing logic
        study = SubmissionStudyFactory(
            submission_id=submission.id,
            external_identifiers_json='["EGA123", "GEO456"]',
            species_json='["Homo sapiens"]',
            diseases_json='["Diabetes"]',
        )
        self.assertEqual(study.external_identifiers, ["EGA123", "GEO456"])
        self.assertEqual(study.species_names, ["Homo sapiens"])

        # Test None handling (edge case)
        study_null = SubmissionStudyFactory(
            submission_id=submission.id,
            species_json=None,
        )
        self.assertEqual(study_null.species_names, [])

    def test_cancel_submission(self):
        sub = create_sub("ELU_I_77")
        db.session.add(sub)
        db.session.commit()

        u = User(
            first_name="AA",
            last_name="BB",
            elixir_sub_id="X",
            email="aa@bb.cc",
            institution_accession="ELU_I_77",
            phone_no="+352 11",
        )
        usr = register_new_user(u)
        update_submission_basic_info(sub, provider_user_ids=[usr.id])

        cancelled = cancel_sub(
            submission=sub, reason="test reason", cancelled_by_user=usr
        )

        self.assertEqual(cancelled.current_status, SubmissionStatusEnum.cancelled)
        self.assertEqual(cancelled.cancellation_reason, "test reason")
        self.assertEqual(cancelled.cancelled_by_user_id, usr.id)
