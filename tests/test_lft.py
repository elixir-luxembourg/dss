import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from flask import Flask

from elixir_dss.clients.lft import LFTHandler


class TestLFTHandler(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            {
                "LFT_HOST": "lft.example.com",
                "LFT_PORT": 8443,
                "LFT_SCHEME": "https",
                "LFT_USERNAME": "test_user",
                "LFT_PASSWORD": "test_pass",
                "LFT_NAMESPACE_ID": "test_namespace",
                "LFT_LINKS_BASE_URL": "https://lft.example.com/links/",
                "LFT_LINK_VALIDITY_DAYS": 7,
            }
        )

    @patch("elixir_dss.clients.lft.LFTClient", None)
    def test_without_lftclient(self):
        handler = LFTHandler(self.app)
        self.assertIsNone(handler.client)

        handler = LFTHandler(self.app)
        with self.assertRaises(RuntimeError):
            handler.get_or_create_link(Mock(id="ds3", external_id="EXT_003"), "SUB_003")

    def test_init_missing_config(self):
        app = Flask(__name__)
        app.config["LFT_HOST"] = "lft.example.com"
        handler = LFTHandler(app)
        self.assertIsNone(handler.client)

    @patch("elixir_dss.clients.lft.LFTClient")
    def test_create_new_link(self, mock_client_class):
        mock_client = mock_client_class.return_value
        mock_client.links_list.return_value = []

        mock_link = Mock(
            id="new_id",
            link_url="/share/link_url",
            expiration_datetime=datetime.now() + timedelta(days=7),
            page_password="pass",
        )
        mock_client.create_link.return_value = mock_link

        handler = LFTHandler(self.app)
        result = handler.get_or_create_link(
            Mock(id="ds2", external_id="EXT_002"), "SUB_002"
        )

        self.assertEqual(result.id, "new_id")
        mock_client.create_link.assert_called_once()
        mock_client.login.assert_called_once()

    @patch("elixir_dss.clients.lft.LFTClient")
    def test_get_existing_link(self, mock_client_class):
        mock_client = mock_client_class.return_value

        mock_link = Mock(
            id="link_id",
            link_url="/share/link_url",
            expiration_datetime=datetime.now() + timedelta(days=5),
            page_password="pass",
        )
        mock_client.links_list.return_value = [mock_link]

        handler = LFTHandler(self.app)
        result = handler.get_or_create_link(
            Mock(id="ds1", external_id="EXT_001"), "SUB_001"
        )

        self.assertEqual(result.id, "link_id")
        self.assertEqual(result.password, "pass")
        mock_client.login.assert_called_once()

    @patch("elixir_dss.clients.lft.LFTClient")
    def test_skip_expired_link(self, mock_client_class):
        mock_client = mock_client_class.return_value

        expired_link = Mock(expiration_datetime=datetime.now() - timedelta(days=1))
        new_link = Mock(
            id="new_id",
            link_url="/share/link_url",
            expiration_datetime=datetime.now() + timedelta(days=7),
            page_password="pass",
        )

        mock_client.links_list.return_value = [expired_link]
        mock_client.create_link.return_value = new_link

        handler = LFTHandler(self.app)
        result = handler.get_or_create_link(
            Mock(id="ds4", external_id="EXT_004"), "SUB_004"
        )

        self.assertEqual(result.id, "new_id")
        mock_client.create_link.assert_called_once()
        mock_client.login.assert_called_once()

    @patch("elixir_dss.clients.lft.LFTClient")
    def test_missing_external_id(self, mock_client_class):
        mock_client = mock_client_class.return_value
        handler = LFTHandler(self.app)

        with self.assertRaises(RuntimeError) as context:
            handler.get_or_create_link(Mock(id="ds5", external_id=None), "SUB_005")
        self.assertIn("Dataset external_id is required", str(context.exception))
        mock_client.login.assert_called_once()

        mock_client.reset_mock()
        with self.assertRaises(RuntimeError) as context:
            handler.get_or_create_link(Mock(id="ds6", external_id=""), "SUB_006")
        self.assertIn("Dataset external_id is required", str(context.exception))
        mock_client.login.assert_called_once()
