Add a LICENSE file to a repository by fetching the official license text from SPDX.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather license requirements

Determine the following from context or by asking:

- **License type:** The SPDX identifier (e.g., `MIT`, `Apache-2.0`, `GPL-3.0-only`)
- **Copyright holder:** Name of the person or organization (infer from package config like `pyproject.toml` author, `package.json` author, or `Cargo.toml` authors)
- **Copyright year:** Default to the current year unless specified otherwise

Common SPDX license identifiers (non-exhaustive):

- `MIT` — MIT License
- `Apache-2.0` — Apache License 2.0
- `GPL-3.0-only` — GNU General Public License v3.0
- `LGPL-3.0-only` — GNU Lesser General Public License v3.0
- `MPL-2.0` — Mozilla Public License 2.0
- `BSL-1.0` — Boost Software License 1.0
- `Unlicense` — The Unlicense
- `AGPL-3.0-only` — GNU Affero General Public License v3.0
- `BSD-3-Clause` — BSD 3-Clause License
- `BSD-2-Clause` — BSD 2-Clause License

### Step 1: Check current license state

Check if a LICENSE file already exists:

```bash
ls LICENSE* 2>/dev/null || echo "No LICENSE file found"
```

If a LICENSE file already exists, ask the user if they want to replace it.

### Step 2: Fetch official license text

Fetch the canonical license text directly from SPDX's GitHub repository using curl:

```bash
curl -s "https://raw.githubusercontent.com/spdx/license-list-data/main/text/<SPDX-ID>.txt"
```

This fetches the authoritative plain text with zero LLM involvement—no hallucination risk.

### Step 3: Create the LICENSE file

Replace placeholders in the fetched text and write to `LICENSE`:

- `<year>` → copyright year
- `<copyright holders>` → copyright holder name

Use `sed` to replace placeholders and write the file:

```bash
curl -s "https://raw.githubusercontent.com/spdx/license-list-data/main/text/<SPDX-ID>.txt" \
  | sed "s/<year>/<YEAR>/g; s/<copyright holders>/<COPYRIGHT_HOLDER>/g" \
  > LICENSE
```

### Step 4: Verify

Verify the LICENSE file was created and contains the complete license text:

```bash
head -20 LICENSE
```

### Step 5: Commit

Ask the user if they want to commit, then use the committer agent.

## Key Principles

- Always fetch license text from SPDX using curl—no LLM token waste or hallucination risk.
- Infer copyright holder from existing package config when possible.
- Use `LICENSE` (no extension) as the standard filename.
