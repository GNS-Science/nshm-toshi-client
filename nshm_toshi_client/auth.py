import base64
import json
import logging
import threading
import time
from pathlib import Path
from urllib import parse
from urllib import request as urllib_request

from requests.auth import AuthBase

CREDENTIALS_PATH = Path.home() / '.toshi' / 'credentials'

logger = logging.getLogger(__name__)


class ToshiTokenManager:
    """Fetches and auto-refreshes Cognito M2M (client_credentials) tokens.

    Tokens are cached and re-fetched transparently when within 60 seconds of
    expiry, so long-running jobs (24h+) never need to manage token lifetime.

    Thread-safe: a single instance can be shared across threads.
    """

    def __init__(self, client_id: str, client_secret: str, cognito_domain: str):
        """
        Args:
            client_id: Cognito automation app client ID
            client_secret: Cognito automation app client secret
            cognito_domain: Cognito hosted UI domain,
                e.g. https://toshi-auth.xxx.auth.ap-southeast-2.amazoncognito.com
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._domain = cognito_domain.rstrip('/')
        self._token: str | None = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        """Return a valid access token, fetching a new one if needed."""
        with self._lock:
            if time.time() > self._expires_at - 60:
                self._fetch()
            if self._token is None:
                raise RuntimeError("ToshiTokenManager: token fetch returned no access_token")
            return self._token

    def _fetch(self) -> None:
        creds = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
        body = parse.urlencode(
            {
                "grant_type": "client_credentials",
                "scope": "toshi/read toshi/write",
            }
        ).encode()
        req = urllib_request.Request(
            f"{self._domain}/oauth2/token",
            data=body,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        logger.debug("ToshiTokenManager: fetching new M2M token from %s", self._domain)
        with urllib_request.urlopen(req) as resp:
            data = json.loads(resp.read())
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        logger.debug("ToshiTokenManager: token acquired, expires in %ss", data["expires_in"])


class ToshiM2MAuth(AuthBase):
    """requests.AuthBase that injects a fresh Bearer token before every request.

    Pass an instance to requests.Session.auth so that token refresh is
    completely transparent to the caller.
    """

    def __init__(self, token_manager: ToshiTokenManager):
        self._manager = token_manager

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self._manager.get_token()}"
        return r


# ---------------------------------------------------------------------------
# JWT helpers (no signature verification — authorizer does that)
# ---------------------------------------------------------------------------


def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verifying signature (for display/expiry checks only)."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('Invalid JWT format')
    payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))


def is_token_expired(token: str, buffer_seconds: int = 60) -> bool:
    """Return True if token expires within buffer_seconds."""
    try:
        payload = decode_jwt_payload(token)
        exp = payload.get('exp', 0)
        return time.time() >= (exp - buffer_seconds)
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Credential file helpers (~/.toshi/credentials)
# ---------------------------------------------------------------------------


def load_credentials() -> dict:
    """Load saved credentials from ~/.toshi/credentials, or return {} if missing."""
    if not CREDENTIALS_PATH.exists():
        return {}
    with open(CREDENTIALS_PATH) as f:
        return json.load(f)


def save_credentials(data: dict) -> None:
    """Write credentials to ~/.toshi/credentials with restricted permissions."""
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.parent.chmod(0o700)
    with open(CREDENTIALS_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    CREDENTIALS_PATH.chmod(0o600)


# ---------------------------------------------------------------------------
# Interactive/scientist auth (refresh_token grant via OAuth2 token endpoint)
# ---------------------------------------------------------------------------


class ToshiCredentialAuth(AuthBase):
    """requests.AuthBase for interactive/scientist use.

    Reads ~/.toshi/credentials (written by ``toshi-auth login``),
    auto-refreshes via OAuth2 refresh_token grant when the access token
    is within 60 seconds of expiry.

    Thread-safe: a single instance can be shared across threads.
    """

    def __init__(self, cognito_domain: str, scientist_client_id: str):
        self._domain = cognito_domain.rstrip('/')
        if not self._domain.startswith('https://'):
            self._domain = f'https://{self._domain}'
        self._client_id = scientist_client_id
        self._lock = threading.Lock()

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self._get_token()}"
        return r

    def _get_token(self) -> str:
        with self._lock:
            creds = load_credentials()
            access_token = creds.get('access_token', '')
            if not access_token:
                raise RuntimeError("No credentials found. Run: toshi-auth login")
            if is_token_expired(access_token):
                refresh_tok = creds.get('refresh_token', '')
                if not refresh_tok:
                    raise RuntimeError("Token expired and no refresh token. Run: toshi-auth login")
                logger.debug("ToshiCredentialAuth: refreshing expired token")
                creds = self._refresh(refresh_tok, creds)
                save_credentials(creds)
                access_token = creds['access_token']
            return access_token

    def _refresh(self, refresh_tok: str, creds: dict) -> dict:
        body = parse.urlencode(
            {
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "refresh_token": refresh_tok,
            }
        ).encode()
        req = urllib_request.Request(
            f"{self._domain}/oauth2/token",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib_request.urlopen(req) as resp:
            data = json.loads(resp.read())
        creds['access_token'] = data['access_token']
        if 'id_token' in data:
            creds['id_token'] = data['id_token']
        creds['expires_at'] = time.time() + data.get('expires_in', 3600)
        if 'refresh_token' in data:
            creds['refresh_token'] = data['refresh_token']
        logger.debug("ToshiCredentialAuth: token refreshed, expires in %ss", data.get('expires_in', 3600))
        return creds
