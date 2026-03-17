---
sidebar_label: Release
sidebar_position: 10
---

Prepare a release by updating the version, building, and verifying the distribution.

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

If the project has a documentation link checker, run it now. Fix any broken links and commit the fixes before proceeding. Abort the release if there are broken links to fix.

Every release should be entirely clean and involve only the version number as a change.

### Step 3: Update version and commit

Update the project's version file (e.g., `pyproject.toml`, `Cargo.toml`, `package.json`) to set the target version, then use the committer agent to commit the change.

### Step 4: Snapshot documentation version

If the project uses versioned documentation, create a snapshot for this release using the project's documentation tool. For example, with Docusaurus:

```bash
cd docs && pnpm docusaurus docs:version <target-version>
```

Then update the documentation configuration to make the new version the default. For Docusaurus, update `docusaurus.config.ts`:

- Set `lastVersion` to `"<target-version>"` in the preset's `docs` options
- Add the new version to the `versions` config object:
  ```ts
  "<target-version>": {
    label: "v<target-version>",
  },
  ```

Use the committer agent to commit the snapshot.

### Step 5: Build and verify

Build the distribution using the project's build tool (e.g., `poetry build`, `cargo package`, `npm pack`) and verify the output looks correct.

### Step 6: Provide publishing instructions

Tell the user the package is ready and provide instructions for publishing to the appropriate registry (e.g., PyPI, crates.io, npm). Recommend testing on a staging registry first if one is available.

## Key Principles

- **Verify before publishing**: Always build and verify the package contents before handing off to the user for publishing
- **User publishes manually**: The user should always manually run the publish command after reviewing the prepared package—never auto-publish
