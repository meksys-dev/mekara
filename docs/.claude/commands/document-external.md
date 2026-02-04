# Document External Dependency

Create comprehensive documentation for an external package in `docs/dependencies/`.

<UserContext>$ARGUMENTS</UserContext>

## Process

### Step 0: Gather information

Gather the following information from the user-provided context or by asking the user:

- Which external package needs documentation (e.g., `claude-agent-sdk-python`)
- Package version being documented
- Upstream documentation URL (if available)
- Source repository URL

If any information is unclear or missing, ask the user for details.

### Step 1: Clone source and prepare references

Clone the source repository to `/tmp/` for local analysis and identify the specific commit hash (first 7 chars) for all source references. Read the existing documentation guidelines in `docs/code-base/documentation/index.md`.

### Step 2: Create the index file

Create `docs/dependencies/<package-name>/index.md` with sidebar*position metadata and a `\_category*.json`file with`{"collapsed": true}`.

The index file should contain:

- Package overview and when to use it
- Metadata table (package version, upstream docs link, source repo link)
- Installation instructions
- Section index with links to child pages and brief descriptions

Follow the pattern in `docs/code-base/index.md` for navigation-focused index pages.

### Step 3: Create the core.md file

Create `docs/dependencies/<package-name>/core.md` (sidebar_position: 2) with the foundational context needed to understand everything else.

Required sections in order:

1. Mental Model - The conceptual framework the SDK uses
2. Capabilities - Table linking to major features/needs (this defines what goes in `capabilities/` folder)
3. Data Structures - Cross-cutting types referenced throughout the SDK
4. API - Minimal interface needed to use the SDK

### Step 4: Create capability-specific pages

For each capability listed in the core.md Capabilities table, create a dedicated page. If there are multiple capabilities, organize them in a `capabilities/` subfolder with its own `index.md`.

Pages that aren't capabilities (error handling, utilities) belong at the top level, not in `capabilities/`.

### Step 5: Verify documentation standards

Ensure all documentation follows these standards:

- Every code snippet is verbatim from source with exact GitHub links
- No fabricated code examples (write tests if you need examples)
- Proper source attribution for all behavioral claims
- Diagrams cite their sources
- Focus on the dependency itself, not how your project uses it
- Include prose and context, not just code dumps

### Step 6: Configure sidebar positioning

Set `sidebar_position` values to ensure the `docs/dependencies/` section appears at the bottom of the sidebar. Check other top-level sections' values and use a higher number.

### Step 7: Build verification

Run `pnpm build` in the `docs/` directory before finishing. The documentation must build without errors.

## Key Principles

### Source Attribution

**Every code snippet must be verbatim from the source with exact GitHub links.**

Format: `From [path/to/file.py:start-end](https://github.com/org/repo/blob/<commit>/path/to/file.py#Lstart-Lend)`

Example:

```
From [`examples/quick_start.py:15-24`](https://github.com/anthropics/claude-agent-sdk-python/blob/d553184/examples/quick_start.py#L15-L24):
```

If you cannot find verbatim source for something, either:

- Write a test in our codebase that passes and reference that
- Link to upstream documentation that defines the structure
- Do not include it

**Never fabricate code examples.** If you write example code, it must be tested.

**Type definitions are not sources for behavior.** A type showing `HookEvent = Literal["PreToolUse"] | Literal["PostToolUse"]` tells you what hooks exist, not when they fire or how they interact.

For behavioral claims (execution order, event flows, lifecycle diagrams):

1. Find the actual implementation in source code, OR
2. Link to upstream documentation that defines the behavior, OR
3. Don't make the claim

Example: A hook execution flow diagram should cite the upstream docs that define when each hook fires, not just the type definition listing hook names.

### Index Files Structure

Index files (`index.md`) should contain:

- Package overview and when to use it
- Metadata table (package version, upstream docs link, source repo link)
- Installation instructions
- Section index with links to child pages and brief descriptions

**Metadata table format:**

```markdown
|                   |                             |
| ----------------- | --------------------------- |
| **Package**       | `package-name>=1.0.0`       |
| **Upstream docs** | https://example.com/docs    |
| **Source repo**   | https://github.com/org/repo |
```

Index files should **not** contain:

- Detailed API documentation (put in child files)
- Code examples beyond a minimal quick start
- Exhaustive lists of types, options, or configurations

