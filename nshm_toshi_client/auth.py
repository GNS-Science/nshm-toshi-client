import base64
import json
import logging
import threading
import time
from urllib import parse
from urllib import request as urllib_request

from requests.auth import AuthBase

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
        resp = json.loads(urllib_request.urlopen(req).read())
        self._token = resp["access_token"]
        self._expires_at = time.time() + resp["expires_in"]
        logger.debug("ToshiTokenManager: token acquired, expires in %ss", resp["expires_in"])


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
