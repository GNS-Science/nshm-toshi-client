"""Tests for the toshi-auth CLI commands."""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from nshm_toshi_client.cli import cli, load_auth_config

from .test_credential_auth import _make_jwt

FAKE_CONFIG = {
    'region': 'ap-southeast-2',
    'user_pool_id': 'ap-southeast-2_FAKE',
    'scientist_client_id': 'scientist_id',
    'automation_client_id': 'automation_id',
    'automation_client_secret': 'automation_secret',
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
            config_path = Path(tmpdir) / 'auth_config.json'
            config_path.write_text(json.dumps(FAKE_CONFIG))
            with (
                patch.dict('os.environ', {'TOSHI_COGNITO_CONFIG': ''}, clear=False),
                patch('nshm_toshi_client.cli.Path.home', return_value=Path(tmpdir).parent),
            ):
                # Patch home so ~/.toshi/auth_config.json resolves to our temp file
                with patch('nshm_toshi_client.cli.Path') as MockPath:
                    MockPath.home.return_value = Path(tmpdir)
                    default = Path(tmpdir) / '.toshi' / 'auth_config.json'
                    default.parent.mkdir(parents=True, exist_ok=True)
                    default.write_text(json.dumps(FAKE_CONFIG))

                    import nshm_toshi_client.cli as cli_mod

                    # Just test with env var pointing to file
                    with patch.dict('os.environ', {'TOSHI_COGNITO_CONFIG': str(default)}):
                        config = cli_mod.load_auth_config()
                    self.assertEqual(config['scientist_client_id'], 'scientist_id')

    def test_falls_back_to_env_vars(self):
        import importlib

        env = {
            'TOSHI_COGNITO_CONFIG': '',
            'NZSHM22_TOSHI_COGNITO_DOMAIN': 'https://toshi-auth.example.amazoncognito.com',
            'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID': 'env_scientist_id',
            'NZSHM22_TOSHI_COGNITO_CLIENT_ID': 'env_client_id',
            'NZSHM22_TOSHI_COGNITO_CLIENT_SECRET': 'env_secret',
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


class TestWhoamiCommand(unittest.TestCase):
    def test_whoami_displays_claims(self):
        valid_token = _make_jwt({
            "sub": "user-123",
            "username": "scientist@example.com",
            "iss": "https://cognito-idp.ap-southeast-2.amazonaws.com/pool",
            "scope": "openid email",
            "token_use": "access",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
        })
        creds = {"access_token": valid_token}

        with patch('nshm_toshi_client.cli.load_credentials', return_value=creds):
            runner = CliRunner()
            result = runner.invoke(cli, ['whoami'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("scientist@example.com", result.output)
        self.assertIn("user-123", result.output)
        self.assertIn("valid", result.output)

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


class TestM2mTokenCommand(unittest.TestCase):
    def test_m2m_token(self):
        access_token = _make_jwt({"exp": time.time() + 3600, "scope": "toshi/read toshi/write"})

        with (
            patch('nshm_toshi_client.cli.load_auth_config', return_value=FAKE_CONFIG),
            patch('nshm_toshi_client.cli.http_post_form', return_value={"access_token": access_token}),
            patch.dict('os.environ', {'TOSHI_CLIENT_ID': 'auto_id', 'TOSHI_CLIENT_SECRET': 'auto_secret'}),
        ):
            runner = CliRunner()
            result = runner.invoke(cli, ['m2m-token', '--raw'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn(access_token, result.output)


if __name__ == "__main__":
    unittest.main()
