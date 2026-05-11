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
        refresh_response.read.return_value = json.dumps(
            {"access_token": new_token, "expires_in": 3600}
        ).encode()
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
                # Clear M2M vars so they don't take precedence
                'NZSHM22_TOSHI_COGNITO_CLIENT_ID': '',
                'NZSHM22_TOSHI_COGNITO_CLIENT_SECRET': '',
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


if __name__ == "__main__":
    unittest.main()
