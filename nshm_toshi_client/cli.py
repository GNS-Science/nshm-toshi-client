"""
Toshi Auth CLI — scientist and automation token management.

Usage:
    toshi-auth login         # Username/password login, saves token to ~/.toshi/credentials
    toshi-auth logout        # Delete saved credentials
    toshi-auth token         # Print current Bearer token (auto-refresh)
    toshi-auth whoami        # Decode and display JWT claims
    toshi-auth aws-creds     # Exchange token for AWS STS credentials

Token storage:
    ~/.toshi/credentials (JSON)
    ~/.aws/credentials [toshi] (via aws-creds command)

Configuration:
    Reads ~/.toshi/auth_config.json or TOSHI_COGNITO_CONFIG env var,
    falling back to NZSHM22_TOSHI_COGNITO_* env vars.

Install:
    pip install nshm-toshi-client[cli]
"""

try:
    import click
except ImportError:
    raise SystemExit("toshi-auth requires the 'cli' extra. Install with: pip install nshm-toshi-client[cli]") from None

import base64
import configparser
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    import boto3

from nshm_toshi_client.auth import (
    CREDENTIALS_PATH,
    decode_jwt_payload,
    is_token_expired,
    load_credentials,
    save_credentials,
)
from nshm_toshi_client.aws import (
    ConfigIncompleteError,
    IdentityPoolError,
    NoCredentialsError,
    RefreshFailedError,
    get_aws_session,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# boto3 is an optional dependency (cli extra). Import here so it lands in
# sys.modules when available; callers fetch it via _get_boto3() so that
# tests can inject a mock via patch.dict('sys.modules', {'boto3': ...}).
try:
    import boto3  # noqa: F401
except ImportError:
    pass


def _get_boto3():
    """Return the boto3 module, or raise a ClickException if unavailable."""
    mod = sys.modules.get('boto3')
    if mod is None:
        raise click.ClickException("This command requires boto3. Install with: pip install nshm-toshi-client[cli]")
    return mod


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_auth_config() -> dict:
    """Load Cognito config for use by the CLI.

    Delegates resolution to `config.load_cognito_config`, which checks
    NZSHM22_TOSHI_COGNITO_* env vars first and falls back to a JSON file at
    `TOSHI_COGNITO_CONFIG` or `~/.toshi/auth_config.json`.

    Raises `click.ClickException` if no usable config is found (the runtime
    `ToshiClientBase` returns an empty dict in the same situation).
    """
    from nshm_toshi_client.config import load_cognito_config

    config = load_cognito_config()

    if not config.get('scientist_client_id'):
        raise click.ClickException(
            'No auth config found.\n'
            'Either:\n'
            '  - copy docs/auth_config.example.json to ~/.toshi/auth_config.json and edit it,\n'
            '  - set TOSHI_COGNITO_CONFIG to a config file path, or\n'
            '  - set the NZSHM22_TOSHI_COGNITO_* env vars (at minimum\n'
            '    NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID and NZSHM22_TOSHI_COGNITO_REGION).'
        )

    # boto3 cognito clients want the bare hostname, not the https:// URL.
    if config.get('cognito_domain'):
        config['cognito_domain'] = config['cognito_domain'].removeprefix('https://')
    return config


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no requests dep for this CLI)
# ---------------------------------------------------------------------------


def http_post_form(url: str, data: dict, auth: tuple[str, str] | None = None) -> dict:
    """POST application/x-www-form-urlencoded, return parsed JSON."""
    body = urlencode(data).encode()
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if auth:
        credentials = base64.b64encode(f'{auth[0]}:{auth[1]}'.encode()).decode()
        headers['Authorization'] = f'Basic {credentials}'
    req = Request(url, data=body, headers=headers, method='POST')
    with urlopen(req) as resp:
        return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Username / Password flow (USER_PASSWORD_AUTH via Cognito InitiateAuth API)
# ---------------------------------------------------------------------------


