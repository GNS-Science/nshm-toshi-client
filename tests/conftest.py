"""Shared test helpers."""

import json
from unittest.mock import MagicMock

DEFAULT_TOKEN_RESPONSE = json.dumps({"access_token": "fake.jwt.token", "expires_in": 3600}).encode()


def mock_urlopen(response_bytes=DEFAULT_TOKEN_RESPONSE):
    """Return a mock that urlopen() can return — supports context-manager use."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_bytes
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp
