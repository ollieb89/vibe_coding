# Claude Code Plugins & Extensions Overview

## 1. Executive Summary
Unlike traditional IDEs with a dedicated "Plugin Store," Claude Code extends its functionality primarily through **Model Context Protocol (MCP) Servers** and **Tool/Command Suites**.
There is no single "install plugin" command; instead, you "add MCP servers" or "clone command suites" into your configuration.

**Key Insight:** The ecosystem is split into **MCP Servers** (Backend capabilities like DB access) and **Slash Command Suites** (Frontend workflows like `/plan`).

---

## 2. Top Extension Registries

| Repository | Focus | Best For |
| :--- | :--- | :--- |
| **`awesome-claude-code`** | The Central Hub | Finding MCP servers, slash commands, and templates. |
| **`claudemarketplaces.com`** | Visual Directory | Browsing available MCP integrations. |
| **`modelcontextprotocol/servers`** | Official MCPs | High-quality, maintained servers (GitHub, Postgres, etc.). |

---

## 3. Essential Plugins (MCP Servers)
These provide *capabilities* to Claude.

### 🧠 Core Capabilities
*   **`Memory MCP` (Ensue/Official)**
    *   **Function:** Persists memories across sessions (user preferences, architectural decisions).
    *   **Value:** Prevents Claude from forgetting your coding style.

*   **`Filesystem MCP`**
    *   **Function:** Advanced file manipulation (often built-in, but can be enhanced).
    *   **Value:** Safe file editing with permissions.

### 🛠️ Developer Tools
*   **`GitHub MCP`**
    *   **Function:** Full control over Issues, PRs, and Repo management.
    *   **Command:** `claude mcp add github`

*   **`Playwright MCP`**
    *   **Function:** Browser automation.
    *   **Use Case:** "Go to localhost:3000 and tell me if the login button works."

*   **`Snyk MCP`**
    *   **Function:** Security scanning for dependencies.

---

## 4. Top Workflow Extensions (Command Suites)
These provide *workflows* (recipes) to Claude.

*   **`Repomix`**
    *   **Function:** Packs your entire repository into a single context-optimized format.
    *   **Use Case:** "Analyze my entire codebase for architectural flaws."

*   **`Claude-Flow` / `Spec Workflow`**
    *   **Function:** Enforces a structured development lifecycle (Spec -> Plan -> Code -> Review).
    *   **Value:** Prevents "coding without a plan."

*   **`Claude Taskmaster`**
    *   **Function:** Converts PRDs (Product Requirement Docs) into actionable tasks.

---

## 5. Installation & Configuration

### Installing an MCP Server
You add servers via the CLI or `settings.json`.
```bash
# Example: Adding GitHub MCP
claude mcp add github -- npx -y @modelcontextprotocol/server-github
```

### Configuration File (`~/.claude/settings.json`)
This file controls your active plugins/MCPs.
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "postgres": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/postgres", "postgresql://user:pass@localhost/db"]
    }
  }
}
```

---

## 6. Implementation Strategy

To build a "Fully Loaded" Claude Environment:

1.  **Memory Layer:** Install `Memory MCP` to retain context.
2.  **Dev Layer:** Install `GitHub MCP` and `Postgres MCP` (if applicable).
3.  **Workflow Layer:** Clone a command suite like `Claude-Flow` into `~/.claude/commands/` to get standardized `/plan` and `/spec` commands.

**References:**
*   [Model Context Protocol Hub](https://modelcontextprotocol.io)
*   [Awesome Claude Code](https://github.com/topics/claude-code)
