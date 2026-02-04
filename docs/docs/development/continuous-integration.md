---
sidebar_position: 5
---

# Continuous Integration

GitHub Actions runs pre-commit hooks and tests on every push to `main` and every pull request against `main`. This ensures all code meets quality standards before merging.

## Workflows

### Build and Deploy Docs

The build and deploy docs workflow (`.github/workflows/build-docs.yml`) automatically deploys the documentation site to GitHub Pages on every push to `main`:

1. Sets up Node.js 20 and pnpm
2. Installs documentation dependencies
3. Runs `pnpm run build` in the `docs/` directory
4. Uploads the built site as a GitHub Pages artifact
5. Deploys to GitHub Pages

The workflow can also be triggered manually via `workflow_dispatch` for testing from other branches. See [Deploy](./deploy.md#github-pages-automatic) for details.

### Pre-commit

The pre-commit workflow (`.github/workflows/pre-commit.yml`) runs the same hooks as local development:

1. Sets up Python 3.11, Node.js 20, Poetry, and pnpm
2. Installs all dependencies
3. Runs `pre-commit run --all-files`

This catches any issues that might slip through if a contributor skips local hooks.

### Tests

The tests workflow (`.github/workflows/tests.yml`) runs the pytest test suite:

1. Sets up Python 3.11 and Poetry
2. Installs all dependencies
3. Runs `poetry run pytest`

## Dependency Caching

Both workflows cache Poetry dependencies based on lockfiles, and the pre-commit workflow also caches pnpm dependencies for the docs site.

## Version Pinning

All tool versions are pinned to ensure reproducible builds:

| Tool   | Version | Source              |
| ------ | ------- | ------------------- |
| Python | 3.11    | `pyproject.toml`    |
| Poetry | 2.1.1   | Workflow file       |
| Node   | 20      | `docs/package.json` |
| pnpm   | 10.12.4 | `docs/package.json` |

When upgrading any of these locally, update the workflow file to match.

## Branch Protection

A [GitHub ruleset](https://github.com/meksys-dev/mekara/rules/10492367) enforces the following on the default branch (`main`):

- **Pull request required**: All changes must go through a PR (no direct pushes)
- **No force push**: History rewrites are blocked to preserve commit history
- **Required status checks**: Both `pre-commit` and `tests` jobs must pass before merging
- **Strict mode**: PR branches must be up-to-date with `main` before merging

This ensures all code on `main` has passed CI, incorporates the latest changes, and maintains a clean history.

### PR Automation

The repository has two automation settings enabled:

- **Auto-merge**: PRs merge automatically once all required status checks pass
- **Auto-delete branches**: PR branches are deleted after merge to keep the repository clean

:::note

If these get disabled (e.g., after a repository settings reset), re-enable via the GitHub API:

```bash
gh api repos/meksys-dev/mekara --method PATCH \
  --field allow_auto_merge=true \
  --field delete_branch_on_merge=true
```

:::

## Private Resources

### Fonts

CI does not have access to the private font submodule (`docs/static/fonts/private/`). The Docusaurus build handles this gracefully by checking for an actual font file before including `fonts.css`. See [UI Customizations](../code-base/documentation/ui-customizations.md#conditional-loading) for details.

### AI Dojo Repository

Some visual snapshot tests require cloning the private `meksys-dev/ai-dojo` repository to set up test fixtures at specific git tags. CI accesses this via the `DOJO_ACCESS_TOKEN` repository secret.

To configure:

1. Create a GitHub PAT with `repo` scope
2. Add it as a repository secret named `DOJO_ACCESS_TOKEN` at [Settings → Secrets → Actions](https://github.com/meksys-dev/mekara/settings/secrets/actions)

The tests workflow configures git to use this token for all GitHub HTTPS URLs:

```yaml
- name: Configure git for private repo access
  run: |
    git config --global url."https://${{ secrets.DOJO_ACCESS_TOKEN }}@github.com/".insteadOf "https://github.com/"
```

If the token is missing or invalid, tests that require the dojo repo will skip gracefully with a message indicating authentication may be required.
