# Usage

## Authentication

There are three ways to authenticate with the Toshi API, listed in priority order.
`ToshiClientBase` auto-detects the method based on what is configured.

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

The Secrets Manager fetch happens once at construction; Cognito access tokens
are refreshed transparently from there. Long-running jobs (24h+) never need
to manage token lifetime.

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

First install the CLI and log in:

```bash
pip install nshm-toshi-client[cli]
toshi-auth login
```

This saves tokens to `~/.toshi/credentials`. Then set these env vars:

```bash
export NZSHM22_TOSHI_API_URL=https://example-api-url.com/graphql
export NZSHM22_TOSHI_COGNITO_DOMAIN=https://toshi-auth.example.auth.ap-southeast-2.amazoncognito.com
export NZSHM22_TOSHI_COGNITO_SCIENTIST_CLIENT_ID=your_scientist_client_id
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

### 3. API key (legacy)

```bash
export NZSHM22_TOSHI_API_URL=https://example-api-url.com/graphql
export NZSHM22_TOSHI_API_KEY=your-api-key
export NZSHM22_TOSHI_S3_URL=https://example-s3-url.com
```

```python
from nshm_toshi_client import ToshiFile, API_URL, API_KEY, S3_URL

headers = {"x-api-key": API_KEY}
api = ToshiFile(API_URL, S3_URL, None, headers=headers)
file = api.get_file("{example_id}")
```

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
| `toshi-auth m2m-token [--raw]` | Obtain M2M token via client credentials grant |
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
