"""Runtime configuration for the nshm-toshi-client.

Reads ``NZSHM22_TOSHI_*`` and ``COGNITO_*`` environment variables that relate
to use of the toshi API and exposes them as module-level constants consumed by
:class:`~nshm_toshi_client.toshi_client_base.ToshiClientBase` and the CLI.

``API_KEY`` resolution order
----------------------------
1. ``NZSHM22_TOSHI_API_KEY`` environment variable.
2. AWS Secrets Manager — only when ``NZSHM22_TOSHI_API_KEY`` is unset, **Cognito
   M2M is not configured** (``NZSHM22_TOSHI_M2M_SECRET_ARN`` and
   ``NZSHM22_TOSHI_COGNITO_DOMAIN`` are not both set), and the process is running
   inside an AWS Batch job (``AWS_BATCH_JOB_ID`` set).
   The secret is chosen by inspecting ``API_URL``:

   * URL contains ``TEST`` → secret ``NZSHM22_TOSHI_API_SECRET_TEST``,
     key ``NZSHM22_TOSHI_API_KEY_TEST``
   * URL contains ``PROD`` → secret ``NZSHM22_TOSHI_API_SECRET_PROD``,
     key ``NZSHM22_TOSHI_API_KEY_PROD``

   This allows AWS Batch tasks to receive the API key via IAM-controlled secrets
   rather than plain environment variables.  It is a temporary measure until M2M
   JWT auth fully replaces the legacy API key.  To test Cognito M2M auth from a
   Batch container, set ``NZSHM22_TOSHI_M2M_SECRET_ARN`` and
   ``NZSHM22_TOSHI_COGNITO_DOMAIN`` — the Secrets Manager fetch is then skipped
   automatically.

3. Empty string — Cognito JWT auth is used instead (auto-detected by
   :class:`~nshm_toshi_client.toshi_client_base.ToshiClientBase`).

Helper
------
:func:`get_auth_kwargs` returns constructor keyword arguments appropriate for the
resolved auth mode, so callers do not need to branch on whether a legacy key is
available.

:func:`load_cognito_config` resolves the Cognito config from env vars, with JSON-file fallback.
"""

import base64
import json
import logging
import os
from pathlib import Path

import boto3

logger = logging.getLogger(__name__)


def _load_config_file() -> dict | None:
    """Return parsed contents of the JSON config file, or None if not found/invalid.

    Resolves the path from the `TOSHI_COGNITO_CONFIG` env var, falling back to
    `~/.toshi/auth_config.json`.
    """
    path_str = os.getenv('TOSHI_COGNITO_CONFIG', '')
    path = Path(path_str) if path_str else Path.home() / '.toshi' / 'auth_config.json'
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read Cognito config from %s: %s", path, exc)
        return None


_COGNITO_ENV_VARS = {
    'cognito_domain': 'NZSHM22_TOSHI_COGNITO_DOMAIN',
    'scientist_client_id': 'NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID',
    'region': 'NZSHM22_TOSHI_COGNITO_REGION',
    'user_pool_id': 'NZSHM22_TOSHI_COGNITO_USER_POOL_ID',
    'identity_pool_id': 'NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID',
}
COGNITO_CONFIG_KEYS = tuple(_COGNITO_ENV_VARS)


def load_cognito_config() -> dict:
    """Resolve the Cognito config from env vars, with JSON-file fallback.

    Env vars take precedence over the file on a per-key basis: if the env var
    is set, it wins; if not, the corresponding key from the JSON file is used.

    Supported env vars:
    - ``NZSHM22_TOSHI_COGNITO_DOMAIN``
    - ``NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID``
    - ``NZSHM22_TOSHI_COGNITO_REGION``
    - ``NZSHM22_TOSHI_COGNITO_USER_POOL_ID``
    - ``NZSHM22_TOSHI_COGNITO_IDENTITY_POOL_ID``

    Used by both `toshi-auth` (CLI) and `ToshiClientBase` (runtime) so a
    scientist who set up `~/.toshi/auth_config.json` does not also have to
    export the matching env vars.

    Returns a dict with keys: cognito_domain, scientist_client_id, region,
    user_pool_id, identity_pool_id. Missing values are empty strings, except
    region which defaults to 'ap-southeast-2'.
    """
    config = {k: os.getenv(env, '') for k, env in _COGNITO_ENV_VARS.items()}

    # Always read the file so that all keys are picked up regardless of
    # which env vars are set.
    file_config = _load_config_file() or {}
    for key in _COGNITO_ENV_VARS:
        if not config[key] and file_config.get(key):
            config[key] = file_config[key]

    if not config['region']:
        config['region'] = 'ap-southeast-2'
    return config


def _get_secret(secret_name, region_name):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            return json.loads(get_secret_value_response['SecretString'])
        else:
            return base64.b64decode(get_secret_value_response['SecretBinary'])


def get_auth_kwargs() -> dict:
    """Return toshi-client constructor kwargs for the current auth mode.

    Legacy (API_KEY resolved): passes x-api-key header.
    Cognito (no API_KEY): returns {} so the client auto-detects ~/.toshi/credentials.
    """
    return {'headers': {'x-api-key': API_KEY}} if API_KEY else {}


# M2M JWT auth (Cognito client credentials grant)
COGNITO_DOMAIN = os.getenv('NZSHM22_TOSHI_COGNITO_DOMAIN', '')
M2M_SECRET_ARN = os.getenv('NZSHM22_TOSHI_M2M_SECRET_ARN', '')

# Interactive/scientist auth (Cognito user pool)
COGNITO_SCIENTIST_CLIENT_ID = os.getenv('NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID', '')
COGNITO_REGION = os.getenv('NZSHM22_TOSHI_COGNITO_REGION', 'ap-southeast-2')
COGNITO_USER_POOL_ID = os.getenv('NZSHM22_TOSHI_COGNITO_USER_POOL_ID', '')

API_URL = os.getenv('NZSHM22_TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
S3_URL = os.getenv('NZSHM22_TOSHI_S3_URL', "http://localhost:4569")
# Temporary: legacy x-api-key resolution.
# In Batch containers NZSHM22_TOSHI_API_KEY is typically absent; fetch from
# Secrets Manager on startup.  Skipped when Cognito M2M is configured
# (M2M_SECRET_ARN + COGNITO_DOMAIN both set) so Batch jobs can migrate to M2M
# by simply setting those env vars, without code changes.
API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")
if not API_KEY and not (M2M_SECRET_ARN and COGNITO_DOMAIN) and os.getenv('AWS_BATCH_JOB_ID'):
    if 'TEST' in API_URL.upper():
        API_KEY = _get_secret("NZSHM22_TOSHI_API_SECRET_TEST", "us-east-1").get("NZSHM22_TOSHI_API_KEY_TEST")
    elif 'PROD' in API_URL.upper():
        API_KEY = _get_secret("NZSHM22_TOSHI_API_SECRET_PROD", "us-east-1").get("NZSHM22_TOSHI_API_KEY_PROD")
