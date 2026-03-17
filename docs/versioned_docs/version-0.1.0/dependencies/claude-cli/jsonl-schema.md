---
sidebar_position: 1
---

# JSONL Transcript Schema

Claude Code stores conversation transcripts as JSONL (JSON Lines) files, with one JSON object per line. These files capture the complete conversation history including messages, tool usage, thinking, and file state.

## File Location

Transcripts are stored in `~/.claude/projects/<project-path-hash>/<session-id>.jsonl`.

## Message Types

Each line is a JSON object with a `type` field indicating the message type:

### `user`

A message from the user or a tool result.

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "Hello, Claude!"
  },
  "uuid": "610cc996-000a-4690-b67e-4aec1ba1eafd",
  "timestamp": "2026-02-01T14:59:02.592Z"
}
```

When `content` is an array, it typically contains a tool result:

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [
      {
        "type": "tool_result",
        "tool_use_id": "toolu_01R1b3BtKU87UuQpwY4Boxri",
        "content": "File created successfully at: /path/to/file.md"
      }
    ]
  },
  "toolUseResult": {
    "type": "create",
    "filePath": "/path/to/file.md",
    "content": "..."
  }
}
```

### `assistant`

A message from Claude. The `content` field contains an array of content blocks.

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [
      {
        "type": "thinking",
        "thinking": "Let me analyze this request..."
      },
      {
        "type": "text",
        "text": "I'll help you with that."
      },
      {
        "type": "tool_use",
        "id": "toolu_01R1b3BtKU87UuQpwY4Boxri",
        "name": "Write",
        "input": {
          "file_path": "/path/to/file.md",
          "content": "# Hello"
        }
      }
    ]
  },
  "uuid": "700505d4-46d3-44ab-b1d3-3d7ce2b81f1a",
  "timestamp": "2026-02-01T14:59:16.906Z"
}
```

### `file-history-snapshot`

Captures the state of tracked files at a point in the conversation.

```json
{
  "type": "file-history-snapshot",
  "messageId": "700505d4-46d3-44ab-b1d3-3d7ce2b81f1a",
  "snapshot": {
    "messageId": "610cc996-000a-4690-b67e-4aec1ba1eafd",
    "trackedFileBackups": {
      "README.md": {
        "backupFileName": "af3e97218f6be007@v2",
        "version": 2,
        "backupTime": "2026-02-01T14:59:02.697Z"
      },
      ".mekara/scripts/nl/sync-help.md": {
        "backupFileName": null,
        "version": 1,
        "backupTime": "2026-02-01T14:59:17.220Z"
      }
    },
    "timestamp": "2026-02-01T14:59:02.694Z"
  },
  "isSnapshotUpdate": true
}
```

### `progress`

Transient progress updates (e.g., hook execution status). These are typically skipped when rendering.

```json
{
  "type": "progress",
  "data": {
    "type": "hook_progress",
    "hookEvent": "PreToolUse",
    "hookName": "PreToolUse:Write",
    "command": "mekara hook auto-approve"
  },
  "toolUseID": "toolu_01R1b3BtKU87UuQpwY4Boxri"
}
```

## Content Block Types

Within assistant messages, the `content` array contains blocks of these types:

### `thinking`

Claude's extended thinking (reasoning before responding).

```json
{
  "type": "thinking",
  "thinking": "The user wants me to...",
  "signature": "..."
}
```

The `signature` field is a cryptographic signature for thinking verification.

### `text`

Plain text response from Claude.

```json
{
  "type": "text",
  "text": "Here's the solution..."
}
```

### `tool_use`

A tool invocation request.

```json
{
  "type": "tool_use",
  "id": "toolu_01R1b3BtKU87UuQpwY4Boxri",
  "name": "Bash",
  "input": {
    "command": "ls -la",
    "description": "List directory contents"
  }
}
```

The `id` field links this to the corresponding `tool_result`.

### `tool_result`

Result of a tool invocation (appears in user messages).

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01R1b3BtKU87UuQpwY4Boxri",
  "content": "total 48\ndrwxr-xr-x  12 user  staff   384 Feb  1 10:00 .",
  "is_error": false
}
```

## Tool Schemas

Each tool has an input schema (in `tool_use.input`) and an output schema (in `toolUseResult`).

### Bash

**Input:**

```json
{
  "command": "npm install",
  "description": "Install dependencies",
  "timeout": 120000
}
```

**Output (`toolUseResult`):**

```json
{
  "stdout": "added 150 packages...",
  "stderr": "",
  "interrupted": false,
  "isImage": false
}
```

### Read

**Input:**

```json
{
  "file_path": "/path/to/file.ts",
  "offset": 100,
  "limit": 50
}
```

