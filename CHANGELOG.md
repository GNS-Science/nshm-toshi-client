
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
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
