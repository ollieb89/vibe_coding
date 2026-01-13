# Claude Code Custom Commands & Workflows Overview

## 1. Executive Summary
"Claude Code" (Anthropic's agentic CLI) is a highly extensible tool that moves beyond simple chat by integrating directly with your shell and file system. Its power lies in **Custom Commands** (Slash Commands) and **Context Configuration** (`CLAUDE.md`).

Unlike traditional CLIs with static binaries, Claude Code's "commands" are typically **Markdown files** containing prompt engineering, shell scripts, and MCP (Model Context Protocol) tool calls. This makes them easy to read, modify, and share.

**Key Insight:** The "best" commands aren't single binaries, but **Command Suites** (repositories of `.md` recipes) and **MCP Servers** that expose functionality to Claude.

---

## 2. Top Repositories & Command Suites
The following repositories contain curated collections of commands, sub-agents, and workflow templates.

| Repository | Focus | Best For |
| :--- | :--- | :--- |
| **`awesome-claude-code`** (Various authors*) | Curated Lists | Finding the latest tools, MCP servers, and community guides. |
| **`VoltAgent/awesome-claude-code-subagents`** | Specialized Agents | "Sub-agents" designed for specific domains (e.g., security audit, QA). |
| **`ruvnet/claude-flow`** | `CLAUDE.md` Templates | Standardizing project context. Contains templates for React, Python, etc. |
| **`quemsah/awesome-claude-plugins`** | Metrics & Discovery | Automated tracking of popular plugins and tools across GitHub. |

*\*Note: "Awesome" lists are community-driven. The `jqueryscript` and `awesomeclaude.ai` forks are popular entry points.*

---

## 3. Essential Command Recipes (The "Must-Haves")
These are specific high-value commands you should implement in your `.claude/commands/` directory.

### 🛠️ The "Sanity" Commit (`/commit`)
*   **Goal:** Prevent bad code from entering history.
*   **Mechanism:** Runs `git diff`, checks for `TODO`/`FIXME`/`console.log`, and generates a semantic commit message.
*   **Workflow:**
    1.  User types `/commit "optional context"`.
    2.  Claude reads staged files.
    3.  If "blockers" (like debug prints) exist -> Aborts with warning.
    4.  If clean -> Generates Conventional Commit message & executes `git commit`.

### 🔄 The Context Refresher (`/catchup`)
*   **Goal:** Re-sync Claude after a `/clear` or long session.
*   **Mechanism:** Reads `git status` and uncommitted changes to "catch up" on what happened since context was wiped.
*   **Workflow:** `/clear` -> `/catchup` -> Claude is back in context without re-reading the whole repo.

### 🎫 Ticket Manager (`/ticket`)
*   **Goal:** Turn a Jira/GitHub issue into code.
*   **Mechanism:** Uses **GitHub MCP** or **Jira MCP**.
*   **Workflow:**
    1.  `/ticket PROJ-123`
    2.  Claude fetches issue details via MCP.
    3.  Create branch `feat/PROJ-123`.
    4.  Implements changes based on acceptance criteria.

### 🧱 Project Scaffolding (`/project:new`)
*   **Goal:** Standardized file creation (Namespaced).
*   **Location:** `.claude/commands/project/new.md` (Invoked as `/project:new`).
*   **Workflow:** prompts for parameters (component name, type) and creates file + test + storybook entry simultaneously.

---

## 4. The Architecture of Custom Commands

### File Structure
Commands are Markdown files. The filename becomes the command.
```text
.claude/
  commands/
    commit.md        -> /commit
    review.md        -> /review
    test/
      ui.md          -> /test:ui
  CLAUDE.md          -> (Auto-loaded Context)
```

### The `CLAUDE.md` Context File
This is not a command, but the **brain** behind the commands. It should contain:
*   **Build/Test Commands:** `npm run build`, `pytest`.
*   **Style Guide:** "Use Functional Components", "Snake_case for variables".
*   **Architecture:** High-level system design.
*   **Note:** Use `ruvnet/claude-flow` templates to generate this.

### MCP: The Engine
Custom commands often just wrap **MCP Tools**.
*   **Filesystem MCP:** Reads/Writes code.
*   **GitHub MCP:** Manages PRs/Issues.
*   **Postgres MCP:** Queries DBs directly.
*   **Playwright MCP:** E2E testing / Browser automation.

---

## 5. Implementation Strategy for You
To build a robust Claude Code environment, follow this "Starter Pack" plan:

1.  **Initialize Context:** Create a `CLAUDE.md` in your root using a template from `claude-flow` that matches your tech stack.
2.  **Install Core MCPs:** Ensure `filesystem` and `github` MCP servers are active.
3.  **Create "Global" Commands (`~/.claude/commands/`):**
    *   `commit.md` (The sanity checker).
    *   `review.md` (For PR reviews).
4.  **Create "Project" Commands (`.claude/commands/`):**
    *   `deploy.md` (Specific to your infra).
    *   `db:migrate.md` (Safe migration runner).

**References:**
*   [Anthropic Custom Commands Docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/commands)
*   [Awesome Claude Code (GitHub)](https://github.com/topics/claude-code)
