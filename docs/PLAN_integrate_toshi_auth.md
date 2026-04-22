# Plan: Integrate toshi_auth into nshm-toshi-client

## Context

`toshi_auth.py` currently lives in the API repo (`nshm-toshi-api/auth/`) but is a client-side
tool. All consumers — scientists running local Runzi scripts and Batch jobs — use
`nshm-toshi-client`. Moving auth into the library means:

- Scientists get `toshi_auth` CLI by installing the client package
- `ToshiClientBase` auto-detects `~/.toshi/credentials` for interactive users — no app code changes
- Auth logic lives in one place, not split across repos
- M2M (already implemented) and interactive auth share the same transport abstraction

---

## New Dependencies

Add to `pyproject.toml` `[tool.poetry.dependencies]`:

```toml
boto3 = ">=1.26"        # Cognito login (InitiateAuth), aws-creds (GetCredentialsForIdentity)
click = ">=8.0"         # CLI entry point
python-dotenv = ">=1.0" # load .env for local dev compat
```

---

## Files to Create / Modify

### Modify: `nshm_toshi_client/auth.py`

Add `ToshiCredentialAuth` — reads `~/.toshi/credentials`, auto-refreshes via OAuth2
`refresh_token` grant (no boto3 needed for refresh — uses same urllib pattern as
`ToshiTokenManager._fetch()`).

```python
CREDENTIALS_PATH = Path.home() / ".toshi" / "credentials"

class ToshiCredentialAuth(AuthBase):
    """requests.AuthBase for interactive/scientist use.

    Reads ~/.toshi/credentials, auto-refreshes via OAuth2 refresh_token grant.
    Requires NZSHM22_TOSHI_COGNITO_DOMAIN and NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID.
    """

    def __init__(self, cognito_domain: str, scientist_client_id: str):
        self._domain = cognito_domain.rstrip('/')
        self._client_id = scientist_client_id

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self._get_token()}"
        return r

    def _get_token(self) -> str:
        creds = self._load()
        if _is_token_expired(creds["access_token"], buffer_seconds=60):
            creds = self._refresh(creds["refresh_token"])
            self._save(creds)
        return creds["access_token"]

    def _load(self) -> dict:
        # read JSON from CREDENTIALS_PATH

    def _refresh(self, refresh_tok: str) -> dict:
        # POST {domain}/oauth2/token
        # grant_type=refresh_token, client_id=..., refresh_token=...
        # returns dict with access_token, id_token, expires_in

    def _save(self, creds: dict) -> None:
        # write JSON to CREDENTIALS_PATH, mode 0o600
```

Also extract shared helpers from `toshi_auth.py`:
- `_is_token_expired(token, buffer_seconds)` — decode JWT payload, check `exp` claim
- `CREDENTIALS_PATH` constant

### Modify: `nshm_toshi_client/config.py`

Add env var for scientist app client (separate from automation client):

```python
COGNITO_SCIENTIST_CLIENT_ID = os.getenv('NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID', '')
```

### Modify: `nshm_toshi_client/toshi_client_base.py`

Extend auto-detection. New priority order in `__init__`:

| Priority | Condition | Auth used |
|----------|-----------|-----------|
| 1 | Explicit `token_manager=` param | `ToshiM2MAuth(token_manager)` |
| 2 | `COGNITO_CLIENT_ID` + `_SECRET` + `_DOMAIN` all set | Auto `ToshiTokenManager` (M2M) |
| 3 | `CREDENTIALS_PATH` exists + `COGNITO_DOMAIN` + `COGNITO_SCIENTIST_CLIENT_ID` set | `ToshiCredentialAuth` (interactive) |
| 4 | Explicit `headers=` | Static headers as-is |
| 5 | Explicit `auth_token=` | Static `Bearer {token}` |

```python
elif CREDENTIALS_PATH.exists() and COGNITO_DOMAIN and COGNITO_SCIENTIST_CLIENT_ID:
    logger.debug("ToshiClientBase: auto-configuring interactive auth from ~/.toshi/credentials")
    auth = ToshiCredentialAuth(COGNITO_DOMAIN, COGNITO_SCIENTIST_CLIENT_ID)
    transport = RequestsHTTPTransport(url=url, auth=auth, use_json=True, retries=retries, timeout=timeout)
```

### New: `nshm_toshi_client/cli.py`

Move `toshi_auth.py` here. Update imports to use shared helpers from `auth.py`
(`_is_token_expired`, `CREDENTIALS_PATH`). Keep all 5 commands unchanged:

| Command | Description |
|---------|-------------|
| `toshi-auth login` | Username/password → `USER_PASSWORD_AUTH` via boto3 → `~/.toshi/credentials` |
| `toshi-auth token [--raw]` | Print current Bearer token, auto-refresh if needed |
| `toshi-auth whoami` | Decode and display JWT claims |
| `toshi-auth m2m-token [--raw]` | Client credentials grant for automation |
| `toshi-auth aws-creds [--profile]` | Exchange Cognito token for STS creds → `~/.aws/credentials` |

### Modify: `pyproject.toml`

Add CLI entry point:

```toml
[tool.poetry.scripts]
toshi-auth = "nshm_toshi_client.cli:cli"
```

---

## New Env Vars

| Variable | Who sets it | Purpose |
|----------|-------------|---------|
| `NZSHM22_TOSHI_COGNITO_CLIENT_ID` | Batch job def / CI | M2M token fetch |
| `NZSHM22_TOSHI_COGNITO_CLIENT_SECRET` | Secrets Manager / CI secret | M2M token fetch |
| `NZSHM22_TOSHI_COGNITO_DOMAIN` | Both contexts | OAuth2 token endpoint URL |
| `NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID` | Scientist local `.env` | Credential refresh (interactive) |

---

## Tests

### New: `tests/test_credential_auth.py`

1. `test_uses_valid_token_from_credentials_file` — mock credentials file with non-expired
   token; assert Bearer header set correctly, no refresh call made
2. `test_refreshes_expired_token` — mock credentials file with expired token; mock OAuth2
   refresh endpoint; assert new token used and credentials file updated
3. `test_toshi_client_base_auto_detects_credentials_file` — set
   `NZSHM22_TOSHI_COGNITO_DOMAIN` + `NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID` env vars,
   mock credentials file; assert `ToshiCredentialAuth` wired in automatically and
   correct `Authorization` header sent

---

## What Changes in nshm-toshi-api

Once `nshm-toshi-client` is released with the CLI:

- `auth/toshi_auth.py` can be removed or replaced with a deprecation notice pointing
  to `toshi-auth` (the library's CLI entry point)
- `auth/README.md` updated to reference `toshi-auth` command from the client package

---

## Verification

```bash
# Install with new deps
poetry install

# Run full test suite
poetry run pytest tests/ -v

# Smoke test CLI
poetry run toshi-auth login
poetry run toshi-auth whoami
poetry run toshi-auth token --raw

# Verify auto-detection: with ~/.toshi/credentials present and env vars set,
# constructing ToshiClientBase with no explicit auth should use ToshiCredentialAuth
python -c "
from nshm_toshi_client.toshi_client_base import ToshiClientBase
c = ToshiClientBase('http://localhost:5000/graphql', auth_token=None, with_schema_validation=False)
print('transport auth:', type(c._client.transport.auth))
"
```
