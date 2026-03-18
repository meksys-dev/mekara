---
sidebar_position: 5
sidebar_label: "Specifications"
---

# Standard Mekara Specs

A spec is the natural language source of truth for a system, including systems that are subsystems of larger systems. It should describe a system with enough detail to fully reconstruct the system from the spec alone.

It is the authoritative reference for what the individual components of a system are, what the system does, and how its components interact to perform those functions. Only trivial differences should exist between different valid interpretations of the spec -- anything of importance should be nailed down explicitly.

:::note[Specs vs. Design Documents]
[Design Documents](./design-documents.md) describe _transitions_ — how to get from state A to state B. They have implementation plans with phases and checkboxes, and become obsolete once the work is done.

Specifications describe _steady state_ — what the system looks like when it's done. They are living documents that stay current as the system evolves.
:::

## Standard Structure

Specs use a fixed hierarchy of five sections. Each section constrains the sections below it — lower sections must be fully consistent with higher ones. If a conflict is detected and the most obvious solution is to edit the higher section, a human must be notified of this finding.

:::info[Terminology]

Because the systems being described here are most often software modules or services that form part of a greater whole, for the rest of this document:

- **"module"** will be used to refer to the (sub)system being specced out
- **"system"** will refer to the larger system that a module lives in

In case the spec is for a top-level system, simply ignore all references to "system."

:::

### Purpose

One to three sentences describing what the module does and why it exists. Lead with the high-level role the module plays, then mention specifics only as examples of that role.

It should be clear from reading this what role the module plays in the system. Any potential consumers of this module should be able to discern whether it would be useful for them or not.

**Example:**

```markdown
## Purpose

The scripting module provides everything needed to go from a script
name to a ready-to-execute script object. This includes runtime
primitives, name-to-path resolution, NL prompt construction,
standards injection, and auto step execution.
```

### Scope

What the module is responsible for and, critically, what it is NOT responsible for. Explicit scope boundaries keep abstractions clean and easy to reason about. They also make scope creep highly visible and legible to humans, creating friction to discourage LLM agents from shoehorning unrelated changes onto existing modules when entirely new modules would make much more sense.

**Out-of-scope items should define boundaries relative to what's in scope** — not list unrelated things from around the project. Each out-of-scope item should reference an in-scope capability and clarify where the module's responsibility ends. For example, "orchestrating the execution of loaded scripts" as an out-of-scope item draws a boundary relative to the in-scope capability of "loading scripts," while "CLI command registration" is just a random other module and doesn't help a reader understand this module's boundaries.

**Example:**

```markdown
## Scope

**In scope:**

- Loading script files from disk
- Resolving script names to file paths

**Out of scope:**

- Orchestrating script execution across multiple steps
  (the module loads scripts but does not run them)
- Deciding when to execute steps
  (the module provides execution harness but does not sequence steps)
```

### Requirements

Requirements describe the **actions** the module performs, organized as prose subsections. Each requirement names an action ("resolves names", "loads scripts", "models primitives") with constraints and details hanging off it. Even pure data modeling is an action ("models the step types that scripts are built from").

Use prose for the main description of each requirement. Use bullet points only for lists of constraints or enumerated items within a requirement — not as the primary format for requirements themselves.

**Example:**

```markdown
## Requirements

### Loads scripts into ready-to-use objects

The module takes a script name and returns a fully-processed object
that consumers can use directly without additional loading.

**Resolution:** The module resolves script names to file paths by searching:

- project
- user
- bundled

in that order, taking the first match.

**Constraints:**

- Every resolved script has an NL source.
- Compiled scripts must exist at the same or higher precedence level
  as their NL source.
```

### Architecture

The architecture section describes the module's **public contract** — everything a consumer needs to know to use the module correctly. It should be organized around how consumers interact with each capability, not as a flat reference dump.

**Tell a story.** Each subsection should correspond to a capability from Requirements. Within each subsection, introduce the types, functions, and data flow that a consumer encounters when using that capability. Types appear in context — "you call this function, you get back this type, here's what's on it" — not in alphabetical order or grouped by source file.

**What belongs in Architecture:**

- Public types with their fields, relationships, and derived properties — if a type is returned by a public function, carried on a public object, or raised as an error consumers catch, it belongs here
- Public functions with their signatures and behavior
- Data flow showing how pieces connect (Mermaid diagrams are encouraged)
- Invariants that constrain the public contract (e.g., "these are distinct types, not subtypes" or "this field is always present")

**What does NOT belong in Architecture:**

- File layout (language-specific)
- Private helpers and internal types
- Algorithm pseudocode
- Language-specific design choices that don't affect the public contract

**Invariants** are architectural rules that constrain the public contract. They should be phrased as assertions that can be verified by inspection. Only include invariants about _this_ module — not about other modules' behavior. Don't restate requirements as invariants; if a requirement already says "NL source is always present," an invariant saying the same thing is redundant.

**Example:**

