---
sidebar_position: 6
---

# Deploy

The docs site is automatically deployed to GitHub Pages on every merge to `main`.

## GitHub Pages (Automatic)

The `.github/workflows/build-docs.yml` workflow automatically builds and deploys the docs to GitHub Pages on every push to `main`. The workflow can also be triggered manually from any branch.

GitHub Pages for this project is configured in Settings → Pages with "Source" set to "GitHub Actions".

### Testing Documentation Changes

To verify your documentation changes build correctly before merging:

1. Push your branch to GitHub
2. Go to Actions → "Build and Deploy Docs"
3. Click "Run workflow" and select your branch

The workflow will build and deploy your branch to GitHub Pages so you can preview the changes.

### Workflow Details

The workflow (`.github/workflows/build-docs.yml`):

1. Installs pnpm 10.12.4 and Node.js 20
2. Builds the docs with `pnpm run build`
3. Uploads the `docs/build` directory as a Pages artifact
4. Deploys to GitHub Pages using the official `deploy-pages` action

The workflow includes concurrency control to prevent simultaneous deployments and requires `pages: write` and `id-token: write` permissions.
