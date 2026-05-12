"""
Toshi Auth CLI — scientist and automation token management.

Usage:
    toshi-auth login         # Username/password login, saves token to ~/.toshi/credentials
    toshi-auth logout        # Delete saved credentials
    toshi-auth token         # Print current Bearer token (auto-refresh)
    toshi-auth whoami        # Decode and display JWT claims
    toshi-auth m2m-token     # Client credentials flow for automation/Runzi
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
    raise SystemExit(
        "toshi-auth requires the 'cli' extra. Install with: pip install nshm-toshi-client[cli]"
    ) from None

import base64
import configparser
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from nshm_toshi_client.auth import (
    CREDENTIALS_PATH,
    decode_jwt_payload,
    is_token_expired,
    load_credentials,
    save_credentials,
)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_auth_config() -> dict:
    """Load Cognito config from JSON file or env vars.

    Priority:
        1. JSON file at $TOSHI_COGNITO_CONFIG
        2. JSON file at ~/.toshi/auth_config.json
        3. NZSHM22_TOSHI_COGNITO_* env vars
    """
    config_path = os.environ.get('TOSHI_COGNITO_CONFIG', '')
    if not config_path:
        default = Path.home() / '.toshi' / 'auth_config.json'
        if default.exists():
            config_path = str(default)

    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)

    # Fall back to env vars
    from nshm_toshi_client.config import (
        COGNITO_CLIENT_ID,
        COGNITO_CLIENT_SECRET,
        COGNITO_DOMAIN,
        COGNITO_REGION,
        COGNITO_SCIENTIST_CLIENT_ID,
        COGNITO_USER_POOL_ID,
    )

    if not COGNITO_DOMAIN:
        raise click.ClickException(
            'No auth config found.\n'
            'Either place auth_config.json at ~/.toshi/auth_config.json,\n'
            'set TOSHI_COGNITO_CONFIG to a config file path,\n'
            'or set NZSHM22_TOSHI_COGNITO_* env vars.'
        )

    return {
        'region': COGNITO_REGION,
        'user_pool_id': COGNITO_USER_POOL_ID,
        'scientist_client_id': COGNITO_SCIENTIST_CLIENT_ID,
        'automation_client_id': COGNITO_CLIENT_ID,
        'automation_client_secret': COGNITO_CLIENT_SECRET,
        'cognito_domain': COGNITO_DOMAIN.removeprefix('https://'),
    }


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
    try:
        import boto3
    except ImportError:
        raise click.ClickException(
            "Login requires boto3. Install with: pip install nshm-toshi-client[cli]"
        ) from None

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
    try:
        import boto3
    except ImportError:
        raise click.ClickException(
            "Token refresh requires boto3. Install with: pip install nshm-toshi-client[cli]"
        ) from None

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
# Client Credentials flow (M2M / Runzi)
# ---------------------------------------------------------------------------


def client_credentials_flow(config: dict) -> str:
    """Obtain access token via client credentials (no user context)."""
    domain = config['cognito_domain']
    client_id = os.environ.get('TOSHI_CLIENT_ID', config.get('automation_client_id', ''))
    client_secret = os.environ.get('TOSHI_CLIENT_SECRET', config.get('automation_client_secret', ''))

    if not client_id or not client_secret:
        raise click.ClickException(
            'Automation client credentials not found.\n'
            'Set TOSHI_CLIENT_ID and TOSHI_CLIENT_SECRET in .env,\n'
            'or configure automation_client_id/secret in auth_config.json.'
        )

    token_url = f'https://{domain}/oauth2/token'
    scopes = 'toshi/read toshi/write'

    resp = http_post_form(
        token_url,
        {
            'grant_type': 'client_credentials',
            'scope': scopes,
        },
        auth=(client_id, client_secret),
    )

    if 'access_token' not in resp:
        raise click.ClickException(f'Token error: {resp}')

    return resp['access_token']


# ---------------------------------------------------------------------------
# AWS Credentials flow (Cognito Identity Pool -> STS)
# ---------------------------------------------------------------------------


def get_aws_credentials(config: dict, access_token: str, profile: str = 'toshi') -> str:
    """Exchange Cognito token for AWS STS credentials via Identity Pool."""
    try:
        import boto3
    except ImportError:
        raise click.ClickException(
            "AWS credentials exchange requires boto3. Install with: pip install nshm-toshi-client[cli]"
        ) from None

    region = config['region']
    identity_pool_id = config.get('identity_pool_id')

    if not identity_pool_id:
        raise click.ClickException('Identity Pool ID not found in config.')

    cognito_identity = boto3.client('cognito-identity', region_name=region)

    click.echo(f'Getting Identity ID from pool: {identity_pool_id} ...')
    resp = cognito_identity.get_id(
        IdentityPoolId=identity_pool_id,
        Logins={
            f'cognito-idp.{region}.amazonaws.com/{config["user_pool_id"]}': access_token,
        },
    )
    identity_id = resp['IdentityId']
    click.echo(f'  Identity ID: {identity_id}')

    click.echo('Getting temporary AWS credentials ...')
    resp = cognito_identity.get_credentials_for_identity(
        IdentityId=identity_id,
        Logins={
            f'cognito-idp.{region}.amazonaws.com/{config["user_pool_id"]}': access_token,
        },
    )

    creds = resp['Credentials']
    click.echo(f'  AccessKeyId: {creds["AccessKeyId"]}')
    click.echo(f'  Expires: {creds["Expiration"].astimezone(timezone.utc).isoformat()}')

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
    parser.set(profile, 'aws_access_key_id', creds['AccessKeyId'])
    parser.set(profile, 'aws_secret_access_key', creds['SecretKey'])
    parser.set(profile, 'aws_session_token', creds['SessionToken'])
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


@cli.command('m2m-token')
@click.option('--raw', is_flag=True, help='Print just the raw token string (no "Bearer " prefix)')
def m2m_token(raw):
    """Obtain M2M (machine-to-machine) token via Client Credentials for Runzi/automation."""
    config = load_auth_config()
    access_token = client_credentials_flow(config)

    payload = decode_jwt_payload(access_token)
    exp = payload.get('exp', 0)
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)

    click.echo(f'M2M token obtained. Expires: {exp_dt.isoformat()}', err=True)
    click.echo(f'Scopes: {payload.get("scope", "none")}', err=True)

    if raw:
        click.echo(access_token)
    else:
        click.echo(f'Bearer {access_token}')


@cli.command('aws-creds')
@click.option('--profile', default='toshi', help='AWS credentials profile name', show_default=True)
def aws_creds(profile):
    """Exchange Cognito token for AWS STS credentials and write to ~/.aws/credentials."""
    config = load_auth_config()
    creds = load_credentials()

    access_token = creds.get('access_token', '')
    if not access_token:
        raise click.ClickException('Not logged in. Run: toshi-auth login')

    if is_token_expired(access_token, buffer_seconds=300):
        refresh_tok = creds.get('refresh_token', '')
        if not refresh_tok:
            raise click.ClickException('Token expired and no refresh token. Run: toshi-auth login')
        click.echo('Token expired, refreshing...', err=True)
        try:
            token_resp = refresh_token(config, refresh_tok)
            access_token = token_resp['access_token']
            creds['access_token'] = access_token
            creds['expires_at'] = time.time() + token_resp.get('expires_in', 3600)
            if 'refresh_token' in token_resp:
                creds['refresh_token'] = token_resp['refresh_token']
            save_credentials(creds)
        except Exception as e:
            raise click.ClickException(f'Token refresh failed: {e}. Run: toshi-auth login') from None

    result_profile = get_aws_credentials(config, access_token, profile)

    click.echo(f'\nAWS credentials saved to profile [{result_profile}] in ~/.aws/credentials')
    click.echo(f'Use with: export AWS_PROFILE={result_profile}')
    click.echo(f'Or: aws --profile {result_profile} s3 ls')
