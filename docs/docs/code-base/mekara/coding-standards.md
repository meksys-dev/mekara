---
sidebar_position: 99
---

# Coding Standards

Lessons learned from real mistakes during development. Each entry shows what went wrong, why, and what the correct approach looks like.

## Extend, don't duplicate

### Example: Adding `write_bundled_standard` alongside `write_bundled_command`

**Agent's solution:** Proposed a new MCP tool `write_bundled_standard(name, force)` mirroring the existing `write_bundled_command(name, force)` — same parameters, same VCR wrapper pattern, same event type shape, same registration in `run_server()`, new recording script.

**Why this is wrong:** When new functionality is a natural extension of an existing operation (writing a bundled file to disk), adding a parallel entry point doubles the surface area for no gain. Callers now have to know which tool to call. The VCR layer, event registry, permissions lists, docs, and recording scripts all need duplicate entries. The API grows without the concept growing.

**Human-provided fix:** Extend `write_bundled` to handle both cases. Auto-detect whether the name refers to a command or standard; use `standard:` prefix to disambiguate when needed. One tool, one event type, one recording script that covers both cases:

```python
def write_bundled(self, name: str, force: bool = False) -> str:
    if name.startswith("standard:"):
        return self._write_bundled_standard(name[len("standard:"):], force)
    # auto-detect command vs standard ...
```

## Rename when scope changes

### Example: Keeping `write_bundled_command` as-is instead of renaming to `write_bundled`

**Agent's solution:** When consolidating `write_bundled_standard` into existing `write_bundled_command` logic, the agent kept the `write_bundled_command` name.

**Why this is wrong:** When a function's responsibility grows beyond what its name describes, the name should change to match the new scope. Leaving the old name in place creates confusion about which to use and leaves stale references throughout the codebase (docs, permissions, VCR events, tests).

**Human-provided fix:** Rename `write_bundled_command` → `write_bundled` across all call sites.

## Extract shared logic, don't repeat it across helpers

### Example: Duplicated read-check-write pattern in `_write_bundled_command` and `_write_bundled_standard`

**Agent's solution:** Both private helpers independently implemented the same three-step pattern:

```python
# In _write_bundled_command:
if local_nl_path.exists() and not force:
    rel_path = local_nl_path.relative_to(self.executor.working_dir)
    return f"Error: Local override already exists at {rel_path}. Use force=True to overwrite."
nl_content = self.fs_access.read_file(bundled_nl_path)
self.fs_access.write_file(local_nl_path, nl_content)

# In _write_bundled_standard (identical structure):
if local_std_path.exists() and not force:
    rel_path = local_std_path.relative_to(self.executor.working_dir)
    return f"Error: Local override already exists at {rel_path}. Use force=True to overwrite."
content = self.fs_access.read_file(bundled_std_path)
self.fs_access.write_file(local_std_path, content)
```

**Why this is wrong:** Duplicated logic means two places to update when the behavior changes (error message wording, path formatting, etc.). Both helpers do exactly the same thing: guard on existence, read source, write destination.

**Human-provided fix:** Extract `_copy_bundled_file` and use it in both:

```python
def _copy_bundled_file(self, src: Path, dst: Path, force: bool) -> str | None:
    if dst.exists() and not force:
        rel = dst.relative_to(self.executor.working_dir)
        return f"Error: Local override already exists at {rel}. Use force=True to overwrite."
    self.fs_access.write_file(dst, self.fs_access.read_file(src))
    return None

def _write_bundled_command(self, name: str, bundled_nl_path: Path, force: bool) -> str:
    local_nl_path = ...
    if error := self._copy_bundled_file(bundled_nl_path, local_nl_path, force):
        return error
    ...

def _write_bundled_standard(self, name: str, force: bool) -> str:
    ...
    if error := self._copy_bundled_file(bundled_std_path, local_std_path, force):
        return error
    ...
```

## No defensive local imports

### Example: `from mekara.utils.project import ...` inside method bodies

**Agent's solution:** Placed imports inside method bodies to avoid hypothetical circular imports:

```python
def write_bundled(self, name: str, force: bool = False) -> str:
    from mekara.utils.project import bundled_commands_dir, bundled_scripts_dir, bundled_standards_dir
    ...

def _write_bundled_command(self, name: str, bundled_nl_path: Path, force: bool) -> str:
    from mekara.utils.project import bundled_scripts_dir
    ...

def _write_bundled_standard(self, name: str, force: bool) -> str:
    from mekara.utils.project import bundled_standards_dir
    ...
```

**Why this is wrong:** Local imports hide dependencies, hurt readability, and are never necessary unless a circular import actually occurs and breaks at runtime. There was no such circular import here — this was purely defensive.

**Human-provided fix:** Move imports to the top of the module:

```python
from mekara.utils.project import (
    bundled_commands_dir,
    bundled_scripts_dir,
    bundled_standards_dir,
    find_project_root,
)
```
