---
sidebar_label: Setup Docs
sidebar_position: 4
---

Set up a documentation site using either a subdirectory or separate orphan branch with git worktree.

<UserContext>$ARGUMENTS</UserContext>

## Information Needed

Ask the user:

1. Which documentation setup approach do you prefer?
   - **Subdirectory (`docs/` folder)**: Documentation lives in `docs/` subdirectory of the main repository. Easier to maintain and deploy alongside the main project. Documentation changes are part of the main project's git history. Recommended for simpler projects or when you want docs close to code.
   - **Separate worktree branch**: Documentation lives in a separate git worktree with orphan branch. Completely isolated git history for documentation. Can be deployed independently of the main project. Recommended for complex documentation or separate deployment needs.

## Process

### Step 1: Gather context

Identify from the user context:

- Repository path (where the main project lives)
- Documentation framework (recommended: Docusaurus, Material for MkDocs, VitePress)
- Stack/tooling for the docs framework (infer from main project or ask)
- For worktree approach: Branch name for docs (default: `docs`) and worktree directory name (default: same as branch name)

Ask only if the details without a default are genuinely missing from the context.

**Decision Point: Confirm chosen approach**

Present the user's choice back to them and confirm:

- "Based on your preference, I'll set up documentation using the [subdirectory/worktree branch] approach. Is that correct?"

Wait for user confirmation before proceeding.

## Approach A: Subdirectory Setup (`docs/` folder)

### Step 2A: Create docs subdirectory

Create and navigate to the docs directory:

```bash
mkdir docs
cd docs
```

### Step 3A: Initialize documentation project

Initialize the project using the appropriate tooling for the stack. Examples:

**Material for MkDocs (Python):**

```bash
uv init --no-readme
```

**Docusaurus (Node.js):**

```bash
npm init -y
```

**VitePress (Node.js):**

```bash
npm init -y
```

Note: If the base project is already using a package manager and the docs use the same language, reuse the same package manager for the documentation site.

## Approach B: Separate Worktree Branch Setup

### Step 2B: Check for branch name conflicts

Check if there are existing branches that would conflict with creating the docs branch:

```bash
git branch -a | grep "^[[:space:]]*<branch-name>/"
```

If any branches like `<branch-name>/*` exist, they will prevent creating the branch. Delete conflicting branches with user confirmation.

### Step 3B: Create git worktree with orphan branch

Create a detached worktree and checkout an orphan branch in it:

```bash
git worktree add -d ../<worktree-name>
cd ../<worktree-name>
git checkout --orphan <branch-name>
```

The orphan branch starts with a fresh history, separate from the main project.

### Step 4B: Initialize documentation project

Clean the worktree and initialize the project using the appropriate tooling for the stack:

```bash
rm -rf * .gitignore
```

Then initialize based on the stack. Examples:

**Material for MkDocs (Python):**

```bash
uv init --no-readme
```

**Docusaurus (Node.js):**

```bash
npm init -y
```

**VitePress (Node.js):**

```bash
npm init -y
```

Note: If the base project is already using a package manager and the docs use the same language, reuse the same package manager for the documentation site.

## Common Steps (After Project Initialization)

### Step 4: Add documentation framework dependencies

Add the documentation framework using the appropriate package manager. Examples:

**Material for MkDocs (Python):**

```bash
uv add mkdocs-material 'mkdocstrings[python]'
```

**Docusaurus (Node.js):**

```bash
npx create-docusaurus@latest . classic
```

**VitePress (Node.js):**

```bash
npm add -D vitepress
```

### Step 5: Initialize documentation framework

Run the framework's initialization command to create the basic structure. Examples:

**Material for MkDocs:**

```bash
uv run mkdocs new .
```

**Docusaurus:**

```bash
# Already initialized by create-docusaurus in Step 4
```

**VitePress:**

```bash
npx vitepress init
```

### Step 6: Set up commit hooks

