Set up GitHub Pages deployment workflow for a documentation site with automatic deployment on merges to main.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather documentation site details

Identify from the repo:

- Where the documentation site lives (subdirectory path like `docs/`, or worktree path)
- What build tool is used (npm/pnpm/yarn for JS docs, poetry for Python docs, etc.)
- What the build command is (e.g., `pnpm run build`, `mkdocs build`, `sphinx-build`)
- What directory contains the built output (e.g., `build/`, `site/`, `_site/`)
- The repository's GitHub organization/username and repo name
- Whether there are private submodules that need access tokens

If any of these are unclear from the repo, ask the user.

### Step 1: Determine the correct baseUrl for GitHub Pages

GitHub Pages serves from `https://<org>.github.io/<repo>/` unless using a custom domain.

Check the current baseUrl configuration:

- For Docusaurus: check `url` and `baseUrl` in `docusaurus.config.ts`
- For other static site generators: check their equivalent config

If the current config assumes root path (`baseUrl: "/"`) or a custom domain, update it to use the GitHub Pages URL format:

- `url: "https://<org>.github.io"`
- `baseUrl: "/<repo>/"`

### Step 2: Create the GitHub Actions workflow

Create `.github/workflows/build-docs.yml` (or similar name) with:

1. Trigger on push to main and manual workflow_dispatch
2. Required permissions: `contents: read`, `pages: write`, `id-token: write`
3. Concurrency control to prevent simultaneous deployments
4. Build job that:
   - Checks out the repository with submodules if needed
   - Sets up the build environment (Node.js, Python, Ruby, etc. depending on stack)
   - Installs dependencies
   - Runs the build command
   - Uploads the built directory as a GitHub Pages artifact
5. Deploy job that:
   - Depends on the build job
   - Uses the `github-pages` environment
   - Deploys using `actions/deploy-pages@v4`

**For repositories with private submodules:**

- Create a GitHub Personal Access Token with access to the private repositories
- Add it as a repository secret (e.g., `SUBMODULE_ACCESS_TOKEN`)
- Pass it to the checkout action: `token: ${{ secrets.SUBMODULE_ACCESS_TOKEN }}`

**Example workflow structures for different stacks:**

<details>
<summary>Docusaurus (Node.js + pnpm)</summary>

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true # if needed
          token: ${{ secrets.SUBMODULE_TOKEN }} # if private submodules

      - uses: pnpm/action-setup@v4
        with:
          version: 10.12.4 # pin version

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: pnpm
          cache-dependency-path: docs/pnpm-lock.yaml

      - name: Install dependencies
        working-directory: docs
        run: pnpm install

      - name: Build docs
        working-directory: docs
        run: pnpm run build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: docs/build

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

</details>

<details>
<summary>MkDocs (Python + Poetry)</summary>

```yaml
name: Build and Deploy Docs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: 2.1.1

      - name: Install dependencies
        run: poetry install --with docs

      - name: Build docs
        run: poetry run mkdocs build

      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

</details>

Pin all tool versions (Node, Python, pnpm, poetry, etc.) to ensure reproducible builds.

### Step 3: Configure the GitHub Pages environment

In the repository settings:

1. Go to Settings → Pages
2. Set "Source" to "GitHub Actions"

If you need to test the workflow from a feature branch before merging to main:

1. Temporarily add your branch to the workflow trigger: `branches: [main, feature-branch-name]`
2. Add the branch to the github-pages environment's allowed deployment branches:
   ```bash
   gh api repos/<org>/<repo>/environments/github-pages/deployment-branch-policies \
     --method POST --field name='feature-branch-name' --field type='branch'
   ```
3. After testing, remove the temporary trigger and delete the branch policy

### Step 4: Test the deployment

Push the workflow file and configuration changes to trigger a build.

Monitor the workflow:

```bash
gh run list --workflow=build-docs.yml --limit=1
gh run watch <run-id>
```

Verify the deployed site loads at `https://<org>.github.io/<repo>/`

If the site shows "Docusaurus site did not load properly" or similar errors, check the baseUrl configuration matches the GitHub Pages URL structure.

### Step 5: Update documentation

Update the project's deployment documentation (typically in `docs/docs/development/deploy.md` or similar) to:

- Document that GitHub Pages is configured in Settings → Pages with Source set to "GitHub Actions"
- Explain how to manually trigger the workflow for testing documentation changes
- Document the workflow file location and what it does
- If using private submodules, document the required repository secret

Update CI/CD documentation (typically `docs/docs/development/continuous-integration.md`) to mention the deployment workflow.

### Step 6: Clean up and commit

If you added temporary branch triggers for testing, remove them before committing.

Wait for user confirmation, then use the committer agent to commit all changes:

- Workflow file (`.github/workflows/build-docs.yml`)
- Configuration changes (baseUrl updates)
- Documentation updates
