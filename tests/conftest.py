import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    os.environ["ELIXIR_DSS_ENV"] = "test"
