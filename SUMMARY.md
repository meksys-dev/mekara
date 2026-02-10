# Mekara: A Complete Summary

## What Is Mekara?

Mekara (មករា -- Khmer for "January," the start of a new cycle) is a **"Workflows as Code"** tool that extends Claude Code with automation scripts. It runs as an MCP (Model Context Protocol) server inside Claude Code, providing `/commands` that blend deterministic automation with AI judgment.

The tagline: *You be you, if you were fast like AI and consistent like code.*

## Why Does Mekara Exist?

### The Core Problem

When you use Claude Code slash commands (skills), **everything gets delegated to the AI** -- even completely deterministic steps like running `git checkout -b my-branch` or `npm install`. Each step requires an LLM round-trip: the AI reads the instruction, decides what to do, generates the command, executes it, reads the output, and moves on. This is slow and expensive for steps that don't require any judgment.

### The Core Insight

Many workflows are a mix of:
- **Deterministic steps** that always do the same thing (run a shell command, create a file, check git status)
- **Judgment steps** that genuinely need AI reasoning (interpret an error, decide how to resolve a merge conflict, write documentation)

Mekara separates these two types. Deterministic steps (`auto`) run **imperatively** -- straight to the terminal, no AI round-trip. Judgment steps (`llm`) still get delegated to the AI as normal. The result is the same workflow, but the deterministic parts execute instantly while only the parts that actually need intelligence use the LLM.

### The Broader Vision

Beyond just speed optimization, Mekara is a proof-of-concept for three ideas:

1. **Natural language is the programming language.** Mekara scripts start as plain English instructions (`.md` files), get compiled into Python generators that interleave `auto` and `llm` steps, and execute via MCP. The natural language source remains the canonical version -- the compiled code is derived from it.

2. **Automating the processes that produce code, not the code itself.** Rather than generating application code, Mekara automates the *development workflow* -- branching, merging, documenting, testing, PR creation -- the stuff that surrounds the code.

3. **Recursive self-improvement of workflows.** After using a workflow and finding it lacking, you can run `/recursive-self-improvement` to have the AI update the workflow script based on what went wrong. The workflows literally get better each time you use them.

## Key Technical Concepts

### Script Lifecycle
1. **Write** a natural language script (`.md` file) describing the workflow in plain English
2. **Compile** it to a Python generator that separates deterministic (`auto`) and judgment (`llm`) steps
3. **Execute** via MCP -- auto steps run instantly, llm steps pause for Claude
4. **Improve** via `/recursive-self-improvement` when the workflow needs refinement

### Script Resolution Precedence
When you invoke a command, mekara looks for it in this order:
1. Local project (`.mekara/scripts/`)
2. User home (`~/.mekara/scripts/`)
3. Bundled with mekara (shipped in the package)

This means projects can override bundled commands, and users can have personal customizations.

### VCR Testing
Mekara includes a "Video Cassette Recorder" system that records script execution (MCP calls, shell commands, outputs) to YAML files. These cassettes can be replayed for deterministic testing -- the real application code runs, but shell commands return recorded results. This enables testing complex multi-step workflows without actually running them.

## High-Level Architecture

### How It Works

```
User types /command in Claude Code
    |
    v
Mekara hook intercepts the command
    |
    v
Claude calls mcp__mekara__start(name, arguments)
    |
    v
MCP server loads script, runs auto steps instantly
    |
    v
Hits an llm step --> returns control to Claude
    |
    v
Claude handles the judgment step (user interaction, reasoning)
    |
    v
Claude calls mcp__mekara__continue_compiled_script(outputs)
    |
    v
Server resumes, runs more auto steps instantly
    |
    v
Repeat until script completes
```

## Categories of Commands
These commands are written in natural language (as `.md` files) and can be compiled by the AI into Python scripts that run deterministic steps instantly while still delegating judgment calls to the LLM.

### Core Workflow (the daily loop)
- `/start` -- Begin work on a new feature branch
- `/change` -- Full end-to-end feature workflow
- `/finish` -- Create PR and merge
- `/merge-main` -- Merge latest from main with conflict resolution

### Planning
- `/plan-design-doc` -- Interactive design document creation
- `/plan-refactor` -- Incremental refactoring plan
- `/implement-next-commit` -- Execute next phase from a plan
- `/check-plan-completion` -- Verify plan goals are met
- `/archive-roadmap` -- Clean up completed roadmap docs

### Documentation
- `/document` -- Sync docs to recent code changes
- `/document-branch` -- Document an entire branch from git history
- `/document-complex-feature` -- Document features with trial-and-error history
- `/split-docs-page` -- Break large docs into smaller pages

### Workflow Creation & Improvement
- `/systematize` -- Capture a successful approach as a command
- `/compile` -- Compile natural language to fast Python
- `/recursive-self-improvement` -- Improve commands from experience
- `/standardize` -- Extract and enforce shared standards
- `/debug-script-compilation` -- Debug script compilation issues
- `/rsi-documentation` -- Improve documentation conventions
- `/rsi-scripting` -- Improve script creation conventions

### Branch & PR Management
- `/analyze-branch-for-extraction` -- Find independently extractable changes
- `/extract-pr` -- Extract subset of changes into clean PR
- `/salvage` -- Create handoff prompt for fresh agent

### Recovery
- `/stop-fucking-up` -- Force AI to stop and reflect on mistakes
- `/salvage` -- Hand off work to a fresh agent with context

### Project Setup
- `/project:new` -- Complete project from scratch
- `/project:new-repo-init` -- Minimal repository setup
- `/project:setup-docs` -- Set up documentation site
- `/project:setup-github-repo` -- GitHub repo with CI and protection
- `/project:setup-pre-commit-hooks` -- Linting/formatting hooks
- `/project:setup-github-pages` -- GitHub Pages deployment
- `/project:setup-standard-mekara-docs` -- Standard docs structure
- `/project:worktree-init` -- Convert repo to worktree structure
- `/project:add-license` -- Add LICENSE from SPDX
- `/project:release` -- Prepare PyPI release

### AI Tooling
- `/ai-tooling:setup-mekara-mcp` -- Set up mekara integration with Claude Code

### Test/Demo
- `/test:random`, `/test:nested`, `/test:double-or-nothing`, `/test:imagine-object` -- Demo and test commands

### Codebase Structure

```
src/mekara/
  cli.py              # CLI entrypoint and Claude Code hook handlers
  mcp/
    server.py          # MCP server (4 tools: start, continue, finish_nl, status)
    executor.py        # Core execution engine (stack-based, pull-based)
  scripting/
    runtime.py         # The three primitives (Auto, Llm, CallScript)
    resolution.py      # Find scripts by name (local > user > bundled)
    loading.py         # Load and instantiate scripts
    auto.py            # Execute auto steps (shell/Python)
    nl.py              # Natural language script processing
    standards.py       # Reusable standards injection
  vcr/                 # Record/replay system for testing
  utils/
    project.py         # Project root detection and path utilities
  bundled/
    scripts/
      nl/              # Bundled natural language scripts (ship with mekara)
      compiled/        # Bundled compiled scripts

.mekara/
  scripts/
    nl/                # Project-specific natural language scripts (canonical source)
    compiled/          # Project-specific compiled scripts (auto-generated)
  standards/           # Project-specific standards

docs/docs/             # Docusaurus documentation site (single source of truth)
tests/                 # Test suite with VCR cassette recordings
```