**Child pages** should **not** repeat upstream docs/source links—keep those only in the index.

Follow the pattern in `docs/code-base/index.md` for navigation-focused index pages.

### Core File Organization

The core.md file provides foundational context needed to understand everything else. It should contain only the bare minimum for coherent understanding.

**Required sections in order:**

1. **Mental Model** — The conceptual framework the SDK uses. What abstractions does it expose? How do they relate?

2. **Capabilities** — A table linking to the major features/needs the SDK addresses. Link directly in the capability name:

   ```markdown
   | Capability                      | Description                                               |
   | ------------------------------- | --------------------------------------------------------- |
   | [Streaming](./streaming.md)     | Receive incremental updates as Claude generates responses |
   | [Permissions](./permissions.md) | Control tool execution via modes and callbacks            |
   ```

   **This table is the authoritative list of capabilities.** When organizing files into a `capabilities/` subfolder, only include pages listed in this table. Other pages (like error handling, utilities) belong at the top level, not in `capabilities/`.

3. **Data Structures** — Cross-cutting types referenced throughout the SDK. Define them once here, reference from other pages.

4. **API** — The minimal interface needed to use the SDK. Keep examples concise; detailed usage goes in feature-specific pages.

**What belongs in core.md vs separate files:**

The core file is for context that's necessary to understand _everything else_. A topic belongs in core.md if readers need it before they can make sense of other pages. If a topic can stand alone without requiring the reader to first understand it, extract it to its own file.

For example, in an RBAC library, permissions would be core. In a streaming SDK where permissions are just one configuration option, they belong in a separate file.

**Referencing shared types:**

Instead of duplicating definitions, link to core.md:

```markdown
- `content`: List of [content blocks](./core.md#content-block-types)
```

```markdown
All client methods produce a stream of [Message objects](./core.md#message-types).
```

### Tables vs Lists

See [Conventions](../../../docs/code-base/documentation/conventions.md#tables-vs-lists) for general guidance.

### Documenting Data Structures

See [Conventions](../../../docs/code-base/documentation/conventions.md#documenting-data-structures) for general guidance.

**Additional considerations for dependency docs:**

- If the SDK parses data into a dataclass, document it as that class with its fields
- If it's a raw dict (like `StreamEvent.event`), note that and show the structure

Check the source code to see how the SDK actually handles the data:

```bash
grep -r "content_block" /tmp/repo/src --include="*.py" -A 5
```

### Prose and Context

Documentation is not just code dumps. Every section needs:

1. An introductory sentence explaining what this is and when to use it
2. Code examples with attribution
3. Explanatory text connecting concepts

Bad:

```markdown
## Event Types

| Event Type      | Description     | Key Fields |
| --------------- | --------------- | ---------- |
| `message_start` | Response begins | `message`  |
```

Good:

```markdown
## Event Types

The `event.type` field indicates what kind of streaming event you received. Each event type has a different structure.

Event structures are defined by the [Anthropic API streaming specification](https://docs.anthropic.com/en/api/streaming).

### message_start

Response begins.

- `type`: `"message_start"`
- `message`: Partial message object
  - `id`: String message identifier
    ...
```

### Focus on the Dependency

Document the dependency itself, not how your project uses it. Avoid phrases like "Here's how mekara handles streaming" — focus on the SDK's behavior and API.

### Diagrams

See [Conventions](../../../docs/code-base/documentation/conventions.md#diagrams) for general Mermaid usage.

**Additional requirement for dependency docs:** Every diagram must cite a source for the flow it represents (upstream docs, source code, etc.).

### File Structure

The standard file structure is:

```
docs/dependencies/
├── index.md                # sidebar_position: high number (bottom)
└── <package-name>/
    ├── _category_.json     # { "collapsed": true }
    ├── index.md            # Package overview + section index only
    ├── core.md             # Mental model, data structures, minimal API
    ├── capabilities/       # Only pages listed in core.md capabilities table
    │   ├── index.md
    │   └── <capability>.md
    └── <other>.md          # Non-capability pages (errors, utilities) at top level
```

### Sidebar Configuration

- Use `sidebar_position` in frontmatter to control ordering
- The `docs/dependencies/` section is top-level and should appear at the very bottom of the sidebar—check other top-level sections' `sidebar_position` values and use a higher number
- Individual dependencies should be collapsed by default (create `_category_.json` with `{ "collapsed": true }`)
