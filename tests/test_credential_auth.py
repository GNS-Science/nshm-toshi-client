"""Tests for credential helpers, JWT utilities, and ToshiCredentialAuth."""

import base64
import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests_mock

from nshm_toshi_client.auth import (
    ToshiCredentialAuth,
    decode_jwt_payload,
    is_token_expired,
    load_credentials,
    save_credentials,
)

from .conftest import mock_urlopen as _mock_urlopen


def _make_jwt(payload: dict) -> str:
    """Build a minimal unsigned JWT for testing."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).rstrip(b'=').decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    return f"{header}.{body}.sig"


class TestDecodeJwtPayload(unittest.TestCase):
    def test_decodes_valid_jwt(self):
        token = _make_jwt({"sub": "user1", "exp": 9999999999})
        payload = decode_jwt_payload(token)
        self.assertEqual(payload["sub"], "user1")

    def test_raises_on_invalid_format(self):
        with self.assertRaises(ValueError):
            decode_jwt_payload("not.a.valid.jwt.too.many.parts")

    def test_raises_on_no_dots(self):
        with self.assertRaises(ValueError):
            decode_jwt_payload("nodotsatall")


class TestIsTokenExpired(unittest.TestCase):
    def test_valid_token_not_expired(self):
        token = _make_jwt({"exp": time.time() + 3600})
        self.assertFalse(is_token_expired(token))

    def test_expired_token(self):
        token = _make_jwt({"exp": time.time() - 100})
        self.assertTrue(is_token_expired(token))

    def test_near_expiry_within_buffer(self):
        token = _make_jwt({"exp": time.time() + 30})  # within 60s buffer
        self.assertTrue(is_token_expired(token, buffer_seconds=60))

    def test_malformed_token_returns_true(self):
        self.assertTrue(is_token_expired("garbage"))


class TestLoadSaveCredentials(unittest.TestCase):
    def test_round_trip(self, tmp_path=None):
        """Write and read back credentials via a temp path."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_path = Path(tmpdir) / 'credentials'
            data = {"access_token": "abc", "refresh_token": "xyz"}

            with patch('nshm_toshi_client.auth.CREDENTIALS_PATH', fake_path):
                save_credentials(data)
                loaded = load_credentials()

            self.assertEqual(loaded["access_token"], "abc")
            self.assertEqual(loaded["refresh_token"], "xyz")
            # Check file permissions (owner-only, not enforced on Windows)
            if sys.platform != 'win32':
                self.assertEqual(fake_path.stat().st_mode & 0o777, 0o600)

    def test_load_missing_file_returns_empty(self):
        fake_path = Path('/nonexistent/path/credentials')
        with patch('nshm_toshi_client.auth.CREDENTIALS_PATH', fake_path):
            self.assertEqual(load_credentials(), {})


