---
sidebar_position: 1
---

# Testing

This section covers the test suite implementation and testing utilities.

## Pages

- [VCR Agent Recordings](../vcr-agent-recordings/usage.md) – How to enable, record, and replay cassettes for hermetic runs

## Test Structure

```
tests/
├── test_cli.py              # CLI streaming and output formatting tests
├── test_project_root.py     # Project root detection tests
├── test_scripting.py        # Script execution and LLM step tests
├── cassettes/               # VCR cassettes for deterministic LLM test replay
└── golden_casts/            # Golden fixtures for chat transcripts
```

## Test Types

- **Unit tests** — Test individual functions and classes in isolation
- **Integration tests** — Test component interactions (e.g., script execution with LLM steps)