**Output (`toolUseResult`):**

```json
{
  "type": "text",
  "file": {
    "filePath": "/path/to/file.ts",
    "content": "file contents..."
  }
}
```

### Write

**Input:**

```json
{
  "file_path": "/path/to/file.ts",
  "content": "file contents..."
}
```

**Output (`toolUseResult`):**

```json
{
  "type": "create",
  "filePath": "/path/to/file.ts",
  "content": "file contents..."
}
```

### Edit

**Input:**

```json
{
  "file_path": "/path/to/file.ts",
  "old_string": "const foo = 1;",
  "new_string": "const foo = 2;",
  "replace_all": false
}
```

**Output (`toolUseResult`):**

```json
{
  "type": "update",
  "filePath": "/path/to/file.ts",
  "oldString": "const foo = 1;",
  "newString": "const foo = 2;",
  "content": "full new file contents...",
  "structuredPatch": [
    {
      "oldStart": 10,
      "oldLines": 3,
      "newStart": 10,
      "newLines": 3,
      "lines": [
        " const bar = 2;",
        "-const foo = 1;",
        "+const foo = 2;",
        " const baz = 3;"
      ]
    }
  ],
  "originalFile": "full old file contents..."
}
```

The `structuredPatch` field is an array of diff hunks. Each hunk has:

- `oldStart` / `oldLines`: Line range in the original file
- `newStart` / `newLines`: Line range in the new file
- `lines`: Unified diff lines (` ` = context, `-` = removed, `+` = added)

### Grep / Glob

**Input:**

```json
{
  "pattern": "function.*export",
  "path": "/src"
}
```

**Output:** Uses Bash-style output with `stdout` containing the search results.

### Task

**Input:**

```json
{
  "description": "Find all test files",
  "prompt": "Search for files matching *.test.ts",
  "subagent_type": "Explore"
}
```

**Output:** Varies based on subagent type; typically returns text in `tool_result.content`.

## Slash Commands

When users type a slash command (e.g., `/sync-help`), Claude CLI expands it into script instructions before sending to the API. The transcript contains two consecutive user messages:

1. **User's typed command** with command tags:

   ```json
   {
     "type": "user",
     "message": {
       "role": "user",
       "content": "<command-message>sync-help</command-message>\n<command-name>/sync-help</command-name>"
     }
   }
   ```

2. **CLI-expanded script content** marked with `isMeta: true`:
   ```json
   {
     "type": "user",
     "message": {
       "role": "user",
       "content": [{ "type": "text", "text": "Synchronize documentation..." }]
     },
     "isMeta": true
   }
   ```

The `isMeta: true` field indicates this message was inserted by Claude CLI's command expansion system. This content is intended for Claude to read and execute, not for display in user-facing interfaces.

## User-Defined Hooks

User-defined hooks (configured via `userPromptSubmitHook` or similar) can insert text into the conversation when triggered. However, **hook-inserted text does not appear in JSONL transcripts**.

For example, if a user types `//systematize` and a hook inserts instructions for the systematization process, the transcript will only show:

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": "//systematize have the output file be sync-help.md. do not bother with documentation"
  }
}
```

There is no second message containing the hook-inserted instructions. Claude receives and responds to those instructions, but they are not recorded in the JSONL file.

:::warning[Transcript Limitation]
When analyzing transcripts, you may see Claude respond to instructions that don't appear in the visible messages. This is because text inserted by hooks are not captured inside of these `.jsonl` transcript files at all.
:::

## Metadata Fields

Messages include various metadata fields:

| Field                     | Description                                                            |
| ------------------------- | ---------------------------------------------------------------------- |
| `uuid`                    | Unique identifier for the message                                      |
| `parentUuid`              | UUID of the parent message in the conversation                         |
| `timestamp`               | ISO 8601 timestamp                                                     |
| `sessionId`               | Session identifier                                                     |
| `cwd`                     | Current working directory                                              |
| `gitBranch`               | Current git branch                                                     |
| `requestId`               | API request identifier                                                 |
| `sourceToolAssistantUUID` | For tool results, the assistant message that initiated the tool        |
| `isMeta`                  | `true` if message was inserted by Claude CLI's slash command expansion |

## toolUseResult Field

User messages containing tool results include a `toolUseResult` field with structured data about what the tool did. See [Tool Schemas](#tool-schemas) for the output format of each tool.

The `type` field indicates the operation:

- `text` - Text output (Read file contents, Bash stdout)
- `create` - File creation (Write to new file)
- `update` - File modification (Edit, Write to existing file)

The `tool_result.content` field contains the same information as a plain string, which is sufficient for display purposes.
