---
sidebar_position: 2
sidebar_label: "Documentation"
---

import Version from '@site/src/components/Version';

# Standard Mekara Documentation

This page documents the documentation conventions for all [standard Mekara <Version /> projects](./project.md). Individual projects may have additional conventions documented in their own `conventions.md`.

## Documentation Layout

The standard Mekara project comes with a few subdivisions:

```
docs/
├── index.md
├── usage/
├── development/
│   ├── index.md
│   └── workflows.md         # project-specific commands
├── code-base/
│   ├── index.md
│   ├── <project-name>/      # main project implementation details
│   ├── documentation/       # documentation site implementation
│   └── ...                  # other subsystems as needed
├── dependencies/            # optional
└── roadmap/                 # optional
```

These are the common recommended sections, not an exhaustive list—projects may add other sections as needed.

- `index.md` is an introduction to the project: what it is, why it's useful, how to navigate the documentation website.
- `usage/` is a guide for the end users of this project. A user should not have to read anything outside of this section in order to understand how to use the product.
- `development/` is a _how-to_ guide for developers of this project. Any actions or processes that a developer might be expected to perform or interact with in the course of development (e.g. repo setup, artifact builds, CI checks, etc.) should be documented here.
- `code-base/` is a _navigation_ guide for developers of this project. Any navigation aids (such as this very page) that helps a developer find and understand the code, docs, data, or any other necessary information should be documented here.
- `dependencies/` (optional) contains essential information on the project's major yet obscure dependencies that developers (and LLMs) might not be fully familiar with. Quickstart introduction guides and documentation of dependency quirks should all live here. Not all projects need this section.
- `roadmap/` (optional) contains detailed plans for the development of future features. These plans may be in-progress, and allows for a [trunk based merge strategy](https://trunkbaseddevelopment.com/) with short-lived implementation branches to avoid keeping large features stuck in merge hell. Not all projects need this section.

**Quick decision tree:**

- Is it a command users run? → `usage/`
- Is it a command developers run? → `development/`
- Is it explaining how code works internally? → `code-base/`
- Is it explaining how code interfaces with an external API? → `dependencies/`
- Is it a design for something not yet built? → `roadmap/`

More details can be found below:

### usage/

**Answers:** "As an end user, how do I use this product?"

End-user documentation: installation, CLI usage, and user-facing features.

**Update when:** You change how users interact with the product (new commands, changed flags, output format changes).

- Example: New commandline command is added
- Example: Major user-noticeable change to existing command
- Example: New page in website is added
- **Does not include**: Internal implementation details, development workflows, or how to build/test the project

**Clarification: User-Noticeability**

Subtleties and corner cases that only matter to maintainers belong in `code-base/`, not `usage/`. This includes descriptions of UX behavior -- while these certainly affect the user's interaction with the product, the user is unlikely to notice or care unless it gets in their way.

#### Usage-specific Guidelines

When documenting user-noticeable features in `docs/docs/usage/`:

- **Avoid duplication**: Don't repeat general behaviors in individual command docs. If something applies to all Mekara commands (like project root detection), document it once in `usage/index.md`

- **Error message documentation:** Show the error first, then explain what it means and how to resolve it
  - Good:

    ```
    **Error:** ✗ Could not find project root

    What this error means: ...
    To resolve this error, ...
    ```

  - Bad: "If you see this error: ..." (explanation before the actual error)

### development/

**Answers:** "As a developer on this project, how do I use the project's development tooling?"

Development workflows and processes for both human and AI agents. Includes build commands, test commands, development workflows, and how to run things.

**Update when:** You change build commands, add new dev tools, modify CI/CD, or update development conventions.

- Example: "Run `poetry run pytest -m 'not requires_llm'` to skip LLM tests"
- Example: "Use `poetry install --with dev` to install dependencies"
- Example: URLs to access dev services (e.g., `http://localhost:4913` for docs site)
- Example: Login/authentication steps for dev tools
- **Does not include**: What the code does (that's `code-base/`) or how end users interact with the CLI (that's `usage/`)

**Project-specific commands**: The `development/workflows.md` file documents custom project-specific commands and workflows. When you create new systematized commands with `/systematize`, they will be documented here by default.

**Clarification: "Usage" vs "Live Development Usage"**

- If the content is about _running commands during development_ (flags, env vars, where local artifacts go, how to re-record fixtures), it belongs in `development/` (typically `development/build-and-test.md`).
- If the content is about _consuming internal subsystems from code_ (protocol boundaries, data structures, how to wire components together), it belongs in `code-base/`.

### code-base/

**Answers:** "As a developer on this project, how do I implement/fix this feature?"

Navigation guide to the codebase as a static entity: implementation details, gotchas, and architecture for re-implementors. Explains what exists, how it's structured, and why certain decisions were made.

**Update when:** You add new modules, change architecture, or discover important implementation details that future maintainers need to know.

- **After refactoring**: Update `code-base/` with patterns learned during the refactoring session. Document code smells you encountered, why they were problematic, and the better pattern you applied. This helps future developers recognize and avoid similar issues.
- **Does not include**: The actual code (readers can look at that directly), active workflows or commands (that's development/), or UI details already in `usage/`

**Clarification: Consumer vs Maintainer**

- "How do I use this subsystem from within the repo?" (interfaces, boundaries, mental model) belongs in `code-base/`.
- "How does this subsystem work internally and what pitfalls/failed approaches exist?" also belongs in `code-base/` (often as a dedicated pitfalls/implementation page), but keep _command-running_ instructions in `development/`.

**Clarification: User vs Developer**

- User-facing explanations ("what is this?") go in `usage/`
- Implementation details ("how does this work?") go in `code-base/`

#### Code-specific Guidelines

When documenting your own code in `docs/docs/code-base/`:

- **NEVER put code verbatim into docs**: Documentation should explain concepts, architecture, and behavior - not duplicate code. When documenting implementation details, describe what the code does and why, reference the source file and function names, and explain the reasoning. Do not paste large code blocks into documentation files. Small code snippets (including snippets with `...` as a placeholder for elided content) are acceptable for illustration, but anything substantial should remain in the source code with documentation explaining it.
- **Don't duplicate code, but do illustrate patterns**: Documentation should explain concepts, not duplicate source files. However, small illustrative code snippets are essential to show what patterns actually look like.
  - **Don't**: Show entire functions or components - readers can look at the source directly
  - **Do**: Include focused snippets that illustrate specific patterns or gotchas
  - **Use `...` placeholders** to show structure without duplicating entire implementations
  - **Common mistakes**:
    - Bad: Showing the entire configuration initialization block
    - Good: "The SDK is configured with `allowed_tools` for safe operations and `setting_sources` to load saved rules" (for simple config)
    - Good: Focused code snippet showing a specific pattern (see "Code Snippets and Explanations" in General Guidelines)

- **Use proper heading hierarchy**: Use markdown headings (`####`) instead of bolded text for section titles
- **Avoid line numbers**: Don't reference specific line numbers (e.g., `cli.py:220-308`) as they change frequently
  - Good: "in the `permission_callback` function in `src/myproject/cli.py`"
  - Bad: "in `permission_callback` (cli.py:220-308)"
- **List items, not code**: When describing what exists in the code, list the actual items rather than showing code
  - Good: "The following tools are auto-allowed: Read, Glob, Grep..."
  - Bad: `` `auto_allow_tools = {"Read", "Glob", "Grep"}` ``
- **Use a dedicated "Edge cases" section** instead of admonitions.
  - Place edge case writeups in the most specific existing doc that fits (e.g., subsystem docs).
  - Check existing docs for a suitable home before putting edge cases in roadmap notes.
- When creating a dedicated "Pitfalls" page (or section) to capture edge cases and failed approaches, standardize each entry so readers can scan quickly and maintainers can add new items consistently.

  Use the same headings for every item:
  - **Symptoms**: What you observe (errors, surprising behavior, timing issues)
  - **Root cause**: Why it happens
  - **Resolution**: What to do instead
  - **References**: Links to the relevant code/docs

- **Document bug fixes that reveal implementation pitfalls.** Bug fixes must be documented in `code-base/` even when:
  - The fix is "just a bug fix" with no user-facing change
  - The code change is small (a single conditional check)
  - The "what" hasn't changed—only the "why" is new information

  The test: would a future implementer need to rediscover this through debugging? If the bug involved understanding how two components interact, how formatting responsibilities are split, or why certain wording matters—document it.

  Use admonitions to highlight pitfalls in the relevant section. Examples of bugs worth documenting:
  - Duplicate output from two formatters both adding the same instruction
  - Race conditions between async components
  - Subtle differences in wording that affect LLM behavior

### dependencies/

**Answers:** "As a developer on this project, how do I develop code that interfaces with this external library?"

Documentation for external packages the project depends on, comprehensive enough for reimplementation without upstream docs.

**Update when:**

- You add a new dependency that you are unfamiliar with and requires a lot of research (saves future agents and devs from redoing your research)
- The API of an existing dependency changes
- You discover a surprising quirk of this dependency
- You discover anything about the dependency's behavior that is not documented in its official docs

#### Dependency-specific Guidelines

When documenting external dependencies in `docs/docs/dependencies/`:

- **Be comprehensive**: Include all aspects of the dependency that we actually use in our project
- **Purpose**: Future developers (human and AI) should not need to research the dependency's official docs or comb through source code to understand how we use it
- **Cite sources**: Always link to official documentation and quote critical specifications verbatim
  - Example: Per [Claude Code Settings](https://code.claude.com/docs/en/settings#permission-settings): "Bash rules use prefix matching, not regex"
  - **For source code citations**: When citing specific code from a dependency's repository, link to the specific file and line range on GitHub using a pinned commit hash. Format: `[`path/to/file.py:line-range`](https://github.com/org/repo/blob/COMMIT/path/to/file.py#Lstart-Lend)`. This applies to all dependencies with public repositories.
    - Example: ``[`_internal/query.py:163-165`](https://github.com/org/repo/blob/d553184/src/package/_internal/query.py#L163-L165)``
    - Never use local `/tmp/` paths or other temporary file references in documentation
- **Include examples**: Show real code examples demonstrating our usage patterns
  - **Do not** make up your own code examples. Either use examples verbatim from the official docs, or use examples from a working code-base. Anything else is not guaranteed to work, no matter how much sense it makes. Give sources for your examples so that the reader can look at the code in-context.
- **Document edge cases**: If behavior is non-obvious (e.g., prefix matching vs regex), document it explicitly with citations
- For code snippet guidelines, see "Code Snippets and Explanations" in General Guidelines

#### Documenting Dependency Bugs

When you discover a bug in a dependency that requires a workaround in the project code:

1. **Document the bug** in the dependency's documentation folder (e.g., `docs/docs/dependencies/some-library/known-issues.md`):
   - **Status**: Indicate if the bug is active and the version/commit it was observed in
   - **Root cause**: Explain what's actually happening at the code level with file/line references
   - **Evidence**: Show the conflicting type annotations, TODO comments, or other proof
   - **Symptoms**: Describe how the bug manifests (error messages, unexpected behavior)
   - **Data format**: If relevant, show the actual vs. expected data structures
   - **Expected behavior**: What should happen when the bug is fixed
   - **Impact**: Severity assessment (Low/Medium/High) and what applications must do to work around it
   - **Keep it focused**: Dependency docs document the dependency only, not our code

2. **Document the workaround** in the code documentation folder (e.g., `docs/docs/code-base/our-module/`):
   - Add a bold **"Workaround for [Dependency] bug:"** prefix to make it obvious
   - Link to the bug documentation in the dependency's known-issues file for context
   - Explain what our workaround implementation does and why it's necessary
   - This is where implementation details live (function names, approach, data conversions, etc.)

3. **Separation of concerns**:
   - **Dependency docs** (`docs/docs/dependencies/`): Document the dependency itself, including its bugs
   - **Code-layout docs** (`docs/docs/code-base/`): Document our code, including workarounds for dependency bugs
   - **Cross-reference**: Code-layout docs reference dependency docs for context, but not vice versa

**Example structure:**

In `docs/docs/dependencies/foo/known-issues.md`:

```markdown
## Some Bug Name

**Status:** Active bug as of version 1.2.3

### Root Cause

[what's happening in the dependency]

### Symptoms

[how the bug manifests]

### Expected Behavior

[what should happen when fixed]

### Impact

Medium - Applications must implement conversion logic to handle this.
```

In `docs/docs/code-base/our-module.md`:

```markdown
#### Some Feature

**Workaround for Foo bug:** Brief description. See [Foo Known Issues: Bug Name](../../dependencies/foo/known-issues.md#bug-name) for context on the underlying issue.

Our `workaround_function()` implementation:

1. Does X to handle the bug
2. Does Y for future compatibility
3. Does Z for error handling
```

### roadmap/

**Answers:** "As a developer on this project, what should I build next?"

Design documents for planned features. These may be in-progress features. All documents here should adhere to the [design documents standard](./design-documents.md).

**Update when:** You're designing a new feature and want to capture the vision and technical approach before implementation.

## General Guidelines

### Formatting

- Use bullet points for lists of rules or guidelines.
- Indent code blocks and continuations under their parent bullet to keep them in the same `<li>`.
- Do not insert new headings mid-list. If you need to add a new section, end the list first so you don't break the structure of the surrounding bullets.
- Use bold sparingly—only to emphasize critical rules that must not be missed.
- Do not use horizontal rules (`---`) as section dividers. Use markdown headings to separate sections instead.

### Writing Style

- **Integrate with existing information, don't repeat it.** When adding new details to existing documentation, incorporate them into the existing prose flow rather than repeating the entire sentence with the new information appended.
  - Good: Change "Parses JSONL chat transcript files" to "Parses [Claude Code JSONL transcript files](https://docs.anthropic.com/claude/docs/chat-history-format)"
  - Bad: Add a new sentence saying "We use Claude Code's JSONL format" after the existing description
  - When the existing text flows well, edit it to include the new detail inline rather than adding redundant sentences
- **Link first mention.** When referencing an external resource or format, link it on the first mention of the term, not in a separate explanatory sentence afterward.
- **Lead with the requirement, then the implementation.** When documenting a pitfall or edge case, state the behavioral requirement first, then describe how the code enforces it or what configuration is required.
- **Document current state, not setup instructions.** Documentation should describe the current state of the system, not provide setup instructions for things that are already set up once the docs are merged to main.
  - Bad: "To enable GitHub Pages deployment: 1. Go to Settings → Pages 2. Set Source to GitHub Actions"
  - Good: "GitHub Pages is configured in Settings → Pages with Source set to GitHub Actions"
  - If something requires initial setup that hasn't been done yet, document where the configuration lives and what it should be set to, not step-by-step instructions assuming it hasn't been configured.
- **Link to other docs**: Use markdown links to reference other documentation pages, not plain file paths
  - Good: `See [Feature X](../code-base/feature-x.md) for implementation details`
  - Bad: `See docs/docs/code-base/feature-x.md for details`

### Code Snippets and Explanations

These guidelines apply whenever code appears in documentation, regardless of section (`usage/`, `code-base/`, `dependencies/`, etc.):

- **Pair code with explanations**: Never drop a code snippet into documentation without explanatory text. Provide context that explains what the code does, when to use it, what parameters mean, and why the pattern is used.
  - Don't assume code is self-explanatory
  - Bad: A heading followed immediately by code with no explanation
  - Bad: Just showing code without explaining what parameters mean or why the pattern is used
  - Bad: Just describing the pattern in words without showing what it looks like in code
  - Good: A heading, followed by 1-2 sentences of context, then the code example
  - Good: Code snippet + explanation (for patterns that benefit from seeing the code)
  - Example of good balance:

    ````markdown
    Import from `@site/src/components/Foo` and pass `bar` (description of parameter):

    ```tsx
    import Foo from "@site/src/components/Foo";

    <Foo bar="value" />;
    ```

    See `docs/example.md` for a complete working example.
    ````

- **Explain WHY, not just WHAT**: When documenting a pattern or recommendation, explain the reasoning and consequences.
  - **State the consequences of not following the pattern**: What breaks? What goes wrong? What subtle bugs emerge?
  - **Don't just assert**: Never write "Use X instead of Y" without explaining why X is better and what happens if you use Y
  - Examples:
    - Bad: "Use `sys.exit()` instead of `ctx.exit()`"
    - Good: "Use `sys.exit()` instead of `ctx.exit()`. When running with `standalone_mode=False` (used in tests), `ctx.exit()` does not raise `SystemExit`, which means tests will incorrectly see exit code 0 even when commands fail. This causes test failures to go undetected."
  - The reader should understand not just the rule, but the underlying reason and what breaks if they ignore it

### External Source Code Citations

When citing specific code from an external library's repository, link to the specific file and line range on GitHub using a pinned commit hash:

```markdown
[`path/to/file.py:163-165`](https://github.com/org/repo/blob/d553184/src/package/path/to/file.py#L163-L165)
```

This format applies to all external dependencies with public repositories. The pinned commit hash ensures the link remains valid even as the repository evolves.

### File & Directory Naming

- Use kebab-case for all file and directory names (e.g., `build-and-test.md`, `code-base/`). This ensures lowercase URLs.
- Name files using the kebab-cased version of their sidebar title (e.g., `continuous-integration.md` for title "Continuous Integration").
- Every folder should have an `index.md` that serves as the section introduction. Include a bulleted list that links to all direct children in that folder:
  - Good: `- [VCR Recordings](./vcr-recordings.md) – Brief description`
  - Good: `- [Quickstart](./quickstart/) – Brief description` (for subdirectories)
  - Bad: Just describing the features without linking to them

### Tables vs Lists

- Tables are for enums and simple key-value mappings:
  - Permission modes: `"default"`, `"acceptEdits"`, `"plan"`, `"bypassPermissions"`
  - Feature comparisons: query() vs ClaudeSDKClient
  - Simple mappings where each row has the same structure
- Lists are for data structures with fields:
  - Message types with their fields
  - Event types with their fields
  - Any structure where you need to show nested properties
- The test: if you find yourself putting structured data (like "Key Fields: `index`, `delta`") into a table column, it should be a list with fields expanded instead.

### Data Structures

- Each data structure should be a heading (###) with its fields as a nested list:

  ```markdown
  ### message_start

  Response begins.

  - `type`: `"message_start"`
  - `message`: Partial message object
    - `id`: String message identifier
    - `type`: `"message"`
    - `role`: `"assistant"`
    - `model`: String model name
  ```

- Expand nested structures fully unless they're documented elsewhere. If documented elsewhere, link to that section:

  ```markdown
  - `delta`: [Delta object](#delta-types)
  ```

### Diagrams

- Use Mermaid diagrams instead of ASCII art.
- **Always use `flowchart TD` (top-down) or `flowchart TB` (top-bottom).** Horizontal flows (`LR`) get squished in narrow viewports and on mobile. There are no exceptions.

  ````markdown
  ```mermaid
  flowchart TD
      A[Step 1] --> B[Step 2]
      B --> C{Decision?}
      C -->|Yes| D[Path A]
       C -->|No| E[Path B]
  ```
  ````
