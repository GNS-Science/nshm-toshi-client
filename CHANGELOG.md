
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-05-14

### Removed
- Unused runtime deps: `async-timeout`, explicit `requests-toolbelt` (now provided via `gql[requests]` extra)
- Unused dev dep: `pandas-stubs` (also drops transitive `numpy`)
- Duplicate `mkdocs` entry in doc group

## [1.2.0] - 2026-05-12

### Added
- M2M (machine-to-machine) JWT auth with transparent token refresh (`ToshiTokenManager`, `ToshiM2MAuth`)
- Interactive/scientist auth with auto-refresh from `~/.toshi/credentials` (`ToshiCredentialAuth`)
- `ToshiClientBase` auto-detects auth method from env vars or credentials file
- `toshi-auth` CLI with commands: `login`, `logout`, `token`, `whoami`, `m2m-token`, `aws-creds`
- CLI available via optional extra: `pip install nshm-toshi-client[cli]`
- `auth_token` is now optional across all client classes when using token manager or credential auth
- Comprehensive test coverage for auth flows, CLI commands, and subclass kwargs passthrough

### Changed
- Updated usage docs with all three auth methods and CLI reference
- Fixed stale cookiecutter placeholders in CONTRIBUTING.md and installation.md
- Updated supported Python versions in CONTRIBUTING.md (3.10+)
- Migrated to uv, upgraded dependencies
- Deps: patch (5 pkgs), minor (10 pkgs), major: backrefs 6→7, cryptography 46→47, pandas-stubs 2→3

### Removed
- Removed stale demo scripts
- Removed implemented auth integration plan doc

## [1.1.1] - 2026-01-20
### Changed
 - update dependencies for new advisories

## [1.1.0] - 2025-12-12
### Added
 - `model_type` and `task_type` arguments to `RuptureGenerationTask.create_task` for compatibility with toshi-api 0.5.1
 - create and upload `RuptureSet`
 - `upload_content_v2` uses toshi-API `post_url_v2` and `post_data_v2`

### Changed
 - Updated vulnerable dependencies 

### Removed
 - Removed un-used dependencies


## [1.0.2] - 2025-11-06

### Changes
 - remove python 3.9 support
 - migrate pyproject.toml to PEP508
 - package updates
 - update CI/CD workflows

## [1.0.1] - 2023-11-14
### Changes
 - added requests and aiohttp extras to gql dependency
 - update poetry config
 - apply formatting / linter rules
 - remove twine from setup
 - update mkdocs config

## [1.0.0] - 2022-05-13
### Added
- ToshiFile.download_file function
- doco for env variables
### Changes
- update usage.md with download_file instruction usage
- File.file_size from Int to BigInt

## [0.6.1] - 2022-05-05
### Changes
 - disabled schema validation (for now?)

## [0.6.0] - 2022-05-04
### Added
- get_file method to ToshiFile class
- tests for get_file method
- update usage.md

## [0.5.3] - 2022-05-02
### Changes
- using poetry in place of setup.py.

### Added
- [Docs](https://gns-science.github.io/nshm-toshi-client) in /docs are published (mkdocs)
- CHANGELOG.md and version management using `poetry run bump2version major|minor|patch`
- CONTRIBUTING.md
- testing pytest
- coverage via pytest-cov
- linting with flake8 (although very limited right now)
- formatting with black
- GH workflows:
    - test matrix in tox covering [Windows, Posix, Macos] * [py38 ,py3.9]
    - publish coverage
    - publish package to test.pypi.org and pypi.org

## [0.5.2] - 2022-03-11

### Changes
- Don't set logging level.
