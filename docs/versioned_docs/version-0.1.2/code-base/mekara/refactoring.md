---
sidebar_position: 3
---

# Refactoring Patterns

This document captures lessons learned from refactoring sessions to help future developers (human and AI) avoid common pitfalls and recognize code smells.

## Eliminate Unnecessary Indirection

### Problem: Pointless Wrapper Functions

**Bad:**

```python
def _build_client(options: ClaudeAgentOptions) -> ClaudeSDKClient:
    """Create a ClaudeSDKClient instance."""
    return ClaudeSDKClient(options)

# Later in code...
client_factory: Callable[[ClaudeAgentOptions], ClaudeSDKClient] = _build_client
```

**Why it's bad:**

- The "factory" function does nothing - it just calls the constructor directly
- Adds cognitive overhead without providing flexibility
- Makes code harder to trace and understand

**Good:**

```python
# Just create the client directly where you need it
client = ClaudeSDKClient(options, transport=transport)
```

### Problem: Redundant Local Variable Copies

**Bad:**

```python
class ChatSession:
    def start(self) -> None:
        # Copy instance variables to local variables for no reason
        current_image = self.image
        current_prompt = self.initial_prompt
        resume_session_id = self.resume_session_id

        while True:
            # Use local copies
            config = ChatLoopConfig(image=current_image, ...)
            # Later modify locals
            current_image = None
```

**Why it's bad:**

- Creates confusion about which variable is the source of truth
- Requires synchronization between locals and instance attributes
- Adds cognitive load when reading the code

**Good:**

```python
class ChatSession:
    def start(self) -> None:
        while True:
            # Use instance attributes directly
            config = ChatLoopConfig(image=self.image, ...)
            # Modify instance attributes directly
            self.image = None
```

## Keep Helper Methods Where They Belong

### Problem: Module-Level Functions That Should Be Methods

**Bad:**

```python
# Module level - but only used by one class
def _ensure_async_client(client: ClientContext) -> AsyncContextManager:
    if isinstance(client, ClaudeSDKClient):
        return cast(AsyncContextManager[ClaudeSDKClient], client)
    return client

def _show_cwd_deleted_message() -> None:
    click.echo("⚠️  Working directory was deleted.")

class ChatSession:
    def start(self) -> None:
        client = _ensure_async_client(self.client_factory(options))
        # ...
        _show_cwd_deleted_message()
```

**Why it's bad:**

- Functions with leading underscore at module level look like private internals
- Breaks encapsulation - helpers are scattered outside the class
- Harder to find related code
- Can't access `self` naturally

**Good:**

```python
class ChatSession:
    def _show_cwd_deleted_message(self) -> None:
        """Show user-friendly message when working directory is deleted."""
        click.echo("⚠️  Working directory was deleted.")

    async def start(self) -> None:
        # Direct access to client creation
        client = ClaudeSDKClient(options, transport=transport)
        # ...
        self._show_cwd_deleted_message()
```

**When module-level functions ARE appropriate:**

- Pure utility functions used by multiple classes
- Public API functions that aren't tied to a class
- Functions that need to be independently testable

## Proper Dependency Injection

### Problem: Class Instantiating Its Own Dependencies

**Bad:**

```python
class ChatSession:
    def __init__(self, create_options: Callable[[], Options], ...):
        self.create_options = create_options

    async def run(self):
        options = self.create_options()
        client = ClaudeSDKClient(options)  # Creates its own dependency
        ...
```

**Why it's bad:**

- Testing requires mocks/patches to intercept `ClaudeSDKClient`
- The class controls when and how the client is created
- Hard to inject test doubles or alternative implementations
- Couples the class to a specific implementation

**Good:**

```python
class ChatSession:
    def __init__(self, client: ClaudeAgentProtocol, ...):
        self.client = client  # Receives a pre-constructed client

    async def run(self):
        # Use the injected client directly
        async with self.client as c:
            ...
```

**Why it's better:**

- Caller controls client creation—can pass `RealClient` or `VcrClient`
- Testing uses real implementations with recorded responses, no mocks
- Class is decoupled from client construction details
- `restart()` method on the client interface handles session resume cleanly

**Implementation pattern:**

```python
# Define a protocol for the dependency
class ClaudeAgentProtocol(Protocol):
    async def __aenter__(self) -> ClaudeSDKClient: ...
    async def __aexit__(self, ...): ...
    def restart(self, resume_session_id: str | None = None) -> "ClaudeAgentProtocol": ...

# Real implementation wraps the SDK
class RealClient(ClaudeAgentProtocol):
    def __init__(self, options: ClaudeAgentOptions): ...

# Test implementation uses recorded responses
class VcrClient(ClaudeAgentProtocol):
    def __init__(self, options: ClaudeAgentOptions, cassette: VCRCassette): ...
```

## Red Flags to Watch For

When reviewing code, these patterns often indicate unnecessary complexity:

1. **Module-level function with underscore prefix** - Should it be a method?
2. **Variable assignment immediately before use** - Do you need the intermediate variable?
3. **Factory that just calls a constructor** - Why not call the constructor directly?
4. **Passing both a factory and its output** - The factory isn't providing value
5. **Local variable shadowing instance attribute** - Why not use the instance attribute?
6. **Function that only has one caller** - Should it be a method of that class?
7. **Class instantiating its own external dependencies** - Should it receive them via constructor?
8. **Module-level mutable state** - Should the state be encapsulated in a class instance created at the appropriate scope?
