"""Tests for ToshiTokenManager and ToshiM2MAuth."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import requests_mock

from nshm_toshi_client.auth import ToshiM2MAuth, ToshiTokenManager, _fetch_m2m_credentials
from nshm_toshi_client.toshi_client_base import ToshiClientBase

from .conftest import mock_secrets_manager
from .conftest import mock_urlopen as _mock_urlopen

COGNITO_DOMAIN = "https://toshi-auth.example.auth.ap-southeast-2.amazoncognito.com"
SECRET_ARN = "arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:toshi-m2m-AbCdEf"

TOKEN_RESPONSE = json.dumps({"access_token": "fake.jwt.token", "expires_in": 3600}).encode()


class TestFetchM2MCredentials(unittest.TestCase):
    def test_returns_parsed_payload(self):
        with mock_secrets_manager(client_id="cid", client_secret="csec") as sm:
            client_id, client_secret = _fetch_m2m_credentials(SECRET_ARN)
        self.assertEqual(client_id, "cid")
        self.assertEqual(client_secret, "csec")
        sm.get_secret_value.assert_called_once_with(SecretId=SECRET_ARN)


class TestToshiTokenManager(unittest.TestCase):
    def _make_manager(self):
        with mock_secrets_manager():
            return ToshiTokenManager(cognito_domain=COGNITO_DOMAIN, secret_arn=SECRET_ARN)

    def test_requires_secret_arn(self):
        with patch.dict('os.environ', {'NZSHM22_TOSHI_M2M_SECRET_ARN': ''}):
            with self.assertRaises(ValueError) as ctx:
                ToshiTokenManager(cognito_domain=COGNITO_DOMAIN)
            self.assertIn("M2M credentials not configured", str(ctx.exception))

    def test_reads_secret_arn_from_env(self):
        with patch.dict('os.environ', {'NZSHM22_TOSHI_M2M_SECRET_ARN': SECRET_ARN}):
            with mock_secrets_manager(client_id="env-cid", client_secret="env-csec"):
                manager = ToshiTokenManager(cognito_domain=COGNITO_DOMAIN)
        self.assertEqual(manager._client_id, "env-cid")
        self.assertEqual(manager._client_secret, "env-csec")

    def test_token_fetched_on_first_get(self):
        manager = self._make_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()) as mock_open:
            token = manager.get_token()

        self.assertEqual(token, "fake.jwt.token")
        mock_open.assert_called_once()

        # Verify POST body and Basic auth header
        req = mock_open.call_args[0][0]
        self.assertIn("/oauth2/token", req.full_url)
        self.assertIn("grant_type=client_credentials", req.data.decode())
        self.assertTrue(req.get_header("Authorization").startswith("Basic "))

    def test_token_cached_within_expiry(self):
        manager = self._make_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()) as mock_open:
            t1 = manager.get_token()
            t2 = manager.get_token()

        self.assertEqual(t1, t2)
        mock_open.assert_called_once()  # only one fetch for two calls

    def test_token_refreshed_near_expiry(self):
        manager = self._make_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()) as mock_open:
            manager.get_token()  # initial fetch
            manager._expires_at = time.time() + 30  # simulate near-expiry (< 60s buffer)
            manager.get_token()  # should re-fetch

        self.assertEqual(mock_open.call_count, 2)

    def test_token_not_refreshed_well_before_expiry(self):
        manager = self._make_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()) as mock_open:
            manager.get_token()  # initial fetch
            manager._expires_at = time.time() + 600  # well within window
            manager.get_token()  # should use cache

        self.assertEqual(mock_open.call_count, 1)


class TestToshiM2MAuth(unittest.TestCase):
    def test_sets_authorization_header(self):
        manager = MagicMock(spec=ToshiTokenManager)
        manager.get_token.return_value = "fake.jwt.token"

        auth = ToshiM2MAuth(manager)

        mock_request = MagicMock()
        mock_request.headers = {}
        auth(mock_request)

        self.assertEqual(mock_request.headers["Authorization"], "Bearer fake.jwt.token")

    def test_calls_get_token_on_each_request(self):
        manager = MagicMock(spec=ToshiTokenManager)
        manager.get_token.return_value = "fake.jwt.token"
        auth = ToshiM2MAuth(manager)

        for _ in range(3):
            mock_request = MagicMock()
            mock_request.headers = {}
            auth(mock_request)

        self.assertEqual(manager.get_token.call_count, 3)


class TestToshiClientBaseWithTokenManager(unittest.TestCase):
    def test_token_manager_auto_created_from_secret_arn(self):
        """When NZSHM22_TOSHI_M2M_SECRET_ARN is set, token manager is wired in automatically."""
        API_URL = "http://fake_api/graphql"
        env = {
            'NZSHM22_TOSHI_M2M_SECRET_ARN': SECRET_ARN,
            'NZSHM22_TOSHI_COGNITO_DOMAIN': COGNITO_DOMAIN,
        }
        with patch.dict('os.environ', env):
            import importlib

            import nshm_toshi_client.config as cfg
            import nshm_toshi_client.toshi_client_base as base

            importlib.reload(cfg)
            importlib.reload(base)

            with (
                mock_secrets_manager(),
                patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()),
            ):
                with requests_mock.Mocker() as m:
                    m.post(API_URL, json={"data": {"about": "test-api"}})
                    client = base.ToshiClientBase(API_URL, auth_token=None, with_schema_validation=False)
                    client.run_query("{ about }")

            history = m.request_history
            self.assertEqual(history[0].headers.get("Authorization"), "Bearer fake.jwt.token")

        importlib.reload(cfg)
        importlib.reload(base)

    def test_warns_when_secret_arn_overrides_explicit_auth_token(self):
        """SECRET_ARN env should shadow auth_token but emit a warning so callers aren't surprised."""
        API_URL = "http://fake_api/graphql"
        env = {
            'NZSHM22_TOSHI_M2M_SECRET_ARN': SECRET_ARN,
            'NZSHM22_TOSHI_COGNITO_DOMAIN': COGNITO_DOMAIN,
        }
        with patch.dict('os.environ', env):
            import importlib

            import nshm_toshi_client.config as cfg
            import nshm_toshi_client.toshi_client_base as base

            importlib.reload(cfg)
            importlib.reload(base)

            with (
                mock_secrets_manager(),
                patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()),
            ):
                with requests_mock.Mocker() as m:
                    m.post(API_URL, json={"data": {"about": "test-api"}})
                    with self.assertLogs("nshm_toshi_client.toshi_client_base", level="WARNING") as cm:
                        base.ToshiClientBase(
                            API_URL,
                            auth_token="explicit-token",
                            with_schema_validation=False,
                        )
                    self.assertTrue(any("auth_token ignored" in m for m in cm.output))

        importlib.reload(cfg)
        importlib.reload(base)

    def test_raises_when_no_auth_configured(self):
        """Missing all auth paths should raise ValueError, not silently send 'Bearer None'."""
        import nshm_toshi_client.config as cfg
        import nshm_toshi_client.toshi_client_base as base

        env = {
            'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
        }
        with patch.dict('os.environ', env):
            import importlib

            importlib.reload(cfg)
            importlib.reload(base)

            with patch.object(base, 'CREDENTIALS_PATH') as mock_path:
                mock_path.exists.return_value = False
                with self.assertRaises(ValueError) as ctx:
                    base.ToshiClientBase("http://fake/graphql", with_schema_validation=False)
                self.assertIn("No auth configured", str(ctx.exception))

        importlib.reload(cfg)
        importlib.reload(base)

    def test_token_manager_injected_into_transport(self):
        API_URL = "http://fake_api/graphql"

        with mock_secrets_manager():
            manager = ToshiTokenManager(cognito_domain=COGNITO_DOMAIN, secret_arn=SECRET_ARN)

        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()):
            with requests_mock.Mocker() as m:
                m.post(API_URL, json={"data": {"about": "test-api"}})
                client = ToshiClientBase(
                    API_URL,
                    auth_token=None,
                    with_schema_validation=False,
                    token_manager=manager,
                )
                client.run_query("{ about }")

        history = m.request_history
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].headers.get("Authorization"), "Bearer fake.jwt.token")


if __name__ == "__main__":
    unittest.main()
