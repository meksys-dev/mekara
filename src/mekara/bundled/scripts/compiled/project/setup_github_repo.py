"""Auto-generated script. Source: .claude/commands/project/setup-github-repo.md"""

import json
from typing import Generator

from mekara.scripting.runtime import Auto, ShellResult, auto, llm


def _apply_branch_protection(
    org: str, repo_name: str, branch: str, required_checks: list[str], context: str
) -> Generator[Auto, ShellResult, None]:
    """Apply branch protection rules to a branch."""
    protection_config = {
        "required_status_checks": {
            "strict": True,
            "contexts": required_checks,
        },
        "enforce_admins": True,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "required_conversation_resolution": False,
        "lock_branch": False,
        "allow_fork_syncing": False,
        "required_linear_history": True,
    }
    config_json = json.dumps(protection_config)
    api_path = f"repos/{org}/{repo_name}/branches/{branch}/protection"
    yield auto(
        f"""gh api {api_path} --method PUT --input - <<'EOF'
{config_json}
EOF""",
        context=context,
    )


def _verify_branch_protection(
    org: str, repo_name: str, branch: str, context: str
) -> Generator[Auto, ShellResult, None]:
    """Verify branch protection settings match expectations."""
    result = yield auto(
        f"gh api repos/{org}/{repo_name}/branches/{branch}/protection",
        context=context,
    )
    protection = json.loads(result.output)
    errors = []

    if not protection.get("required_status_checks", {}).get("strict"):
        errors.append("Strict status checks not enabled")
    if not protection.get("enforce_admins", {}).get("enabled"):
        errors.append("Enforce admins not enabled")
    if protection.get("allow_force_pushes", {}).get("enabled"):
        errors.append("Force pushes not disabled")
    if not protection.get("required_linear_history", {}).get("enabled"):
        errors.append("Required linear history not enabled")

    if errors:
        raise RuntimeError(
            f"Branch protection verification for '{branch}' failed:\n"
            + "\n".join(f"- {e}" for e in errors)
        )


def _verify_repo_settings(
    org: str, repo_name: str, context: str
) -> Generator[Auto, ShellResult, None]:
    """Verify repository settings for auto-merge and auto-delete."""
    result = yield auto(
        f"gh api repos/{org}/{repo_name}",
        context=context,
    )
    repo = json.loads(result.output)
    errors = []

    if not repo.get("allow_auto_merge"):
        errors.append("Auto-merge not enabled")
    if not repo.get("delete_branch_on_merge"):
        errors.append("Delete branch on merge not enabled")

    if errors:
        raise RuntimeError(
            "Repository settings verification failed:\n" + "\n".join(f"- {e}" for e in errors)
        )


def _create_pr_and_merge(title: str, body: str) -> Generator[Auto, ShellResult, None]:
    """Create a PR, enable auto-merge, wait for CI, and verify merge."""
    pr_result = yield auto(
        f"""gh pr create --title "{title}" --body "$(cat <<'EOF'
{body}
EOF
)"
""",
        context="Create a pull request with the specified title and body.",
    )

    # gh pr create outputs the PR URL, e.g., "https://github.com/owner/repo/pull/22"
    pr_url = pr_result.output.strip()
    pr_number = pr_url.rstrip("/").split("/")[-1]

    yield auto(
        f"gh pr merge {pr_number} --auto --squash",
        context="Enable auto-merge so the PR merges automatically once CI passes.",
    )

    yield auto(
        f"sleep 10 && gh pr checks {pr_number} --watch",
        context="Wait 10 seconds for CI checks to kick off, then wait for them to pass.",
    )

    # Verify PR merged
    pr_state_result = yield auto(
        f"gh pr view {pr_number} --json state",
        context=(
            "Once checks pass, the PR should auto-merge. Verify the PR state with "
            '`gh pr view <pr-number> --json state`. Expect `{"state":"MERGED"}`. '
            "If the PR state is unexpected, wait to confirm next steps with the user "
            "instead of continuing."
        ),
    )
    pr_data = json.loads(pr_state_result.output)
    if pr_data["state"] != "MERGED":
        raise RuntimeError(
            f"Expected PR state to be MERGED, but got {pr_data['state']}. "
            "Please check the PR status and confirm next steps."
        )


