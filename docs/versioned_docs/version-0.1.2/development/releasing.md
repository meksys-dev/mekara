---
sidebar_position: 7
---

# Releasing to PyPI

This page covers one-time setup and version management commands. Follow the [release process](/wiki/project/release) for routine releases after setup.

## Setup PyPI Tokens

### Configure Real PyPI

```bash
# Get token from https://pypi.org/manage/account/token/
poetry config pypi-token.pypi pypi-<your-token-here>
```

### Configure TestPyPI (Optional)

```bash
# Get token from https://test.pypi.org/manage/account/token/
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi pypi-<test-token-here>
```

## Version Management

```bash
# Bump alpha: 0.1.0a1 -> 0.1.0a2
poetry version prerelease

# Stable release
poetry version 0.1.0
```
