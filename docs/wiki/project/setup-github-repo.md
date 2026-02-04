---
sidebar_label: Setup GitHub Repo
sidebar_position: 6
---

Set up a new GitHub repository with CI workflows and comprehensive branch protection rules.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather repository and stack details

Review the current session to identify:

- Repository name and organization/owner (or ask if creating new repo)
- Whether this is a new repo or existing repo needing GitHub setup
- Stack details: language, build/test tooling, package manager
- What CI checks should run (typically: linting, formatting, type checking, tests)
- Whether the repo is public or private (default to private)

Infer these from the session context when possible. Only ask if genuinely unclear.

### Step 1: Create GitHub repository and push code (if new repo)

If the repository doesn't exist on GitHub yet:

```bash
gh repo create <org>/<repo-name> --private --source=. --remote=origin --push
```

Adjust `--private`/`--public` based on requirements. Skip this step if the repo already exists on GitHub.

### Step 2: Create CI workflows

Create `.github/workflows/` directory and add workflow files based on the stack. There should at least be these two workflows:

- A workflow to run pre-commit hook checks on all files
- A workflow to run all tests in the project

For example, if using Python with pre-commit:

- Create a pre-commit workflow that runs `pre-commit run --all-files`
- Create a tests workflow that runs the test suite

For other stacks, adapt the workflow structure but follow these principles:

- Use the official setup action for the language (e.g., `actions/setup-python`, `actions/setup-node`)
- Install dependencies using the project's package manager
- Run the same checks locally that will run in CI
- Enable caching for faster CI runs

Example workflow structure (adapt commands to the stack):

```yaml
name: <Check Name>
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  <job-name>:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up <language>
        uses: actions/setup-<language>@v5
        with:
          <language>-version: "<version>"
      - name: Install <package-manager>
        # Stack-specific installation
      - name: Install dependencies
        run: <install-command>
      - name: Run <check>
        run: <check-command>
```

### Step 3: Commit and push workflows

```bash
git add .github/
git commit -m "Add CI workflows for <stack-specific checks>

- <Workflow 1>: <description>
- <Workflow 2>: <description>"
git push
```

### Step 4: Configure branch protection rules

Identify the CI job names from the workflows created in Step 2. These will be used as required status checks.

**Important:** If a workflow uses a matrix strategy, the status check name will be `<job-name> (<matrix-value>)`, not just `<job-name>`. For example, a job named `test` with `matrix: python-version: ['3.12']` will create a check named `test (3.12)`.

To verify the exact check names, push the workflows first and check the PR status checks, or look at a previous workflow run in the Actions tab.

Set up comprehensive branch protection:

```bash
gh api repos/<org>/<repo>/branches/main/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "<job-name-1>",
      "<job-name-2>"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "allow_fork_syncing": false,
  "required_linear_history": true
}
EOF
```

Key protection features:

- `strict: true` - Branches must be up-to-date before merging
- `enforce_admins: true` - Rules apply to everyone, including admins
- `allow_force_pushes: false` - No force pushing to main
- `required_linear_history: true` - Enforces clean, linear git history

### Step 5: Enable repository settings

Enable auto-merge and auto-delete merged branches:

```bash
gh api repos/<org>/<repo> \
  --method PATCH \
  --field allow_auto_merge=true \
  --field delete_branch_on_merge=true
```

### Step 6: Verify configuration

Verify branch protection and repository settings:

```bash
gh api repos/<org>/<repo>/branches/main/protection | jq '{
  strict_status_checks: .required_status_checks.strict,
  required_checks: .required_status_checks.contexts,
  enforce_admins: .enforce_admins.enabled,
  allow_force_pushes: .allow_force_pushes.enabled,
  required_linear_history: .required_linear_history.enabled
}'

gh api repos/<org>/<repo> | jq '{
  delete_branch_on_merge: .delete_branch_on_merge,
  allow_auto_merge: .allow_auto_merge
}'
```

Confirm all settings match expectations:

- Required status checks are configured
- Strict mode is enabled
- Force pushes are disabled
- Linear history is required
- Auto-merge and auto-delete are enabled

### Step 7 (Optional): Set up docs branch CI and protection (if separate docs branch exists)

If there's no docs branch (either locally or remotely), skip to Step 8.

Otherwise, ensure the docs branch exists both locally (as a worktree at `../docs`) and remotely. Then repeat Steps 2, 3, 4, and 6 in the `../docs` worktree directory (typically only pre-commit workflow needed for docs, no tests). Use `branches/docs/protection` in Step 4.

### Step 8: Document CI and branch protection in README

Update the project README to document the CI workflows and branch protection rules that were just set up.

Add sections covering:

- **CI Workflows**: List each workflow file with a brief description of what it does
- **Branch Protection**: Document the protection rules (required checks, linear history, no force pushes, etc.). If a separate `docs` branch is used, make sure to mention branch protection coverage for this branch as well.

Example documentation structure:

```markdown
## Continuous Integration

This repository uses GitHub Actions for continuous integration. All checks must pass before code can be merged to `main` or `docs`.

### Workflows

**<Workflow Name>** (`.github/workflows/<filename>.yml`)

- Description of what this workflow does
- What checks it runs

### Branch Protection

The `main` and `docs` branches are protected with the following rules:

- ✅ All CI checks must pass before merging
- ✅ Branches must be up-to-date with `main` or `docs` before merging
- ✅ Linear history required (squash or rebase merge only)
- ✅ No force pushes allowed
- ✅ No direct commits to `main` or `docs` (all changes via pull requests)
- ✅ Rules enforced for all users, including admins
- ✅ Merged branches are automatically deleted
```

### Step 9: Create branch for documentation changes

**This is the first test of the new branch protection workflow!** Since we just set up branch protection, we can no longer push directly to main.

```bash
git checkout -b docs/add-ci-documentation
```

### Step 10: Commit the README changes

Stage and commit the documentation updates:

```bash
git add README.md
git commit -m "Document CI workflows and branch protection in README

Added comprehensive documentation for:
- GitHub Actions workflows and what they check
- Branch protection rules and requirements
- CI/CD process and merge requirements"
```

### Step 11: Push the branch and create a pull request

Push the branch to the remote and create a PR. Use `-u` to set up tracking for the branch:

```bash
git push -u origin docs/add-ci-documentation

gh pr create --title "Document CI workflows and branch protection" --body "$(cat <<'EOF'
## Summary

Documents the CI workflows and branch protection rules in the README.

## Test plan

- [x] Pre-commit hooks pass
- [x] All CI checks will run on this PR
- [x] Demonstrates the new branch protection workflow in action
EOF
)"
```

### Step 12: Enable auto-merge

Enable auto-merge so the PR merges automatically once CI passes:

```bash
gh pr merge --auto --squash
```

### Step 13: Wait for CI checks to pass

Wait 10 seconds for CI checks to kick off, then wait for them to pass:

```bash
sleep 10 && gh pr checks <pr-number> --watch
```

### Step 14: Verify PR merged

Once checks pass, the PR should auto-merge. Verify the PR state:

```bash
gh pr view <pr-number> --json state
```

Expect `{"state":"MERGED"}`. If the PR state is unexpected, wait to confirm next steps with the user instead of continuing.

### Step 15: Return to main branch

Switch back to main and pull to get the merged changes:

```bash
git checkout main && git pull
```
