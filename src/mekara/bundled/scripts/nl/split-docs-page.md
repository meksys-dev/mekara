Refactor a large documentation page into a folder of smaller pages, while preserving all information and keeping links and documentation structure consistent.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following information from the user-provided context:

- The doc file to split (path under `docs/docs/`)
- The new folder name (kebab-case) and which pages to create (e.g., `index.md`, `usage.md`, `implementation.md`, `pitfalls.md`)
- Any requested classification rules (what belongs in each page/folder), if the split is non-standard
- Whether anything should move between parent documentation folders (e.g. `../usage/`, `../development/`, `../code-base/`, `../dependencies/`), if the user explicitly requests it

If any of that is unclear, ask the user.

If the split matches standard patterns described in `docs/docs/code-base/documentation/conventions.md` (for example: “usage / implementation / pitfalls”), do not ask for additional classification rules. If the user's request classification rules appear to contradict existing conventions, ask and confirm with the user that this is in fact what they wish to do.

### Step 1: Inventory references

Run:

```bash
rg -n "<old-doc-path>|<old-doc-slug>|\\(<old-link-target>\\)" docs/docs -S
```

Collect every inbound link to the page you’re splitting and any references that will need updating.

### Step 2: Read the source page and outline the split

Skim headings and build a concrete mapping of sections → destination files.

Key constraint: do not lose any information; everything must land somewhere appropriate.

### Step 3: Create the new folder structure

Run:

```bash
mkdir -p <new-folder-path>
```

Create `index.md` inside the folder that:

- Briefly introduces the section
- Lists all direct children as bulleted links with short descriptions (format: `- [Title](./file.md) – Brief description`)

If the surrounding docs use `_category_.json`, add one consistent with nearby folders.

### Step 4: Split content into pages

Move the content into the new files (for example: `usage.md`, `implementation.md`, `pitfalls.md`) following the user’s classification rules as well as all content placement rules in @docs/docs/code-base/documentation/conventions.md#content-placement.

### Step 5: Update links and doc trees

Run:

```bash
rg -n "vcr-agent-recordings\\.md|<old-doc-slug>" docs/docs -S
```

Update all references to point at the new paths.

Also update any documentation “directory tree” pages that describe the folder structure (commonly `docs/docs/code-base/documentation/index.md`), and any local index pages that link to the old file.

### Step 6: Verify nothing was lost

Run:

```bash
git diff --stat
```

Confirm:

- All content moved somewhere appropriate
- The new folder has a correct `index.md` with links to the children
- No remaining links point at the deleted/old page

### Step 7: Run validation

Run:

```bash
poetry run pytest tests/ && cd docs && pnpm run build
```

Fix any doc build issues (broken links, formatting) and any test regressions before handing off.

## Key Principles

- Preserve information; change structure only.
- Put command-running guidance in `development/`, and code-consumption guidance in `code-base/`.
- Update inbound links and documentation directory trees whenever files/folders move.
- Standardize pitfalls/edge case documentation so it’s easy to scan and maintain.
