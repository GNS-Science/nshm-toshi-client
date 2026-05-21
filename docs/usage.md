# Usage

## Authentication

There are three ways to authenticate with the Toshi API, listed in priority order.
`ToshiClientBase` auto-detects the method based on what is configured:

1. M2M — used when `NZSHM22_TOSHI_M2M_SECRET_ARN` and `NZSHM22_TOSHI_COGNITO_DOMAIN` are both set.
2. Interactive scientist — used when `~/.toshi/credentials` exists and the Cognito domain + scientist client ID are configured (via `~/.toshi/auth_config.json` or the matching `NZSHM22_TOSHI_COGNITO_*` env vars).
3. Legacy API key — **not auto-detected**; you must pass `headers={"x-api-key": ...}` explicitly.

If both M2M env vars and `~/.toshi/credentials` are present on the same machine, M2M wins.
`ToshiClientBase` logs a warning when auto-detection overrides an explicit `auth_token` or `headers` argument.

### 1. M2M (machine-to-machine) — for automation and batch jobs

M2M credentials live in AWS Secrets Manager and are fetched at process start
using the runtime's IAM role. The secret value must be JSON:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

Grant your runtime IAM role `secretsmanager:GetSecretValue` on the secret ARN,
then set these env vars and the client configures itself automatically:

```bash
export NZSHM22_TOSHI_API_URL=https://example-api-url.com/graphql
export NZSHM22_TOSHI_COGNITO_DOMAIN=https://toshi-auth.example.auth.ap-southeast-2.amazoncognito.com
export NZSHM22_TOSHI_M2M_SECRET_ARN=arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:toshi-m2m-AbCdEf
```

```python
from nshm_toshi_client import ToshiFile

api = ToshiFile(
    "https://example-api-url.com/graphql",
    "https://example-s3-url.com",
)
file = api.get_file("{example_id}")
```

The Secrets Manager fetch happens once when `ToshiTokenManager` is constructed
(either explicitly, or implicitly by `ToshiClientBase` when auto-detecting);
Cognito access tokens are refreshed transparently from there. Long-running
jobs (24h+) never need to manage token lifetime.

You can also pass a `ToshiTokenManager` explicitly:

```python
from nshm_toshi_client.auth import ToshiTokenManager
from nshm_toshi_client import ToshiFile

mgr = ToshiTokenManager(
    cognito_domain="https://toshi-auth.example.auth.ap-southeast-2.amazoncognito.com",
    secret_arn="arn:aws:secretsmanager:ap-southeast-2:123456789012:secret:toshi-m2m-AbCdEf",
)
api = ToshiFile(
    "https://example-api-url.com/graphql",
    "https://example-s3-url.com",
    token_manager=mgr,
)
```

### 2. Interactive credentials — for scientists

Install the CLI:

```bash
pip install nshm-toshi-client[cli]
```

