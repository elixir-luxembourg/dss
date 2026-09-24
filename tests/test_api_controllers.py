from elixir_dss.models.submission import SubmissionStatusEnum

from tests import BaseTest
from tests.factories import (
    SubmissionAccessFactory,
    SubmissionAttachmentFactory,
    SubmissionFactory,
    SubmissionStudyFactory,
    SubmissionDatasetFactory,
    UserFactory,
)


class ApiControllersTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.api_key_header = {"X-API-Key": "test-secret-key"}

    def test_healthz(self):
        response = self.client.get("/api/v1/healthz", headers=self.api_key_header)

        self.assert200(response)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")

    def test_list_submissions(self):
        completed_submission = SubmissionFactory(
            ref_name="sub-completed", current_status=SubmissionStatusEnum.completed
        )
        draft_submission = SubmissionFactory(
            ref_name="sub-draft", current_status=SubmissionStatusEnum.draft
        )
        response = self.client.get("/api/v1/submissions", headers=self.api_key_header)

        self.assert200(response)
        data = response.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(len(data["data"]), 1)
        submission_ids = {s["id"] for s in data["data"]}
        self.assertIn(completed_submission.id, submission_ids)
        self.assertNotIn(draft_submission.id, submission_ids)
        for submission in data["data"]:
            self.assertIn("id", submission)
            self.assertIn("ref_name", submission)
            self.assertIn("status", submission)

    def test_list_submissions_empty(self):
        response = self.client.get("/api/v1/submissions", headers=self.api_key_header)

        self.assert200(response)
        data = response.get_json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["data"], [])

    def test_list_submissions_without_api_key(self):
        response = self.client.get("/api/v1/submissions")

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid or missing API key")

    def test_get_submission_datasets(self):
        submission = SubmissionFactory(
            ref_name="test-submission", current_status=SubmissionStatusEnum.completed
        )
        study = SubmissionStudyFactory(submission_id=submission.id, name="Test Study")
        for i in range(2):
            SubmissionDatasetFactory(
                submission_id=submission.id, title=f"Dataset {i + 1}", study_id=study.id
            )
        response = self.client.get(
            f"/api/v1/submissions/{submission.id}/datasets",
            headers=self.api_key_header,
        )

        self.assert200(response)
        data = response.get_json()
        self.assertIn("data", data)
        self.assertIn("count", data)
        self.assertIn("submission", data)
        self.assertIn("dataset_id", data["data"][0])
        self.assertEqual(data["count"], 2)
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["submission"]["id"], submission.id)
        self.assertEqual(data["submission"]["ref_name"], "test-submission")
        self.assertEqual(data["submission"]["status"], "Complete")

    def test_get_submission_datasets_not_found(self):
        response = self.client.get(
            "/api/v1/submissions/99999/datasets", headers=self.api_key_header
        )

        self.assert404(response)

    def test_get_submission_datasets_empty(self):
        submission = SubmissionFactory(
            ref_name="empty-submission", current_status=SubmissionStatusEnum.completed
        )
        response = self.client.get(
            f"/api/v1/submissions/{submission.id}/datasets",
            headers=self.api_key_header,
        )

        self.assert200(response)
        data = response.get_json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["data"], [])

    def test_get_submission_datasets_with_wrong_status(self):
        submission = SubmissionFactory(
            ref_name="wrong-status-submission",
            current_status=SubmissionStatusEnum.draft,
        )
        response = self.client.get(
            f"/api/v1/submissions/{submission.id}/datasets",
            headers=self.api_key_header,
        )

        self.assert404(response)

    def test_get_submission_datasets_without_api_key(self):
        response = self.client.get("/api/v1/submissions/1/datasets")

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid or missing API key")

    def test_list_submissions_with_status_filter(self):
        verification = SubmissionFactory(
            ref_name="sub-verification",
            current_status=SubmissionStatusEnum.data_approval,
        )
        completed = SubmissionFactory(
            ref_name="sub-done", current_status=SubmissionStatusEnum.completed
        )
        response = self.client.get(
            "/api/v1/submissions?status=data_approval,completed",
            headers=self.api_key_header,
        )

        self.assert200(response)
        data = response.get_json()
        submission_ids = {s["id"] for s in data["data"]}
        self.assertIn(verification.id, submission_ids)
        self.assertIn(completed.id, submission_ids)

    def test_list_submissions_default_is_completed_only(self):
        SubmissionFactory(
            ref_name="sub-verification-hidden",
            current_status=SubmissionStatusEnum.data_approval,
        )
        response = self.client.get("/api/v1/submissions", headers=self.api_key_header)

        self.assert200(response)
        self.assertEqual(response.get_json()["count"], 0)

    def test_list_submissions_with_unknown_status(self):
        response = self.client.get(
            "/api/v1/submissions?status=nonsense", headers=self.api_key_header
        )

        self.assertEqual(response.status_code, 400)

    def test_get_submission_returns_placement_metadata(self):
        submission = SubmissionFactory(
            ref_name="sub-metadata",
            current_status=SubmissionStatusEnum.completed,
            local_project_name="TEST-PROJECT",
            local_custodians_json='["Jane Roe <jane.roe@example.org>"]',
        )
        user = UserFactory()
        SubmissionAccessFactory(
            submission_id=submission.id, user_id=user.id, role="recipient"
        )
        SubmissionAttachmentFactory(
            submission_id=submission.id, file_names="consent.pdf dmp.pdf"
        )
        response = self.client.get(
            f"/api/v1/submissions/{submission.id}", headers=self.api_key_header
        )

        self.assert200(response)
        data = response.get_json()["data"]
        self.assertEqual(data["local_project_name"], "TEST-PROJECT")
        self.assertEqual(data["local_custodians"][0]["name"], "Jane Roe")
        self.assertEqual(data["access"][0]["role"], "recipient")
        self.assertEqual(
            data["attachments"][0]["file_names"], ["consent.pdf", "dmp.pdf"]
        )

    def test_get_submission_readable_at_any_status(self):
        submission = SubmissionFactory(
            ref_name="sub-cancelled", current_status=SubmissionStatusEnum.cancelled
        )
        response = self.client.get(
            f"/api/v1/submissions/{submission.id}", headers=self.api_key_header
        )

        self.assert200(response)
        self.assertEqual(response.get_json()["data"]["status_code"], "cancelled")