def execute(request: str):
    """Set up a new GitHub repository with CI workflows and comprehensive branch
    protection rules.
    """

    # Step 0: Gather repository and stack details
    # Review the current session to identify repository details, stack, and CI requirements
    repo_info = yield llm(
        """Review the current session to identify:
- Repository name and organization/owner (or ask if creating new repo)
- Whether this is a new repo or existing repo needing GitHub setup
- Stack details: language, build/test tooling, package manager
- What CI checks should run (typically: linting, formatting, type checking, tests)
- Whether the repo is public or private (default to private)

Infer these from the session context when possible. Only ask if genuinely unclear.""",
        expects={
            "repo_name": "repository name",
            "org_or_owner": "GitHub organization or username",
            "is_private": "true if private repo, false if public",
        },
    )

    repo_name = repo_info.outputs["repo_name"]
    org = repo_info.outputs["org_or_owner"]
    is_private = repo_info.outputs["is_private"].lower() == "true"

    # Check if repository already exists on GitHub
    repo_exists_result = yield auto(
        f"gh repo view {org}/{repo_name}",
        context="Check if the repository already exists on GitHub using gh repo view",
    )
    repo_exists = repo_exists_result.success

    # Step 1: Create GitHub repository and push code (if new repo)
    if not repo_exists:
        privacy_flag = "--private" if is_private else "--public"
        yield auto(
            f"gh repo create {org}/{repo_name} {privacy_flag} --source=. --remote=origin --push",
            context=(
                "If the repository doesn't exist on GitHub yet, create it with "
                "`gh repo create <org>/<repo-name> --private --source=. "
                "--remote=origin --push`. Adjust `--private`/`--public` based on "
                "requirements. Skip this step if the repo already exists on GitHub."
            ),
        )

    # Step 2: Create CI workflows
    # This requires LLM judgment to create appropriate workflow files based on stack
    yield llm(
        """Create `.github/workflows/` directory and add workflow files based on the
stack. There should at least be these two workflows:
- A workflow to run pre-commit hook checks on all files
- A workflow to run all tests in the project

For example, if using Python with pre-commit:
- Create a pre-commit workflow that runs `pre-commit run --all-files`
- Create a tests workflow that runs the test suite

For other stacks, adapt the workflow structure but follow these principles:
- Use the official setup action for the language (e.g., `actions/setup-python`,
  `actions/setup-node`)
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
          <language>-version: '<version>'
      - name: Install <package-manager>
        # Stack-specific installation
      - name: Install dependencies
        run: <install-command>
      - name: Run <check>
        run: <check-command>
```"""
    )

    # Step 3: Commit and push workflows
    yield llm(
        """Stage and commit the workflow files with git add .github/ and git commit.
Use a commit message in the format:
'Add CI workflows for <stack-specific checks>

- <Workflow 1>: <description>
- <Workflow 2>: <description>'"""
    )

    yield auto("git push", context="Push workflows to GitHub")

    # Step 4: Configure branch protection rules
    # Need LLM to identify CI job names from created workflows
    job_names = yield llm(
        """Identify the CI job names from the workflows created in Step 2. These
will be used as required status checks.

**Important:** If a workflow uses a matrix strategy, the status check name will
be `<job-name> (<matrix-value>)`, not just `<job-name>`. For example, a job
named `test` with `matrix: python-version: ['3.12']` will create a check named
`test (3.12)`.

To verify the exact check names, push the workflows first and check the PR
status checks, or look at a previous workflow run in the Actions tab.

List all the job names that should be required status checks.""",
        expects={
            "required_checks": (
                "JSON array of job names as they will appear in GitHub status checks"
            )
        },
    )

    # Parse the required checks from LLM output
    required_checks = json.loads(job_names.outputs["required_checks"])

    yield from _apply_branch_protection(
        org,
        repo_name,
        "main",
        required_checks,
        context=(
            "Set up comprehensive branch protection with required status checks, "
            "strict mode, enforce admins, no force pushes, and required linear "
            "history"
        ),
    )

    # Step 5: Enable repository settings
    yield auto(
        f"gh api repos/{org}/{repo_name} --method PATCH "
        f"--field allow_auto_merge=true --field delete_branch_on_merge=true",
        context="Enable auto-merge and auto-delete merged branches",
    )

    # Step 6: Verify configuration
    yield from _verify_branch_protection(
        org,
        repo_name,
        "main",
        context=(
            "Verify branch protection settings match expectations: strict status checks "
            "enabled, enforce admins enabled, force pushes disabled, required linear "
            "history enabled"
        ),
    )

    yield from _verify_repo_settings(
        org,
        repo_name,
        context="Verify repository settings for auto-merge and auto-delete are enabled",
    )

    # Step 7 (Optional): Set up docs branch CI and protection (if separate docs branch exists)
    # Check if docs branch exists locally or remotely
    local_check = yield auto(
        "test -d ../docs/.git || test -f ../docs/.git",
        context="Check if docs branch exists locally as worktree at ../docs",
    )
    remote_check = yield auto(
        "git ls-remote --heads origin docs",
        context="Check if docs branch exists remotely",
    )

    has_local = local_check.success
    has_remote = remote_check.success and remote_check.output.strip()

    # If no docs branch either locally or remotely, skip to Step 8
    if not has_local and not has_remote:
        has_docs_branch = False
    else:
        has_docs_branch = True

        # Ensure docs branch exists both locally and remotely
        if not has_local:
            yield auto(
                "git worktree add ../docs docs",
                context="Create local worktree from remote docs branch",
            )
        if not has_remote:
            yield auto(
                "cd ../docs && git push -u origin docs",
                context="Push local docs branch to remote",
            )

    if has_docs_branch:
        # Repeat Steps 2, 3, 4, and 6 in the ../docs worktree directory
        yield llm(
            "Repeat Step 2 in the `../docs` worktree directory: create "
            "`.github/workflows/` with CI workflow files. Typically only "
            "pre-commit workflow is needed for docs, no tests. If workflows "
            "already exist, skip this step."
        )

        yield llm(
            "Repeat Step 3 in the `../docs` worktree: stage and commit the "
            "workflow files. If no new workflows were created, skip this step."
        )

        yield auto(
            "cd ../docs && git push",
            context="Push docs workflow commits to GitHub",
        )

        # Step 4 (for docs): Configure branch protection rules for docs
        docs_job_names = yield llm(
            "Identify the CI job names from the workflows on the docs branch "
            "(in ../docs/.github/workflows/). These will be used as required "
            "status checks.\n\n"
            "**Important:** If a workflow uses a matrix strategy, the status "
            "check name will be `<job-name> (<matrix-value>)`, not just "
            "`<job-name>`.\n\n"
            "List all the job names from the docs branch workflows that should "
            "be required status checks.",
            expects={
                "required_checks": (
                    "JSON array of job names as they will appear in GitHub status checks"
                )
            },
        )

        docs_required_checks = json.loads(docs_job_names.outputs["required_checks"])

        yield from _apply_branch_protection(
            org,
            repo_name,
            "docs",
            docs_required_checks,
            context=(
                "Set up comprehensive branch protection for docs branch with "
                "required status checks, strict mode, enforce admins, no force "
                "pushes, and required linear history"
            ),
        )

        # Step 6 (for docs): Verify docs branch protection
        yield from _verify_branch_protection(
            org,
            repo_name,
            "docs",
            context="Verify docs branch protection settings match expectations",
        )

    # Step 8: Document CI and branch protection in README
    docs_note = ""
    if has_docs_branch:
        docs_note = """

If a separate docs branch exists, add this note:

```markdown
**Note:** The `docs` branch has the same protection rules as `main`.
All documentation changes require pull requests and passing CI checks.
```"""

    yield llm(
        f"""Update the project README to document the CI workflows and branch
protection rules that were just set up.

Add sections covering:
- **CI Workflows**: List each workflow file with a brief description of what
  it does
- **Branch Protection**: Document the protection rules (required checks, linear
  history, no force pushes, etc.)
- **Docs Branch Protection**: If a separate docs branch exists, document that
  it has the same protection rules

Example documentation structure:

```markdown
## Continuous Integration

This repository uses GitHub Actions for continuous integration. All checks must
pass before code can be merged to `main`.

### Workflows

**<Workflow Name>** (`.github/workflows/<filename>.yml`)
- Description of what this workflow does
- What checks it runs

### Branch Protection

The `main` branch is protected with the following rules:

- ✅ All CI checks must pass before merging
- ✅ Branches must be up-to-date with `main` before merging
- ✅ Linear history required (squash or rebase merge only)
- ✅ No force pushes allowed
- ✅ No direct commits to `main` (all changes via pull requests)
- ✅ Rules enforced for all users, including admins
- ✅ Merged branches are automatically deleted
```{docs_note}"""
    )

    # Step 9: Create branch for documentation changes
    # This is the first test of the new branch protection workflow!
    yield auto(
        "git checkout -b docs/add-ci-documentation",
        context=(
            "**This is the first test of the new branch protection workflow!** "
            "Since we just set up branch protection, we can no longer push directly "
            "to main."
        ),
    )

    # Step 10: Commit the README changes
    yield llm(
        """Stage and commit the documentation updates with git add README.md and
git commit. Use this commit message:
'Document CI workflows and branch protection in README

Added comprehensive documentation for:
- GitHub Actions workflows and what they check
- Branch protection rules and requirements
- CI/CD process and merge requirements'"""
    )

    # Step 11: Push the branch and create a pull request
    yield auto(
        "git push -u origin docs/add-ci-documentation",
        context=(
            "Push the branch to the remote and create a PR. Use `-u` to set up "
            "tracking for the branch."
        ),
    )

    pr_body = """## Summary

Documents the CI workflows and branch protection rules in the README.

## Test plan

- [x] Pre-commit hooks pass
- [x] All CI checks will run on this PR
- [x] Demonstrates the new branch protection workflow in action"""

    # Steps 11-14: Create PR, enable auto-merge, wait for CI, verify merge
    yield from _create_pr_and_merge(
        title="Document CI workflows and branch protection",
        body=pr_body,
    )

    # Step 15: Return to main branch
    yield auto(
        "git checkout main && git pull",
        context="Switch back to main and pull to get the merged changes.",
    )
