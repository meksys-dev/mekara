Prepare a Python package for PyPI release by updating the version, building, and verifying the distribution.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Verify clean main branch

Check that the current branch is main and has zero differences from origin:

```bash
git checkout main && git diff --exit-code origin/main
```

**If there are any differences:**
1. Address the differences (commit changes, pull updates, etc.)
2. **Abort this release** and inform the user

Releases must start from a clean main branch with no uncommitted or unpushed changes.

### Step 1: Gather information

Gather the following information from the user-provided context:
- Target version (e.g., `0.1.0a1` for first alpha, `0.1.0` for stable)

If unclear, ask the user for the target version.

### Step 2: Check for broken external links

Check for broken external links in documentation:

```bash
python scripts/check-external-links.py
```

**If broken links are found:**

1. Fix the broken links in the documentation. Ask the user if it's unclear what the replacement link should be.
2. Use the committer agent to commit the fixes
3. **Abort this release** and inform the user.

Every release should be entirely clean and involve only the version number as a change. Do not proceed with the release if there are broken links to fix.

### Step 3: Update version and commit

Update `pyproject.toml` to set the target version in the `[tool.poetry]` section, then use the committer agent to commit the change.

### Step 4: Build and verify

Clean previous builds, build fresh distributions, and verify:

```bash
rm -rf dist/ && poetry build
```

Then run verification checks:

```bash
ls -lh dist/
tar -tzf dist/*.tar.gz | grep "bundled/scripts/nl.*\.md" | wc -l
tar -tzf dist/*.tar.gz | grep -E "docs/|tests/" && echo "Found excluded files (unexpected)" || echo "No excluded files (correct)"
```

### Step 5: Provide publishing instructions

Tell the user the package is ready and provide these instructions:

**To test on TestPyPI first (recommended):**
```bash
poetry publish -r testpypi
```

Then install and test:
```bash
python -m venv /tmp/test-mekara
source /tmp/test-mekara/bin/activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mekara==<version>
mekara --version
deactivate
rm -rf /tmp/test-mekara
```

**To publish to real PyPI**
```bash
poetry publish
```

## Key Principles

- **Verify before publishing**: Always build and verify the package contents before handing off to the user for publishing
- **Test on TestPyPI first**: TestPyPI exists specifically for testing the full publish/install flow without affecting the real PyPI index
- **User publishes manually**: The user should always manually run the publish command after reviewing the prepared package—never auto-publish