```markdown
## Architecture

### Script Loading

A consumer loads a script by calling `load_script(name, request, base_dir)`.
It returns either a `LoadedNLScript` or a `LoadedCompiledScript`, both
fully processed and ready to use.

If the script cannot be found or loaded, `load_script` raises `ScriptLoadError`.

The returned object carries a `target` field of type `ResolvedTarget`,
which provides metadata about where the script was found:

**`ResolvedTarget`:**

| Field      | Type                 | Description                              |
| ---------- | -------------------- | ---------------------------------------- |
| `compiled` | `ScriptInfo \| None` | Compiled script info, or None if NL-only |
| `nl`       | `ScriptInfo`         | NL source info (always present)          |
| `name`     | `str`                | Canonical name with colons preserved     |

The loaded script types share content fields but are distinct types
(not subtypes of each other) — consumers must be able to distinguish
them by type narrowing. Both carry:

| Field       | Type             | Description                      |
| ----------- | ---------------- | -------------------------------- |
| `target`    | `ResolvedTarget` | Resolution result                |
| `nl_source` | `str`            | Raw NL content before processing |
| `prompt`    | `str`            | Processed content ready to use   |

`LoadedCompiledScript` adds one field:

| Field       | Type              | Description                                              |
| ----------- | ----------------- | -------------------------------------------------------- |
| `generator` | `ScriptGenerator` | The script's generator (from calling `execute(request)`) |
```

### Implementation

How the module fulfills the public contract internally. This section is language- and stack-specific — a reimplementation in another language would replace this section while keeping Purpose through Architecture intact.

Contents:

- **File layout** — how the module is organized on disk
- **Design choices** — language-specific decisions (e.g., "frozen dataclasses for immutability", "importlib for module loading")
- **Internal types** — types that consumers never see (constants, private helpers, internal enums)
- **Algorithms** — step-by-step logic for non-trivial operations, including edge cases and fallback behavior

This is the most detailed section. The "reconstruct from spec" test applies here: given only this section and the sections above, an implementer should be able to produce code that passes all tests and satisfies all requirements, with differences limited to local variable names, formatting, and other trivial choices.

**Example:**

```markdown
## Implementation

### File Layout

src/mekara/scripting/
├── **init**.py # Package exports (runtime primitives only)
├── runtime.py # Step types and result types
├── resolution.py # Name → path resolution
├── loading.py # Script loading entrypoint
├── auto.py # Auto step execution
├── nl.py # NL prompt construction
└── standards.py # Standards resolution and loading

### Design Choices

- `ResolvedTarget` and `ScriptInfo` are frozen dataclasses
  (immutable after construction)
- Compiled modules are loaded via `importlib.util`

### Internal Types

#### Precedence Level Constants

| Constant                | Value | Description    |
| ----------------------- | ----- | -------------- |
| `_LOCAL_COMPILED_LEVEL` | 1     | Local compiled |
| `_LOCAL_NL_LEVEL`       | 2     | Local NL       |
| ...                     | ...   | ...            |

### Algorithms

#### Precedence Resolution

`resolve_target(name, base_dir)`:

1. Compute underscore variant of name
2. Find NL source at highest precedence (local, user, bundled)
3. If no NL found, return None
4. Find compiled at same or higher precedence than NL
5. Build canonical name and return ResolvedTarget
```

## Guidelines

### Writing Guidelines

- **A spec covers exactly one module — nothing more.** Do not spec out types, functions, or behaviors from other modules, even if those modules interact closely with the one being specced. If a neighboring module's interface matters, reference it by name; don't reproduce its contents.
- **Don't spec types this module doesn't use.** If a type is defined in this module but only raised or used by another module (never by this module itself), it's misplaced code — flag it for relocation, don't include it in the spec.
- **Every piece of data must have a clear job.** For every type, field, and function in Architecture, you should be able to articulate when a consumer encounters it and why they need it. If you can't, it probably doesn't belong. Writing the spec is an opportunity to identify dead code, redundant fields, and misplaced types.
- **No redundancy between sections.** Each piece of information should live in exactly one place in the hierarchy. If a requirement is restated as an invariant, one of them is wrong — either the requirement is incomplete (add the detail there) or the invariant is redundant (remove it).
- **Update the spec when the code changes.** The spec is the source of truth. If you change the code without updating the spec, the spec becomes a lie and loses its value. Treat spec-code divergence as a bug.

### Precedence Rule

Each section constrains everything below it:

- **Purpose** defines what the module does. Scope must be consistent with Purpose.
- **Scope** defines boundaries. Requirements must operate within Scope.
- **Requirements** define guarantees. Architecture must support all Requirements.
- **Architecture** defines structure. Implementation must fit the Architecture.

When reviewing a proposed change to a module, check it against the hierarchy top-down. A change that satisfies a lower-level requirement but violates a higher-level constraint is wrong — fix the change, not the constraint (unless the constraint itself needs evolving, which requires explicit human approval).
