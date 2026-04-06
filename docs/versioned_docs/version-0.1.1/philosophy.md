---
sidebar_position: 2
title: Philosophy
---

**The bottlenecks in software development are changing.** It used to be bits, which were so scarce that we would even shave two digits off of years, resulting in [Y2K](https://en.wikipedia.org/wiki/Year_2000_problem). Then it became code, and to economize on code written we ended up with bloated Electron apps and the [left-pad incident](https://en.wikipedia.org/wiki/Npm_left-pad_incident). Now language has become the final bottleneck for transmuting ideas into execution, a bottleneck that has always existed between humans but is becoming increasingly applicable to machines. The final runtime artifact is merely the tip of the iceberg of the entire ecosystem comprising the codebase, the infra, the dev tooling, the devs themselves, and the organizational structure linking the devs. Through the [**Standard Mekara Workflow**](./standards/workflow/), Mekara serves as a proof-of-concept for streamlining the processes that produce the code [rather than the code itself](https://www.chrisgregori.dev/opinion/code-is-cheap-now-software-isnt).

**The runtime artifacts are morphing.** Used to be you "programmed" [ENIAC](https://en.wikipedia.org/wiki/ENIAC) by physically rearranging the circuits via the plugboard -- physically hardcoded circuits were the runtime artifact. Then came [stored programs](https://en.wikipedia.org/wiki/Stored-program_computer), and digital binaries became the runtime artifact. Then came interpreted programs, and the source code itself became the runtime artifact. Now prompts are becoming the runtime artifact -- what is a program after all, but [a collection of rules and instructions](https://github.com/bmad-code-org/BMAD-METHOD) on how to manipulate data? Through [the compilation and nested invocation](index.md) of agent commands, Mekara serves as a proof-of-concept for treating natural language scripts as first-class programs.

**The silos are eroding.** Silos used to be CPU architectures; then compilers, JITs, and fat binaries made the same code work across different architectures. Silos became the OS itself; then app frameworks such as Electron, Flutter, and Unity made code work the same across different OS's, both mobile and desktop. Silos became the stack you develop your code on, but now that machines can remix language and code alike faster than humans can think, LLMs promise a final evolution of [literate programming](https://en.wikipedia.org/wiki/Literate_programming) into a future where code becomes documentation and documentation becomes code, a future where the final "silos" are the constellation of ideas that together form a cohesive project. Through the definition of [**Standard Mekara Documentation**](./standards/documentation/), Mekara serves as a proof-of-concept for leveraging natural language as the natural source of truth, accessible to humans and AI alike.

**What is good for the human is good for the AI.** How long does it take before a human dropped into the middle of your codebase can make a meaningful contribution? If good documentation and tests shorten that time for a human, the same is doubly true for LLMs. How do you induct new human engineers into the processes that your team runs on? You train them on how to do something, you watch them fail at it, and you correct them on their mistakes. If good actionable feedback is necessary for humans to improve, the same is doubly true for LLMs. Mekara is a proof-of-concept for bridging that gap between utility for humans and utility for machines.

**Mekara itself was built using these principles.** As the areas of human concern and meddling move progressively up the stack, the points at which quality control checks are introduced also move up the stack. Most of the code that comprises Mekara, the unit tests that check that code, and the documentation for that code have never reviewed by a human past its initial conception. Instead, through the [recording and replay](./code-base/mekara/vcr-agent-recordings/usage/) of interactions between a hermetically sealed Mekara and its environment, we do black box verification that Mekara's algorithms continue to produce the same exact interactions with the outside world. A future is coming where black box testing can ensure that the instructions in user guides are always up-to-date and fully reproducible.

**Mekara endorses fork-first development.** Ultra-personalization is the name of the game in the Age of AI. Claude Opus 4.5 is already quite good at [managing merge conflicts](https://github.com/meksys-dev/mekara/tree/main/.mekara/scripts/nl/merge-main.md) by first understanding the intentions behind different commits, and the [costs of maintaining a fork](https://hamishcampbell.com/foss-just-fork-it-delusion/) are only going to monotonically decrease. While we welcome pull requests, we also **strongly** encourage you to dare to be your own self-reliant upstream. If Mekara is to succeed at all in its purpose, it will do so merely by serving as the bootstrapper for [your own personal AI factory](https://www.john-rush.com/posts/ai-20250701.html) &mdash; whatever form that ends up taking.

## Inspirations

Some of the other projects that we took inspiration from include:

- The [BMAD method](https://github.com/bmad-code-org/BMAD-METHOD) for showing us how structured prompts can come together to form something that is recognizably programmatic
- [DeepWiki](https://deepwiki.com/) and [DeepWiki-Open](https://github.com/AsyncFuncAI/deepwiki-open) for showing us how the AI can create and update structured documentation
- [Claude Code](https://claude.com/product/claude-code) and [OpenCode](https://opencode.ai/) for showing us the possibilities of the agentic coding paradigm

If you find Mekara to be a useful contribution to the ongoing conversation around the future of software development, please consider crediting us as well.

:::info

Want to hire out the brains behind Mekara? Want to work with us to define the software engineering standards of the future? Shoot us an email at magic@meksys.com!

:::
