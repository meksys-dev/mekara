---
sidebar_position: 7
---

# Releasing to PyPI

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

## Publish to TestPyPI

```bash
# Build
rm -rf dist/
poetry build

# Publish
poetry publish -r testpypi

# Test
python -m venv /tmp/test-mekara
source /tmp/test-mekara/bin/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mekara==0.1.0a1
mekara --version
deactivate
rm -rf /tmp/test-mekara
```

## Publish to Real PyPI

:::warning
Only run after merging to main.
:::

```bash
# Build
rm -rf dist/
poetry build

# Publish
poetry publish
```

Verify at https://pypi.org/project/mekara/

## Version Management

```bash
# Bump alpha: 0.1.0a1 -> 0.1.0a2
poetry version prerelease

# Stable release
poetry version 0.1.0
```