For subdirectory approach: Reuse the existing commit hooks tooling from the main project if it exists. Check for existing hooks configuration in the main project directory.

For worktree approach: Set up commit hooks following the approach in `/project/setup-pre-commit-hooks`: use proper tooling with git-tracked config files (pre-commit for Python, husky + lint-staged for Node.js).

Include hooks for:

- Markdown/content formatting
- Documentation build validation (build with strict mode if available)
- If code files exist (Python plugins, custom components, etc.): formatting, linting, type-checking

Install the hooks and verify they work by running them manually.

### Step 7: Verify the documentation site works

Test that the documentation site builds and serves correctly using the framework's dev server command. Examples:

**Material for MkDocs:**

```bash
uv run mkdocs serve
```

**Docusaurus:**

```bash
npm start
```

**VitePress:**

```bash
npm run docs:dev
```

Retrieve a page from the local server URL and verify the site renders correctly.

### Step 8: Create .gitignore

Create `.gitignore` to exclude framework-specific build artifacts and dependencies. Examples:

**Material for MkDocs:**

```
site/
.cache/
__pycache__/
*.py[cod]
.venv/
```

**Docusaurus:**

```
.docusaurus/
build/
node_modules/
.cache/
```

**VitePress:**

```
.vitepress/dist/
.vitepress/cache/
node_modules/
```

**Important**: Before staging files, remove any unwanted files generated by the initialization process (e.g., `main.py` from `uv init`, sample code files, etc.). These are typically boilerplate files that aren't needed for documentation.

Run `git status` to confirm no unwanted files are staged.

### Step 9: Commit the documentation setup

For both approaches: Stage all files in the current git working tree:

```bash
git add .
```

Commit with a descriptive message. If commit hooks modify files (e.g., formatting), stage the changes and commit again.

Use a commit message that describes:

- What documentation framework was set up
- Key features (theme, plugins, tooling)
- Dependency/package management approach

**CRITICAL: Never disable or skip git hooks.** If hooks are hanging or failing:

1. Kill the commit and debug the hooks separately (run the hook tool manually, e.g. `lefthook run pre-commit`, `pre-commit run --all-files`, `npm run lint`, etc.)
2. Fix the hook configuration or the underlying issue
3. Only then retry the commit with hooks enabled

Never use `--no-verify`, `LEFTHOOK=0`, `HUSKY=0`, `PRE_COMMIT_ALLOW_NO_CONFIG=1`, or any other mechanism to bypass hooks.

**Notes**:

- For subdirectory approach: This commits the `docs/` directory and its contents as part of the main repository.
- For worktree approach: This creates the initial commit on the orphan docs branch. When you run `git log --graph --all`, you'll see both the main branch history and the docs branch. However, the docs branch itself is orphaned - run `git rev-list --count HEAD` to verify it has only 1 commit, or `git log` (without `--all`) to see only the docs branch history.

### Step 10: Document the documentation setup in main project README

Switch back to the main project directory and update `README.md` to document where documentation lives:

```bash
cd <main-project-directory>
```

**For subdirectory approach**, add a Documentation section like:

```markdown
## Documentation

Project documentation lives in the `docs/` directory.

To run the documentation site locally:

\`\`\`bash
cd docs
<framework-specific dev server command>
\`\`\`
```

**For worktree approach**, add a Documentation section like:

```markdown
## Documentation

Project documentation lives in the `docs` branch, an orphan branch with separate history from the main codebase.

### Local Setup for Contributors

Set up the docs branch as a sibling worktree:

\`\`\`bash

# From the project root, add the docs branch as a sibling worktree

git worktree add ../docs docs
\`\`\`

This creates the following directory structure:

\`\`\`
parent-directory/
├── <project-name>/ # main branch (this repo)
└── docs/ # docs branch worktree
\`\`\`

Note: Documentation updates require coordinating branches in both worktrees when changes span code and docs.
```

Commit this README update to the main branch.
