import json
import logging
from datetime import date, datetime
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from elixir_dss import app, db, lft
from elixir_dss.clients.daisy import get_elu_entities
from elixir_dss.clients.idservice import generate_id, IDServiceError
from elixir_dss.clients.lft import LFTHandler
from elixir_dss.exceptions import RecordLifecycleException, RecordNotExistsException
from elixir_dss.importer.submission_exporter import (
    SubmissionExporter,
    normalize,
    _parse_json_string,
)
from elixir_dss.models.security import Role, User
from elixir_dss.models.services import (
    assign_role_to_user,
    create_sub,
    deactivate_user,
    delete_sub,
    register_new_user,
    send_new_message_notification,
    update_submission_basic_info,
    clone_sub,
    revert_sub,
    steer_sub,
    cancel_sub,
    invite_recipients,
    invite_submitters,
    update_user_info,
    approve_metadata,
    reject_metadata,
    approve_data,
    reject_data,
)
from elixir_dss.models.submission import (
    ContactType,
    Submission,
    SubmissionAccess,
    SubmissionAttachment,
    SubmissionStatusEnum,
    SubmissionDatasetCreator,
    SubmissionMessage,
    format_local_custodian,
    parse_local_custodian,
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
        self.assertEqual(pinar.assigned_role_ids(), [pinar.assigned_roles[0].id])
        self.assertEqual(pinar.display_name(), "Pınar Alper")

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
        sub = db.get_or_404(Submission, submission_rec.id)
        sub_id = sub.id
        self.assertEqual(sub.ref_name, "ELX_LU_SUB-1")
        self.assertEqual(sub.current_status, SubmissionStatusEnum.draft)
        self.assertIsNotNone(sub.created_on)

        self.assertTrue(sub.is_deletable())
        self.assertFalse(sub.is_in_progress())
        self.assertEqual(0, len(sub.submission_accesses))
        self.assertEqual(0, len(sub.studies))
        self.assertEqual(0, len(sub.datasets))
        self.assertFalse(sub.has_dataset())
        self.assertIsNotNone(sub.to_dict())
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

        self.assertEqual(1, len(db.get_or_404(Submission, sub_id).submission_accesses))

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
        sub = db.get_or_404(Submission, sub_id)
        update_submission_basic_info(sub, provider_user_ids=[usr.id])

        self.assertEqual(1, len(SubmissionAccess.query.all()))
        self.assertEqual(1, len(sub.submission_accesses))

        # Steer to METADATA_SUBMISSION
        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_submission)

        # Steer fails without Study/Dataset
        self._assert_steer_fails(sub_id)

        # Add metadata
        study_rec = SubmissionStudyFactory(
            submission_id=sub_id, study_contacts=[ContactFactory()]
        )
        SubmissionDatasetFactory(submission_id=sub_id, study_id=study_rec.id)
        db.session.commit()
        self.assertTrue(sub.has_dataset())

        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_approval)

        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_upload)

        revert_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.metadata_approval)

        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_upload)

        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.data_approval)

        steer_sub(sub_id)
        sub = db.get_or_404(Submission, sub_id)
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
        c1.contact_category = db.get_or_404(ContactType, 1)
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

        submission_rec = db.get_or_404(Submission, submission_rec.id)
        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)

        self.assertEqual(exp["submission"]["submission_id"], submission_rec.ref_name)
        self.assertEqual(len(exp["studies"]), 1)
        self.assertEqual(len(exp["studies"][0]["datasets"]), 2)

    def test_export_submission_structure(self):
        submission_rec = create_sub("ELU_I_5")
        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)

        expected_submission_keys = {
            "submission_id",
            "created_on",
            "finalised_on",
            "status",
            "local_project_name",
            "local_custodians_json",
            "institution_accession",
            "providers",
        }

        self.assertSetEqual(set(exp["submission"].keys()), expected_submission_keys)

    def test_export_study_structure(self):
        submission_rec = create_sub("ELU_I_5")
        SubmissionStudyFactory(submission_id=submission_rec.id)

        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)

        expected_study_keys = {
            "title",
            "description",
            "ethics_approval_no",
            "ethics_approval_exists",
            "study_types",
            "multi_center_study",
            "species_json",
            "diseases_json",
            "number_of_subjects",
            "sample_sources_json",
            "informed_consent_given",
            "external_id",
            "datasets",
        }

        self.assertSetEqual(set(exp["studies"][0].keys()), expected_study_keys)

    def test_export_dataset_structure(self):
        submission_rec = create_sub("ELU_I_5")
        study_rec = SubmissionStudyFactory(submission_id=submission_rec.id)

        SubmissionDatasetFactory(
            submission_id=submission_rec.id,
            study_id=study_rec.id,
        )

        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)

        dataset = exp["studies"][0]["datasets"][0]

        expected_dataset_keys = {
            "dataset_id",
            "title",
            "description",
            "study",
            "external_id",
            "gdpr_data_types",
            "scientific_data_types",
            "contains_personal_data",
            "data_processing_type",
            "special_category_data",
            "special_subjects",
            "consent_status",
            "legal_basis_collection",
            "legal_basis_sharing",
            "records",
            "dataset_version",
            "creation_date",
            "last_update_date",
            "file_types",
            "data_standards",
            "size_bytes",
            "uc_project_limited",
            "uc_research_use_limited",
            "uc_research_area_restriction",
            "uc_research_area_notes",
            "uc_geographic_restriction",
            "uc_geographic_notes",
            "uc_recipient_type_restriction",
            "uc_recipient_type_notes",
            "uc_user_restriction",
            "uc_user_notes",
            "uc_publication_restriction",
            "uc_publication_notes",
            "uc_time_restriction",
            "uc_time_notes",
            "uc_lcsb_time_restriction",
            "uc_lcsb_time_date",
            "uc_return_requirement",
            "uc_return_notes",
            "uc_ip_restriction",
            "uc_ip_notes",
            "uc_dac_required",
            "uc_dac_notes",
            "uc_access_form_required",
            "uc_other_notes",
        }

        self.assertSetEqual(set(dataset.keys()), expected_dataset_keys)

    def test_normalize(self):
        self.assertEqual(normalize(None), "-")
        self.assertEqual(normalize(""), "-")
        self.assertEqual(normalize([]), "-")

        self.assertEqual(normalize(True), "Yes")
        self.assertEqual(normalize(False), "No")

        self.assertEqual(normalize(["a", "b"]), "a, b")

        self.assertEqual(normalize(date(2024, 6, 1)), "2024-06-01")

        self.assertEqual(normalize('["Genomics", "RNASeq"]'), "Genomics, RNASeq")
        self.assertEqual(normalize('{"key": "value"}'), "key: value")

        self.assertEqual(normalize("test"), "test")

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
        original = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=original.id)
        SubmissionDatasetFactory(submission_id=original.id, study_id=study.id)

        submissions_before = Submission.query.count()

        with patch.object(db.session, "commit", side_effect=Exception("DB error")):
            with self.assertRaises(Exception):
                clone_sub(original.id, clone_studies=True, clone_datasets=True)

        self.assertEqual(submissions_before, Submission.query.count())
        self.assertIsNotNone(db.session.get(Submission, original.id))

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

        study_bad = SubmissionStudyFactory(
            submission_id=submission.id, species_json="{bad json"
        )
        self.assertEqual(study_bad.species_names, [])

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

    def test_update_user_info_fields(self):
        user = UserFactory(
            first_name="Old",
            last_name="Name",
            email="old@example.com",
            phone_no="000000",
            institution_accession="OLD_INST",
        )

        update_user_info(
            user,
            first_name="New",
            last_name="User",
            email="new@example.com",
            phone_no="123456",
            institution_accession="NEW_INST",
            institution_division="New Division",
            addr_line1="Street 1",
            addr_line2="Street 2",
        )

        u = db.session.get(User, user.id)
        self.assertEqual(u.first_name, "New")
        self.assertEqual(u.last_name, "User")
        self.assertEqual(u.email, "new@example.com")
        self.assertEqual(u.phone_no, "123456")
        self.assertEqual(u.institution_accession, "NEW_INST")
        self.assertEqual(u.institution_division, "New Division")
        self.assertEqual(u.addr_line1, "Street 1")
        self.assertEqual(u.addr_line2, "Street 2")

        roles_before = list(u.assigned_roles)
        update_user_info(user)
        self.assertEqual(u.first_name, "New")
        self.assertEqual(list(u.assigned_roles), roles_before)

    def test_user_and_contact_emails_are_normalized(self):
        user = UserFactory(email=" User.Name@Example.COM ")
        contact = ContactFactory(email=" Contact.Name@Example.COM ")

        self.assertEqual(user.email, "user.name@example.com")
        self.assertEqual(contact.email, "contact.name@example.com")

    @patch("elixir_dss.models.services.persist_and_send_notification")
    def test_approve_metadata(self, _mock_notify):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        reviewer = UserFactory()
        approve_metadata(sub.id, reviewer.id, feedback="Looks good")

        sub = db.session.get(Submission, sub.id)
        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        assert sub.current_status == SubmissionStatusEnum.data_upload
        assert "Metadata approved" in msg.message_text
        assert msg.sender_user_id == reviewer.id

    @patch("elixir_dss.models.services.persist_and_send_notification")
    def test_reject_metadata(self, _mock_notify):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        reviewer = UserFactory()
        reject_metadata(sub.id, reviewer.id, feedback="Missing fields")

        sub = db.session.get(Submission, sub.id)
        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        assert sub.current_status == SubmissionStatusEnum.metadata_submission
        assert "Metadata rejected" in msg.message_text
        assert msg.sender_user_id == reviewer.id

    @patch("elixir_dss.models.services.persist_and_send_notification")
    def test_approve_data(self, _mock_notify):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        reviewer = UserFactory()
        approve_data(sub.id, reviewer.id, feedback="Data good")

        sub = db.session.get(Submission, sub.id)
        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        assert sub.current_status == SubmissionStatusEnum.completed
        assert "Data approved" in msg.message_text
        assert msg.sender_user_id == reviewer.id

    @patch("elixir_dss.models.services.persist_and_send_notification")
    def test_reject_data(self, _mock_notify):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        reviewer = UserFactory()
        reject_data(sub.id, reviewer.id, feedback="Incorrect format")

        sub = db.session.get(Submission, sub.id)
        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        assert sub.current_status == SubmissionStatusEnum.data_upload
        assert "Data rejected" in msg.message_text
        assert msg.sender_user_id == reviewer.id

    def test_submission_export(self):
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)

        exporter = SubmissionExporter([sub])

        output = StringIO()
        result = exporter.export_to_file(output)
        assert result is True
        content = output.getvalue()
        assert len(content) > 0
        assert sub.ref_name in content

        sub.exported = False
        db.session.commit()

        buffer = exporter.export_to_buffer(StringIO())
        data = json.loads(buffer.getvalue())
        assert "$schema" in data
        assert "items" in data
        assert len(data["items"]) == 1
        assert "submission" in data["items"][0]

    def test_parse_json_string(self):
        assert _parse_json_string('["a", "b"]') == "a, b"
        assert _parse_json_string('{"k": "v"}') == "k: v"
        assert _parse_json_string("[]") == "-"
        assert _parse_json_string("{}") == "-"
        assert _parse_json_string("hello") is None
        assert _parse_json_string("[invalid") is None

    def test_datetime_template_filter(self):
        dt_filter = app.jinja_env.filters["dt"]
        date_filter = app.jinja_env.filters["date"]

        self.assertIsNone(dt_filter(None))

        d = datetime(2026, 1, 15, 10, 30)
        self.assertEqual(dt_filter(d), "2026-01-15,  10:30")
        self.assertEqual(dt_filter(d, "%Y/%m/%d"), "2026/01/15")

        self.assertEqual(date_filter(d), "2026-01-15")

    def test_lft_handler_invalidate_no_client(self):
        handler = LFTHandler()
        handler.client = None
        mock_logger = MagicMock()
        handler._logger = mock_logger

        handler.invalidate_links_for_submission(1)

        mock_logger.warning.assert_called_once_with("LFT not configured")

    def test_lft_handler_login_failed(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.client.login.side_effect = Exception("login err")
        handler.username = "u"
        handler.password = "p"
        handler._logger = MagicMock()
        handler.namespace_id = "ns"

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, internal_id="ds1"
        )
        db.session.commit()

        handler.invalidate_links_for_submission(sub.id)

        handler.client.login.assert_called_once_with("u", "p")
        handler.client.delete_share.assert_not_called()
        handler.client.links_list.assert_not_called()
        handler._logger.error.assert_called_once()
        self.assertIn("login failed", handler._logger.error.call_args[0][0])

    def test_lft_handler_invalidate_no_internal_id(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.username = "u"
        handler.password = "p"
        handler._logger = MagicMock()
        handler.namespace_id = "ns"

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, internal_id=None
        )
        db.session.commit()

        handler.invalidate_links_for_submission(sub.id)

        handler.client.login.assert_called_once_with("u", "p")
        handler.client.delete_share.assert_not_called()
        handler.client.links_list.assert_not_called()

    def test_lft_handler_invalidate_delete_links(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.username = "u"
        handler.password = "p"
        handler._logger = logging.getLogger("test")
        handler.namespace_id = "ns"

        mock_link = MagicMock()
        mock_link.hashid = "abc"
        handler.client.links_list.return_value = [mock_link]

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, internal_id="ds1"
        )
        db.session.commit()

        handler.invalidate_links_for_submission(sub.id, delete_share=False)
        handler.client.delete_link.assert_called_once()

    def test_lft_handler_invalidate_exception(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.client.delete_share.side_effect = Exception("fail")
        handler.username = "u"
        handler.password = "p"
        handler._logger = MagicMock()
        handler.namespace_id = "ns"

        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_upload)
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, internal_id="ds1"
        )
        SubmissionDatasetFactory(
            submission_id=sub.id, study_id=study.id, internal_id="ds2"
        )
        db.session.commit()

        handler.invalidate_links_for_submission(sub.id)

        self.assertEqual(handler.client.delete_share.call_count, 2)
        self.assertEqual(handler._logger.error.call_count, 2)

    def test_lft_handler_get_or_create_login_failed(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.client.login.side_effect = Exception("login fail")
        handler.username = "u"
        handler.password = "p"
        handler.namespace_id = "ns"

        with self.assertRaises(RuntimeError):
            handler.get_or_create_link(MagicMock(internal_id="ds1"), "sub1")

    def test_lft_handler_get_or_create_link_list_error(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.client.links_list.side_effect = Exception("list fail")
        handler.username = "u"
        handler.password = "p"
        handler.namespace_id = "ns"
        handler.links_url = "https://lft.example.com/"

        with self.assertRaises(RuntimeError):
            handler.get_or_create_link(MagicMock(internal_id="ds1"), "sub1")

    def test_lft_handler_get_or_create_create_error(self):
        handler = LFTHandler()
        handler.client = MagicMock()
        handler.client.links_list.return_value = []
        handler.client.create_link.side_effect = Exception("create fail")
        handler.username = "u"
        handler.password = "p"
        handler.namespace_id = "ns"
        handler.links_url = "https://lft.example.com/"
        handler.link_validity_days = 1

        with self.assertRaises(RuntimeError):
            handler.get_or_create_link(MagicMock(internal_id="ds1"), "sub1")

    # --- submission.py model coverage tests ---

    def test_attachment_files_urls_none(self):
        """Cover SubmissionAttachment.files_urls() when file_names is None."""
        att = SubmissionAttachment()
        att.file_names = None
        self.assertIsNone(att.files_urls())

    def test_generate_id_no_endpoint(self):
        """Cover idservice.py generate_id when endpoint not configured."""
        original = app.config.get("IDSERVICE_ENDPOINT")
        try:
            app.config["IDSERVICE_ENDPOINT"] = None
            with self.assertRaises(IDServiceError):
                generate_id("test")
        finally:
            app.config["IDSERVICE_ENDPOINT"] = original

    def test_get_elu_entities_no_daisy(self):
        """Cover daisy.py get_elu_entities when DAISY_USE is False."""
        original = app.config.get("DAISY_USE")
        try:
            app.config["DAISY_USE"] = False
            result = get_elu_entities("partners")
            self.assertIsInstance(result, list)
        finally:
            app.config["DAISY_USE"] = original

    def test_provider_institute_name_none(self):
        """Cover Submission.provider_institute_name() None path."""
        sub = SubmissionFactory(institution_accession=None)
        self.assertIsNone(sub.provider_institute_name())

    def test_provider_institute_address(self):
        """Cover Submission.provider_institute_address()."""
        sub = SubmissionFactory(institution_accession="ELU_I_77")
        with patch("elixir_dss.models.submission.get_elu_partners") as mock_partners:
            mock_partners.return_value = [
                {"external_id": "ELU_I_77", "name": "Test Uni", "address": "123 Street"}
            ]
            result = sub.provider_institute_address()
            self.assertEqual(result, "123 Street")

        sub.institution_accession = None
        self.assertIsNone(sub.provider_institute_address())

    def test_is_detail_info_complete(self):
        """Cover Submission.is_detail_info_complete()."""
        sub = SubmissionFactory()
        self.assertFalse(sub.is_detail_info_complete())

        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()
        sub = db.session.get(Submission, sub.id)
        self.assertTrue(sub.is_detail_info_complete())

    def test_contact_to_dict(self):
        """Cover Contact.to_dict()."""
        sub = SubmissionFactory()
        contact = ContactFactory(
            submission_id=sub.id, first_name="Jane", last_name="Doe"
        )
        db.session.commit()

        d = contact.to_dict()
        self.assertEqual(d["first_name"], "Jane")
        self.assertEqual(d["last_name"], "Doe")
        self.assertIn("email", d)
        self.assertIn("institution", d)
        self.assertIn("is_main_contact", d)
        self.assertIn("category", d)

    def test_study_json_properties(self):
        """Cover diseases_names, sample_sources_names, other_subject_characteristics_list."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(
            submission_id=sub.id,
            diseases_json=json.dumps(["MONDO:0005015"]),
            sample_sources_json=json.dumps(["blood", "tissue"]),
            other_subject_characteristics_json=json.dumps(["smoker"]),
        )
        db.session.commit()

        self.assertEqual(study.diseases_names, ["MONDO:0005015"])
        self.assertEqual(study.sample_sources_names, ["blood", "tissue"])
        self.assertEqual(study.other_subject_characteristics_list, ["smoker"])

    def test_dataset_json_methods_none_paths(self):
        """Cover sci_data_type_names, gdpr_data_type_names when None."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        # Columns are NOT NULL in DB, so set to None in-memory to cover the guard clause
        ds.sci_datatypes_json = None
        ds.gdpr_datatypes_json = None
        self.assertEqual(ds.sci_data_type_names(), [])
        self.assertEqual(ds.gdpr_data_type_names(), [])

    def test_dataset_json_methods_loaded_paths(self):
        """Cover data_standard_names, file_type_names, sample_type_names with data."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            data_standards_json=json.dumps(["CDISC", "HL7"]),
            file_types_json=json.dumps(["CSV", "TSV"]),
            sample_types_json=json.dumps(["blood", "tissue"]),
        )
        db.session.commit()

        self.assertEqual(ds.data_standard_names(), ["CDISC", "HL7"])
        self.assertEqual(ds.file_type_names(), ["CSV", "TSV"])
        self.assertEqual(ds.sample_type_names(), ["blood", "tissue"])

    def test_dataset_sample_type_names_none(self):
        """Cover sample_type_names when None."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            sample_types_json=None,
        )
        db.session.commit()
        self.assertEqual(ds.sample_type_names(), [])

    def test_dataset_has_special_category_data(self):
        """Cover has_special_category_data()."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            gdpr_datatypes_json=json.dumps(["genetic"]),
        )
        db.session.commit()
        self.assertTrue(ds.has_special_category_data())

        ds.gdpr_datatypes_json = json.dumps(["basic"])
        self.assertFalse(ds.has_special_category_data())

        ds.gdpr_datatypes_json = None
        self.assertFalse(ds.has_special_category_data())

    def test_dataset_has_special_subjects_display(self):
        """Cover has_special_subjects_display()."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(
            submission_id=sub.id,
            study_id=study.id,
            has_special_subjects=True,
        )
        db.session.commit()
        self.assertEqual(ds.has_special_subjects_display(), "Yes")

        ds.has_special_subjects = False
        self.assertEqual(ds.has_special_subjects_display(), "No")

    def test_dataset_creator_fullname(self):
        """Cover SubmissionDatasetCreator.fullname()."""
        sub = SubmissionFactory()
        study = SubmissionStudyFactory(submission_id=sub.id)
        ds = SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        creator = SubmissionDatasetCreator(
            dataset_id=ds.id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            institution="Uni",
            role="PI",
        )
        db.session.add(creator)
        db.session.commit()
        self.assertEqual(creator.fullname(), "John DOE")

    # --- services.py coverage tests ---

    def test_security_has_role_from_none(self):
        """Cover User.has_role_from when assigned_roles is None."""
        user = MagicMock(spec=User)
        user.assigned_roles = None
        result = User.has_role_from(user, ["admin"])
        self.assertFalse(result)

    def test_revert_sub_no_prev_state(self):
        """Cover revert_sub when in draft state."""
        sub = create_sub("ELU_I_77")
        with self.assertRaises(RecordLifecycleException):
            revert_sub(sub.id)

    def test_assign_role_invalid(self):
        """Cover assign_role_to_user with non-existent role."""
        user = UserFactory()
        with self.assertRaises(RecordNotExistsException):
            assign_role_to_user(user, "nonexistent_role")

    @patch("elixir_dss.models.services.persist_and_send_notification")
    def test_approve_metadata_no_feedback(self, _mock_notify):
        """Cover approve_metadata without feedback."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        reviewer = UserFactory()
        approve_metadata(sub.id, reviewer.id)

        db.session.expire_all()
        updated_sub = db.session.get(Submission, sub.id)
        self.assertEqual(updated_sub.current_status, SubmissionStatusEnum.data_upload)

        msg = SubmissionMessage.query.filter_by(submission_id=sub.id).first()
        self.assertEqual(msg.message_text, "Metadata approved.")
        self.assertEqual(msg.message_type, "metadata_approval")

    def test_update_user_info_add_role(self):
        """Cover update_user_info adding a new role."""
        user = UserFactory()
        admin_role = Role.query.filter_by(name="admin").first()
        self.assertIsNotNone(admin_role, "admin role must exist in seed data")

        update_user_info(user, assigned_role_ids=[admin_role.id])
        self.assertIn(admin_role, user.assigned_roles)

    def test_steer_to_data_approval_lft_exception(self):
        """Cover _apply_steer_side_effects lft exception path."""
        sub = create_sub("ELU_I_77")
        user = UserFactory()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        study = SubmissionStudyFactory(submission_id=sub.id)
        SubmissionDatasetFactory(submission_id=sub.id, study_id=study.id)
        db.session.commit()

        steer_sub(sub.id)  # draft -> metadata_submission
        steer_sub(sub.id)  # metadata_submission -> metadata_approval
        steer_sub(sub.id)  # metadata_approval -> data_upload

        with (
            patch.object(lft, "client", MagicMock()),
            patch.object(
                lft,
                "invalidate_links_for_submission",
                side_effect=Exception("LFT fail"),
            ),
        ):
            steer_sub(sub.id)  # data_upload -> data_approval (exception caught)
            sub_obj = db.session.get(Submission, sub.id)
            self.assertEqual(sub_obj.current_status, SubmissionStatusEnum.data_approval)

    def test_invite_submitters_with_send_invite(self):
        """Cover invite_submitters → send_invitations path."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        contact = ContactFactory(
            submission_id=sub.id,
            send_invite=True,
            email="newinvitee@example.com",
            first_name="Invite",
            last_name="User",
        )
        db.session.commit()

        # Let send_invitations execute but mock persist_and_send_notification
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_persist:
            invite_submitters(sub, [contact])
            mock_persist.assert_called_once()
            text_email = mock_persist.call_args.args[3]
            html_email = mock_persist.call_args.args[4]
            expected_url = f"https://dss.example.com/submission/view/{sub.id}"
            self.assertIn(expected_url, text_email)
            self.assertIn(expected_url, html_email)
            invited_user = User.query.filter_by(email="newinvitee@example.com").first()
            self.assertIsNotNone(invited_user)

    def test_clone_sub_with_contacts(self):
        """Cover clone_sub contact cloning."""
        sub = create_sub("ELU_I_77")
        ContactFactory(submission_id=sub.id, first_name="Clone", last_name="Me")
        db.session.commit()

        clone = clone_sub(sub.id, clone_studies=False, clone_datasets=False)
        self.assertEqual(len(clone.submission_contacts), 1)
        self.assertEqual(clone.submission_contacts[0].first_name, "Clone")

    def test_update_submission_revoke_access(self):
        """Cover revoke access path in update_submission_basic_info."""
        sub = create_sub("ELU_I_77")
        user1 = UserFactory(email="user1_rev@test.com")
        user2 = UserFactory(email="user2_rev@test.com")

        update_submission_basic_info(sub, provider_user_ids=[user1.id, user2.id])
        self.assertEqual(len(sub.submission_accesses), 2)

        update_submission_basic_info(sub, provider_user_ids=[user1.id])
        accesses = SubmissionAccess.query.filter_by(submission_id=sub.id).all()
        access_user_ids = [a.user_id for a in accesses]
        self.assertIn(user1.id, access_user_ids)
        self.assertNotIn(user2.id, access_user_ids)

    def test_cancel_sub_lft_exception(self):
        """Cover cancel_sub LFT exception path."""
        sub = create_sub("ELU_I_77")
        user = UserFactory()
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        with (
            patch.object(lft, "client", MagicMock()),
            patch.object(
                lft,
                "invalidate_links_for_submission",
                side_effect=Exception("LFT fail"),
            ),
        ):
            result = cancel_sub(sub, "test cancel", user)
            self.assertEqual(result.current_status, SubmissionStatusEnum.cancelled)

    def test_send_new_message_notification(self):
        """Cover send_new_message_notification."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_submission)
        user = UserFactory()
        update_submission_basic_info(sub, provider_user_ids=[user.id])

        msg = SubmissionMessage(
            submission_id=sub.id,
            sender_user_id=user.id,
            message_text="test message",
            message_type="general",
        )
        db.session.add(msg)
        db.session.commit()

        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_persist:
            send_new_message_notification(msg)
            mock_persist.assert_called_once()

    def test_send_metadata_rejected_with_recipients(self):
        """Cover send_metadata_rejected_notification recipients loop."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.metadata_approval)
        user = UserFactory(email="provider@example.com")
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        reviewer = UserFactory()
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_notify:
            reject_metadata(sub.id, reviewer.id, feedback="Fix data")

        mock_notify.assert_called_once()
        recipients = mock_notify.call_args[0][2]
        self.assertIn("provider@example.com", recipients)

        db.session.expire_all()
        updated_sub = db.session.get(Submission, sub.id)
        self.assertEqual(
            updated_sub.current_status, SubmissionStatusEnum.metadata_submission
        )

    def test_send_data_rejected_with_recipients(self):
        """Cover send_data_rejected_notification recipients loop."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.data_approval)
        user = UserFactory(email="provider@example.com")
        update_submission_basic_info(sub, provider_user_ids=[user.id])
        db.session.commit()

        reviewer = UserFactory()
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_notify:
            reject_data(sub.id, reviewer.id, feedback="Wrong format")

        mock_notify.assert_called_once()
        recipients = mock_notify.call_args[0][2]
        self.assertIn("provider@example.com", recipients)

        db.session.expire_all()
        updated_sub = db.session.get(Submission, sub.id)
        self.assertEqual(updated_sub.current_status, SubmissionStatusEnum.data_upload)

    # --- submission_exporter.py error path tests ---

    def test_export_to_file_error(self):
        """Cover export_to_file exception handling."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        exporter = SubmissionExporter([sub])

        with patch.object(exporter, "export_to_buffer", side_effect=Exception("boom")):
            result = exporter.export_to_file(StringIO())
            self.assertFalse(result)

    def test_export_to_buffer_error(self):
        """Cover export_to_buffer exception handling."""
        sub = SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        exporter = SubmissionExporter([sub])

        with patch.object(
            exporter, "export_submission", side_effect=Exception("export fail")
        ):
            with self.assertRaisesRegex(Exception, "export fail"):
                exporter.export_to_buffer(StringIO())

    def test_parse_json_string_invalid_json(self):
        """Cover _parse_json_string json.loads exception."""
        # Must start with [ and end with ] to pass bracket check, but be invalid JSON
        result = _parse_json_string("[not valid json]")
        self.assertIsNone(result)


