import { useState, useEffect } from "react";
import type React from "react";
import BrowserOnly from "@docusaurus/BrowserOnly";
import useBaseUrl from "@docusaurus/useBaseUrl";
import styles from "./styles.module.css";

interface ContentBlock {
  type: "thinking" | "text" | "tool_use" | "tool_result";
  text?: string;
  thinking?: string;
  name?: string;
  id?: string;
  input?: Record<string, unknown>;
  tool_use_id?: string;
  content?: string;
  is_error?: boolean;
}

interface FileBackup {
  content?: string;
  [key: string]: unknown;
}

interface FileHistorySnapshot {
  messageId: string;
  trackedFileBackups: Record<string, FileBackup>;
  timestamp: string;
}

interface RawMessage {
  type: "user" | "assistant" | "file-history-snapshot" | "progress";
  message?: {
    role: string;
    content: string | ContentBlock[];
  };
  snapshot?: FileHistorySnapshot;
  uuid?: string;
}

interface ToolUseWithResult {
  toolUse: ContentBlock;
  toolResult?: ContentBlock;
}

interface ClaudeContentItem {
  kind: "thinking" | "text" | "tool";
  thinking?: string;
  text?: string;
  tool?: ToolUseWithResult;
}

interface ClaudeTurn {
  type: "claude";
  content: ClaudeContentItem[];
}

interface UserTurn {
  type: "user";
  text: string;
}

interface FileSnapshotTurn {
  type: "file-snapshot";
  snapshot: FileHistorySnapshot;
}

type Turn = ClaudeTurn | UserTurn | FileSnapshotTurn;

interface ClaudeChatProps {
  src: string;
}

function groupMessagesIntoTurns(messages: RawMessage[]): Turn[] {
  const turns: Turn[] = [];
  let currentClaudeTurn: ClaudeTurn | null = null;
  // Map from tool_use_id to the content item (so we can update it with result later)
  let pendingToolUses: Map<string, ToolUseWithResult> = new Map();

  for (const msg of messages) {
    if (msg.type === "progress") continue;

    if (msg.type === "file-history-snapshot" && msg.snapshot) {
      if (currentClaudeTurn) {
        turns.push(currentClaudeTurn);
        currentClaudeTurn = null;
        // Keep pendingToolUses - results may come after snapshot
      }
      turns.push({ type: "file-snapshot", snapshot: msg.snapshot });
      continue;
    }

    if (msg.type === "user" && msg.message) {
      const content = msg.message.content;

      if (Array.isArray(content) && content[0]?.type === "tool_result") {
        const result = content[0];
        if (result.tool_use_id && pendingToolUses.has(result.tool_use_id)) {
          // Update the existing tool with its result (it's already in content)
          const toolWithResult = pendingToolUses.get(result.tool_use_id)!;
          toolWithResult.toolResult = result;
          pendingToolUses.delete(result.tool_use_id);
        }
        continue;
      }

      if (typeof content === "string") {
        if (currentClaudeTurn) {
          turns.push(currentClaudeTurn);
          currentClaudeTurn = null;
        }
        pendingToolUses = new Map(); // Clear pending tools on new user message
        turns.push({ type: "user", text: content });
      }
      continue;
    }

    if (msg.type === "assistant" && msg.message) {
      if (!currentClaudeTurn) {
        currentClaudeTurn = { type: "claude", content: [] };
      }

      const content = msg.message.content;
      const blocks =
        typeof content === "string"
          ? [{ type: "text" as const, text: content }]
          : content;

      for (const block of blocks) {
        if (block.type === "thinking" && block.thinking) {
          currentClaudeTurn.content.push({
            kind: "thinking",
            thinking: block.thinking,
          });
        } else if (block.type === "text" && block.text) {
          currentClaudeTurn.content.push({ kind: "text", text: block.text });
        } else if (block.type === "tool_use" && block.id) {
          // Add tool to content immediately, result will be filled in later
          const toolItem: ToolUseWithResult = { toolUse: block };
          currentClaudeTurn.content.push({ kind: "tool", tool: toolItem });
          pendingToolUses.set(block.id, toolItem);
        }
      }
    }
  }

  if (currentClaudeTurn) {
    turns.push(currentClaudeTurn);
  }

  return turns;
}

