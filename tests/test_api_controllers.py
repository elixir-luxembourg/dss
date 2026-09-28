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
        self.page_size = self.app.config["API_PAGE_SIZE"]

    def test_healthz_needs_no_credentials(self):
        response = self.client.get("/api/v1/healthz")

        self.assert200(response)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_list_submissions(self):
        completed_submission = SubmissionFactory(
            ref_name="sub-completed",
            current_status=SubmissionStatusEnum.completed,
            local_project_name="Test Project",
        )
        SubmissionFactory(
            ref_name="sub-draft",
            current_status=SubmissionStatusEnum.draft,
            local_project_name="Secret Project",
        )
        response = self.client.get("/api/v1/submissions", headers=self.api_key_header)

        self.assert200(response)
        data = response.get_json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["data"][0]["id"], completed_submission.id)
        self.assertEqual(data["data"][0]["local_project_name"], "Test Project")

    def test_list_submissions_reports_unserved_statuses_on_request(self):
        draft_submission = SubmissionFactory(
            ref_name="sub-draft",
            current_status=SubmissionStatusEnum.draft,
            local_project_name="Secret Project",
        )
        response = self.client.get(
            "/api/v1/submissions?status=draft", headers=self.api_key_header
        )

        self.assert200(response)
        data = response.get_json()["data"]
        self.assertEqual(data[0]["id"], draft_submission.id)
        self.assertEqual(sorted(data[0]), ["id", "ref_name", "status", "status_code"])

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

    def test_list_submissions_with_several_statuses(self):
        SubmissionFactory(current_status=SubmissionStatusEnum.data_approval)
        SubmissionFactory(current_status=SubmissionStatusEnum.cancelled)
        SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        SubmissionFactory(current_status=SubmissionStatusEnum.draft)
        response = self.client.get(
            "/api/v1/submissions?status=data_approval&status=cancelled&status=completed",
            headers=self.api_key_header,
        )

        self.assert200(response)
        codes = {row["status_code"] for row in response.get_json()["data"]}
        self.assertEqual(codes, {"data_approval", "cancelled", "completed"})

    def test_list_submissions_rejects_unknown_parameter(self):
        SubmissionFactory(current_status=SubmissionStatusEnum.draft)
        response = self.client.get(
            "/api/v1/submissions?statuses=completed", headers=self.api_key_header
        )

        self.assert400(response)
        self.assertNotIn("statuses", response.get_json()["error"])

    def test_list_submissions_with_unknown_status(self):
        response = self.client.get(
            "/api/v1/submissions?status=not_a_status", headers=self.api_key_header
        )

        self.assert400(response)
        self.assertNotIn("not_a_status", response.get_json()["error"])

    def test_listing_and_datasets_serve_the_same_representation(self):
        submission = SubmissionFactory(
            current_status=SubmissionStatusEnum.completed,
            local_project_name="Test Project",
        )
        listed = self.client.get(
            "/api/v1/submissions", headers=self.api_key_header
        ).get_json()["data"][0]
        alongside_datasets = self.client.get(
            f"/api/v1/submissions/{submission.id}/datasets",
            headers=self.api_key_header,
        ).get_json()["submission"]

        self.assertEqual(listed, alongside_datasets)
        self.assertEqual(listed["local_project_name"], "Test Project")

    def test_listing_serves_the_details_a_consumer_places_with(self):
        submission = SubmissionFactory(
            ref_name="detailed-submission",
            current_status=SubmissionStatusEnum.completed,
            local_project_name="Test Project",
            local_custodians_json='[{"name": "Jane Doe", "email": "jane@uni.lu"}]',
        )
        user = UserFactory(first_name="Ann", last_name="Smith", email="ann@uni.lu")
        SubmissionAccessFactory(submission_id=submission.id, user_id=user.id)
        SubmissionAttachmentFactory(
            submission_id=submission.id, folder_name="box", file_names="a.vcf b.vcf"
        )
        response = self.client.get("/api/v1/submissions", headers=self.api_key_header)

        self.assert200(response)
        data = response.get_json()["data"][0]
        self.assertEqual(data["ref_name"], "detailed-submission")
        self.assertEqual(data["local_project_name"], "Test Project")
        self.assertEqual(data["local_custodians"][0]["email"], "jane@uni.lu")
        self.assertEqual(data["access"][0]["email"], "ann@uni.lu")
        self.assertEqual(data["attachments"][0]["file_names"], ["a.vcf", "b.vcf"])

    def test_get_submission_datasets_refused_at_every_other_status(self):
        """Adding a status to ALLOWED_STATUSES must be a deliberate act."""
        served = {
            SubmissionStatusEnum.data_approval,
            SubmissionStatusEnum.completed,
            SubmissionStatusEnum.cancelled,
        }
        for status in set(SubmissionStatusEnum) - served:
            submission = SubmissionFactory(current_status=status)
            response = self.client.get(
                f"/api/v1/submissions/{submission.id}/datasets",
                headers=self.api_key_header,
            )

            self.assertEqual(response.status_code, 409)
            self.assertIn(status.value, response.get_json()["error"])

    def test_listing_pages_through_every_submission_exactly_once(self):
        total = self.page_size + 2
        for _ in range(total):
            SubmissionFactory(current_status=SubmissionStatusEnum.completed)

        seen, after, pages = [], 0, 0
        while True:
            rows = self.client.get(
                f"/api/v1/submissions?after={after}", headers=self.api_key_header
            ).get_json()["data"]
            pages += 1
            if not rows:
                break
            self.assertLessEqual(len(rows), self.page_size)
            seen.extend(row["id"] for row in rows)
            after = rows[-1]["id"]

        self.assertEqual(pages, 3)
        self.assertEqual(len(seen), total)
        self.assertEqual(len(set(seen)), total)
        self.assertEqual(seen, sorted(seen))

    def test_listing_cursor_is_stable_when_rows_are_inserted(self):
        for _ in range(self.page_size + 1):
            SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        first = self.client.get(
            "/api/v1/submissions", headers=self.api_key_header
        ).get_json()["data"]

        SubmissionFactory(current_status=SubmissionStatusEnum.completed)
        second = self.client.get(
            f"/api/v1/submissions?after={first[-1]['id']}", headers=self.api_key_header
        ).get_json()["data"]

        self.assertEqual(len(first), self.page_size)
        self.assertFalse({row["id"] for row in first} & {row["id"] for row in second})
