"""Tests for nshm_toshi_client.config module-level API_KEY resolution."""

import importlib
import json
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch


@contextmanager
def _mock_api_key_secret(api_key_value: str, secret_key: str):
    """Patch boto3 so _get_secret returns a dict with the given API key value."""
    sm = MagicMock()
    sm.get_secret_value.return_value = {
        'SecretString': json.dumps({secret_key: api_key_value}),
    }
    mock_boto3 = MagicMock()
    mock_boto3.session.Session.return_value.client.return_value = sm
    with patch.dict('sys.modules', {'boto3': mock_boto3}):
        yield sm


class TestApiKeyResolution(unittest.TestCase):
    def tearDown(self):
        import nshm_toshi_client.config as cfg

        importlib.reload(cfg)

    def test_secrets_manager_skipped_when_m2m_configured(self):
        """When M2M env vars are set, the Secrets Manager fetch must not fire."""
        env = {
            'AWS_BATCH_JOB_ID': 'fake-job-id',
            'NZSHM22_TOSHI_API_URL': 'https://test.example/graphql',
            'NZSHM22_TOSHI_API_KEY': '',
            'NZSHM22_TOSHI_M2M_SECRET_ARN': 'arn:aws:secretsmanager:ap-southeast-2:123:secret:m2m',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://fake.auth.example.com',
        }
        with patch.dict('os.environ', env, clear=False):
            import nshm_toshi_client.config as cfg

            with _mock_api_key_secret('should-not-appear', 'NZSHM22_TOSHI_API_KEY_TEST') as sm:
                importlib.reload(cfg)
                self.assertEqual(cfg.API_KEY, '')
                sm.get_secret_value.assert_not_called()

    def test_secrets_manager_called_in_batch_without_m2m(self):
        """In a Batch job without M2M env vars the Secrets Manager fetch still fires."""
        sentinel_key = 'fetched-from-secrets-manager'
        env = {
            'AWS_BATCH_JOB_ID': 'fake-job-id',
            'NZSHM22_TOSHI_API_URL': 'https://test.example/graphql',
            'NZSHM22_TOSHI_API_KEY': '',
            'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
        }
        with patch.dict('os.environ', env, clear=False):
            import nshm_toshi_client.config as cfg

            with _mock_api_key_secret(sentinel_key, 'NZSHM22_TOSHI_API_KEY_TEST') as sm:
                importlib.reload(cfg)
                self.assertEqual(cfg.API_KEY, sentinel_key)
                sm.get_secret_value.assert_called_once()

    def test_explicit_api_key_env_var_always_wins(self):
        """NZSHM22_TOSHI_API_KEY env var is used as-is; Secrets Manager is never called."""
        env = {
            'AWS_BATCH_JOB_ID': 'fake-job-id',
            'NZSHM22_TOSHI_API_URL': 'https://test.example/graphql',
            'NZSHM22_TOSHI_API_KEY': 'explicit-key',
            'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
        }
        with patch.dict('os.environ', env, clear=False):
            import nshm_toshi_client.config as cfg

            with _mock_api_key_secret('should-not-appear', 'NZSHM22_TOSHI_API_KEY_TEST') as sm:
                importlib.reload(cfg)
                self.assertEqual(cfg.API_KEY, 'explicit-key')
                sm.get_secret_value.assert_not_called()
