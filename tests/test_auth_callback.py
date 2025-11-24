from unittest.mock import patch

from flask import url_for

from elixir_dss.models.security import User
from tests import BaseIntegrationTest
from tests.factories import (
    ContactFactory,
    SubmissionAccessFactory,
    SubmissionFactory,
    UserFactory,
)


class AuthCallbackTest(BaseIntegrationTest):
    def _mock_oauth(self, mock_oauth, sub="test_sub_123", email="test@example.com"):
        mock_oauth.keycloak.authorize_access_token.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "id_token": "id",
            "expires_in": 3600,
        }
        mock_oauth.keycloak.userinfo.return_value = {
            "sub": sub,
            "email": email,
            "name": "Test User",
        }

    @patch("elixir_dss.controllers.web_controllers.oauth")
    def test_with_existing_user(self, mock_oauth):
        user = UserFactory()
        self._mock_oauth(mock_oauth, sub=user.elixir_sub_id, email=user.email)
        response = self.client.get(url_for("auth_callback"), follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("home"), response.location)

    @patch("elixir_dss.controllers.web_controllers.oauth")
    def test_without_existing_user(self, mock_oauth):
        self._mock_oauth(mock_oauth)
        response = self.client.get(url_for("auth_callback"), follow_redirects=False)

        user = User.query.filter_by(elixir_sub_id="test_sub_123").first()
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("home"), response.location)

    @patch("elixir_dss.controllers.web_controllers.oauth")
    def test_with_invited_user_redirects_to_one_submission(self, mock_oauth):
        submission = SubmissionFactory()
        contact = ContactFactory(submission_id=submission.id)
        invited_user = UserFactory(elixir_sub_id=contact.email, email=contact.email)
        SubmissionAccessFactory(submission_id=submission.id, user_id=invited_user.id)

        self._mock_oauth(mock_oauth, sub="new-oidc-sub", email=contact.email)

        response = self.client.get(url_for("auth_callback"), follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(invited_user.elixir_sub_id, "new-oidc-sub")
        self.assertIn(f"/submission/view/{submission.id}", response.location)

    @patch("elixir_dss.controllers.web_controllers.oauth")
    def test_with_invited_user_redirects_to_my_submissions(self, mock_oauth):
        email = "john@uni.lu"
        invited_user = UserFactory(elixir_sub_id=email, email=email)
        for _ in range(2):
            submission = SubmissionFactory()
            ContactFactory(submission_id=submission.id, email=email)
            SubmissionAccessFactory(
                submission_id=submission.id, user_id=invited_user.id
            )

        self._mock_oauth(mock_oauth, sub="new-oidc-sub", email=email)

        response = self.client.get(url_for("auth_callback"), follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(invited_user.elixir_sub_id, "new-oidc-sub")
        self.assertIn("/my_submissions", response.location)

    def test_get_accessible_submission_ids_filters_correctly(self):
        sub1, sub2, sub3 = [SubmissionFactory() for _ in range(3)]
        user = UserFactory()

        for sub in [sub1, sub3]:
            SubmissionAccessFactory(submission_id=sub.id, user_id=user.id)

        ids = user.get_accessible_submission_ids()

        self.assertEqual(len(ids), 2)
        self.assertIn(sub1.id, ids)
        self.assertIn(sub3.id, ids)
        self.assertNotIn(sub2.id, ids)
