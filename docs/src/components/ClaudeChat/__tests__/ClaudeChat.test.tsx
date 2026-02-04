import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ClaudeChat from "../index";
import fs from "fs";
import path from "path";

const testFixture = fs.readFileSync(
  path.join(__dirname, "fixtures/test-chat.jsonl"),
  "utf-8",
);

const edgeCasesFixture = fs.readFileSync(
  path.join(__dirname, "fixtures/edge-cases.jsonl"),
  "utf-8",
);

describe("ClaudeChat", () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it("renders user messages", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("hm... is that up-to-date with the README?"),
    ).toBeInTheDocument();
  });

  it("renders claude text responses with newlines preserved", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText(/The CLI currently has:/i)).toBeInTheDocument();
    });

    // Check that markdown-like content is present
    expect(screen.getByText(/Main description/i)).toBeInTheDocument();
  });

  it("renders thinking collapsed by default with toggle", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    // Should have "show thinking" toggle buttons
    const toggles = screen.getAllByText(/show thinking/i);
    expect(toggles.length).toBeGreaterThan(0);

    // Thinking content should NOT be visible by default
    expect(
      screen.queryByText(/I should run the CLI with --help/i),
    ).not.toBeInTheDocument();
  });

  it("expands thinking when toggle is clicked", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    // Click the first "show thinking" toggle
    const toggles = screen.getAllByText(/show thinking/i);
    await userEvent.click(toggles[0]);

    // Now thinking should be visible
    await waitFor(() => {
      expect(
        screen.getByText(/I should run the CLI with --help/i),
      ).toBeInTheDocument();
    });
  });

  it("renders tool use with tool name and command", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    // Tool name should be visible
    expect(screen.getAllByText("Bash").length).toBeGreaterThan(0);
    // Command should be visible
    expect(screen.getByText("uv run dojo --help")).toBeInTheDocument();
  });

  it("consolidates consecutive claude messages into one turn", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    const claudeLabels = screen.getAllByText("Claude");
    const userLabels = screen.getAllByText("User");

    expect(claudeLabels.length).toBeLessThan(10);
    expect(userLabels.length).toBeGreaterThan(0);
  });

  it("renders message labels", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    expect(screen.getAllByText("User").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Claude").length).toBeGreaterThan(0);
  });

  it("shows loading state initially", () => {
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<ClaudeChat src="/chats/test.jsonl" />);

    expect(screen.getByText("Loading chat...")).toBeInTheDocument();
  });

  it("shows error state on fetch failure", async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error("Network error"),
    );

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("Error loading chat: Network error"),
      ).toBeInTheDocument();
    });
  });

  it("shows error state on HTTP error response", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: "Not Found",
    });

    render(<ClaudeChat src="/chats/nonexistent.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("Error loading chat: HTTP 404: Not Found"),
      ).toBeInTheDocument();
    });
  });

  it("expands tool block to show details and result", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("uv run dojo --help")).toBeInTheDocument();
    });

    // Click to expand the Bash tool
    const bashHeaders = screen.getAllByText("Bash");
    await userEvent.click(bashHeaders[0].closest("button")!);

    // Tool result should now be visible
    await waitFor(() => {
      expect(screen.getByText(/positional arguments/i)).toBeInTheDocument();
    });
  });

  it("shows thinking-only block expanded by default without toggle", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("edit the file")).toBeInTheDocument();
    });

    // Thinking-only block should be visible without clicking
    expect(
      screen.getByText("This is a thinking-only block with no other content."),
    ).toBeInTheDocument();

    // Should NOT have a "show thinking" toggle for thinking-only blocks
    const thinkingOnlyBlock = screen
      .getByText("This is a thinking-only block with no other content.")
      .closest("div");
    expect(
      thinkingOnlyBlock?.parentElement?.querySelector("button"),
    ).toBeNull();
  });

  it("renders Edit tool with diff format", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("/path/to/file.ts")).toBeInTheDocument();
    });

    // Click to expand Edit tool
    const editTool = screen.getByText("/path/to/file.ts").closest("button")!;
    await userEvent.click(editTool);

    // Should show diff with - and + prefixes
    await waitFor(() => {
      expect(screen.getByText("- const foo = 1;")).toBeInTheDocument();
      expect(screen.getByText("+ const foo = 42;")).toBeInTheDocument();
      expect(screen.getByText("+ const baz = 3;")).toBeInTheDocument();
    });
  });

  it("renders Write tool with file content", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("/path/to/newfile.ts")).toBeInTheDocument();
    });

    // Click to expand Write tool
    const writeTool = screen
      .getByText("/path/to/newfile.ts")
      .closest("button")!;
    await userEvent.click(writeTool);

    // Should show file content
    await waitFor(() => {
      expect(screen.getByText(/export const hello/)).toBeInTheDocument();
    });
  });

  it("renders Grep tool with pattern and path", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("Grep")).toBeInTheDocument();
    });

    // Pattern should be visible in header
    expect(screen.getByText("export.*const")).toBeInTheDocument();

    // Click to expand
    const grepTool = screen.getByText("export.*const").closest("button")!;
    await userEvent.click(grepTool);

    // Should show path in details
    await waitFor(() => {
      expect(screen.getByText("in /src")).toBeInTheDocument();
    });
  });

  it("renders file history snapshot with file list", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("README.md")).toBeInTheDocument();
    });

    // Click to expand file snapshot
    const fileSnapshot = screen.getByText("README.md").closest("button")!;
    await userEvent.click(fileSnapshot);

    // Should show backup metadata
    await waitFor(() => {
      expect(screen.getByText(/version:/i)).toBeInTheDocument();
    });
  });

  it("maintains chronological order within a turn", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(testFixture),
    });

    render(<ClaudeChat src="/chats/test.jsonl" />);

    await waitFor(() => {
      expect(
        screen.getByText("what's the current state of the help message?"),
      ).toBeInTheDocument();
    });

    // Get the first Claude message container
    const claudeMessages = document.querySelectorAll(
      '[class*="claudeMessage"]',
    );
    expect(claudeMessages.length).toBeGreaterThan(0);

    const firstClaude = claudeMessages[0];

    // Find the positions of thinking toggle, tool, and text
    const thinkingToggle = firstClaude.querySelector(
      '[class*="thinkingToggle"]',
    );
    const toolBlock = firstClaude.querySelector('[class*="toolBlock"]');

    // Both should exist in first Claude turn
    expect(thinkingToggle).toBeInTheDocument();
    expect(toolBlock).toBeInTheDocument();

    // Verify order: thinking toggle should come before tool block
    if (thinkingToggle && toolBlock) {
      const thinkingPos = thinkingToggle.compareDocumentPosition(toolBlock);
      expect(thinkingPos & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
  });

  it("parses command tags and displays command with special formatting", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      text: () => Promise.resolve(edgeCasesFixture),
    });

    render(<ClaudeChat src="/chats/edge-cases.jsonl" />);

    await waitFor(() => {
      expect(screen.getByText("/sync-help")).toBeInTheDocument();
    });

    // Command should be displayed as text
    const commandBadge = screen.getByText("/sync-help");
    expect(commandBadge).toBeInTheDocument();

    // Command should have the commandBadge class
    expect(commandBadge.className).toContain("commandBadge");

    // Raw XML tags should NOT be visible
    expect(screen.queryByText("<command-name>")).not.toBeInTheDocument();
    expect(screen.queryByText("</command-name>")).not.toBeInTheDocument();
    expect(screen.queryByText("<command-message>")).not.toBeInTheDocument();
    expect(screen.queryByText("</command-message>")).not.toBeInTheDocument();
  });
});