def password_flow_login(config: dict) -> dict:
    """Authenticate with email + password via Cognito USER_PASSWORD_AUTH."""
    boto3 = _get_boto3()

    region = config['region']
    client_id = config['scientist_client_id']

    email = click.prompt('Email')
    password = click.prompt('Password', hide_input=True)

    cognito = boto3.client('cognito-idp', region_name=region)
    try:
        resp = cognito.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': email, 'PASSWORD': password},
            ClientId=client_id,
        )
    except cognito.exceptions.NotAuthorizedException:
        raise click.ClickException('Invalid username or password.') from None
    except cognito.exceptions.UserNotFoundException:
        raise click.ClickException('User not found.') from None
    except Exception as e:
        raise click.ClickException(f'Authentication failed: {e}') from None

    if 'ChallengeName' in resp:
        raise click.ClickException(f'Unexpected auth challenge: {resp["ChallengeName"]}. Contact your administrator.')

    auth = resp['AuthenticationResult']
    return {
        'access_token': auth['AccessToken'],
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'token_type': auth.get('TokenType', 'Bearer'),
        'expires_in': auth.get('ExpiresIn', 3600),
    }


def refresh_token(config: dict, refresh_tok: str) -> dict:
    """Use refresh token to get a new access token via Cognito InitiateAuth."""
    boto3 = _get_boto3()

    region = config['region']
    client_id = config['scientist_client_id']

    cognito = boto3.client('cognito-idp', region_name=region)
    resp = cognito.initiate_auth(
        AuthFlow='REFRESH_TOKEN_AUTH',
        AuthParameters={'REFRESH_TOKEN': refresh_tok},
        ClientId=client_id,
    )
    auth = resp['AuthenticationResult']
    return {
        'access_token': auth['AccessToken'],
        'id_token': auth.get('IdToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
    }


# ---------------------------------------------------------------------------
# AWS Credentials flow (Cognito Identity Pool -> STS)
# ---------------------------------------------------------------------------


def get_aws_credentials(session: "boto3.Session", profile: str = 'toshi') -> str:
    """Write STS credentials from a boto3 Session to ~/.aws/credentials.

    The Session is produced by ``nshm_toshi_client.aws.get_aws_session()``,
    which handles the Cognito Identity Pool federation.  Keeping these two
    steps separate lets non-CLI callers use the Session directly without
    touching the credentials file.
    """
    frozen = session.get_credentials().get_frozen_credentials()
    region = session.region_name

    click.echo(f'  AccessKeyId: {frozen.access_key}')

    aws_credentials_path = Path.home() / '.aws' / 'credentials'
    aws_credentials_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = ''
    if aws_credentials_path.exists():
        with open(aws_credentials_path) as f:
            config_content = f.read()

    parser = configparser.ConfigParser()
    parser.read_string(config_content)

    if profile not in parser.sections():
        parser.add_section(profile)
    parser.set(profile, 'aws_access_key_id', frozen.access_key)
    parser.set(profile, 'aws_secret_access_key', frozen.secret_key)
    parser.set(profile, 'aws_session_token', frozen.token)
    parser.set(profile, 'region', region)

    with open(aws_credentials_path, 'w') as f:
        parser.write(f)

    aws_credentials_path.chmod(0o600)

    return profile


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Toshi API auth helper — manage JWT tokens for nshm-toshi-api."""


@cli.command()
def login():
    """Login with email and password (works from SSH terminals and local machines)."""
    config = load_auth_config()
    token_resp = password_flow_login(config)

    creds = load_credentials()
    creds['access_token'] = token_resp['access_token']
    creds['id_token'] = token_resp.get('id_token', '')
    creds['refresh_token'] = token_resp.get('refresh_token', '')
    creds['token_type'] = token_resp.get('token_type', 'Bearer')
    creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
    save_credentials(creds)

    payload = decode_jwt_payload(token_resp['access_token'])
    click.echo(f'\nLogged in as: {payload.get("username") or payload.get("sub", "unknown")}')
    click.echo(f'Scopes: {payload.get("scope", "none")}')
    exp = payload.get('exp', 0)
    click.echo(f'Expires: {datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}')
    click.echo(f'\nToken saved to: {CREDENTIALS_PATH}')


@cli.command()
def logout():
    """Delete the saved credentials at ~/.toshi/credentials."""
    if CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()
        click.echo(f'Logged out. Removed {CREDENTIALS_PATH}')
    else:
        click.echo('Already logged out (no credentials file found).')


@cli.command()
@click.option('--raw', is_flag=True, help='Print just the raw token string')
def token(raw):
    """Print current Bearer token, auto-refreshing if expired."""
    config = load_auth_config()
    creds = load_credentials()

    access_token = creds.get('access_token', '')
    refresh_tok = creds.get('refresh_token', '')

    if not access_token:
        raise click.ClickException('Not logged in. Run: toshi-auth login')

    if is_token_expired(access_token):
        if not refresh_tok:
            raise click.ClickException('Token expired and no refresh token. Run: toshi-auth login')
        click.echo('Token expired, refreshing...', err=True)
        try:
            token_resp = refresh_token(config, refresh_tok)
            access_token = token_resp['access_token']
            creds['access_token'] = access_token
            creds['id_token'] = token_resp.get('id_token', '')
            creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
            if 'refresh_token' in token_resp:
                creds['refresh_token'] = token_resp['refresh_token']
            save_credentials(creds)
        except Exception as e:
            raise click.ClickException(f'Token refresh failed: {e}. Run: toshi-auth login') from None

    if raw:
        click.echo(access_token)
    else:
        click.echo(f'Bearer {access_token}')


@cli.command()
def whoami():
    """Decode and display JWT claims (user, scopes, expiry)."""
    creds = load_credentials()
    access_token = creds.get('access_token', '')

    if not access_token:
        raise click.ClickException('Not logged in. Run: toshi-auth login')

    payload = decode_jwt_payload(access_token)
    expired = is_token_expired(access_token, buffer_seconds=0)

    click.echo('\n=== Token Info ===')
    click.echo(f'Subject (sub):  {payload.get("sub", "n/a")}')
    click.echo(f'Username:       {payload.get("username") or payload.get("cognito:username", "n/a")}')
    click.echo(f'Issuer (iss):   {payload.get("iss", "n/a")}')
    click.echo(f'Audience (aud): {payload.get("aud") or payload.get("client_id", "n/a")}')
    click.echo(f'Scopes:         {payload.get("scope", "none")}')
    click.echo(f'Token use:      {payload.get("token_use", "n/a")}')

    exp = payload.get('exp', 0)
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
    status = 'EXPIRED' if expired else 'valid'
    click.echo(f'Expires:        {exp_dt.isoformat()} [{status}]')

    iat = payload.get('iat', 0)
    if iat:
        iat_dt = datetime.fromtimestamp(iat, tz=timezone.utc)
        click.echo(f'Issued at:      {iat_dt.isoformat()}')

    click.echo(f'\nGroups:         {payload.get("cognito:groups", [])}')


@cli.command('aws-creds')
@click.option('--profile', default='toshi', help='AWS credentials profile name', show_default=True)
def aws_creds(profile):
    """Exchange Cognito token for AWS STS credentials and write to ~/.aws/credentials.

    For in-process Python callers, use ``nshm_toshi_client.aws.get_aws_session()``
    directly — this command exists for shells, the ``aws`` CLI, and tools that
    already use the boto3 default credential chain.
    """
    click.echo('Getting AWS credentials via Identity Pool...')
    try:
        session = get_aws_session()
    except (NoCredentialsError, RefreshFailedError, ConfigIncompleteError) as exc:
        raise click.ClickException(f'{exc}') from None
    except IdentityPoolError as exc:
        raise click.ClickException(f'Identity Pool federation failed: {exc}') from None

    result_profile = get_aws_credentials(session, profile)

    click.echo(f'\nAWS credentials saved to profile [{result_profile}] in ~/.aws/credentials')
    click.echo(f'Use with: export AWS_PROFILE={result_profile}')
    click.echo(f'Or: aws --profile {result_profile} s3 ls')
