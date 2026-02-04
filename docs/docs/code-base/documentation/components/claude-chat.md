---
sidebar_position: 2
---

# ClaudeChat

Component for rendering Claude Code conversation transcripts (JSONL files) as static HTML. Located at `src/components/ClaudeChat/index.tsx`.

## Usage in MDX

```mdx
import ClaudeChat from "@site/src/components/ClaudeChat";

<ClaudeChat src="/chats/my-conversation.jsonl" />
```

Place JSONL files in `docs/static/chats/` to serve them from the docs site.

## Props

- `src` (string, required): Path to the JSONL file relative to the static directory (e.g., `/chats/demo.jsonl`)

## Data Source

The component parses [Claude CLI JSONL transcript files](../../../dependencies/claude-cli/jsonl-schema.md). These files are produced by Claude Code and contain the full conversation history including messages, tool usage, thinking, and file snapshots.

:::note[Slash Command Expansion]
Slash commands (e.g., `/sync-help`) produce two user messages in the transcript:

1. The user's typed command with `<command-name>` tags (string content)
2. The CLI-expanded script content marked with `"isMeta": true` (array content)

The component only displays the first message (the user's typed command). The `isMeta: true` message contains expanded script instructions for Claude to execute and is intentionally not rendered in the UI.

User-defined hooks that insert text don't appear in transcripts at all—see [JSONL Schema: User-Defined Hooks](../../../dependencies/claude-cli/jsonl-schema.md#user-defined-hooks) for details.
:::

## Implementation Pattern

This component uses **BrowserOnly wrapper** to avoid SSR issues:

```tsx
export default function ClaudeChat(props: ClaudeChatProps) {
  return (
    <BrowserOnly fallback={<div>Loading chat...</div>}>
      {() => <ClaudeChatInner {...props} />}
    </BrowserOnly>
  );
}
```

The inner component fetches the JSONL file client-side and parses it into turns.

:::warning[useBaseUrl Required]
The `src` prop must be resolved with `useBaseUrl()` before fetching. Without this, the fetch URL won't include the Docusaurus `baseUrl` (e.g., `/mekara/`), and the request will return the SPA fallback HTML instead of the JSONL file:

```tsx
// Wrong - fetches /chats/demo.jsonl, gets HTML
fetch(src);

// Correct - fetches /mekara/chats/demo.jsonl, gets JSONL
const resolvedSrc = useBaseUrl(src);
fetch(resolvedSrc);
```

:::

## Message Grouping

The component groups raw JSONL messages into consolidated "turns" for display:

1. **User turns**: User text messages (tool results are matched to their tool uses, not shown as separate turns)
2. **Claude turns**: Consecutive assistant messages are merged into a single turn, preserving chronological order of thinking, text, and tool usage
3. **File snapshot turns**: File history snapshots are rendered as expandable file lists

## Content Rendering

### Thinking Blocks

- **Collapsible** when the turn also contains text or tool usage—shows "show thinking ▶" toggle
- **Expanded by default** when the turn contains only thinking (no other content)
- Displayed in dimmed, italicized text (`--ifm-color-emphasis-500`)
- Toggle arrow is not italicized (uses separate `.thinkingArrow` class)

### Tool Blocks

Each tool shows a clickable header with:

- **Tool name** (bold): e.g., "Bash", "Edit", "Read"
- **Primary info** (monospace): The most relevant parameter (command, file path, pattern)
- **Expand arrow**: Click to show details

Expanded view shows:

- Tool-specific formatted input (not raw JSON)
- Tool result (if available), with no "Result:" label unless it's an error
- No horizontal divider if there's no additional metadata above the result

Tool-specific formatting:

- **Bash**: Shows command; description in details
- **Read**: Shows file path; line range in details if specified
- **Write**: Shows file path; full content in code block
- **Edit**: Shows file path; plain-text diff with `- old` / `+ new` lines
- **Grep/Glob**: Shows pattern; path in details if specified
- **Task**: Shows description; prompt in details
- **Default**: Shows first field value; all fields as key-value pairs

### File Snapshots

- Dashed border container listing tracked files
- Click to expand within the same dashed border (header loses bottom border, content has no top border)
- Shows backup metadata (version, backup time) or file content if available

### Text Blocks

Newlines are preserved using `<br />` elements, not CSS `white-space: pre-wrap`, to maintain proper paragraph flow.

**Command Detection:**

User messages are parsed to detect slash commands (e.g., `/sync-help`). The component looks for the pattern:

```xml
<command-message>sync-help</command-message>
<command-name>/sync-help</command-name>
```

When detected:

- The raw XML tags are stripped from the displayed text
- The command name (e.g., `/sync-help`) is rendered in bold, cyan-colored, monospace text using `var(--ifm-color-primary)`
- Any remaining text after the command is displayed normally

This provides a cleaner visual presentation compared to showing the raw XML markup.

## Chronological Order

Content within a Claude turn is rendered in the exact order it appears in the JSONL:

```
thinking → tool use → tool result → text
```

Not grouped by type (which would show all thinking first, then all text, then all tools).

:::note[Tool Result Timing]
Tool uses are added to the turn immediately when encountered. The result is attached later when the `tool_result` message arrives. This handles cases where a `file-history-snapshot` appears between `tool_use` and `tool_result`—the tool is already in the content array, so the turn isn't empty.

The `pendingToolUses` map stores references to tool objects already in the content array, allowing results to be attached in place. The map persists across `file-history-snapshot` boundaries but is cleared on new user text messages.
:::

## What's Displayed vs. Skipped

**Displayed:**

- User text messages
- Claude thinking, text, and tool usage
- Tool results (matched to their tool uses)
- File history snapshots

**Skipped (metadata/transient):**

- `progress` messages (hook status updates like "running auto-approve hook")
- Message metadata (uuid, timestamp, sessionId, parentUuid, etc.)
- `toolUseResult` field (duplicates `tool_result.content` with different structure)

## Testing

Tests are in `src/components/ClaudeChat/__tests__/ClaudeChat.test.tsx` using Jest + React Testing Library. Two fixtures are used:

- `fixtures/test-chat.jsonl` - Extracted from a real conversation file
- `fixtures/edge-cases.jsonl` - Synthetic data for specific edge cases (Edit diffs, Write content, Grep patterns, thinking-only blocks, file snapshots)

Coverage includes:

- User and Claude message rendering
- Command tag parsing and formatting (removes XML tags, displays command badge)
- Thinking collapse/expand behavior
- Thinking-only blocks (no toggle, expanded by default)
- Tool block expansion with details and results
- Tool-specific formatting (Bash, Read, Write, Edit, Grep)
- File snapshot rendering
- Chronological ordering within turns
- Loading, error, and HTTP error states

## Dependencies

No additional npm packages required—uses standard React and Docusaurus utilities (`BrowserOnly`, `useBaseUrl`).