function formatToolInput(
  name: string,
  input: Record<string, unknown>,
): { primary: string; details: React.ReactNode } {
  if (name === "Bash") {
    const command = (input.command as string) || "";
    const description = input.description as string | undefined;
    return {
      primary: command,
      details: description ? <p>{description}</p> : null,
    };
  }

  if (name === "Read") {
    const filePath = (input.file_path as string) || "";
    const offset = input.offset as number | undefined;
    const limit = input.limit as number | undefined;
    return {
      primary: filePath,
      details:
        offset || limit ? (
          <p>
            Lines {offset || 1} - {(offset || 1) + (limit || 0)}
          </p>
        ) : null,
    };
  }

  if (name === "Write") {
    const filePath = (input.file_path as string) || "";
    const content = (input.content as string) || "";
    return {
      primary: filePath,
      details: <pre className={styles.codeBlock}>{content}</pre>,
    };
  }

  if (name === "Edit") {
    const filePath = (input.file_path as string) || "";
    const oldStr = (input.old_string as string) || "";
    const newStr = (input.new_string as string) || "";
    return {
      primary: filePath,
      details: (
        <div className={styles.diffBlock}>
          <div className={styles.diffOld}>
            {oldStr.split("\n").map((line, i) => (
              <div key={i} className={styles.diffLineOld}>
                - {line}
              </div>
            ))}
          </div>
          <div className={styles.diffNew}>
            {newStr.split("\n").map((line, i) => (
              <div key={i} className={styles.diffLineNew}>
                + {line}
              </div>
            ))}
          </div>
        </div>
      ),
    };
  }

  if (name === "Grep" || name === "Glob") {
    const pattern = (input.pattern as string) || "";
    const path = input.path as string | undefined;
    return {
      primary: pattern,
      details: path ? <p>in {path}</p> : null,
    };
  }

  if (name === "Task") {
    const description = (input.description as string) || "";
    const prompt = (input.prompt as string) || "";
    return {
      primary: description,
      details: prompt ? <pre className={styles.codeBlock}>{prompt}</pre> : null,
    };
  }

  // Default: show all fields nicely
  const entries = Object.entries(input);
  return {
    primary: entries[0] ? String(entries[0][1]).slice(0, 50) : "",
    details: (
      <div>
        {entries.map(([key, value]) => (
          <div key={key} className={styles.detailRow}>
            <span className={styles.detailKey}>{key}:</span>{" "}
            {typeof value === "string" ? (
              value.includes("\n") ? (
                <pre className={styles.codeBlock}>{value}</pre>
              ) : (
                <span>{value}</span>
              )
            ) : (
              <span>{JSON.stringify(value)}</span>
            )}
          </div>
        ))}
      </div>
    ),
  };
}