Then give the CLI the Cognito pool details. The simplest way is a JSON config file —
copy [`docs/auth_config.example.json`](auth_config.example.json) to
`~/.toshi/auth_config.json` and fill in the values for your Toshi deployment (ask
the Toshi admin if you don't have them):

```bash
mkdir -p ~/.toshi
cp auth_config.example.json ~/.toshi/auth_config.json
# then edit ~/.toshi/auth_config.json
```

Log in (you'll be prompted for email + password):

```bash
toshi-auth login
```

This saves tokens to `~/.toshi/credentials`. Both `toshi-auth` and
`ToshiClientBase` read the same `~/.toshi/auth_config.json`, so no extra
env vars are needed for Cognito auth. You still need the API URL:

```bash
export NZSHM22_TOSHI_API_URL=https://example-api-url.com/graphql
```

The client detects `~/.toshi/credentials` and refreshes tokens automatically:

```python
from nshm_toshi_client import ToshiFile

api = ToshiFile(
    "https://example-api-url.com/graphql",
    "https://example-s3-url.com",
)
file = api.get_file("{example_id}")
```

> **Alternative:** instead of `~/.toshi/auth_config.json`, you can set the
> `NZSHM22_TOSHI_COGNITO_*` env vars (domain, scientist client ID, region,
> user pool ID). Env vars take precedence over the file on a per-key basis,
> so you can mix the two (e.g. file for shared defaults, env to override
> `NZSHM22_TOSHI_COGNITO_DOMAIN` in a dev pool).

### 3. API key (legacy)

```bash
export NZSHM22_TOSHI_API_URL=https://example-api-url.com/graphql
export NZSHM22_TOSHI_API_KEY=your-api-key
export NZSHM22_TOSHI_S3_URL=https://example-s3-url.com
```

```python
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL, get_auth_kwargs

headers = {"x-api-key": API_KEY}
api = ToshiFile(API_URL, S3_URL, None, **get_auth_kwargs())
file = api.get_file("{example_id}")
```

The helper function `get_auth_kwargs()` returns the correct constructor keyword arguments for whichever auth mode is active, so callers can initialise the client without branching. When a legacy API key resolved (via env var or Secrets Manager), `get_auth_kwargs()` returns `{'headers': {'x-api-key': API_KEY}}`. Otherwise it returns `{}`, letting `ToshiClientBase` fall through to Cognito auto-detection (M2M or interactive credentials, as described above).

`nshm_toshi_client.API_KEY` provides a universal way for applications to define the API key. For local machine usage it is obtained from the `NZSHM22_TOSHI_API_KEY` environment variable. When `NZSHM22_TOSHI_API_KEY` is not set and the process is running inside an AWS Batch job (`AWS_BATCH_JOB_ID` is set), the legacy API key can be sourced automatically from AWS Secrets Manager. The secret is chosen from the API URL — URLs containing `TEST` use `NZSHM22_TOSHI_API_SECRET_TEST`; URLs containing `PROD` use `NZSHM22_TOSHI_API_SECRET_PROD`. Grant the task's IAM role `secretsmanager:GetSecretValue` on the relevant secret ARN; no extra env vars are needed. If `NZSHM22_TOSHI_M2M_SECRET_ARN` and `NZSHM22_TOSHI_COGNITO_DOMAIN` are both set, the Secrets Manager fetch is skipped entirely and the client uses Cognito M2M auth instead — set those env vars in the Batch task definition to migrate to Cognito auth without touching code.

## Scopes

Toshi API authorisation is gated by OAuth scopes defined as a **Resource
Server** in the Cognito user pool. The naming convention is
`{resource_server}/{scope}` — e.g. `toshi/read`, `toshi/write`. Scopes
themselves are deployment configuration; this client only *requests* them.

You can see what scopes the token you currently hold actually has:

```bash
toshi-auth whoami
```


### Where scopes come from

| Auth method | How scopes are chosen |
|---|---|
| **M2M** (`client_credentials` grant) | Client explicitly requests `toshi/read toshi/write`. This is **hardcoded** at `nshm_toshi_client/auth.py:72`. The automation app client in Cognito must be configured to permit those scopes, or the token request fails with `invalid_scope`. |
| **Scientist** (`USER_PASSWORD_AUTH`) | Client does **not** request scopes. Cognito returns whatever the scientist app client is configured to grant by default (set per deployment under App clients → Allowed custom scopes). |
| **Legacy API key** | Not a Cognito token — scopes don't apply; access is gated by the API key itself on the server side. |

### Testing scope behaviour

When verifying scope policy against a deployment:

- A token with only `toshi/read` should be rejected by the API on any write mutation.
- A token with no `toshi/*` scope should be rejected on every call.
- An M2M token request will fail at Cognito (not the API) if the automation app client isn't permitted the hardcoded scopes — look for `invalid_scope` in the Cognito response.
- Scientist scope changes don't require a code release — but a user already holding a token must `toshi-auth logout && toshi-auth login` to pick up the new scopes.

To find the authoritative scope definition: AWS Console → Cognito → your
user pool → App integration → **Resource servers** (defines available scopes)
and **App clients** → Allowed custom scopes (grants scopes per client).

---

## toshi-auth CLI

Install with `pip install nshm-toshi-client[cli]`.

The CLI reads config from `~/.toshi/auth_config.json`, or `TOSHI_COGNITO_CONFIG`
env var pointing to a config file, or falls back to `NZSHM22_TOSHI_COGNITO_*` env vars.

| Command | Description |
|---------|-------------|
| `toshi-auth login` | Username/password login, saves tokens to `~/.toshi/credentials` |
| `toshi-auth logout` | Delete saved credentials at `~/.toshi/credentials` |
| `toshi-auth token [--raw]` | Print current Bearer token, auto-refreshing if expired |
| `toshi-auth whoami` | Decode and display JWT claims (user, scopes, expiry) |
| `toshi-auth aws-creds [--profile]` | Exchange Cognito token for AWS STS credentials |

## Methods

### ToshiFile.get_file

```python
from nshm_toshi_client import ToshiFile

api = ToshiFile(API_URL, S3_URL)
file = api.get_file("{example_id}")
```

Example response:

```python
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426,
  'meta': {'mykey': 'myvalue', 'mykey2': 'myothervalue'}
}
```

### ToshiFile.get_file_download_url

```python
file = api.get_file_download_url("{example_id}", True)
```

Example response:

```python
{'__typename': 'InversionSolutionNrml',
  'id': 'SW52ZXJzaW9uU29sdXRpb25Ocm1sOjEwMDM0Mw==',
  'file_name': 'NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip',
  'file_size': 3331426,
  'meta': {'mykey': 'myvalue', 'mykey2': 'myothervalue'},
  'file_url': 'https://s3.amazonaws.com/toshi-files/NZSHM22_InversionSolution-QXV0b21hdGlvblRhc2s6MTAwMTA4_nrml.zip'
}
```

### ToshiFile.download_file

```python
api.download_file("{example_id}", "/tmp/downloads")
```

If successful, prints:

```
saving to /tmp/downloads/{example_id}
```

If failure, prints:

```
Download failed: status code {status_code} (eg. 404)
```
