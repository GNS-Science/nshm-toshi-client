"""Programmatic AWS-credentials helper for Cognito Identity Pool federation.

Use this module when you need a ``boto3.Session`` for **AWS service** access
(S3, Batch, SSM, …).  It is *not* used by ``ToshiClientBase``, which
authenticates to the Toshi GraphQL API using a JWT Bearer token sourced from
``~/.toshi/credentials``.

``get_aws_session()`` is the in-process equivalent of ``toshi-auth aws-creds``
(the CLI command that writes ``~/.aws/credentials``).  Both start from the same
``id_token`` in ``~/.toshi/credentials``; the CLI persists the resulting STS
credentials to disk for the ``aws`` CLI and boto3's default credential chain,
while this function returns the ``boto3.Session`` directly — no file round-trip,
typed exceptions, and token refresh handled automatically.

Typical usage::

    from nshm_toshi_client.aws import get_aws_session, CognitoAuthError

    try:
        session = get_aws_session()
        s3 = session.client('s3')
    except CognitoAuthError as exc:
        # Not logged in, refresh failed, config incomplete, etc.
        raise SystemExit(f"Re-authenticate: {exc}") from exc
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import boto3

# ---------------------------------------------------------------------------
# Exception hierarchy — defined in auth.py, re-exported here for the public API
# ---------------------------------------------------------------------------

from nshm_toshi_client.auth import (  # noqa: E402
    CognitoAuthError,
    ConfigIncompleteError,
    IdentityPoolError,
    NoCredentialsError,
    RefreshFailedError,
)

__all__ = [
    'CognitoAuthError',
    'NoCredentialsError',
    'RefreshFailedError',
    'ConfigIncompleteError',
    'IdentityPoolError',
    'get_aws_session',
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_aws_session() -> boto3.Session:
    """Return a boto3.Session whose credentials come from Cognito Identity Pool
    federation, using tokens cached by ``toshi-auth login``. Refreshes if expired.

    Raises:
        NoCredentialsError: ~/.toshi/credentials is missing or lacks id_token.
        RefreshFailedError: refresh token expired or the token endpoint rejected it.
        ConfigIncompleteError: auth_config or env vars are missing required keys.
        IdentityPoolError: cognito-identity GetId/GetCredentialsForIdentity rejected.
    """
    import boto3 as _boto3
    import botocore.exceptions

    from nshm_toshi_client.auth import ToshiCredentialAuth
    from nshm_toshi_client.config import COGNITO_CONFIG_KEYS, load_cognito_config

    # 1. Resolve config and validate all required keys are present.
    config = load_cognito_config()
    missing = [k for k in COGNITO_CONFIG_KEYS if not config.get(k)]
    if missing:
        raise ConfigIncompleteError(missing)

    region = config['region']
    user_pool_id = config['user_pool_id']
    identity_pool_id = config['identity_pool_id']

    # 2. Get a fresh id_token, refreshing if the stored token is expired.
    #    NoCredentialsError / RefreshFailedError propagate directly.
    auth = ToshiCredentialAuth(
        cognito_domain=config['cognito_domain'],
        scientist_client_id=config['scientist_client_id'],
    )
    id_token = auth.get_id_token()

    # 3. Exchange id_token for STS credentials via Cognito Identity Pool.
    logins = {f'cognito-idp.{region}.amazonaws.com/{user_pool_id}': id_token}
    cognito_identity = _boto3.client('cognito-identity', region_name=region)
    try:
        get_id_resp = cognito_identity.get_id(IdentityPoolId=identity_pool_id, Logins=logins)
        creds_resp = cognito_identity.get_credentials_for_identity(IdentityId=get_id_resp['IdentityId'], Logins=logins)
    except botocore.exceptions.ClientError as exc:
        raise IdentityPoolError(str(exc)) from exc

    aws_creds = creds_resp['Credentials']
    return _boto3.Session(
        aws_access_key_id=aws_creds['AccessKeyId'],
        aws_secret_access_key=aws_creds['SecretKey'],
        aws_session_token=aws_creds['SessionToken'],
        region_name=region,
    )
