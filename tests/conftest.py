"""Shared test helpers."""

import json
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

DEFAULT_TOKEN_RESPONSE = json.dumps({"access_token": "fake.jwt.token", "expires_in": 3600}).encode()


def mock_urlopen(response_bytes=DEFAULT_TOKEN_RESPONSE):
    """Return a mock that urlopen() can return — supports context-manager use."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_bytes
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@contextmanager
def mock_secrets_manager(client_id="test-client-id", client_secret="test-client-secret"):
    """Patch boto3.client('secretsmanager') to return the given credentials.

    Use to construct a ToshiTokenManager in tests without hitting AWS:

        with mock_secrets_manager():
            mgr = ToshiTokenManager(cognito_domain="...", secret_arn="arn:fake")
    """
    sm = MagicMock()
    sm.get_secret_value.return_value = {
        'SecretString': json.dumps({'client_id': client_id, 'client_secret': client_secret}),
    }
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = sm
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        yield sm