class RecipientInvitationTest(BaseTest):
    def _make_submission(self, *entries):
        return SubmissionFactory(
            current_status=SubmissionStatusEnum.draft,
            local_custodians_json=json.dumps(list(entries)),
        )

    def _invite(self, submission):
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as notification:
            invite_recipients(submission)
        return notification

    def test_local_custodian_serialization(self):
        entry = {"name": "Jane Doe", "email": "jane@uni.lu"}
        formatted = format_local_custodian(entry)
        self.assertEqual(formatted, "Jane Doe <jane@uni.lu>")
        self.assertEqual(parse_local_custodian(formatted), entry)

        sub = self._make_submission("Legacy Name", entry)
        self.assertEqual(
            sub.local_custodian_entries(),
            [
                {"name": "Legacy Name", "email": None},
                entry,
            ],
        )
        self.assertEqual(sub.local_custodians(), ["Legacy Name", "Jane Doe"])

    def test_invite_recipients_creates_access_and_notification(self):
        sub = self._make_submission({"name": "Jane Doe", "email": "jane.doe@uni.lu"})
        notification = self._invite(sub)

        user = User.query.filter_by(email="jane.doe@uni.lu").one()
        self.assertTrue(user.has_role_from(["user"]))
        access = SubmissionAccess.query.filter_by(
            submission_id=sub.id, user_id=user.id
        ).one()
        self.assertEqual(access.role, SubmissionAccess.ROLE_RECIPIENT)

        notification.assert_called_once()
        subject, _, recipients, text_email, _ = notification.call_args.args
        self.assertIn("you have been assigned as Recipient", subject)
        self.assertIn("jane.doe@uni.lu", recipients)
        self.assertIn(f"https://dss.example.com/submission/view/{sub.id}", text_email)

    def test_invite_recipients_does_not_downgrade_submitter(self):
        submitter = UserFactory(email="submitter@uni.lu")
        sub = self._make_submission(
            {"name": "Submitter User", "email": "submitter@uni.lu"}
        )
        update_submission_basic_info(sub, provider_user_ids=[submitter.id])
        notification = self._invite(sub)

        access = SubmissionAccess.query.filter_by(
            submission_id=sub.id, user_id=submitter.id
        ).one()
        self.assertEqual(access.role, SubmissionAccess.ROLE_SUBMITTER)
        notification.assert_not_called()

    def test_invite_recipients_skips_deactivated_accounts(self):
        inactive_user = deactivate_user(UserFactory(email="inactive@uni.lu"))
        sub = self._make_submission(
            {"name": "Inactive User", "email": "inactive@uni.lu"}
        )

        with (
            patch(
                "elixir_dss.models.services.persist_and_send_notification"
            ) as mock_persist,
            patch("elixir_dss.models.services.flash") as mock_flash,
        ):
            invite_recipients(sub)

        self.assertIsNone(
            SubmissionAccess.query.filter_by(user_id=inactive_user.id).first()
        )
        mock_persist.assert_not_called()
        mock_flash.assert_called_once()
        self.assertIn("deactivated", mock_flash.call_args.args[0])

    def test_invite_recipients_warns_for_names_without_email(self):
        sub = self._make_submission({"name": "No Email", "email": None})

        with (
            patch(
                "elixir_dss.models.services.persist_and_send_notification"
            ) as mock_persist,
            patch("elixir_dss.models.services.flash") as mock_flash,
        ):
            invite_recipients(sub)

        self.assertEqual(SubmissionAccess.query.count(), 0)
        mock_persist.assert_not_called()
        mock_flash.assert_called_once()
        self.assertIn("No Email", mock_flash.call_args.args[0])

    def test_invite_recipients_synchronizes_access(self):
        sub = self._make_submission({"name": "Jane Doe", "email": "jane.doe@uni.lu"})
        with patch("elixir_dss.models.services.persist_and_send_notification"):
            invite_recipients(sub)
            invite_recipients(sub)
        self.assertEqual(SubmissionAccess.query.count(), 1)

        sub.local_custodians_json = json.dumps(
            [{"name": "John Roe", "email": "john.roe@uni.lu"}]
        )
        db.session.commit()
        with patch("elixir_dss.models.services.persist_and_send_notification"):
            invite_recipients(sub)

        remaining = SubmissionAccess.query.filter_by(submission_id=sub.id).all()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].user.email, "john.roe@uni.lu")

    def test_provider_sync_respects_recipient_role(self):
        recipient_user = UserFactory(email="recipient@uni.lu")
        provider_user = UserFactory(email="provider@uni.lu")
        sub = self._make_submission(
            {"name": "Recipient User", "email": "recipient@uni.lu"}
        )
        self._invite(sub)

        update_submission_basic_info(sub, provider_user_ids=[provider_user.id])
        access = SubmissionAccess.query.filter_by(
            submission_id=sub.id, user_id=recipient_user.id
        ).one()
        self.assertEqual(access.role, SubmissionAccess.ROLE_RECIPIENT)

        update_submission_basic_info(
            sub, provider_user_ids=[provider_user.id, recipient_user.id]
        )
        self.assertEqual(access.role, SubmissionAccess.ROLE_SUBMITTER)

    def test_provider_sync_notifies_once_for_new_and_upgraded_users(self):
        provider_user = UserFactory(email="provider@uni.lu")
        other_user = UserFactory(email="other@uni.lu")
        sub = self._make_submission(
            {"name": "Recipient User", "email": "recipient@uni.lu"}
        )
        sub.current_status = SubmissionStatusEnum.metadata_submission
        update_submission_basic_info(sub, provider_user_ids=[provider_user.id])
        self._invite(sub)
        recipient_user = User.query.filter_by(email="recipient@uni.lu").one()

        # one save adding a new provider and upgrading the recipient
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_notify:
            update_submission_basic_info(
                sub,
                provider_user_ids=[
                    provider_user.id,
                    other_user.id,
                    recipient_user.id,
                ],
            )

        mock_notify.assert_called_once()
        recipients = mock_notify.call_args[0][2]
        self.assertIn("recipient@uni.lu", recipients)

    def test_clone_preserves_access_roles(self):
        provider_user = UserFactory(email="provider@uni.lu")
        sub = self._make_submission(
            {"name": "Recipient User", "email": "recipient@uni.lu"}
        )
        update_submission_basic_info(sub, provider_user_ids=[provider_user.id])
        self._invite(sub)

        clone = clone_sub(sub.id, clone_studies=False, clone_datasets=False)

        roles = {access.user.email: access.role for access in clone.submission_accesses}
        self.assertEqual(roles["provider@uni.lu"], SubmissionAccess.ROLE_SUBMITTER)
        self.assertEqual(roles["recipient@uni.lu"], SubmissionAccess.ROLE_RECIPIENT)

    def test_rejected_notifications_exclude_recipients(self):
        provider_user = UserFactory(email="provider@uni.lu")
        sub = self._make_submission(
            {"name": "Recipient User", "email": "recipient@uni.lu"}
        )
        sub.current_status = SubmissionStatusEnum.metadata_approval
        update_submission_basic_info(sub, provider_user_ids=[provider_user.id])
        self._invite(sub)

        reviewer = UserFactory()
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_notify:
            reject_metadata(sub.id, reviewer.id, feedback="Fix data")

        recipients = mock_notify.call_args[0][2]
        self.assertIn("provider@uni.lu", recipients)
        self.assertNotIn("recipient@uni.lu", recipients)

    def test_approved_notifications_exclude_recipients(self):
        provider_user = UserFactory(email="provider@uni.lu")
        sub = self._make_submission(
            {"name": "Recipient User", "email": "recipient@uni.lu"}
        )
        sub.current_status = SubmissionStatusEnum.metadata_approval
        update_submission_basic_info(sub, provider_user_ids=[provider_user.id])
        self._invite(sub)

        reviewer = UserFactory()
        with patch(
            "elixir_dss.models.services.persist_and_send_notification"
        ) as mock_notify:
            approve_metadata(sub.id, reviewer.id)

        recipients = mock_notify.call_args[0][2]
        self.assertIn("provider@uni.lu", recipients)
        self.assertNotIn("recipient@uni.lu", recipients)
