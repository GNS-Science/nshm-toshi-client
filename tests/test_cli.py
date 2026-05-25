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
            # Clear any NZSHM22_TOSHI_COGNITO_* env vars that might bleed in from
            # the developer's environment and override the file values.
            clean_env = {
                'TOSHI_COGNITO_CONFIG': f.name,
                'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
                'NZSHM22_TOSHI_COGNITO_REGION': '',
                'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': '',
                'NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID': '',
            }
            with patch.dict('os.environ', clean_env):
                config = load_auth_config()
        self.assertEqual(config['region'], 'ap-southeast-2')
        self.assertEqual(config['scientist_client_id'], 'scientist_id')

    def test_loads_from_default_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            default = Path(tmpdir) / '.toshi' / 'auth_config.json'
            default.parent.mkdir(parents=True, exist_ok=True)
            default.write_text(json.dumps(FAKE_CONFIG))

            # Clear any NZSHM22_TOSHI_COGNITO_* env vars that might bleed in from
            # the developer's environment and override the file values.
            clean_env = {
                'TOSHI_COGNITO_CONFIG': str(default),
                'NZSHM22_TOSHI_COGNITO_DOMAIN': '',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
                'NZSHM22_TOSHI_COGNITO_REGION': '',
                'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': '',
                'NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID': '',
            }
            with patch.dict('os.environ', clean_env):
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

    def test_load_cognito_config_per_key_env_over_file(self):
        """Env vars win per-key; file fills only the keys env left blank."""
        from nshm_toshi_client.config import load_cognito_config

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(
                {
                    'cognito_domain': 'file-domain.example.com',
                    'scientist_client_id': 'file_scientist_id',
                    'region': 'us-west-2',
                    'user_pool_id': 'file_pool',
                },
                f,
            )
            f.flush()
            env = {
                'TOSHI_COGNITO_CONFIG': f.name,
                # env sets cognito_domain only; file should fill the rest
                'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://env-domain.example.com',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': '',
                'NZSHM22_TOSHI_COGNITO_REGION': '',
                'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': '',
            }
            with patch.dict('os.environ', env):
                config = load_cognito_config()

        self.assertEqual(config['cognito_domain'], 'https://env-domain.example.com')
        self.assertEqual(config['scientist_client_id'], 'file_scientist_id')
        self.assertEqual(config['region'], 'us-west-2')
        self.assertEqual(config['user_pool_id'], 'file_pool')

    def test_identity_pool_id_from_file_when_all_env_vars_set(self):
        """identity_pool_id must be read from the file even when all four COGNITO env vars are set.

        Regression test for issue #48 (Bug 2): the old implementation only
        consulted auth_config.json inside an ``if not all(...)`` guard over the
        four env-backed keys, so identity_pool_id was silently dropped whenever
        all four env vars were present.
        """
        from nshm_toshi_client.config import load_cognito_config

        file_data = {
            'cognito_domain': 'file-domain.example.com',
            'scientist_client_id': 'file_scientist_id',
            'region': 'ap-southeast-2',
            'user_pool_id': 'ap-southeast-2_POOL',
            'identity_pool_id': 'ap-southeast-2:fake-pool-id',
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(file_data, f)
            f.flush()
            env = {
                'TOSHI_COGNITO_CONFIG': f.name,
                # All four env vars fully populated — this triggered the bug
                'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://env-domain.example.com',
                'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'env_scientist_id',
                'NZSHM22_TOSHI_COGNITO_REGION': 'ap-southeast-2',
                'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': 'ap-southeast-2_POOL',
                'NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID': '',  # not set via env
            }
            with patch.dict('os.environ', env):
                config = load_cognito_config()

        # identity_pool_id must be picked up from the file
        self.assertEqual(config['identity_pool_id'], 'ap-southeast-2:fake-pool-id')
        # env vars still win for the four env-backed keys
        self.assertEqual(config['cognito_domain'], 'https://env-domain.example.com')
        self.assertEqual(config['scientist_client_id'], 'env_scientist_id')

    def test_identity_pool_id_from_env_var(self):
        """NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID env var is honoured."""
        from nshm_toshi_client.config import load_cognito_config

        env = {
            'TOSHI_COGNITO_CONFIG': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://env-domain.example.com',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'env_scientist_id',
            'NZSHM22_TOSHI_COGNITO_REGION': 'ap-southeast-2',
            'NZSHM22_TOSHI_COGNITO_USER_POOL_ID': 'ap-southeast-2_POOL',
            'NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID': 'ap-southeast-2:env-pool-id',
        }
        with (
            patch.dict('os.environ', env),
            patch('nshm_toshi_client.config._load_config_file', return_value=None),
        ):
            config = load_cognito_config()

        self.assertEqual(config['identity_pool_id'], 'ap-southeast-2:env-pool-id')


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
    """Tests for the aws-creds CLI command.

    The command now delegates to get_aws_session() (from nshm_toshi_client.aws)
    and passes the resulting Session to get_aws_credentials(session, profile).
    Refresh / credential logic is covered in tests/test_aws.py.
    """

    def _mock_session(self, access_key='AKIAFAKE', secret='secret', token='session', region='ap-southeast-2'):
        """Return a mock boto3 Session with get_credentials().get_frozen_credentials()."""
        frozen = MagicMock()
        frozen.access_key = access_key
        frozen.secret_key = secret
        frozen.token = token
        session = MagicMock()
        session.get_credentials.return_value.get_frozen_credentials.return_value = frozen
        session.region_name = region
        return session

    # --- happy path ---

    def test_aws_creds_calls_get_aws_credentials_with_session(self):
        """aws-creds obtains a Session then delegates disk-write to get_aws_credentials."""
        mock_session = self._mock_session()

        with (
            patch('nshm_toshi_client.cli.get_aws_session', return_value=mock_session),
            patch('nshm_toshi_client.cli.get_aws_credentials', return_value='myprofile') as mock_write,
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds', '--profile', 'myprofile'])

        self.assertEqual(result.exit_code, 0, result.output)
        mock_write.assert_called_once_with(mock_session, 'myprofile')
        self.assertIn("AWS credentials saved", result.output)

    # --- error translation ---

    def test_aws_creds_not_logged_in(self):
        from nshm_toshi_client.aws import NoCredentialsError

        with patch('nshm_toshi_client.cli.get_aws_session', side_effect=NoCredentialsError("No credentials")):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("No credentials", result.output)

    def test_aws_creds_refresh_failed(self):
        from nshm_toshi_client.aws import RefreshFailedError

        with patch('nshm_toshi_client.cli.get_aws_session', side_effect=RefreshFailedError("Token expired")):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Token expired", result.output)

    def test_aws_creds_config_incomplete(self):
        from nshm_toshi_client.aws import ConfigIncompleteError

        with patch(
            'nshm_toshi_client.cli.get_aws_session',
            side_effect=ConfigIncompleteError(['identity_pool_id']),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("identity_pool_id", result.output)

    def test_aws_creds_identity_pool_error(self):
        from nshm_toshi_client.aws import IdentityPoolError

        with patch(
            'nshm_toshi_client.cli.get_aws_session',
            side_effect=IdentityPoolError("NotAuthorizedException"),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['aws-creds'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Identity Pool federation failed", result.output)

    # --- get_aws_credentials unit test (file-write step) ---

    def test_get_aws_credentials_writes_credentials_file(self):
        """get_aws_credentials(session, profile) extracts creds from Session and writes ~/.aws/credentials."""
        from nshm_toshi_client.cli import get_aws_credentials

        mock_session = self._mock_session(access_key='AKIAFAKE', secret='secret', token='session_tok')

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('nshm_toshi_client.cli.Path.home', return_value=Path(tmpdir)):
                profile = get_aws_credentials(mock_session, profile='toshi')

            self.assertEqual(profile, 'toshi')
            written = (Path(tmpdir) / '.aws' / 'credentials').read_text()
            self.assertIn('[toshi]', written)
            self.assertIn('aws_access_key_id = AKIAFAKE', written)
            self.assertIn('aws_secret_access_key = secret', written)
            self.assertIn('aws_session_token = session_tok', written)


if __name__ == "__main__":
    unittest.main()
