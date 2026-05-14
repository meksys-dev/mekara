---
sidebar_position: 1
title: For Humans
---

# Development Quickstart

## Prerequisites

- Python:
  - Python 3.11+
  - [Poetry](https://python-poetry.org/) for virtual environments (`pipx install poetry`)
  - [pre-commit](https://pre-commit.com/) for Git pre-commit hooks (`pipx install pre-commit`)
- Node:
  - pnpm 10+ (`npm install -g pnpm`).
- Environment:
  - `CLAUDE_API_KEY` or `ANTHROPIC_API_KEY`

## Local Setup

1. Clone the repo into a directory named `main` inside a parent folder:
   ```bash
   mkdir mekara && cd mekara
   git clone git@github.com:meksys-dev/mekara.git main
   cd main
   ```
2. Install hooks and dependencies:
   ```bash
   pre-commit install
   pre-commit install --hook-type post-commit
   poetry install --with dev
   pnpm --dir docs/ i --frozen-lockfile
   ```
3. Choose how to run `mekara` commands:
   - **Option A**: Prefix commands with `poetry run ...` (e.g., `poetry run mekara --help`)
   - **Option B**: Enter the Poetry shell with `poetry shell` to run commands directly
   - **Option C**: Install globally with `pipx install -e .` for system-wide access without `poetry run`
4. Configure Claude Code with mekara MCP server (see [Claude Code Integration](../../code-base/mekara/capabilities/mcp.md))
5. Validate your install:
   - Run `mekara --help` to see available commands
   - Type `/test/random` in Claude Code to test MCP integration

:::note[pipx Global Install]
The `pipx install -e .` option installs mekara in an isolated environment but makes it globally available on your system. This means you get to use `mekara` as if you were an end user who's installed it globally:

- You can run `mekara` from any directory without `poetry run`
- Changes to your local code are immediately reflected (editable install)
- It doesn't interfere with other Python projects or system Python

If you are following the recommended workspace layout, then you should run the install command inside the `main/` folder that always contains the most up-to-date version of mekara.

To uninstall it again later, simply run `pipx uninstall mekara`.
:::

See [Standard Mekara Project: Project Layout](../../standards/project.md#project-layout) for why we clone into `main/` inside a parent folder.

See [Build & Test](../build-and-test.md) for a comprehensive list of commands used in the development process.

## Devcontainer / Codespaces (Alternative)

If you prefer a containerized development environment, the repo includes a devcontainer configuration that:

- Provides Python 3.11 and Node.js 20 environments with all dependencies pre-installed
- Includes Claude Code (`claude`) and pnpm pre-installed globally
- Automatically starts the Docusaurus docs site with live reload

### GitHub Codespaces

1. From the repo on GitHub, click the green "Code" button
2. Select the "Codespaces" tab
3. Click "Create codespace on main" (or your desired branch)
4. Wait for the codespace to build and dependencies to install
5. Run `claude /login`. You will need to copy-paste the displayed URL instead of using the auto-opened URL.

### VS Code Dev Containers

1. Open the repo in VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Click "Reopen in Container" when prompted
3. Wait for the container to build and dependencies to install

---

Inside the devcontainer or GitHub workspace, packages are installed directly into system Python (no virtualenv), so you can run commands directly instead of through `poetry run`:

```bash
mekara --help
```

The docs site runs automatically with live reload enabled at either:

- http://localhost:4913 for dev containers
- `https://<workspace-url>-4913.app.github.dev/` for GitHub workspaces (also available from the "Ports" tab in VS Code)

## Development Workflow

Use the Claude Code slash commands to manage feature branches via git worktrees:

1. `/start <description>` – Create a new worktree for your feature
2. Complete your work in the new worktree with Claude
3. `/finish` – Merge back into `main` and clean up
