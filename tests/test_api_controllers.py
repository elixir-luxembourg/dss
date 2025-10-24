from unittest.mock import Mock, patch

import requests

from elixir_dss.controllers.api_controllers import get_elu_entities
from tests import BaseTest


class TestGetEluEntities(BaseTest):
    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_success_with_items_key(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [{"external_id": "ELU_I_1", "name": "Partner 1", "acronym": "P1"}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_elu_entities("partners")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["external_id"], "ELU_I_1")

    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_success_with_results_key(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {"external_id": "ELU_P_1", "name": "Project 1", "acronym": "PR1"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_elu_entities("projects")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["external_id"], "ELU_P_1")

    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_fallback_on_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_elu_entities("partners")

        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["external_id"], "ELU_I_1")

    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_fallback_on_http_error(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response

        result = get_elu_entities("partners")

        self.assertGreater(len(result), 0)

    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_fallback_on_invalid_json(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = get_elu_entities("partners")

        self.assertGreater(len(result), 0)

    @patch("elixir_dss.controllers.api_controllers.requests.get")
    def test_empty_response(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_elu_entities("partners")

        self.assertEqual(result, [])
