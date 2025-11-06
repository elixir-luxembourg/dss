import json

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
)
from elixir_dss.models.submission import (
    Contact,
    ContactType,
    Submission,
    SubmissionAccess,
    SubmissionAttachment,
    SubmissionDataset,
    SubmissionScope,
    SubmissionStatusEnum,
    SubmissionStudy,
)
from tests import BaseTest

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
        self.assertEqual(18, len(SubmissionScope.query.all()))

        submission_rec = create_sub("Test Submission", "ELU_I_77")

        self.assertEqual(1, len(Submission.query.all()))
        sub = Submission.query.get_or_404(submission_rec.id)
        sub_id = sub.id
        self.assertEqual(sub.title, "Test Submission")
        self.assertEqual(sub.ref_name, "ELX_LU_SUB-1")
        self.assertEqual(sub.current_status, SubmissionStatusEnum.draft)
        self.assertIsNotNone(sub.created_on)
        self.assertEqual(sub.submission_scope_code, "elu")

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
        submission_rec = create_sub("Test Submission", "ELU_I_77")
        sub_id = submission_rec.id

        # Steer fails without Data Provider
        self._assert_steer_fails(
            sub_id, "Steering should fail because provider is missing."
        )

        # Add Data Provider
        usr = self._create_test_user()
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
        self._add_metadata_to_submission(sub_id)

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
        self._assert_steer_fails(sub_id, "Steering should fail because submission is complete.")

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
        submission = create_sub("Test Workflow Submission", "ELU_I_77")
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
        submission_rec = create_sub("Test Submission to be exported.", "ELU_I_5")

        u1 = User(
            first_name="Kavita",
            last_name="Rege",
            elixir_sub_id="SOME_ELX_ID",
            email="kavita.rege@uni.lu",
            addr_line1="Meyerhofstraße 1, 69117",
            addr_line2="Heidelberg, Germany",
            institution_accession="ELU_I_2",
            phone_no="+352123456789",
        )
        usr = register_new_user(u1)

        update_submission_basic_info(
            submission_rec,
            institution_accession="ELU_I_5",
            provider_user_ids=[usr.id],
            local_project_name="Submitting to NCER PD Diagnosis project",
            local_custodians_json=json.dumps(["Enrico Glaab", "Rudi Balling"]),
        )

        study_rec = SubmissionStudy()
        study_rec.submission_id = submission_rec.id
        study_rec.name = "Test Study ABC"
        study_rec.description = "This study does blah blah..."
        study_rec.ethics_approval_exists = True
        study_rec.study_types_json = json.dumps(["Interventional", "Observational"])
        c1 = Contact()
        c1.firstname = "John"
        c1.lastname = "Doe"
        c1.email = "john.doe@acme.edu"
        c1.address = "Some Address"
        c1.contact_category = ContactType.query.get_or_404(1)
        study_rec.study_contacts = [c1]
        db.session.add(study_rec)
        db.session.commit()

        dataset_rec = SubmissionDataset()
        dataset_rec.submission_id = submission_rec.id
        dataset_rec.study_id = study_rec.id
        dataset_rec.title = "Test dataset 1"

        dataset_rec.sci_datatypes_json = json.dumps(
            ["Genomics_variant_array", "RNASeq"]
        )
        dataset_rec.gdpr_datatypes_json = json.dumps(["standard", "ethnic"])
        dataset_rec.subjects_minors = True
        dataset_rec.subjects_notes = "mothers and babies"
        dataset_rec.consent_notes = "Consent is consistent among all subjects"

        db.session.add(dataset_rec)
        db.session.commit()

        dataset_rec2 = SubmissionDataset()
        dataset_rec2.submission_id = submission_rec.id
        dataset_rec2.study_id = study_rec.id
        dataset_rec2.title = "Test dataset 2"

        dataset_rec2.sci_datatypes_json = json.dumps(["Transcriptome_array", "RNASeq"])
        dataset_rec2.gdpr_datatypes_json = json.dumps(["standard", "ethnic"])
        dataset_rec2.consent_status_code = "ht"
        dataset_rec2.consent_notes = "There are three primary consent groups"

        db.session.add(dataset_rec2)
        db.session.commit()

        a_rec = SubmissionAttachment()
        a_rec.submission_id = submission_rec.id
        a_rec.note = "Ethics approval"
        a_rec.folder_name = "1b523cd3-5953-4af2-a0e3-5bd2dde483b5"
        a_rec.file_names = "CNER-AVIS20140713-Dr_RK-ND_COLLECTION.pdf"

        db.session.add(a_rec)
        db.session.commit()

        a_rec = SubmissionAttachment()
        a_rec.submission_id = submission_rec.id
        a_rec.note = "Subject Consents and Info Sheet"
        a_rec.folder_name = "7be19c77-8b8c-4a2c-845b-8764817641e2"
        a_rec.file_names = "CA_UNI_SAAR_58_01.pdf 140174_ND_SIS_v8-0_EN_21JUN2017.pdf"

        db.session.add(a_rec)
        db.session.commit()

        submission_rec = Submission.query.get_or_404(submission_rec.id)
        exporter = SubmissionExporter()
        exp = exporter.export_submission(submission_rec)
        print(json.dumps(exp, indent=4))

    def test_clone_submission_basic(self):
        original = create_sub("Brain Study", "ELU_I_11")
        db.session.add(original)
        db.session.commit()

        clone = clone_sub(original.id)

        # Assert new object is distinct
        self.assertNotEqual(original.id, clone.id)
        self.assertTrue(clone.title.startswith("Brain Study"))
        self.assertIn("(Clone", clone.title)

        self.assertEqual(
            clone.current_status, SubmissionStatusEnum.metadata_submission
        )

        self.assertEqual(len(clone.submission_contacts), 0)
        self.assertEqual(len(clone.datasets), 0)
        self.assertEqual(len(clone.studies), 0)
        self.assertFalse(clone.exported)

        # Db contains two submissions
        subs = Submission.query.all()
        self.assertEqual(2, len(subs))

    def test_clone_with_studies_and_datasets(self):
        sub = create_sub("Genomics Study", "ELU_I_77")
        db.session.add(sub)
        db.session.commit()

        # Add study + dataset
        study = SubmissionStudy(
            submission_id=sub.id,
            name="Study 1",
            description="Genomics cohort",
            ethics_approval_exists=True,
            study_types_json=json.dumps(["Observational"]),
        )
        db.session.add(study)
        db.session.commit()

        dataset = SubmissionDataset(
            submission_id=sub.id,
            study_id=study.id,
            title="Dataset 1",
            gdpr_datatypes_json=json.dumps(["personal"]),
            sci_datatypes_json=json.dumps(["RNASeq"]),
        )
        db.session.add(dataset)
        db.session.commit()

        clone = clone_sub(sub.id, clone_studies=True, clone_datasets=True)
        db.session.commit()

        self.assertEqual(len(clone.studies), 1)
        self.assertEqual(len(clone.datasets), 1)
        self.assertEqual(clone.datasets[0].title, "Dataset 1")
        self.assertNotEqual(clone.datasets[0].id, dataset.id)
        self.assertNotEqual(clone.studies[0].id, study.id)


    def _create_test_user(self):
        """Creates and registers a standard test user"""
        u1 = User(
            first_name="Kavita",
            last_name="Rege",
            elixir_sub_id="SOME_ELX_ID",
            email="kavita.rege@uni.lu",
            addr_line1="Meyerhofstraße 1, 69117",
            addr_line2="Heidelberg, Germany",
            institution_accession="ELU_I_77",
            phone_no="+352123456789",
        )
        return register_new_user(u1)

    def _add_metadata_to_submission(self, sub_id):
        """Creates and adds a Study and Dataset to the submission."""
        submission_rec = Submission.query.get_or_404(sub_id)

        # 1. Create Contact
        c1 = Contact(
            firstname="John",
            lastname="Doe",
            email="john.doe@acme.edu",
            address="Some Address",
            contact_category=ContactType.query.get_or_404(1)
        )

        # 2. Create Study
        study_rec = SubmissionStudy(
            submission_id=submission_rec.id,
            name="Test Study ABC",
            description="This study does blah blah...",
            ethics_approval_exists=True,
            study_types_json=json.dumps(["Interventional", "Observational"]),
            study_contacts=[c1]
        )

        # 3. Create Dataset
        dataset_rec = SubmissionDataset(
            submission_id=submission_rec.id,
            study_id=None,
            title="Test dataset 1",
            sci_datatypes_json=json.dumps(["Genomics_variant_array", "RNASeq"]),
            gdpr_datatypes_json=json.dumps(["standard", "ethnic"]),
        )

        submission_rec.datasets.append(dataset_rec)
        submission_rec.studies.append(study_rec)

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
        SubmissionStudyFactory(submission_id=original.id)
        SubmissionDatasetFactory(submission_id=original.id)

        submissions_before = Submission.query.count()

        with patch.object(db.session, "commit", side_effect=Exception("DB error")):
            with self.assertRaises(Exception):
                clone_sub(original.id, clone_studies=True, clone_datasets=True)

        self.assertEqual(submissions_before, Submission.query.count())
        self.assertIsNotNone(Submission.query.get(original.id))