class TestToshiCredentialAuth(unittest.TestCase):
    DOMAIN = "https://toshi-auth.example.auth.ap-southeast-2.amazoncognito.com"
    CLIENT_ID = "scientist_client_id"

    def test_uses_valid_token(self):
        """When token is not expired, uses it without refreshing."""
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with patch('nshm_toshi_client.auth.load_credentials', return_value=creds):
            auth = ToshiCredentialAuth(self.DOMAIN, self.CLIENT_ID)
            mock_request = MagicMock()
            mock_request.headers = {}
            auth(mock_request)

        self.assertEqual(mock_request.headers["Authorization"], f"Bearer {valid_token}")

    def test_refreshes_expired_token(self):
        """When token is expired, refreshes via OAuth2 token endpoint."""
        expired_token = _make_jwt({"exp": time.time() - 100})
        new_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": expired_token, "refresh_token": "refresh_tok"}

        refresh_response = MagicMock()
        refresh_response.read.return_value = json.dumps({"access_token": new_token, "expires_in": 3600}).encode()
        refresh_response.__enter__ = lambda s: s
        refresh_response.__exit__ = MagicMock(return_value=False)

        with (
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
            patch('nshm_toshi_client.auth.save_credentials') as mock_save,
            patch('nshm_toshi_client.auth.urllib_request.urlopen', return_value=refresh_response) as mock_urlopen,
        ):
            auth = ToshiCredentialAuth(self.DOMAIN, self.CLIENT_ID)
            mock_request = MagicMock()
            mock_request.headers = {}
            auth(mock_request)

        self.assertEqual(mock_request.headers["Authorization"], f"Bearer {new_token}")
        mock_save.assert_called_once()
        saved_creds = mock_save.call_args[0][0]
        self.assertEqual(saved_creds["access_token"], new_token)

        # Verify refresh POST
        req = mock_urlopen.call_args[0][0]
        self.assertIn("grant_type=refresh_token", req.data.decode())
        self.assertIn(f"client_id={self.CLIENT_ID}", req.data.decode())

    def test_raises_when_no_credentials(self):
        with patch('nshm_toshi_client.auth.load_credentials', return_value={}):
            auth = ToshiCredentialAuth(self.DOMAIN, self.CLIENT_ID)
            mock_request = MagicMock()
            mock_request.headers = {}
            with self.assertRaises(RuntimeError, msg="No credentials found"):
                auth(mock_request)

    def test_raises_when_expired_no_refresh_token(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        creds = {"access_token": expired_token}

        with patch('nshm_toshi_client.auth.load_credentials', return_value=creds):
            auth = ToshiCredentialAuth(self.DOMAIN, self.CLIENT_ID)
            mock_request = MagicMock()
            mock_request.headers = {}
            with self.assertRaises(RuntimeError, msg="no refresh token"):
                auth(mock_request)


class TestToshiClientBaseWithCredentialAuth(unittest.TestCase):
    def test_auto_detects_credentials_file(self):
        """When credentials file exists and scientist env vars set, uses ToshiCredentialAuth."""
        import importlib
        import tempfile

        API_URL = "http://fake_api/graphql"

        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_creds_path = Path(tmpdir) / 'credentials'
            fake_creds_path.write_text(json.dumps(creds))

            env = {
                'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://toshi-auth.example.amazoncognito.com',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'scientist_id',
                # Clear M2M secret ARN so it doesn't take precedence
                'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
            }

            with (
                patch.dict('os.environ', env),
                patch('nshm_toshi_client.auth.CREDENTIALS_PATH', fake_creds_path),
                patch('nshm_toshi_client.toshi_client_base.CREDENTIALS_PATH', fake_creds_path),
            ):
                import nshm_toshi_client.config as cfg
                import nshm_toshi_client.toshi_client_base as base

                importlib.reload(cfg)
                importlib.reload(base)

                with requests_mock.Mocker() as m:
                    m.post(API_URL, json={"data": {"about": "test-api"}})
                    client = base.ToshiClientBase(API_URL, with_schema_validation=False)
                    client.run_query("{ about }")

                history = m.request_history
                self.assertEqual(history[0].headers.get("Authorization"), f"Bearer {valid_token}")

            importlib.reload(cfg)
            importlib.reload(base)

    def test_auto_detects_via_auth_config_json_without_env_vars(self):
        """Chris scenario: ~/.toshi/auth_config.json present, no NZSHM22_TOSHI_COGNITO_* env vars,
        ~/.toshi/credentials present. ToshiClientBase should still auto-detect scientist auth.
        """
        import importlib
        import tempfile

        API_URL = "http://fake_api/graphql"
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fake_creds_path = tmp / 'credentials'
            fake_creds_path.write_text(json.dumps(creds))

            auth_config_path = tmp / 'auth_config.json'
            auth_config_path.write_text(
                json.dumps(
                    {
                        'region': 'ap-southeast-2',
                        'user_pool_id': 'ap-southeast-2_FAKE',
                        'scientist_client_id': 'file_scientist_id',
                        'cognito_domain': 'https://toshi-auth.example.amazoncognito.com',
                    }
                )
            )

            env = {
                'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
                'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
                'TOSHI_COGNITO_CONFIG': str(auth_config_path),
            }

            with (
                patch.dict('os.environ', env),
                patch('nshm_toshi_client.auth.CREDENTIALS_PATH', fake_creds_path),
                patch('nshm_toshi_client.toshi_client_base.CREDENTIALS_PATH', fake_creds_path),
            ):
                import nshm_toshi_client.config as cfg
                import nshm_toshi_client.toshi_client_base as base

                importlib.reload(cfg)
                importlib.reload(base)

                with requests_mock.Mocker() as m:
                    m.post(API_URL, json={"data": {"about": "test-api"}})
                    client = base.ToshiClientBase(API_URL, with_schema_validation=False)
                    client.run_query("{ about }")

                history = m.request_history
                self.assertEqual(history[0].headers.get("Authorization"), f"Bearer {valid_token}")

            importlib.reload(cfg)
            importlib.reload(base)

    def _run_with_credentials(self, kwargs, expected_warning):
        """Helper: set up scientist auto-detect, call ToshiClientBase(**kwargs), assert warning."""
        import importlib
        import tempfile

        API_URL = "http://fake_api/graphql"
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with tempfile.TemporaryDirectory() as tmpdir:
            fake_creds_path = Path(tmpdir) / 'credentials'
            fake_creds_path.write_text(json.dumps(creds))

            env = {
                'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://toshi-auth.example.amazoncognito.com',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'scientist_id',
                'NZSHM22_TOSHI_M2M_SECRET_ARN': '',
            }
            with (
                patch.dict('os.environ', env),
                patch('nshm_toshi_client.auth.CREDENTIALS_PATH', fake_creds_path),
                patch('nshm_toshi_client.toshi_client_base.CREDENTIALS_PATH', fake_creds_path),
            ):
                import nshm_toshi_client.config as cfg
                import nshm_toshi_client.toshi_client_base as base

                importlib.reload(cfg)
                importlib.reload(base)

                with requests_mock.Mocker() as m:
                    m.post(API_URL, json={"data": {"about": "test-api"}})
                    with self.assertLogs("nshm_toshi_client.toshi_client_base", level="WARNING") as cm:
                        base.ToshiClientBase(API_URL, with_schema_validation=False, **kwargs)
                    self.assertTrue(
                        any(expected_warning in line for line in cm.output),
                        f"Expected warning containing {expected_warning!r}, got: {cm.output}",
                    )

        # Restore cfg/base with the original (un-patched) env. The reload must run
        # outside `with patch.dict(...)` so the patched env doesn't leak into later tests.
        importlib.reload(cfg)
        importlib.reload(base)

    def test_warns_when_credentials_file_overrides_auth_token(self):
        """Scientist auto-detect should shadow auth_token= and emit a warning."""
        self._run_with_credentials({"auth_token": "explicit-token"}, "auth_token ignored")

    def test_warns_when_credentials_file_overrides_headers(self):
        """Scientist auto-detect should shadow headers= and emit a warning."""
        self._run_with_credentials({"headers": {"x-api-key": "legacy-key"}}, "headers ignored")


class TestSubclassKwargsPassthrough(unittest.TestCase):
    """Verify subclasses forward **kwargs (e.g. token_manager) to ToshiClientBase."""

    API_URL = "http://fake_api/graphql"
    S3_URL = "https://fake-s3.com/"

    def _make_token_manager(self):
        from nshm_toshi_client.auth import ToshiTokenManager

        from .conftest import mock_secrets_manager

        with mock_secrets_manager():
            return ToshiTokenManager(cognito_domain="https://auth.example.com", secret_arn="arn:fake")

    def test_toshi_file_accepts_token_manager(self):
        from nshm_toshi_client.toshi_file import ToshiFile

        mgr = self._make_token_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()):
            with requests_mock.Mocker() as m:
                m.post(self.API_URL, json={"data": {"node": {"id": "abc"}}})
                api = ToshiFile(self.API_URL, self.S3_URL, with_schema_validation=False, token_manager=mgr)
                api.get_file("abc")

            self.assertEqual(m.request_history[0].headers.get("Authorization"), "Bearer fake.jwt.token")

    def test_task_relation_accepts_token_manager(self):
        from nshm_toshi_client.task_relation import TaskRelation

        mgr = self._make_token_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()):
            with requests_mock.Mocker() as m:
                m.post(self.API_URL, json={"data": {"__typename": "QueryRoot"}})
                api = TaskRelation(self.API_URL, with_schema_validation=False, token_manager=mgr)
                api.run_query("{ __typename }")

            self.assertEqual(m.request_history[0].headers.get("Authorization"), "Bearer fake.jwt.token")

    def test_general_task_accepts_token_manager(self):
        from nshm_toshi_client.general_task import GeneralTask

        mgr = self._make_token_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()):
            with requests_mock.Mocker() as m:
                m.post(self.API_URL, json={"data": {"__typename": "QueryRoot"}})
                api = GeneralTask(self.API_URL, self.S3_URL, with_schema_validation=False, token_manager=mgr)
                api.run_query("{ __typename }")

            self.assertEqual(m.request_history[0].headers.get("Authorization"), "Bearer fake.jwt.token")

    def test_strong_motion_station_accepts_token_manager(self):
        from nshm_toshi_client.strong_motion_station import StrongMotionStation

        mgr = self._make_token_manager()
        with patch("nshm_toshi_client.auth.urllib_request.urlopen", return_value=_mock_urlopen()):
            with requests_mock.Mocker() as m:
                m.post(self.API_URL, json={"data": {"__typename": "QueryRoot"}})
                api = StrongMotionStation(self.API_URL, self.S3_URL, with_schema_validation=False, token_manager=mgr)
                api.run_query("{ __typename }")

            self.assertEqual(m.request_history[0].headers.get("Authorization"), "Bearer fake.jwt.token")


if __name__ == "__main__":
    unittest.main()
