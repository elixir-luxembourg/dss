import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    os.environ["ELIXIR_DSS_ENV"] = "test"


@pytest.fixture(scope="function")
def mock_idservice_requests_post():
    with patch("elixir_dss.clients.idservice.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.text = "TEST_DATASET_ID_001"
        mock_post.return_value = mock_resp
        yield mock_post
