"""Tests for nshm_toshi_client.aws — get_aws_session() and typed exceptions."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import botocore.exceptions

from nshm_toshi_client.aws import (
    ConfigIncompleteError,
    IdentityPoolError,
    NoCredentialsError,
    RefreshFailedError,
    get_aws_session,
)

from .test_credential_auth import _make_jwt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FULL_CONFIG = {
    'cognito_domain': 'toshi-auth.example.auth.ap-southeast-2.amazoncognito.com',
    'scientist_client_id': 'scientist_client_id',
    'region': 'ap-southeast-2',
    'user_pool_id': 'ap-southeast-2_FAKE',
    'identity_pool_id': 'ap-southeast-2:fake-pool',
}


def _make_cognito_identity_mock(identity_id='identity-1', access_key='AKIAFAKE', secret='secret', token='session'):
    """Return a mock cognito-identity client that returns a successful STS response."""
    mock = MagicMock()
    mock.get_id.return_value = {'IdentityId': identity_id}
    mock.get_credentials_for_identity.return_value = {
        'Credentials': {
            'AccessKeyId': access_key,
            'SecretKey': secret,
            'SessionToken': token,
        }
    }
    return mock


def _make_boto3_mock(cognito_identity_mock):
    """Return a mock boto3 module whose client() returns cognito_identity_mock."""
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = cognito_identity_mock
    return mock_boto3


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetAwsSessionHappyPath(unittest.TestCase):
    def test_returns_boto3_session(self):
        valid_id_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": _make_jwt({"exp": time.time() + 3600}), "id_token": valid_id_token}

        mock_ci = _make_cognito_identity_mock()
        mock_boto3 = _make_boto3_mock(mock_ci)

        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
            patch.dict('sys.modules', {'boto3': mock_boto3}),
        ):
            get_aws_session()

        # boto3.Session was called with STS creds + region
        mock_boto3.Session.assert_called_once()
        call_kwargs = mock_boto3.Session.call_args[1]
        self.assertEqual(call_kwargs['aws_access_key_id'], 'AKIAFAKE')
        self.assertEqual(call_kwargs['aws_secret_access_key'], 'secret')
        self.assertEqual(call_kwargs['aws_session_token'], 'session')
        self.assertEqual(call_kwargs['region_name'], 'ap-southeast-2')

    def test_logins_map_uses_id_token(self):
        valid_id_token = _make_jwt({"exp": time.time() + 3600, "aud": "scientist_client_id"})
        creds = {"access_token": _make_jwt({"exp": time.time() + 3600}), "id_token": valid_id_token}

        mock_ci = _make_cognito_identity_mock()
        mock_boto3 = _make_boto3_mock(mock_ci)

        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
            patch.dict('sys.modules', {'boto3': mock_boto3}),
        ):
            get_aws_session()

        logins = mock_ci.get_id.call_args[1]['Logins']
        provider_key = 'cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_FAKE'
        self.assertIn(provider_key, logins)
        self.assertEqual(logins[provider_key], valid_id_token)


class TestGetAwsSessionConfigErrors(unittest.TestCase):
    def test_raises_config_incomplete_missing_identity_pool(self):
        config = {**_FULL_CONFIG, 'identity_pool_id': ''}
        with patch('nshm_toshi_client.config.load_cognito_config', return_value=config):
            with self.assertRaises(ConfigIncompleteError) as ctx:
                get_aws_session()
        self.assertIn('identity_pool_id', ctx.exception.missing)

    def test_raises_config_incomplete_multiple_missing(self):
        config = {**_FULL_CONFIG, 'region': '', 'user_pool_id': ''}
        with patch('nshm_toshi_client.config.load_cognito_config', return_value=config):
            with self.assertRaises(ConfigIncompleteError) as ctx:
                get_aws_session()
        self.assertIn('region', ctx.exception.missing)
        self.assertIn('user_pool_id', ctx.exception.missing)

    def test_config_incomplete_error_message_contains_key_name(self):
        config = {**_FULL_CONFIG, 'identity_pool_id': ''}
        with patch('nshm_toshi_client.config.load_cognito_config', return_value=config):
            with self.assertRaises(ConfigIncompleteError) as ctx:
                get_aws_session()
        self.assertIn('identity_pool_id', str(ctx.exception))


class TestGetAwsSessionCredentialErrors(unittest.TestCase):
    def test_raises_no_credentials_when_missing(self):
        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value={}),
        ):
            with self.assertRaises(NoCredentialsError):
                get_aws_session()

    def test_raises_no_credentials_when_id_token_absent(self):
        # access_token present but no id_token
        valid_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": valid_token}
        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
        ):
            with self.assertRaises(NoCredentialsError):
                get_aws_session()

    def test_raises_refresh_failed_when_token_expired_no_refresh(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        creds = {"access_token": expired_token}
        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
        ):
            with self.assertRaises(RefreshFailedError):
                get_aws_session()


class TestGetAwsSessionRefreshOnExpiry(unittest.TestCase):
    def test_refreshes_expired_token_and_federates(self):
        expired_token = _make_jwt({"exp": time.time() - 100})
        new_access = _make_jwt({"exp": time.time() + 3600})
        new_id = _make_jwt({"exp": time.time() + 3600, "aud": "scientist_client_id"})
        creds = {"access_token": expired_token, "id_token": expired_token, "refresh_token": "refresh_tok"}

        refresh_response = MagicMock()
        refresh_response.read.return_value = json.dumps({
            "access_token": new_access,
            "id_token": new_id,
            "expires_in": 3600,
        }).encode()
        refresh_response.__enter__ = lambda s: s
        refresh_response.__exit__ = MagicMock(return_value=False)

        mock_ci = _make_cognito_identity_mock()
        mock_boto3 = _make_boto3_mock(mock_ci)

        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
            patch('nshm_toshi_client.auth.save_credentials'),
            patch('nshm_toshi_client.auth.urllib_request.urlopen', return_value=refresh_response),
            patch.dict('sys.modules', {'boto3': mock_boto3}),
        ):
            get_aws_session()

        # Verify the new id_token (post-refresh) was used in the Logins map
        logins = mock_ci.get_id.call_args[1]['Logins']
        provider_key = 'cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_FAKE'
        self.assertEqual(logins[provider_key], new_id)


class TestGetAwsSessionIdentityPoolError(unittest.TestCase):
    def test_wraps_client_error_as_identity_pool_error(self):
        valid_id_token = _make_jwt({"exp": time.time() + 3600})
        creds = {"access_token": _make_jwt({"exp": time.time() + 3600}), "id_token": valid_id_token}

        mock_ci = MagicMock()
        error = botocore.exceptions.ClientError(
            {'Error': {'Code': 'NotAuthorizedException', 'Message': 'Missing aud'}},
            'GetId',
        )
        mock_ci.get_id.side_effect = error
        mock_boto3 = _make_boto3_mock(mock_ci)

        with (
            patch('nshm_toshi_client.config.load_cognito_config', return_value=_FULL_CONFIG),
            patch('nshm_toshi_client.auth.load_credentials', return_value=creds),
            patch.dict('sys.modules', {'boto3': mock_boto3}),
        ):
            with self.assertRaises(IdentityPoolError):
                get_aws_session()


class TestExceptionHierarchy(unittest.TestCase):
    def test_all_subclass_cognito_auth_error(self):
        from nshm_toshi_client.aws import CognitoAuthError

        self.assertTrue(issubclass(NoCredentialsError, CognitoAuthError))
        self.assertTrue(issubclass(RefreshFailedError, CognitoAuthError))
        self.assertTrue(issubclass(ConfigIncompleteError, CognitoAuthError))
        self.assertTrue(issubclass(IdentityPoolError, CognitoAuthError))

    def test_config_incomplete_stores_missing_list(self):
        exc = ConfigIncompleteError(['region', 'identity_pool_id'])
        self.assertEqual(exc.missing, ['region', 'identity_pool_id'])
        self.assertIn('region', str(exc))
        self.assertIn('identity_pool_id', str(exc))


if __name__ == "__main__":
    unittest.main()
