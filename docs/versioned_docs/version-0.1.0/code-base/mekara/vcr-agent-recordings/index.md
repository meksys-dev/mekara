---
sidebar_position: 6
---

# VCR Agent Recordings

We use VCR recording to capture auto step execution results for deterministic replay. This enables:

- **Testing**: Fast, deterministic tests without executing shell commands
- **Development**: Record/replay for debugging

## Section Index

- [Usage](./usage.md) – Protocol boundaries, what's recorded, and how to enable VCR.
- [Implementation](./implementation.md) – MCP server VCR wiring, tests, and cassette format.
