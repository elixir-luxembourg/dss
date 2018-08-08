import json

from tests.base_test import BaseTest

from elixir_dcp.models.security import User, UsersRoles
from elixir_dcp.models.submission import Submission, SubmissionStatusEnum, SubmissionScope, SubmissionAccess, \
    SubmissionDataset, SubmissionAttachment, SubmissionStudy
from elixir_dcp.models.services import register_new_user, assign_role_to_user, create_sub, steer_sub, \
    update_submission_basic_info, revert_sub, deactivate_user, delete_sub, export_submission, export_studies, export_datasets
from elixir_dcp.exceptions import RecordLifecycleException
from elixir_dcp import db

class ModelPersistenceTest(BaseTest):


    def test_users_roles(self):
        u1 = User(first_name='P\u0131nar', last_name='Alper',
                  elixir_sub_id='DUMMY_ELX_ID', email='pinar.alper@uni.lu',
                  institution='University of Luxembourg',
                  phone_no='+352123456789')
        register_new_user(u1)
        assign_role_to_user(u1, 'admin')

        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]

        self.assertEqual('P\u0131nar', pinar.first_name)
        self.assertEqual('Alper', pinar.last_name)
        self.assertEqual('DUMMY_ELX_ID', pinar.elixir_sub_id)
        self.assertEqual('pinar.alper@uni.lu', pinar.email)
        self.assertEqual('+352123456789', pinar.phone_no)
        self.assertEqual('University of Luxembourg', pinar.institution)

        self.assertEqual(1, len(pinar.assigned_roles))
        self.assertTrue(pinar.is_active())
        self.assertTrue(pinar.is_admin())

        assign_role_to_user(pinar, 'data_provider')
        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]
        self.assertEqual(2, len(pinar.assigned_roles))
        self.assertTrue(pinar.is_admin())

        deactivate_user(pinar)
        users = User.query.all()
        self.assertEqual(1, len(users))
        pinar = users[0]
        self.assertFalse(pinar.is_active())


    def test_create_submission(self):


        self.assertEqual(2, len(SubmissionScope.query.all()))


        # con = db.session.connection()
        # res = con.execute("select sqlite_version();")
        # for row in res:
        #     print(row[0])
        #
        # con.execute("PRAGMA foreign_keys=ON")


        submission_rec = create_sub('Test Submission')

        self.assertEqual(1, len(Submission.query.all()))
        sub = Submission.query.get_or_404(submission_rec.id)
        sub_id = sub.id
        self.assertEqual(sub.title, 'Test Submission')
        self.assertEqual(sub.ref_name, 'ELX_LU_SUB-1')
        self.assertEqual(sub.current_status, SubmissionStatusEnum.draft)
        self.assertIsNone(sub.upload_instructions)
        self.assertIsNotNone(sub.created_on)
        self.assertEqual(sub.submission_scope_code, 'e')

        self.assertTrue(sub.is_deletable())
        self.assertFalse(sub.is_in_progress())
        self.assertEqual(0, len(sub.submission_accesses))
        self.assertEqual(0, len(sub.studies))
        self.assertEqual(0, len(sub.attachments))
        self.assertEqual(0, len(sub.datasets))
        self.assertEqual(0, len(sub.uploadinfos))
        self.assertEqual(0, len(sub.provider_user_names()))
        self.assertEqual(0, len(sub.uploads_instructions_lines()))
        self.assertFalse(sub.has_providers())


        u1 = User(first_name='Kavita', last_name='Rege',
                  elixir_sub_id='SOME_ELX_ID', email='kavita.rege@uni.lu',
                  institution='University of Luxembourg',
                  phone_no='+352123456789')
        usr = register_new_user(u1)
        update_submission_basic_info(sub, provider_user_ids=[usr.id])


        self.assertEqual(1, len(Submission.query.get_or_404(sub_id).submission_accesses))

        delete_sub(sub_id)
        self.assertEqual(0, len(Submission.query.all()))

        #Testing delete-orphan annotations on the relations of Submission
        self.assertEqual(0, len(SubmissionAccess.query.all()))


    def test_steer_submission(self):

        submission_rec = create_sub('Test Submission')

        sub_id = Submission.query.get_or_404(submission_rec.id).id

        try:
            steer_sub(sub_id)
        except RecordLifecycleException:
            # we should not be able to steer the submission
            # because we have not supplied a data provider yet
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Expected Exception not raised')

        u1 = User(first_name='Kavita', last_name='Rege',
                  elixir_sub_id='SOME_ELX_ID', email='kavita.rege@uni.lu',
                  institution='University of Luxembourg',
                  phone_no='+352123456789')
        usr = register_new_user(u1)


        sub = Submission.query.get_or_404(sub_id)

        update_submission_basic_info(sub, provider_user_ids=[usr.id])

        accesses = SubmissionAccess.query.all()
        self.assertEqual(1, len(accesses))
        #
        sub = Submission.query.get_or_404(sub_id)
        self.assertEqual(1,len(sub.submission_accesses))

        steer_sub(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.in_progress_metadata)

        steer_sub(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.in_progress_data)

        revert_sub(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.in_progress_metadata)

        steer_sub(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.in_progress_data)

        steer_sub(sub_id)
        self.assertEqual(sub.current_status, SubmissionStatusEnum.completed)

        try:
            steer_sub(sub_id)
        except RecordLifecycleException:
            # we should not be able to steer the submission
            # because it is already complete
            pass
        except Exception as e:
            self.fail('Unexpected exception raised:', e)
        else:
            self.fail('Expected Exception not raised')


    def test_export_submission(self):

        submission_rec = create_sub('Test Submission to be exported.')

        u1 = User(first_name='Kavita', last_name='Rege',
                  elixir_sub_id='SOME_ELX_ID', email='kavita.rege@uni.lu',  addr_line1='Meyerhofstraße 1, 69117', addr_line2='Heidelberg, Germany',
                  institution='ELU_I_2',
                  phone_no='+352123456789')
        usr = register_new_user(u1)

        update_submission_basic_info(submission_rec, provider_user_ids=[usr.id], collab_local_custodian_json=json.dumps(['Enrico Glaab', 'Rudi Balling']))


        study_rec = SubmissionStudy()
        study_rec.submission_id = submission_rec.id
        study_rec.study_name = 'Test Study ABC'
        study_rec.study_description = 'This study does blah blah...'
        study_rec.ethics_approval_exists = True
        study_rec.study_types_json = json.dumps(["Interventional","Observational"])



        db.session.add(study_rec)
        db.session.commit()


        dataset_rec = SubmissionDataset()
        dataset_rec.submission_id = submission_rec.id
        dataset_rec.study_id = study_rec.id
        dataset_rec.title = 'Test dataset 1'

        dataset_rec.estimate_data_size_code = 'm'
        dataset_rec.data_types_json = json.dumps(["Genomics_variant_array","RNASeq"])
        dataset_rec.subjects_minors = True
        dataset_rec.subjects_notes = 'mothers and babies'
        dataset_rec.consent_notes = 'Consent is consistent among all subjects'

        db.session.add(dataset_rec)
        db.session.commit()


        dataset_rec = SubmissionDataset()
        dataset_rec.submission_id = submission_rec.id
        dataset_rec.study_id = study_rec.id
        dataset_rec.title = 'Test dataset 2'

        dataset_rec.estimate_data_size_code = 'l'
        dataset_rec.data_types_json = json.dumps(["Transcriptome_array","RNASeq"])
        dataset_rec.consent_status_code = 't'
        dataset_rec.consent_notes = 'There are three primary consent groups'

        db.session.add(dataset_rec)
        db.session.commit()


        a_rec = SubmissionAttachment()
        a_rec.submission_id = submission_rec.id
        a_rec.note = 'Ethics approval'
        a_rec.folder_name = '1b523cd3-5953-4af2-a0e3-5bd2dde483b5'
        a_rec.file_names = 'CNER-AVIS20140713-Dr_RK-ND_COLLECTION.pdf'

        db.session.add(a_rec)
        db.session.commit()


        a_rec = SubmissionAttachment()
        a_rec.submission_id = submission_rec.id
        a_rec.note = 'Subject Consents and Info Sheet'
        a_rec.folder_name = '7be19c77-8b8c-4a2c-845b-8764817641e2'
        a_rec.file_names = 'CA_UNI_SAAR_58_01.pdf 140174_ND_SIS_v8-0_EN_21JUN2017.pdf'

        db.session.add(a_rec)
        db.session.commit()

        submission_rec = Submission.query.get_or_404(submission_rec.id)
        exp = export_submission(submission_rec)
        print(json.dumps(exp, indent=4))


