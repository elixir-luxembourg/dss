from elixir_dss.models.submission import SubmissionStatusEnum

from tests import BaseTest
from tests.factories import (
    SubmissionFactory,
    SubmissionStudyFactory,
    SubmissionDatasetFactory,
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

    def test_get_submission_datasets_without_api_key(self):
        response = self.client.get("/api/v1/submissions/1/datasets")

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data["error"], "Invalid or missing API key")