function ToolBlock({ tool }: { key?: string; tool: ToolUseWithResult }) {
  const [expanded, setExpanded] = useState(false);
  const { toolUse, toolResult } = tool;
  const input = toolUse.input || {};
  const { primary, details } = formatToolInput(toolUse.name || "", input);
  const hasDetails = details !== null;

  return (
    <div className={styles.toolBlock}>
      <button
        className={styles.toolHeader}
        onClick={() => setExpanded(!expanded)}
      >
        <span className={styles.toolName}>{toolUse.name}</span>
        <span className={styles.toolPrimary}>{primary}</span>
        <span className={styles.expandIcon}>{expanded ? "▼" : "▶"}</span>
      </button>
      {expanded && (
        <div className={styles.toolDetails}>
          {details}
          {toolResult && (
            <div className={hasDetails ? styles.toolResultSection : undefined}>
              {toolResult.is_error && (
                <div className={styles.toolResultLabel}>Error:</div>
              )}
              <pre className={styles.codeBlock}>{toolResult.content}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FileSnapshotBlock({
  snapshot,
}: {
  key?: number;
  snapshot: FileHistorySnapshot;
}) {
  const [expanded, setExpanded] = useState(false);
  const files = Object.entries(snapshot.trackedFileBackups);

  if (files.length === 0) return null;

  return (
    <div className={styles.fileSnapshot}>
      <button
        className={
          expanded
            ? styles.fileSnapshotHeaderExpanded
            : styles.fileSnapshotHeader
        }
        onClick={() => setExpanded(!expanded)}
      >
        <span className={styles.fileIcon}>📁</span>
        <span className={styles.fileList}>
          {files.map(([name]) => name).join(", ")}
        </span>
        <span className={styles.expandIcon}>{expanded ? "▼" : "▶"}</span>
      </button>
      {expanded && (
        <div className={styles.fileDetailsInline}>
          {files.map(([fileName, backup]) => (
            <div key={fileName} className={styles.fileEntry}>
              <div className={styles.fileName}>{fileName}</div>
              {backup.content ? (
                <pre className={styles.codeBlock}>{backup.content}</pre>
              ) : (
                <div className={styles.fileBackupInfo}>
                  {Object.entries(backup).map(([key, value]) => (
                    <div key={key}>
                      <strong>{key}:</strong>{" "}
                      {typeof value === "string"
                        ? value
                        : JSON.stringify(value)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ThinkingBlock({
  thought,
  collapsible,
}: {
  key?: string;
  thought: string;
  collapsible: boolean;
}) {
  const [expanded, setExpanded] = useState(!collapsible);

  return (
    <div className={styles.thinkingBlock}>
      {collapsible && (
        <button
          className={styles.thinkingToggle}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "hide thinking" : "show thinking"}{" "}
          <span className={styles.thinkingArrow}>{expanded ? "▼" : "▶"}</span>
        </button>
      )}
      {expanded && (
        <div className={styles.thinkingContent}>
          <p>{thought}</p>
        </div>
      )}
    </div>
  );
}

function parseCommandFromText(text: string): {
  command: string | null;
  remainingText: string;
} {
  // Match <command-name>/command-name</command-name> pattern
  const commandMatch = text.match(/<command-name>([^<]+)<\/command-name>/);
  if (commandMatch) {
    // Remove both <command-message> and <command-name> tags
    const cleanedText = text
      .replace(/<command-message>[^<]*<\/command-message>/g, "")
      .replace(/<command-name>[^<]+<\/command-name>/g, "")
      .trim();
    return {
      command: commandMatch[1],
      remainingText: cleanedText,
    };
  }
  return { command: null, remainingText: text };
}

function TextBlock({ text }: { text: string }) {
  const { command, remainingText } = parseCommandFromText(text);

  // If we found a command, display it specially
  if (command) {
    return (
      <>
        <span className={styles.commandBadge}>{command}</span>
        {remainingText && (
          <>
            <br />
            {remainingText.split("\n").map((line, i) => (
              <span key={i}>
                {line}
                {i < remainingText.split("\n").length - 1 && <br />}
              </span>
            ))}
          </>
        )}
      </>
    );
  }

  // Otherwise, render text normally
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => (
        <span key={i}>
          {line}
          {i < lines.length - 1 && <br />}
        </span>
      ))}
    </>
  );
}

function ClaudeTurnBlock({ turn }: { key?: number; turn: ClaudeTurn }) {
  // Check if this turn has any non-thinking content
  const hasNonThinkingContent = turn.content.some(
    (item) => item.kind !== "thinking",
  );

  return (
    <div className={styles.claudeMessage}>
      <div className={styles.messageLabel}>Claude</div>
      <div className={styles.messageContent}>
        {turn.content.map((item, i) => {
          if (item.kind === "thinking" && item.thinking) {
            return (
              <ThinkingBlock
                key={`thinking-${i}`}
                thought={item.thinking}
                collapsible={hasNonThinkingContent}
              />
            );
          }
          if (item.kind === "text" && item.text) {
            return (
              <p key={`text-${i}`}>
                <TextBlock text={item.text} />
              </p>
            );
          }
          if (item.kind === "tool" && item.tool) {
            return <ToolBlock key={`tool-${i}`} tool={item.tool} />;
          }
          return null;
        })}
      </div>
    </div>
  );
}

function ClaudeChatInner({ src }: ClaudeChatProps) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const resolvedSrc = useBaseUrl(src);

  useEffect(() => {
    fetch(resolvedSrc)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        return res.text();
      })
      .then((text) => {
        const lines = text.trim().split("\n");
        const messages = lines
          .map((line) => {
            try {
              return JSON.parse(line) as RawMessage;
            } catch {
              return null;
            }
          })
          .filter((m): m is RawMessage => m !== null);
        setTurns(groupMessagesIntoTurns(messages));
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [resolvedSrc]);

  if (loading) {
    return <div className={styles.loading}>Loading chat...</div>;
  }

  if (error) {
    return <div className={styles.error}>Error loading chat: {error}</div>;
  }

  return (
    <div className={styles.chatContainer}>
      {turns.map((turn, idx) => {
        if (turn.type === "user") {
          return (
            <div key={idx} className={styles.userMessage}>
              <div className={styles.messageLabel}>User</div>
              <div className={styles.messageContent}>
                <TextBlock text={turn.text} />
              </div>
            </div>
          );
        }

        if (turn.type === "claude") {
          return <ClaudeTurnBlock key={idx} turn={turn} />;
        }

        if (turn.type === "file-snapshot") {
          return <FileSnapshotBlock key={idx} snapshot={turn.snapshot} />;
        }

        return null;
      })}
    </div>
  );
}

export default function ClaudeChat(props: ClaudeChatProps) {
  return (
    <BrowserOnly fallback={<div>Loading chat...</div>}>
      {() => <ClaudeChatInner {...props} />}
    </BrowserOnly>
  );
}
