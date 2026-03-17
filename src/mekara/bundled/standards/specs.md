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

One to three sentences describing what the module does and why it exists.

It should be clear from reading this what role the module plays in the system. Any potential consumers of this module should be able to discern whether it would be useful for them or not.

### Scope

What the module is responsible for and, critically, what it is NOT responsible for. Explicit scope boundaries keep abstractions clean and easy to reason about. They also make scope creep highly visible and legible to humans, creating friction to discourage LLM agents from shoehorning unrelated changes onto existing modules when entirely new modules would make much more sense.

**Example:**

```markdown
## Scope

**In scope:**

- Loading script files from disk
- Resolving script names to file paths

**Out of scope:**

- Executing scripts (handled by `mcp/executor.py`)
- Building CLI commands (handled by `cli.py`)
```

### Requirements

Behavioral guarantees the module provides, including documented edge cases.

Each requirement should be specific enough that two independent implementations satisfying the same requirements would produce observably equivalent behavior. Edge cases that are currently handled but not obvious should be explicitly documented here — if a behavior isn't in the requirements, it's not guaranteed.

**Example:**

```markdown
## Requirements

- Loaded scripts always contain fully-processed content (NL source with arguments substituted and standards injected)
- Resolution searches local, user, then bundled directories in that order
- Compiled scripts must exist at the same or higher precedence level as their NL source
```

### Architecture

A description of module structure, including file organization, data flow between components, and key invariants the code must obey. Invariants are architectural rules that constrain implementation. They should be phrased as assertions that can be verified by inspection — "Clean architecture" is not an invariant, but "The executor must remain stateless" is.

Use directory trees and Mermaid diagrams when possible to illustrate the high-level design.

### Implementation

The concrete details of the module, consisting of:

- **Data Structures** — Every enum, class, type alias, or other prominent data structure the module defines or exports. Include all fields with types and descriptions.
- **Interface** — Public functions and methods with signatures, parameters, and return types.
- **Algorithms** — Algorithmic details for non-trivial logic. Include edge cases and fallback behavior.

This is the most detailed section. The "reconstruct from spec" test applies here: given only this section and the sections above, an implementer should be able to produce code that passes all tests and satisfies all requirements, with differences limited to local variable names, formatting, and other trivial choices.

**Example:**

```markdown
## Implementation

### Data Structures

#### `LoadedNLScript`

| Field       | Type             | Description                                 |
| ----------- | ---------------- | ------------------------------------------- |
| `target`    | `ResolvedTarget` | Resolution result with file paths           |
| `nl_source` | `str`            | Raw NL file content before processing       |
| `prompt`    | `str`            | Processed content ready for LLM consumption |

### Interfaces

#### `load_script(name, arguments, project_root) -> LoadedNLScript | LoadedCompiledScript`

Resolves and loads a script by name, returning fully-processed content.

### Algorithms

#### Precedence resolution

Searches local, user, then bundled directories in order. Compiled scripts
must exist at the same or higher precedence level as their NL source.
```

## Guidelines

- **Update the spec when the code changes.** The spec is the source of truth. If you change the code without updating the spec, the spec becomes a lie and loses its value. Treat spec-code divergence as a bug.

### Precedence Rule

Each section constrains everything below it:

- **Purpose** defines what the module does. Scope must be consistent with Purpose.
- **Scope** defines boundaries. Requirements must operate within Scope.
- **Requirements** define guarantees. Architecture must support all Requirements.
- **Architecture** defines structure. Implementation must fit the Architecture.

When reviewing a proposed change to a module, check it against the hierarchy top-down. A change that satisfies a lower-level requirement but violates a higher-level constraint is wrong — fix the change, not the constraint (unless the constraint itself needs evolving, which requires explicit human approval).
