# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**
```bash
uv sync --all-groups --all-extras
```

**Testing:**
```bash
uv run pytest tests/                          # full suite
uv run pytest tests/ -k <pattern>             # single test or subset
uv run tox                                    # full tox matrix (py310–312, lint, format, audit, build)
```

**Linting & formatting:**
```bash
uv run tox -e lint       # ruff check + mypy
uv run tox -e format     # ruff format
```

**Build:**
```bash
uv build
```

## Code Navigation

Prefer LSP over file reads and shell searches:
- `goToDefinition` / `goToImplementation` — jump to source
- `findReferences` — see all usages before renaming or changing signatures
- `workspaceSymbol` — locate where something is defined
- `documentSymbol` — list all symbols in a file
- `hover` — get type info without opening the file
- `incomingCalls` / `outgoingCalls` — trace call hierarchy

Use `grep` / `find` / `Read` only for text/pattern searches (comments, strings, config values) where LSP doesn't apply.

Check LSP diagnostics after every edit; fix type errors and missing imports immediately.

## Architecture

`nshm-toshi-client` is a GraphQL client library for the Toshi API (National Seismic Hazard Model). It manages seismic tasks, file uploads, and authentication for scientific compute jobs.

### Layered structure

**Base client** (`toshi_client_base.py`): wraps `gql.Client` with auth setup and exposes `run_query(qry, variables)`. All domain clients inherit from this.

**Domain clients** (inherit `ToshiClientBase`):
- `general_task.py` — generic task CRUD
- `rupture_generation_task.py` — rupture set upload + inversion solution management
- `strong_motion_station.py` — station data records
- `task_relation.py` — parent/child task links

**File management**:
- `toshi_file.py` — S3 upload/download + GraphQL file metadata
- `toshi_task_file.py` — links files to tasks with roles (READ/WRITE)

**Auth** (`auth.py`):
- `ToshiTokenManager` — M2M Cognito client_credentials flow, auto-refreshes tokens (fetches secret from AWS Secrets Manager via `NZSHM22_TOSHI_M2M_SECRET_ARN`)
- `ToshiCredentialAuth` — interactive refresh_token flow using `~/.toshi/credentials`
- `ToshiM2MAuth` — requests auth handler for M2M flow

**Config** (`config.py`): reads env vars (`NZSHM22_TOSHI_API_URL`, `NZSHM22_TOSHI_S3_URL`, `NZSHM22_TOSHI_API_KEY`, `NZSHM22_TOSHI_M2M_SECRET_ARN`, `NZSHM22_TOSHI_COGNITO_*`). Falls back to `localhost:5000/graphql` and `localhost:4569`.

**CLI** (`cli.py`): `toshi-auth` Click group — `login`, `logout`, `token`, `whoami`, `aws-creds`. Requires `[cli]` extra.

### Auth auto-detection (in `ToshiClientBase.__init__`)

`ToshiClientBase` authenticates to the **Toshi GraphQL API** using JWT Bearer
tokens.  Detection priority order:

1. `NZSHM22_TOSHI_M2M_SECRET_ARN` + `COGNITO_DOMAIN` → M2M token manager
2. `~/.toshi/credentials` + Cognito config → interactive credential auth
3. `auth_token` kwarg → static Bearer header
4. `headers` kwarg → passed directly

### AWS service access (`nshm_toshi_client.aws`)

For AWS service calls (S3, Batch, SSM, …) use `get_aws_session()` — separate
code path from `ToshiClientBase`:

```python
from nshm_toshi_client.aws import get_aws_session, CognitoAuthError

session = get_aws_session()          # boto3.Session with STS creds
session.client('s3').list_buckets()
```

- Returns a `boto3.Session` via Cognito Identity Pool federation using the
  `id_token` from `~/.toshi/credentials`.  Refreshes automatically if expired.
- Typed exception hierarchy: `CognitoAuthError` → `NoCredentialsError`,
  `RefreshFailedError`, `ConfigIncompleteError`, `IdentityPoolError`.
- `~/.aws/credentials` is a **sink** written by `toshi-auth aws-creds` for the
  `aws` CLI / boto3 default credential chain.  `ToshiClientBase` never reads it;
  in-process Python callers should use `get_aws_session()` directly.

### GraphQL call pattern

```python
client = RuptureGenerationTask(toshi_api_url=..., s3_url=..., token_manager=mgr)
result = client.run_query("""
    mutation ($id: ID!) { ... }
""", {"id": "abc"})
# result is None if response contains errors
```

### Testing

Tests use `pytest` + `requests_mock` for HTTP mocking and `unittest.mock` for AWS/boto3. `conftest.py` provides shared fixtures. Test files mirror the module they cover (`test_toshi_file.py` → `toshi_file.py`).
