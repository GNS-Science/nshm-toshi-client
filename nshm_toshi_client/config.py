import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

API_URL = os.getenv('NZSHM22_TOSHI_API_URL', "http://127.0.0.1:5000/graphql")
S3_URL = os.getenv('NZSHM22_TOSHI_S3_URL', "http://localhost:4569")
API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")

# M2M JWT auth (Cognito client credentials grant)
COGNITO_DOMAIN = os.getenv('NZSHM22_TOSHI_COGNITO_DOMAIN', '')

# Interactive/scientist auth (Cognito user pool)
COGNITO_SCIENTIST_CLIENT_ID = os.getenv('NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID', '')
COGNITO_REGION = os.getenv('NZSHM22_TOSHI_COGNITO_REGION', 'ap-southeast-2')
COGNITO_USER_POOL_ID = os.getenv('NZSHM22_TOSHI_COGNITO_USER_POOL_ID', '')


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


def load_cognito_config() -> dict:
    """Resolve the Cognito config from env vars, with JSON-file fallback.

    Env vars take precedence over the file on a per-key basis: if the env var
    is set, it wins; if not, the corresponding key from the JSON file is used.

    Used by both `toshi-auth` (CLI) and `ToshiClientBase` (runtime) so a
    scientist who set up `~/.toshi/auth_config.json` does not also have to
    export the matching env vars.

    Returns a dict with keys: cognito_domain, scientist_client_id, region,
    user_pool_id. May also include `identity_pool_id` if present in the file
    (needed by `toshi-auth aws-creds`). Missing values are empty strings,
    except region which defaults to 'ap-southeast-2'.
    """
    config = {
        'cognito_domain': os.getenv('NZSHM22_TOSHI_COGNITO_DOMAIN', ''),
        'scientist_client_id': os.getenv('NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID', ''),
        'region': os.getenv('NZSHM22_TOSHI_COGNITO_REGION', ''),
        'user_pool_id': os.getenv('NZSHM22_TOSHI_COGNITO_USER_POOL_ID', ''),
    }

    if not all(config[k] for k in ('cognito_domain', 'scientist_client_id', 'region', 'user_pool_id')):
        file_config = _load_config_file()
        if file_config:
            for key in ('cognito_domain', 'scientist_client_id', 'region', 'user_pool_id'):
                if not config[key] and file_config.get(key):
                    config[key] = file_config[key]
            if file_config.get('identity_pool_id'):
                config['identity_pool_id'] = file_config['identity_pool_id']

    if not config['region']:
        config['region'] = 'ap-southeast-2'
    return config
