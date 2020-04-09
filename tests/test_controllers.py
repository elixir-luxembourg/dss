import unittest

from elixir_dcp.models.services import create_sub
from elixir_dcp.models.submission import Submission
from tests import BaseIntegrationTest
from flask import url_for
from elixir_dcp.models.security import User

__author__ = 'Pinar Alper'


class ControllersTest(BaseIntegrationTest):

    def test_get_submissions(self):
        users = User.query.all()
        self.assertEqual(3, len(users))

        self.login("steward1@uni.lu", "steward1")

        response = self.client.get(url_for('list_submissions'))

        self.assertIn("No submissions have been added.", response.data.decode('utf-8'))

    def test_access_control2(self):
        self.login("steward1@uni.lu", "steward1")

        #
        # User with an admin  role cannot access the following end point
        #

        response = self.client.get(url_for('list_my_submissions'))
        self.assert403(response)

    def test_access_control1(self):
        self.login("submitter2@some.edu", "submitter2")

        #
        # User with a data provider role cannot access the following end points
        #

        response = self.client.get(url_for('list_submissions'))
        self.assert403(response)

        response = self.client.get(url_for('edit_user', user_id=0))
        self.assert403(response)

        response = self.client.get(url_for('revert_submission', sub_id=0))
        self.assert403(response)

        response = self.client.get(url_for('send_notification', notification_id=0))
        self.assert403(response)

        response = self.client.get(url_for('list_notifications'))
        self.assert403(response)



    def test_submission_create_submission(self):
        self.login("steward1@uni.lu", "steward1")

        d = url_for('create_submission')
        response = self.client.post(url_for('create_submission'),
                                    data={"title": "Test Submission 123", "institution_accession":"ELU_I_9"},
                                    follow_redirects=True)
        data = response.data.decode('utf-8')
        self.assert200(response)
        self.assertIn("New submission", data)
        self.assertIn("created", data)

#     def test_update_and_steer_submission(self):
#         submission_rec = create_sub('Test Submission')
#
#
#         data_provider = User.query.filter_by(first_name='Kavita').one_or_none()
#
# d = url_for('create_submission')
#         response = self.client.post(url_for('edit_submission', sub_id=submission_rec.id),
#                                     data={"title": "Test Submission 123",
#                                           "submission_scope_code": "e"},
#                                     follow_redirects=True)
#         data = response.data.decode('utf-8')
#         self.assert200(response)

#
# "local_custodians": ['Some PI', 'Some other PI'],
# "local_project_name": "",
# "provider_user_ids": [data_provider.id]
