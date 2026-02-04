---
sidebar_position: 1
title: Introduction
---

> I dream of roombas - thousands of automated AI robots that autonomously maintain codebases\
> — [_Geoffrey Huntley_](https://ghuntley.com/ktlo/)

`mekara` (មករា -- Khmer for January, the start of a brand new cycle of AI-centric software engineering) is **Workflows as Code**: like [IaC](https://en.wikipedia.org/wiki/Infrastructure_as_code) but for your development processes. It mechanizes your codebase by systematically automating your existing manual workflows. You be you, if you were _fast_ like AI and consistent like code.

`mekara` does this through four separate components, any of which can be used in isolation:

1. A set of [core natural language scripts](./usage/index.md#core-commands) (in the form of Claude/OpenCode commands) that allow you to create and mold your own standards and workflow processes.
2. The ability to [compile natural language scripts into code](./usage/compiled-scripts.md), enabling for much faster execution of the deterministic parts of your Claude/OpenCode commands, and more guardrails around getting the LLM to actually execute each of the natural language parts of those commands.
3. A [set of standards](./standards/) and [workflows](./standards/workflow.md) built using the aforementioned core scripts. You should be able to build your own standards and workflows using the very same core scripts.
4. A Wiki made of [how-to's for common development tasks](../wiki/) that ensure best practices and consistency across LLMs. These are meant to also be useful tutorials for humans.

To see this in action, take a look at the example scenarios below:

## Systematize

When you solve a problem with an AI assistant, the solution lives only in that conversation. The next time you face the same problem, you start from scratch. `/systematize` captures your successful approach and turns it into a reusable command—preserving both the steps and the reasoning that made them work.

**Scenario:** Suppose that your README contains the verbatim output of your help text, and you have a sneaking suspicion that the README hasn't been updated since the last time you added a new command. You confirm this with the AI and ask it to update the README:

import ClaudeChat from '@site/src/components/ClaudeChat';

<ClaudeChat src="/chats/sync-help-manual-part1.jsonl" />

From there, you realize this is an action that you're going to be doing over and over again. As such, you run the `/systematize` command to produce [a new command](https://github.com/meksys-dev/ai-dojo/blob/training/intro/systematized/.claude/commands/sync-help.md) that formally records the steps you took to complete this process:

<ClaudeChat src="/chats/sync-help-manual-part2.jsonl" />

Now the next time we want to go through this process again, we just need to invoke our newly systematized command. Not only have we automated away work for ourselves, but in the process of doing so, we have also documented the exact steps taken that will help onboard new humans as well.

<ClaudeChat src="/chats/sync-help-systematized.jsonl" />

:::info[Try it yourself!]
You can try out the process of systematization by cloning our [AI Dojo](https://github.com/meksys-dev/ai-dojo/tree/training/intro/manual) and following these same steps after checking out the `training/intro/manual` tag.
:::

## Mechanize

Natural language commands are flexible but slow—every step requires an LLM round-trip, even when the action is completely deterministic. `/compile` analyzes your command and separates the parts that need judgment from the parts that can run instantly as code. The result: the same workflow, but faster.

**Scenario:** You find that sometimes, when you check whether or not the README is up-to-date, it turns out to be fully up-to-date.

<ClaudeChat src="/chats/sync-help-unchanged.jsonl" />

That is a _lot_ of time and tokens spent on something that could have gone a lot faster. So, we compile the command we have:

<ClaudeChat src="/chats/sync-help-compile.jsonl" />

Note the amount of back-and-forth we have with the LLM over the compilation process: given the potential time savings involved, it is highly recommended to spend some time optimizing this process.

The resulting Python script can be found [here](https://github.com/meksys-dev/ai-dojo/blob/training/intro/mechanized/.mekara/scripts/sync_help.py) -- note the interleaving between fully automated steps and steps that require LLM judgment.

:::info[Try it yourself!]
You can try mechanizing the worfklow yourself on the `training/intro/unchanged` commit on our [AI Dojo](https://github.com/meksys-dev/ai-dojo/).
:::

Now when we run it again, notice how Claude only needs to make a single MCP call. (Unfortunately Claude does not support an override of user commands, or else we could've avoided needing Claude to call `mcp__mekara__start` entirely.)

<ClaudeChat src="/chats/sync-help-mechanized.jsonl" />

:::info[Try it yourself!]
You can try running the compiled script on the `training/intro/mechanized` commit on our [AI Dojo](https://github.com/meksys-dev/ai-dojo/).
:::

### Why not write a fully automated script?

For one, full automation may be brittle:

- If you search for the second code block to edit, the logic may break if another code block is added to the README
- If you search for a heading, the logic may break if the README structure changes
- If you search for the string `dojo --help`, you will still have to search for the next code block -- which is both complicated and will still fail if the README format changes to show both command and output in the same code block
- Even in the current case, searching for the output of `dojo --help` was already broken when an additional warning surfaced with script output, causing the exact match check to fail:

  ```
  warning: The `tool.uv.dev-dependencies` field (used in `pyproject.toml`) is deprecated and will be removed in a future release; use `dependency-groups.dev` instead
  ```

LLMs solve brittleness at the cost of time and money. By picking and choosing which steps we want to fully automate and which steps we want the LLM's judgment on, we can get the best of both worlds.

While the particular scenario presented here is rather contrived, we hope it's still enough to demonstrate the potential of treating natural language as you would any other scripting language.

## Recursive Self-Improvement

No workflow is perfect on the first try. When you run a command and find yourself correcting the AI—explaining edge cases, clarifying ambiguous steps, or handling unexpected situations—that feedback is valuable. `/recursive-self-improvement` captures your corrections and integrates them directly into the command, so future runs benefit from what you learned.

The [self-improvement command](https://github.com/meksys-dev/mekara/blob/main/.claude/commands/recursive-self-improvement.md) completes the core trio. Every time you have to talk with the AI to fix problems following a process you'd previously systematized, you can run `/recursive-self-improvement` afterwards to get the AI to look at the history of your interaction in the session and incorporate your feedback into the process to help all future agents with the task.

## Repeat

With this core trio of Mekara scripts, we were able to grow Mekara into an entire bundle of development processes that integrate together into the [Standard Mekara Workflow](./standards/workflow/), which includes a bundle of repository-initialization scripts that will in aggregate set up a [Standard Mekara Project](./standards/project/) documented using [Standard Mekara Documentation](./standards/documentation/).

Continue on to see the vision and philosophy between Mekara.
