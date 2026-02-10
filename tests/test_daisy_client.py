from unittest.mock import Mock, patch

import requests

from elixir_dss.clients.daisy import get_elu_entities
from .factories import ProjectFactory, PartnerFactory
from tests import BaseTest


class TestGetEluEntities(BaseTest):
    @patch("elixir_dss.clients.daisy.requests.get")
    def test_with_partners(self, mock_get):
        mock_get.return_value = Mock()
        mock_get.return_value.json.return_value = {"items": [PartnerFactory.build()]}
        result = get_elu_entities("partners")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["external_id"], "ELU_I_1")

    @patch("elixir_dss.clients.daisy.requests.get")
    def test_with_projects(self, mock_get):
        mock_get.return_value = Mock()
        mock_get.return_value.json.return_value = {"items": [ProjectFactory.build()]}
        result = get_elu_entities("projects")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["external_id"], "ELU_P_1")

    @patch("elixir_dss.clients.daisy.requests.get")
    def test_fallback_on_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")
        result = get_elu_entities("projects")

        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["external_id"], "ELU_P_1")

    @patch("elixir_dss.clients.daisy.requests.get")
    def test_fallback_on_http_error(self, mock_get):
        mock_get.return_value = Mock()
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("404")

        result = get_elu_entities("projects")

        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["external_id"], "ELU_P_1")

    @patch("elixir_dss.clients.daisy.requests.get")
    def test_fallback_on_invalid_json(self, mock_get):
        mock_get.return_value = Mock()
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        result = get_elu_entities("projects")

        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["external_id"], "ELU_P_1")

    @patch("elixir_dss.clients.daisy.requests.get")
    def test_empty_response(self, mock_get):
        mock_get.return_value = Mock()
        mock_get.return_value.json.return_value = {}
        result = get_elu_entities("projects")

        self.assertEqual(result, [])
