"""Tests for the toshi-auth CLI commands."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from nshm_toshi_client.cli import (
    cli,
    http_post_form,
    load_auth_config,
    password_flow_login,
    refresh_token,
)

from .test_credential_auth import _make_jwt

FAKE_CONFIG = {
    'region': 'ap-southeast-2',
    'user_pool_id': 'ap-southeast-2_FAKE',
    'scientist_client_id': 'scientist_id',
    'cognito_domain': 'toshi-auth.example.amazoncognito.com',
}


class TestLoadAuthConfig(unittest.TestCase):
    def test_loads_from_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(FAKE_CONFIG, f)
            f.flush()
            with patch.dict('os.environ', {'TOSHI_COGNITO_CONFIG': f.name}):
                config = load_auth_config()
        self.assertEqual(config['region'], 'ap-southeast-2')
        self.assertEqual(config['scientist_client_id'], 'scientist_id')

    def test_loads_from_default_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            default = Path(tmpdir) / '.toshi' / 'auth_config.json'
            default.parent.mkdir(parents=True, exist_ok=True)
            default.write_text(json.dumps(FAKE_CONFIG))

            with patch.dict('os.environ', {'TOSHI_COGNITO_CONFIG': str(default)}):
                import nshm_toshi_client.cli as cli_mod

                config = cli_mod.load_auth_config()
            self.assertEqual(config['scientist_client_id'], 'scientist_id')

    def test_falls_back_to_env_vars(self):
        import importlib

        env = {
            'TOSHI_COGNITO_CONFIG': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://toshi-auth.example.amazoncognito.com',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'env_scientist_id',
            'NZSHM22_TOSHI_COGNITO_REGION': 'us-west-2',
            'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': 'us-west-2_FAKE',
        }
        with (
            patch.dict('os.environ', env),
            patch('nshm_toshi_client.cli.Path.home', return_value=Path('/nonexistent')),
        ):
            import nshm_toshi_client.config as cfg

            importlib.reload(cfg)
            config = load_auth_config()

        self.assertEqual(config['scientist_client_id'], 'env_scientist_id')
        self.assertEqual(config['region'], 'us-west-2')

        # Clean up
        importlib.reload(cfg)

    def test_raises_when_no_config(self):
        import importlib

        env = {
            'TOSHI_COGNITO_CONFIG': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
        }
        with (
            patch.dict('os.environ', env),
            patch('nshm_toshi_client.cli.Path.home', return_value=Path('/nonexistent')),
        ):
            import nshm_toshi_client.config as cfg

            importlib.reload(cfg)
            import click

            with self.assertRaises(click.ClickException):
                load_auth_config()

        importlib.reload(cfg)

    def test_raises_when_scientist_client_id_missing(self):
        """Gate is scientist_client_id (what login() consumes), not just cognito_domain."""
        import importlib

        env = {
            'TOSHI_COGNITO_CONFIG': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://toshi-auth.example.amazoncognito.com',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
        }
        with (
            patch.dict('os.environ', env),
            patch('nshm_toshi_client.cli.Path.home', return_value=Path('/nonexistent')),
        ):
            import nshm_toshi_client.config as cfg

            importlib.reload(cfg)
            import click

            with self.assertRaises(click.ClickException) as ctx:
                load_auth_config()
            self.assertIn("auth_config.example.json", str(ctx.exception))

        importlib.reload(cfg)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


class TestHttpPostForm(unittest.TestCase):
    def test_posts_form_data(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('nshm_toshi_client.cli.urlopen', return_value=mock_resp) as mock_open:
            result = http_post_form('https://example.com/token', {'grant_type': 'client_credentials'})

        self.assertEqual(result, {"ok": True})
        req = mock_open.call_args[0][0]
        self.assertIn(b'grant_type=client_credentials', req.data)
        self.assertEqual(req.get_header('Content-type'), 'application/x-www-form-urlencoded')

    def test_posts_with_basic_auth(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"ok": True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('nshm_toshi_client.cli.urlopen', return_value=mock_resp) as mock_open:
            http_post_form('https://example.com/token', {'key': 'val'}, auth=('user', 'pass'))

        req = mock_open.call_args[0][0]
        self.assertTrue(req.get_header('Authorization').startswith('Basic '))


# ---------------------------------------------------------------------------
# Auth flow functions
# ---------------------------------------------------------------------------


def _mock_boto3_with_cognito(cognito_mock):
    """Create a mock boto3 module that returns the given cognito client.

    Ensures the cognito client returned by boto3.client() is always
    the same mock, so exception types set on it are visible in except clauses.
    """
    mock_boto3 = MagicMock()
    # boto3.client('cognito-idp', ...) must return our mock
    mock_boto3.client.return_value = cognito_mock
    return mock_boto3


class TestPasswordFlowLogin(unittest.TestCase):
    def test_successful_login(self):
        mock_cognito = MagicMock()
        mock_cognito.exceptions.NotAuthorizedException = type('NotAuthorizedException', (Exception,), {})
        mock_cognito.exceptions.UserNotFoundException = type('UserNotFoundException', (Exception,), {})
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'access_tok',
                'IdToken': 'id_tok',
                'RefreshToken': 'refresh_tok',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600,
            }
        }
        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with (
            patch.dict('sys.modules', {'boto3': mock_boto3}),
            patch('nshm_toshi_client.cli.click.prompt', side_effect=['user@example.com', 'password123']),
        ):
            result = password_flow_login(FAKE_CONFIG)

        self.assertEqual(result['access_token'], 'access_tok')
        self.assertEqual(result['refresh_token'], 'refresh_tok')
        mock_cognito.initiate_auth.assert_called_once_with(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': 'user@example.com', 'PASSWORD': 'password123'},
            ClientId='scientist_id',
        )

    def test_invalid_credentials(self):
        mock_cognito = MagicMock()
        mock_cognito.exceptions.NotAuthorizedException = type('NotAuthorizedException', (Exception,), {})
        mock_cognito.initiate_auth.side_effect = mock_cognito.exceptions.NotAuthorizedException()
        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with (
            patch.dict('sys.modules', {'boto3': mock_boto3}),
            patch('nshm_toshi_client.cli.click.prompt', side_effect=['user@example.com', 'wrong']),
        ):
            import click

            with self.assertRaises(click.ClickException):
                password_flow_login(FAKE_CONFIG)

    def test_user_not_found(self):
        mock_cognito = MagicMock()
        mock_cognito.exceptions.NotAuthorizedException = type('NotAuthorizedException', (Exception,), {})
        mock_cognito.exceptions.UserNotFoundException = type('UserNotFoundException', (Exception,), {})
        mock_cognito.initiate_auth.side_effect = mock_cognito.exceptions.UserNotFoundException()
        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with (
            patch.dict('sys.modules', {'boto3': mock_boto3}),
            patch('nshm_toshi_client.cli.click.prompt', side_effect=['nobody@example.com', 'pass']),
        ):
            import click

            with self.assertRaises(click.ClickException):
                password_flow_login(FAKE_CONFIG)

    def test_auth_challenge_raises(self):
        mock_cognito = MagicMock()
        mock_cognito.exceptions.NotAuthorizedException = type('NotAuthorizedException', (Exception,), {})
        mock_cognito.exceptions.UserNotFoundException = type('UserNotFoundException', (Exception,), {})
        mock_cognito.initiate_auth.return_value = {'ChallengeName': 'NEW_PASSWORD_REQUIRED'}
        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with (
            patch.dict('sys.modules', {'boto3': mock_boto3}),
            patch('nshm_toshi_client.cli.click.prompt', side_effect=['user@example.com', 'pass']),
        ):
            import click

            with self.assertRaises(click.ClickException):
                password_flow_login(FAKE_CONFIG)


class TestRefreshToken(unittest.TestCase):
    def test_successful_refresh(self):
        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'new_access',
                'IdToken': 'new_id',
                'ExpiresIn': 3600,
            }
        }
        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with patch.dict('sys.modules', {'boto3': mock_boto3}):
            result = refresh_token(FAKE_CONFIG, 'old_refresh_tok')

        self.assertEqual(result['access_token'], 'new_access')
        mock_cognito.initiate_auth.assert_called_once_with(
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={'REFRESH_TOKEN': 'old_refresh_tok'},
            ClientId='scientist_id',
        )


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


class TestWhoamiCommand(unittest.TestCase):
    def test_whoami_displays_claims(self):
        valid_token = _make_jwt(
            {
                "sub": "user-123",
                "username": "scientist@example.com",
                "iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/pool",
                "scope": "openid email",
                "token_use": "access",
                "exp": int(time.time()) + 3600,
                "iat": int(time.time()),
            }
        )
        creds = {"access_token": valid_token}

        with patch('nshm_toshi_client.cli.load_credentials', return_value=creds):
            runner = CliRunner()
            result = runner.invoke(cli, ['whoami'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("scientist@example.com", result.output)
        self.assertIn("user-123", result.output)
        self.assertIn("valid", result.output)

    def test_whoami_expired_token(self):
        expired_token = _make_jwt(
            {
                "sub": "user-123",
                "exp": int(time.time()) - 100,
            }
        )
        creds = {"access_token": expired_token}

        with patch('nshm_toshi_client.cli.load_credentials', return_value=creds):
            runner = CliRunner()
            result = runner.invoke(cli, ['whoami'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("EXPIRED", result.output)

    def test_whoami_not_logged_in(self):
        with patch('nshm_toshi_client.cli.load_credentials', return_value={}):
            runner = CliRunner()
            result = runner.invoke(cli, ['whoami'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Not logged in", result.output)


class TestTokenCommand(unittest.TestCase):
    def test_token_prints_bearer(self):
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(f"Bearer {valid_token}", result.output)

    def test_token_raw_flag(self):
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token', '--raw'])

        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("Bearer", result.output)
        self.assertIn(valid_token, result.output)

    def test_token_not_logged_in(self):
        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value={}),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Not logged in", result.output)

    def test_token_expired_no_refresh(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        creds = {"access_token": expired_token}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("no refresh token", result.output)

    def test_token_refreshes_expired(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        new_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": expired_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
            patch('nshm_toshi_client.cli.refresh_token', return_value={'access_token': new_token, 'expires_in': 3600}),
            patch('nshm_toshi_client.cli.save_credentials'),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token', '--raw'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(new_token, result.output)

    def test_token_refresh_failure(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        creds = {"access_token": expired_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
            patch('nshm_toshi_client.cli.refresh_token', side_effect=Exception("network error")),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['token'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Token refresh failed", result.output)


class TestLoginCommand(unittest.TestCase):
    def test_login_saves_credentials(self):
        access_token = _make_jwt(
            {
                "exp": int(time.time()) + 3600,
                "username": "scientist@example.com",
                "scope": "openid",
            }
        )

        mock_cognito = MagicMock()
        mock_cognito.exceptions.NotAuthorizedException = type('NotAuthorizedException', (Exception,), {})
        mock_cognito.exceptions.UserNotFoundException = type('UserNotFoundException', (Exception,), {})
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': access_token,
                'IdToken': 'id_tok',
                'RefreshToken': 'refresh_tok',
                'TokenType': 'Bearer',
                'ExpiresIn': 3600,
            }
        }

        mock_boto3 = _mock_boto3_with_cognito(mock_cognito)

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value={}),
            patch('nshm_toshi_client.cli.save_credentials') as mock_save,
            patch.dict('sys.modules', {'boto3': mock_boto3}),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['login'], input='user@example.com\npassword123\n')

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Logged in as", result.output)
        self.assertIn("Token saved to", result.output)
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        self.assertEqual(saved['access_token'], access_token)
        self.assertEqual(saved['refresh_token'], 'refresh_tok')


class TestLogoutCommand(unittest.TestCase):
    def test_logout_removes_credentials_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            creds_path = Path(tmpdir) / 'credentials'
            creds_path.write_text(json.dumps({'access_token': 'tok'}))

            with patch('nshm_toshi_client.cli.CREDENTIALS_PATH', creds_path):
                runner = CliRunner()
                result = runner.invoke(cli, ['logout'])

            self.assertEqual(result.exit_code, 0)
            self.assertIn('Logged out', result.output)
            self.assertFalse(creds_path.exists())

    def test_logout_when_not_logged_in(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            creds_path = Path(tmpdir) / 'credentials'

            with patch('nshm_toshi_client.cli.CREDENTIALS_PATH', creds_path):
                runner = CliRunner()
                result = runner.invoke(cli, ['logout'])

            self.assertEqual(result.exit_code, 0)
            self.assertIn('Already logged out', result.output)


class TestAwsCredsCommand(unittest.TestCase):
    def test_aws_creds_not_logged_in(self):
        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value={}),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Not logged in", result.output)

    def test_aws_creds_expired_no_refresh(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        creds = {"access_token": expired_token}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("no refresh token", result.output)

    def test_aws_creds_calls_get_aws_credentials(self):
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
            patch('nshm_toshi_client.cli.get_aws_credentials', return_value='toshi') as mock_get_aws,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds', '--profile', 'myprofile'])

        self.assertEqual(result.exit_code, 0)
        mock_get_aws.assert_called_once_with(FAKE_CONFIG, valid_token, 'myprofile')
        self.assertIn("AWS credentials saved", result.output)

    def test_get_aws_credentials_happy_path(self):
        from datetime import datetime, timezone

        from nshm_toshi_client.cli import get_aws_credentials

        config = {**FAKE_CONFIG, 'identity_pool_id': 'ap-southeast-2:fake-pool'}
        expiration = datetime(2030, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        mock_cognito_identity = MagicMock()
        mock_cognito_identity.get_id.return_value = {'IdentityId': 'identity-1'}
        mock_cognito_identity.get_credentials_for_identity.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKIAFAKE',
                'SecretKey': 'secret',
                'SessionToken': 'session',
                'Expiration': expiration,
            }
        }
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_cognito_identity

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch.dict('sys.modules', {'boto3': mock_boto3}),
                patch('nshm_toshi_client.cli.Path.home', return_value=Path(tmpdir)),
            ):
                profile = get_aws_credentials(config, 'fake-access-token', profile='toshi')

            self.assertEqual(profile, 'toshi')
            written = (Path(tmpdir) / '.aws' / 'credentials').read_text()
            self.assertIn('[toshi]', written)
            self.assertIn('aws_access_key_id = AKIAFAKE', written)
            self.assertIn('aws_secret_access_key = secret', written)
            self.assertIn('aws_session_token = session', written)

    def test_aws_creds_refreshes_expired_token(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        new_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": expired_token, "refresh_token": "refresh_tok"}

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.load_credentials', return_value=creds),
            patch('nshm_toshi_client.cli.refresh_token', return_value={'access_token': new_token, 'expires_in': 3600}),
            patch('nshm_toshi_client.cli.save_credentials'),
            patch('nshm_toshi_client.cli.get_aws_credentials', return_value='toshi') as mock_get_aws,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertEqual(result.exit_code, 0)
        mock_get_aws.assert_called_once_with(FAKE_CONFIG, new_token, 'toshi')


if __name__ == "__main__":
    unittest.main()
