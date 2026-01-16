# Claude Code Commands: The Complete In-Depth Guide (2026)

> **Research Date:** January 13, 2026  
> **Focus:** In-depth analysis of Claude Code slash commands, custom commands, subagent orchestration, MCP integration, and community command suites  
> **Primary Sources:** Anthropic Official Docs, Skywork.ai, PubNub, Shipyard, GitHub community projects, Awesome Claude Code collections, VoltAgent & davepoon command/subagent repos

---

## TABLE OF CONTENTS

1. [Executive Summary](#executive-summary)
2. [Part 1: Built-in Slash Commands](#part-1-built-in-slash-commands)
3. [Part 2: Custom Commands (Markdown-based)](#part-2-custom-commands-markdown-based)
4. [Part 3: The Permission System](#part-3-the-permission-system)
5. [Part 4: MCP Servers & Dynamic Commands](#part-4-mcp-servers--dynamic-commands)
6. [Part 5: Subagent Orchestration & Delegation](#part-5-subagent-orchestration--delegation)
7. [Part 6: Advanced Patterns & Workflows](#part-6-advanced-patterns--workflows)
8. [Part 7: CLAUDE.md Context Architecture](#part-7-claudemd-context-architecture)
9. [Part 8: CLI Commands & Flags Reference](#part-8-cli-commands--flags-reference)
10. [Part 9: Best Practices & Optimization](#part-9-best-practices--optimization)
11. [Appendix: Command Recipes & Examples](#appendix-command-recipes--examples)
12. [Top Community Repositories](#top-community-repositories)

---

## EXECUTIVE SUMMARY

Claude Code has evolved beyond a simple CLI tool into a **multi-agent coordination platform** powered by three interconnected systems.

| System            | What                                          | Purpose                                          |
|-------------------|-----------------------------------------------|--------------------------------------------------|
| Slash Commands    | Built-in commands + custom Markdown files     | Quick access to workflows and utilities         |
| MCP Integration   | External tools (GitHub, Postgres, Playwright) | Extend Claude's capabilities beyond the terminal |
| Subagents         | Specialized AI instances with tool restrictions | Parallelize work, isolate context, preserve main thread |

### Key Innovation (2026)

Automatic subagent delegation now understands task complexity and routes work intelligently:

- Simple fixes → Main Claude agent
- Performance analysis → Performance subagent
- Security review → Security specialist subagent
- Multi-step tasks → Sequential agent chains

**Result:** You describe the goal; Claude Code orchestrates the right team.

### Ecosystem View (Community Repos)

Community repos provide command suites and subagent catalogs that dramatically extend the built-in experience:

| Repo                                      | Focus                            | Best For                                             |
|-------------------------------------------|----------------------------------|------------------------------------------------------|
| `awesome-claude-code`                     | Curated lists                    | Discovering latest tools, MCP servers, guides        |
| `VoltAgent/awesome-claude-code-subagents` | Specialized subagents            | Ready-made domain specialists (security, QA, etc.)   |
| `ruvnet/claude-flow`                      | CLAUDE.md templates              | Standardizing project context across stacks          |
| `wshobson/commands`                       | Production command suites        | Drop-in workflows (spec→plan→code→test→deploy)       |
| `davepoon/claude-code-subagents-collection` | Mixed agents + commands + UI   | Browsing & installing agents/commands via web UI     |

The best setups combine official features with community suites, wiring them together via CLAUDE.md, permissions, and a small set of global commands.

---

## PART 1: BUILT-IN SLASH COMMANDS

Built-in slash commands are always available in every Claude Code session. They control the conversation, configure tools, and manage context.

### Command Taxonomy

Commands fall into four categories:

| Category            | Purpose                               | Examples                         |
|---------------------|----------------------------------------|----------------------------------|
| Context Management  | Control conversation history and focus | `/clear`, `/compact`, `/rewind`  |
| Configuration       | Set permissions, select models, configure tools | `/permissions`, `/model`, `/config` |
| Navigation          | Add directories, manage session state  | `/add-dir`, `/status`, `/memory` |
| Utilities           | Health checks, help, terminal setup    | `/help`, `/doctor`, `/terminal-setup` |

### Category 1: Context Management Commands

#### `/clear`

**Purpose:** Wipe conversation history and start fresh.

**Use cases:**
- Conversation has drifted from original task
- Switching projects mid-session; need a reset
- Emergency cleanup when context is corrupted

**Example:**

```bash
claude
> /clear
→ Conversation cleared. Starting fresh.
> explain the deployment pipeline
```

**Tip:** Prefer `/compact` before `/clear` to preserve a compressed context.

---

#### `/compact [optional focus]`

**Purpose:** Summarize conversation history while keeping context tight.

**Mechanism:**
- Analyzes entire history
- Produces compressed summary of key decisions, code, and errors
- Optional focus string to protect a specific area

**Example:**

```bash
> /compact focus on authentication errors from the last two commits
→ [Context summarized from 47 turns to 8 key decisions]
```

**Why it matters:**
- Claude auto-compacts near the token limit
- Manual compaction lets you choose what to preserve
- Prevents loss of nuance vs. blunt truncation

**Real-world scenario:**

```
You've spent 2 hours building an OAuth flow. The conversation now has 80 turns.
Context is tight. Instead of /clear:

> /compact focus on the login endpoint and token refresh logic
→ Summary keeps auth logic intact, drops debug detours
> Now continue building the logout flow
```

---

#### `/rewind [steps]`

**Purpose:** Step backward in conversation history.

**Mechanism:** Removes the last N turns from context, returning to a clean state.

**Example:**

```bash
> /rewind 3
→ Last 3 turns removed. You're back to: "fix the type errors"
```

**When to use:**
- Experimental turn went wrong; backtrack before it propagates
- Incorrect suggestion; rewind, then provide correction
- Explore different approaches from a known good point

---

### Category 2: Configuration Commands

#### `/permissions`

**Purpose:** View and configure which tools Claude can use.

**Tool categories:**
- `Read` – File reading
- `Write` – File modification/creation
- `Bash` – Shell command execution
- `MCP(...)` – External integrations (GitHub, Postgres, etc.)

**Interactive configuration:**

```bash
claude
> /permissions
→ Interactive menu:
  1. Allow all tools (least safe for production code)
  2. Restrict write access to src/ only
  3. Restrict bash to git/npm commands
  4. Custom configuration
```

**Programmatic configuration (`~/.claude/settings.json`):**

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**)",
      "Bash(git *)",
      "Bash(npm *)",
      "MCP(github)"
    ],
    "deniedTools": [
      "Write(.env*)",
      "Write(production.config.*)",
      "Bash(sudo *)",
      "Bash(rm *)"
    ]
  }
}
```

**Real-world profiles:**

**Web Developer:**

```json
{
  "allowedTools": [
    "Read",
    "Write(src/**)",
    "Write(public/**)",
    "Bash(npm *)",
    "Bash(git *)",
    "MCP(github)",
    "MCP(playwright)"
  ]
}
```

**Backend Engineer (with DB access):**

```json
{
  "allowedTools": [
    "Read",
    "Write(src/**)",
    "Bash(npm *)",
    "Bash(git *)",
    "Bash(docker *)",
    "MCP(github)",
    "MCP(postgres)",
    "MCP(sentry)"
  ]
}
```

**Safety-first (code review mode):**

```json
{
  "allowedTools": [
    "Read",
    "MCP(github)"
  ]
}
```

---

#### `/model [model_name]`

**Purpose:** Switch to a different Claude model or pin a specific version.

**Available models (January 2026):**

- `claude-opus-4.1` – Most capable, higher cost
- `claude-sonnet-4.1` – Balanced, recommended for coding
- `claude-haiku-4` – Fastest, good for subagents
- `claude-3.5-sonnet` – Legacy, deprecated

**Example:**

```bash
> /model claude-haiku-4
→ Model switched to claude-haiku-4 (faster, cheaper for subagents)

> /model claude-opus-4.1
→ Model switched to claude-opus-4.1 (best for complex tasks)
```

**Strategy:**
- Main agent: opus-4.1 for complex planning
- Subagents: haiku-4 for fast parallel work
- Review phases: sonnet-4.1 for balanced tradeoff

---

#### `/config`

**Purpose:** Interactive configuration wizard.

**Configures:**
- Default working directories
- MCP servers
- Permission profiles
- Default model
- Memory settings

**Example:**

```bash
> /config
→ Claude Code Configuration Wizard
  1. Set default working directory
  2. Add MCP servers
  3. Configure permissions
  4. Set default model
  5. Enable memory
  → Select option: 2
  → Available servers: github, postgres, playwright, sentry, filesystem
  → Add server: github
  → GitHub token: [prompt]
  → ✓ Added github MCP
```

---

### Category 3: Navigation Commands

#### `/add-dir [path ...]`

**Purpose:** Add additional working directories (especially for monorepos).

**Effect:** Claude can read/write across multiple roots in a single session.

**Example (monorepo structure):**

```
my-workspace/
├── apps/
│   ├── web/
│   └── mobile/
└── libs/
    ├── shared/
    └── api/
```

**Session setup:**

```bash
cd /my-workspace/apps/web
claude
> /add-dir ../mobile ../../libs/shared ../../libs/api
→ Added directories. Claude can now access all 4 projects.
> Create a shared utility function in libs/shared that both web and mobile can use
→ [Claude modifies files across all 4 directories]
```

**Real-world scenario:**

```bash
# Instead of switching sessions:
claude  # in apps/web
> /add-dir ../mobile ../api
> Create an API endpoint for user data, and a mobile screen to display it
→ [Claude handles both web and mobile in one session]
```

---

#### `/status`

**Purpose:** Display current session status.

**Output includes:**
- Active model and version
- Working directories
- Connected MCP servers
- Current permissions
- Memory status
- Token usage (if tracking)

**Example:**

```bash
> /status
→ Claude Code Session Status
  Model: claude-opus-4.1
  Directories: [/project, /project/api, /project/web]
  MCP Servers: github, postgres, playwright
  Permissions: Read, Write(src/**), Bash(git *, npm *)
  Memory: Enabled (5 items stored)
  Context usage: 12,847 / 200,000 tokens
```

---

#### `/agents`

**Purpose:** List available subagents and their capabilities.

**Output includes:**
- Built-in subagents (Explore, Plan, General)
- Custom subagents in project
- Tool restrictions per agent
- When each is auto-delegated

**Example:**

```bash
> /agents
→ Available Subagents:
  
  [Built-in]
  • Explore (discovery, read files, grep patterns)
  • Plan (architecture design, decision docs)
  • General (fallback for unspecialized tasks)
  
  [Custom Project Agents]
  • SecurityAuditor (restricted to: Read, MCP(snyk))
  • PerformanceAnalyst (restricted to: Read, Bash(profiler))
  • FrontendSpecialist (restricted to: Write(src/components), Bash(npm *))
```

---

#### `/memory`

**Purpose:** Manage persistent memory across sessions.

**Types of memory:**
- **Implicit memory:** Claude remembers your coding style, project conventions
- **Explicit memory:** Items you save for future sessions

**Example:**

```bash
> /memory list
→ Stored items:
  1. "Project uses functional components with hooks"
  2. "Database schema: PostgreSQL v15 with RLS enabled"
  3. "Build process: Vite, target ES2020"

> /memory add "API responses use snake_case; frontend uses camelCase"
→ Saved to memory

> /memory clear-item 2
→ Removed database schema from memory
```

**Pro tip:** Use memory for project constants, style guides, and architectural decisions. Update it when standards change.

---

### Category 4: Utility Commands

#### `/help`

**Purpose:** Display all available commands (built-in + custom).

**Output includes:** Description of each built-in and the discovered custom commands like `/commit`, `/review`, `/plan`, `/test:ui`, `/project:new`.

---

#### `/doctor`

**Purpose:** Diagnose issues with Claude Code setup.

**Checks:**
- Claude CLI installation and version
- ANTHROPIC_API_KEY environment variable
- MCP server connectivity
- Permission system status
- Shell integration (if using /terminal-setup)

**Example:**

```bash
> /doctor
→ Health Check Report:
  ✓ Claude CLI version: 1.4.2 (latest)
  ✓ API key configured
  ✓ MCP servers: github (✓), postgres (✗ - connection timeout)
  ✓ Permissions system: OK
  ✗ Shell integration: Not configured
  → Suggestion: Run /terminal-setup to enable shell aliases
```

---

#### `/terminal-setup`

**Purpose:** Configure shell integration for Claude Code.

**What it does:**
- Creates shell aliases (`claude`, `claude-continue`, etc.)
- Integrates with your `~/.zshrc`, `~/.bashrc`, etc.
- Enables tab-completion for commands

**Example:**

```bash
> /terminal-setup zsh
→ Detected shell: zsh
  Setting up aliases:
    • claude              → interactive REPL
    • claude-continue     → continue session
    • claude-quick        → print mode
  Adding to ~/.zshrc...
  ✓ Setup complete. Restart terminal to activate.
```

---

#### `/hooks`

**Purpose:** Configure lifecycle hooks (code that runs at specific points).

**Available hooks:**
- `PreToolUse` – Before Claude uses a tool (validate commands, log)
- `PostToolSuccess` – After tool succeeds (record, archive)
- `PostToolFailure` – After tool fails (recover, notify)
- `SubagentDelegation` – Before delegating to subagent
- `SubagentReturn` – When subagent returns results

**Example use case (safety gate):**

```bash
> /hooks configure
→ Hook Configuration:
  1. PreToolUse: Validate bash commands before execution
  2. PostToolFailure: Log failures to audit.log
  3. SubagentDelegation: Notify on high-impact delegations
  → Select hooks to configure...
```

**YAML configuration (`~/.claude/hooks.yaml`):**

```yaml
hooks:
  PreToolUse:
    - name: "validate-destructive-commands"
      conditions:
        - tool: Bash
          command: "rm|truncate|drop|delete"
      action: "request-approval"
      prompt: "This command looks destructive. Approve?"
  
  PostToolSuccess:
    - name: "log-file-changes"
      conditions:
        - tool: Write
      action: "log"
      format: "Modified {filename} at {timestamp}"
      logfile: "~/.claude/audit.log"
```

---

#### `/usage` and `/cost`

**Purpose:** Track token consumption and estimated costs.

**Output includes:**
- Tokens used this session
- Tokens used this month
- Cost per model
- Projected monthly cost

**Example:**

```bash
> /usage
→ Token Usage Summary:
  This session: 24,517 tokens
  This month: 847,239 tokens
  
  Model breakdown:
  • claude-opus-4.1:   450,000 tokens @ $15/1M = $6.75
  • claude-haiku-4:    397,239 tokens @ $0.80/1M = $0.32
  
  Total cost this month: $7.07
  Projected monthly cost: $21.21
```

---

## PART 2: CUSTOM COMMANDS (MARKDOWN-BASED)

Custom commands are the workflow layer of Claude Code. They are markdown files that become slash commands when placed in specific directories.

### Architecture Overview

**Command locations:**

```
~/.claude/commands/          → User-level (global)
  ├── commit.md              → /user:commit
  ├── review.md              → /user:review
  └── security/scan.md       → /user:security:scan

.claude/commands/            → Project-level (this project)
  ├── deploy.md              → /deploy
  ├── test/unit.md           → /test:unit
  ├── test/e2e.md            → /test:e2e
  └── db/migrate.md          → /db:migrate
```

Community command suites (e.g., `wshobson/commands`, `davepoon/claude-code-subagents-collection`) ship these structures pre-populated so you can copy them wholesale into `~/.claude/commands/`.

---

### Command Structure: Anatomy

Every custom command is a markdown file with YAML frontmatter followed by prompt instructions.

**Example: `.claude/commands/review.md`**

```markdown
---
name: review
description: Code review checking security, performance, and best practices
model: opus
tools:
  - Read
  - MCP(github)
---

# Code Review Command

You are a senior engineer reviewing code changes.

## Review Focus

1. **Security** (Critical)
   - SQL injection
   - Auth bypass
   - Secrets exposure
   - CORS issues

2. **Performance** (High)
   - N+1 queries
   - Missing indices
   - Unnecessary DOM work
   - Memory leaks

3. **Maintainability** (Medium)
   - Clarity
   - Tests
   - Docs
   - Types

## Your Task

Review the following code changes:

\`\`\`
{cmd:git diff HEAD~1}
\`\`\`

## Output Format

For each issue found:
- **File:** `src/auth.ts` (line 42)
- **Severity:** Critical / Warning / Info
- **Category:** Security / Performance / Maintainability
- **Description:** What's wrong and why
- **Suggestion:** How to fix it
- **Example:** Code snippet showing the fix
```

---

### Command Syntax Reference

Commands support several special syntaxes:

| Syntax                | Purpose                                | Example                       |
|-----------------------|----------------------------------------|-------------------------------|
| `{cmd:shell}`         | Execute shell, include output          | `{cmd:git diff --staged}`     |
| `{file:path}`         | Include file content                   | `{file:src/App.tsx}`          |
| `{{args}}`            | User-provided arguments                | `/fix-issue 123`              |
| `{{env:VAR}}`         | Environment variable expansion         | `{{env:DATABASE_URL}}`        |
| YAML frontmatter      | Name, description, model, tools, etc.  | `--- ... ---`                 |

---

### Example 1: Semantic Commit Command

**File: `.claude/commands/commit.md`**

```markdown
---
name: commit
description: Create semantic commits with debug-code detection
model: sonnet
---

# Semantic Commit Generator

You are a commit message expert and code quality guardian.

## Step 1: Scan for Blockers

Before committing, check for code that must not reach production:

- `console.log()`, `console.debug()`, `console.error()` (leftover debug)
- `debugger;` statement
- `TODO` or `FIXME` without context
- Commented-out code blocks
- Hardcoded credentials or API keys
- Large console.table() calls

If ANY blocker found, REJECT with clear warning.

## Step 2: Analyze Changes

Review the staged changes:

\`\`\`
{cmd:git diff --staged}
\`\`\`

## Step 3: Generate Conventional Commit

Format: `type(scope): description`

Types:
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code reorganization (no feature change)
- `perf:` Performance improvement
- `test:` Test additions/changes
- `docs:` Documentation
- `chore:` Build, deps, CI config
- `style:` Formatting (semicolons, quotes)

Scope: Affected component/module (optional but recommended)

Description: Present tense, lowercase, no period

Example outputs:
- `feat(auth): add OAuth2 login flow`
- `fix(api): handle missing user gracefully`
- `perf(db): add index on user_id column`

---

## Expected Output

If clean:
\`\`\`
feat(auth): add OAuth2 login flow
\`\`\`

If blockers found:
\`\`\`
❌ COMMIT BLOCKED

Blockers detected:
1. Line 47 (App.tsx): console.log('Debug session')
2. Line 92 (auth.ts): TODO Handle expired tokens

Fix these issues, then try /commit again.
\`\`\`
```

**Usage in session:**

```bash
git add src/auth.ts
git add src/components/Login.tsx

claude
> /commit
→ Analyzing staged changes...
→ ✓ No debug code found
→ Generated commit message:
   feat(auth): add OAuth2 login flow
→ Execute this commit? [y/n]: y
→ Committed with message: feat(auth): add OAuth2 login flow
```

This pattern is extended in community suites with variants like `sanity-commit` that integrate ticket IDs, release tags, and remote checks.

---

### Example 2: Task Planner Command

**File: `.claude/commands/plan.md`**

```markdown
---
name: plan
description: Break down a task into detailed implementation steps
model: opus
---

# Task Planning Command

You are a senior architect breaking down complex tasks.

## Input Task

{{args}}

## Your Output

Provide a detailed implementation plan:

1. **Requirements Analysis**
   - What needs to be built?
   - What constraints exist?
   - What dependencies are there?

2. **Architectural Decision**
   - Best tech choices?
   - Patterns to use?
   - Potential pitfalls?

3. **File Structure**
   ```
   Files to create:
   Files to modify:
   Files to delete:
   ```

4. **Implementation Steps**
   Each step as a checkbox:
   - [ ] Step 1: Description
   - [ ] Step 2: Description
   - [ ] Step 3: Description
   Estimate complexity: 1-5 (1=trivial, 5=expert-level)

5. **Testing Strategy**
   - Unit tests needed?
   - Integration tests?
   - E2E tests?

6. **Blockers & Risks**
   - What could go wrong?
   - How to mitigate?

7. **Success Criteria**
   - How do we know it's done?
   - What does done look like?
```

**Usage:**

```bash
claude
> /plan "Add two-factor authentication to the login system"
→ Analyzing task...
→ [Detailed plan with steps, file structure, blockers]
→ Estimated effort: 8 hours (complexity: 4/5)
→ Continue with implementation? Type: /code
```

---

### Example 3: Database Migration Command

**File: `.claude/commands/db/migrate.md`**

```markdown
---
name: migrate
description: Safe database migration runner with rollback capability
tools:
  - Read
  - Bash(npm *)
  - MCP(postgres)
---

# Database Migration Runner

You are a database operations expert.

## Step 1: Validate Pending Migrations

Check for pending migrations:

\`\`\`
{cmd:npm run db:status}
\`\`\`

If none, report "No pending migrations" and exit.

## Step 2: Review Migration Content

\`\`\`
{cmd:find migrations/ -name "*.sql" -type f | sort | tail -5}
\`\`\`

For each pending migration:
- Read the SQL file content
- Scan for dangerous patterns:
  - DROP TABLE without backing up
  - DELETE without WHERE clause
  - ALTER COLUMN that could cause data loss
- Estimate migration time
- Check for locks that might affect production

## Step 3: Pre-flight Check

\`\`\`
{cmd:npm run db:check}
\`\`\`

Expected: No errors, database is healthy.

## Step 4: Run Migration

If safe, run with transaction:

\`\`\`
{cmd:npm run db:migrate}
\`\`\`

Monitor for errors. On failure:
- Automatic rollback triggered
- Report what went wrong
- Suggest fixes

## Step 5: Verify

\`\`\`
{cmd:npm run db:status}
\`\`\`

All migrations should show completed.

## Troubleshooting

If migration fails:
1. Check database logs
2. Inspect rollback status
3. Suggest manual recovery steps
```

This "safe migrate" pattern appears across multiple repos as a best-practice template for DB changes.

---

### Command Parameters & Arguments

Commands can accept user input via `{{args}}`:

**File: `.claude/commands/fix-issue.md`**

```markdown
---
name: fix-issue
description: Fix a specific GitHub issue
---

# Issue Fixer

## Step 1: Fetch Issue

Issue number: {{args}}

\`\`\`
{cmd:gh issue view {{args}}}
\`\`\`

## Step 2: Create Branch

\`\`\`
{cmd:git checkout -b fix/issue-{{args}}}
\`\`\`

## Step 3: Implement

[... your implementation logic ...]

## Step 4: Test & Commit

\`\`\`
{cmd:npm test}
\`\`\`

[Create semantic commit]
```

**Usage:**

```bash
claude
> /fix-issue 123
→ [Fetches issue #123, creates branch fix/issue-123, implements]
```

Community suites extend this idea into more complex workflows such as `/ticket` to pull from Jira/GitHub issues and scaffold branches and task breakdowns.

---

## PART 3: THE PERMISSION SYSTEM

Permissions are how Claude Code enforces safety boundaries. They control which tools Claude can use in which contexts.

### Permission Model

Each tool has a scope that can be restricted:

```
Tool                  Scope Example           Description
────────────────────────────────────────────────────────────
Read                  Read(src/**)            Can read files matching pattern
Write                 Write(src/**, !src/test) Can write to src/, not src/test/
Bash                  Bash(git *, npm *)      Can run git and npm commands only
MCP(github)           MCP(github)             Can use GitHub MCP server
```

---

### Permission Patterns

**Glob patterns:**

```
src/**              All files in src/ and subdirectories
src/*.ts            All .ts files in src/ only
src/{auth,api}/**   Files in src/auth/ or src/api/
!src/test/**        Exclude test directory (with ! prefix)
```

---

### Permission Profiles for Different Workflows

**Profile 1: Full Autonomy (Development)**

```json
{
  "permissions": {
    "allowedTools": ["Read", "Write", "Bash", "MCP(github)"]
  }
}
```

Use for: Local development when you trust the task.

---

**Profile 2: Restricted Write (Code Review)**

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "Write(src/**, !src/deprecated/**)",
      "Bash(git *, npm run test)",
      "MCP(github)"
    ],
    "deniedTools": [
      "Write(.env*)",
      "Write(config/production.*)",
      "Bash(rm *)",
      "Bash(sudo *)"
    ]
  }
}
```

Use for: Code review mode. Can suggest changes but not execute destructive commands.

---

**Profile 3: Read-Only Audit (Security Audit)**

```json
{
  "permissions": {
    "allowedTools": [
      "Read",
      "MCP(snyk)",
      "MCP(github)"
    ]
  }
}
```

Use for: Security audits, dependency scanning. Read-only access.

---

**Profile 4: Subagent with Restricted Tools**

```json
{
  "subagents": {
    "SecurityAuditor": {
      "permissions": {
        "allowedTools": ["Read", "MCP(snyk)"]
      }
    },
    "FrontendDeveloper": {
      "permissions": {
        "allowedTools": [
          "Read",
          "Write(src/components/**, src/pages/**)",
          "Bash(npm run test:ui)",
          "MCP(playwright)"
        ]
      }
    },
    "BackendDeveloper": {
      "permissions": {
        "allowedTools": [
          "Read",
          "Write(src/api/**, src/services/**)",
          "Bash(npm run test)",
          "Bash(npm run lint)",
          "MCP(postgres)",
          "MCP(github)"
        ]
      }
    }
  }
}
```

---

### How Permissions Are Checked

When Claude Code attempts to use a tool:

1. **Check allowlist first**
   - Is this tool in `allowedTools`?
   - Does the pattern match the file/command?
   - → If yes, ALLOW

2. **Check denylist next**
   - Is this tool in `deniedTools`?
   - Does the pattern match?
   - → If yes, DENY

3. **Default behavior**
   - If not in either list → prompt user for approval

---

### Interactive Permission Management

During a session, Claude may request permissions:

```
Claude wants to write to: src/components/Button.tsx
Pattern: Write(src/components/**)

Current permission: Not configured
Allow this write? [y/n/always]: always
→ Added Write(src/components/**) to allowedTools
```

---

## PART 4: MCP SERVERS & DYNAMIC COMMANDS

MCP (Model Context Protocol) servers extend Claude Code with external capabilities.

### The MCP Ecosystem

**Official Anthropic MCP Servers:**
- `filesystem` – Enhanced file operations
- `github` – Issues, PRs, commits
- `postgres` – SQL queries
- `playwright` – Browser automation
- `sentry` – Error tracking

**Community MCP Servers:**
- `memory` – Persistent user memories
- `jira` – Jira integration
- `slack` – Slack integration
- `stripe` – Payment processing
- `airtable` – Data management

---

### Installing & Configuring MCP Servers

**Via CLI:**

```bash
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres postgresql://user:pass@localhost/db
claude mcp add playwright -- npx -y @modelcontextprotocol/server-playwright
```

**Via settings.json:**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxx"
      }
    },
    "postgres": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/postgres", "postgresql://user:pass@db:5432/mydb"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    }
  }
}
```

---

### Dynamic Slash Commands from MCP

MCP servers can expose **prompts** that become slash commands:

**Example: GitHub MCP exposes these commands:**

```bash
/github:pr-create           Create a pull request
/github:issue-search        Search issues
/github:issue-create        Create an issue
/github:review              Review a PR
```

**Usage:**

```bash
claude
> /github:pr-create
→ Interactive: Title, description, base branch, compare branch
→ Creates PR automatically

> /github:issue-search security
→ Searches for issues with "security" in title
→ Returns list with links
```

Workflow recipes in community repos wrap these with custom commands like `/ticket`, `/pr:review`, `/deploy:prod` to build full DevOps pipelines.

---

## PART 5: SUBAGENT ORCHESTRATION & DELEGATION

Subagents are **specialized AI instances** that handle specific tasks in isolation.

### Why Subagents?

| Problem | Solution |
|---------|----------|
| Main conversation too long | Delegate to subagent (preserves main context) |
| Task is specialized | Create specialist subagent (e.g., SecurityAuditor) |
| Verbose output polluting context | Subagent isolation prevents noise |
| Need parallelization | Run up to 10 subagents in parallel |
| Cost optimization | Use cheaper models for subagents |

---

### Built-in Subagents

Three subagents are built-in:

**1. Explore Subagent**
- Tools: `Read`, `Bash(grep)`, `Bash(find)`, `Bash(ls)`
- Purpose: Discover code structure, understand codebase
- Auto-triggers: Questions starting with "find", "where", "what files"

**2. Plan Subagent**
- Tools: `Read`, `Write(ADR/)` (Architecture Decision Records)
- Purpose: Design systems, create plans
- Auto-triggers: Questions about architecture, design, planning

**3. General Subagent**
- Tools: All tools
- Purpose: Fallback for unspecialized tasks
- Auto-triggers: Tasks that don't fit Explore or Plan

---

### Creating Custom Subagents

**File: `.claude/agents/security-auditor.md`**

```yaml
---
name: SecurityAuditor
description: Security specialist focused on vulnerability detection
instructions: |
  You are a security-focused code reviewer specializing in:
  - OWASP Top 10 vulnerabilities
  - Authentication & authorization flaws
  - Injection attacks (SQL, XSS, command)
  - Data exposure and privacy issues
  - Cryptography and secrets management
  
  When reviewing code:
  1. Identify all security issues
  2. Rate severity: Critical/High/Medium/Low
  3. Suggest concrete fixes
  4. Provide secure code examples
  
  Always conservative: flag potential issues even if uncertain.

model: opus
tools:
  - Read
  - MCP(snyk)
  - MCP(github)
```

**Usage:**

```bash
claude
> Have the SecurityAuditor review src/auth.ts for vulnerabilities
→ [SecurityAuditor subagent wakes up, reviews file, reports findings]
```

---

### Subagent Orchestration Patterns

**Pattern 1: Sequential Pipeline**

For workflows requiring ordered steps:

```
Requirements Analyst → System Architect → Implementation → Code Reviewer → QA

Each hands off to next.
```

**Command:**

```bash
> Use the requirements-analyst subagent to break down these requirements
> Then pass results to the system-architect for design
> Then use the implementer to code the solution
> Finally, have the code-reviewer audit the implementation
```

---

**Pattern 2: Parallel Specialization**

For independent analyses:

```
             Performance Analysis
            /                      \
Task  -----<---- Security Analysis  > Aggregator
            \                      /
             Architecture Review
```

**Command:**

```bash
> Analyze this codebase for:
> - Performance bottlenecks (use PerformanceAnalyst)
> - Security vulnerabilities (use SecurityAuditor)  
> - Architectural issues (use ArchitectureReviewer)
> Then summarize findings
```

---

**Pattern 3: Recursive Delegation**

Subagents can delegate to other subagents:

```
Main Claude
    ↓
  Architect
    ├─→ Frontend Specialist
    │    ├─→ UI Components Specialist
    │    └─→ Performance Specialist
    └─→ Backend Specialist
         ├─→ Database Specialist
         └─→ API Specialist
```

---

### Automatic Delegation (New in 2026)

Claude now automatically delegates based on task complexity:

```bash
> Fix this bug in the authentication system
→ Claude analyzes: "This is security-sensitive"
→ Auto-delegates to: SecurityAuditor + Implementer subagents
→ Results returned and integrated

> Write a hello world app
→ Claude analyzes: "This is trivial"
→ Uses main Claude agent directly (no subagent overhead)
```

---

### Controlling Delegation Behavior

**Encourage proactive delegation** with specific phrasing:

```bash
# ✅ GOOD: Encourages subagent use
> Have the performance specialist analyze query patterns proactively

# ✓ OK: Explicit delegation request
> Use the test-runner subagent to fix these failing tests

# ✗ WEAK: Vague, less likely to delegate
> Look at these test failures
```

---

## PART 6: ADVANCED PATTERNS & WORKFLOWS

### Workflow 1: The Explore-Plan-Code-Review Cycle

**Optimal development workflow (Anthropic recommended):**

```
1. EXPLORE
   └─ Ask Claude to read relevant files
   └─ Tell it NOT to write code yet
   └─ Delegate to Explore subagent if complex

2. PLAN
   └─ Create architecture decision records (ADRs)
   └─ Identify files to modify/create
   └─ Document tech choices and tradeoffs

3. CODE
   └─ Implement based on plan
   └─ Create commits with semantic messages
   └─ Run tests continuously

4. REVIEW
   └─ Have SecurityAuditor check for vulns
   └─ Have PerformanceAnalyst check for bottlenecks
   └─ Have linter/formatter verify style
```

---

### Workflow 2: Multi-MCP Orchestration

**Real-world example: Full-stack feature implementation**

```bash
claude /plan "Add OAuth2 authentication"

# Plan outputs detailed breakdown

claude

# Step 1: Create GitHub issue
> /github:issue-create --title "Implement OAuth2" --description "[from plan]"

# Step 2: Create branch
> git checkout -b feat/oauth2

# Step 3: Frontend implementation
> Use the FrontendSpecialist to create login UI
  → Uses: MCP(playwright) for E2E testing

# Step 4: Backend implementation  
> Use the BackendDeveloper to create OAuth2 endpoints
  → Uses: MCP(postgres) for credential storage
  → Uses: MCP(github) to fetch provider config

# Step 5: Security audit
> Have SecurityAuditor review for OWASP compliance
  → Uses: MCP(snyk) for dependency scanning

# Step 6: Create PR
> /github:pr-create --issue "123" --from-branch "feat/oauth2"
```

---

### Workflow 3: Context Management at Scale

**For long sessions (200+ turns), prevent context degradation:**

```bash
# After every 30-50 turns
> /compact focus on [core objective]

# Before switching tasks
> /clear
> /add-dir [new directories if needed]

# Recovering from /clear
> /catchup
```

---

### Workflow 4: Permission-Gated Code Review

```bash
# Switch to review mode
> /permissions
→ Select: "Restrict write access to src/ only"

# Now Claude can:
> Review this PR for security issues
→ [Can suggest changes, propose diffs, cannot modify files]

> Review this function for performance
→ [Can suggest optimizations, cannot implement]

# When review is done
> /permissions
→ Select: "Full Autonomy"
```

---

## PART 7: CLAUDE.md CONTEXT ARCHITECTURE

**CLAUDE.md** is the "brain" of your Claude Code environment. It's the single source of truth for project conventions, tech stack, and architectural patterns.

### Minimal CLAUDE.md Example

```markdown
# Project Context

## Tech Stack
- **Language:** TypeScript 5.2
- **Runtime:** Node.js 20 LTS
- **Framework:** Next.js 14
- **Database:** PostgreSQL 15 with migrations
- **Package Manager:** npm

## Build & Test Commands
```bash
npm run build         # Build for production
npm run dev           # Start development server
npm test              # Run all tests
npm run lint          # ESLint + Prettier
npm run typecheck     # Full TypeScript check
```

## Code Style
- Functional components only (no class components)
- React Hooks for state management
- TypeScript strict mode enabled
- Prettier formatting (2-space indent)
- ESLint with recommended config

## Directory Structure
```
src/
├── app/              # Next.js app router pages
├── components/       # Reusable React components
├── hooks/           # Custom React hooks
├── lib/             # Utilities, helpers
├── types/           # Shared TypeScript types
└── __tests__/       # Test files
```

## Key Conventions
1. Commit messages follow Conventional Commits
2. File naming: PascalCase for components, camelCase for utilities
3. All functions typed; no implicit `any`
4. 80% test coverage minimum for features
5. PR reviews required before merge

## Known Issues & Workarounds
- Migration: We migrated from Pages Router to App Router (2024)
- State: Use Context API, not Redux (team preference)
- DB: PostgreSQL version must be 15+ (RLS features)
```

---

### Advanced CLAUDE.md with Subagent Routing

```markdown
# Project Context with Agent Routing

## Subagent Profiles

### When to use FrontendSpecialist
- Files in `src/components/` or `src/app/`
- React state, hooks, component logic
- UI testing with Playwright
- Styling with Tailwind CSS

### When to use BackendDeveloper
- Files in `src/api/`, `src/lib/services/`
- Database queries and migrations
- Authentication & authorization
- API endpoint design

### When to use PerformanceAnalyst
- Query optimization
- Bundle size reduction
- Rendering performance
- Database index analysis

### When to use SecurityAuditor
- Authentication changes
- Database schema changes
- External API integrations
- Dependency updates
```

Community templates (e.g., `ruvnet/claude-flow`) provide pre-built CLAUDE.md files for Next.js, FastAPI, Go, Rust, full-stack stacks.

---

## PART 8: CLI COMMANDS & FLAGS REFERENCE

These are commands you run in your shell (not inside Claude Code).

### Basic Usage

```bash
# Interactive REPL (start fresh session)
claude

# REPL with initial prompt
claude "Explain this project structure"

# Print mode (one-off query, non-interactive)
claude -p "Review src/auth.ts for security"

# Continue previous session
claude -c

# Continue in print mode
claude -c -p "Run the tests"

# Resume specific session by ID
claude -r abc123def456 "Finish the implementation"
```

---

### Advanced Flags

```bash
# Add working directories (for monorepos)
claude --add-dir ../api ../lib

# Allow specific tools without prompting
claude --allowedTools "Read" "Write(src/**)" "Bash(npm *)"

# Set custom system prompt (replaces all default instructions)
claude --system-prompt "You are a Python expert"

# Append to default system prompt (keeps Claude Code behavior)
claude --append-system-prompt "Focus on performance optimization"

# Process piped input
cat logs.txt | claude -p "Analyze these errors"

# Update to latest version
claude update
```

---

### MCP Management

```bash
# List all connected MCP servers
claude mcp list

# Add an MCP server
claude mcp add github -- npx -y @modelcontextprotocol/server-github

# Remove an MCP server
claude mcp remove github

# Test MCP server connection
claude mcp test github
```

---

## PART 9: BEST PRACTICES & OPTIMIZATION

### Practice 1: Context Management

**✅ Do:**
- Use `/compact` periodically to summarize
- Use subagents for specialized tasks
- Keep CLAUDE.md updated with current conventions
- Use `/memory` for project constants

**❌ Don't:**
- Dump entire codebase into context
- Leave 500+ turns in a single conversation
- Use `/clear` frequently (use `/compact` instead)
- Repeat project information multiple times

---

### Practice 2: Permission Design

**✅ Do:**
- Start restrictive, expand as needed
- Use glob patterns to scope write access
- Restrict bash to safe commands (git, npm, etc.)
- Use deny-lists for dangerous patterns

**❌ Don't:**
- Run with full permissions by default
- Allow `Bash(*)` indiscriminately
- Write to production configs from dev session
- Mix permission profiles (use one profile per session)

---

### Practice 3: Subagent Strategy

**✅ Do:**
- Create specialist subagents for recurring tasks
- Use sequential pipelines for dependent steps
- Run parallel subagents for independent analysis
- Document subagent descriptions clearly

**❌ Don't:**
- Create too many subagents (hard to manage)
- Use subagents for simple, one-off tasks
- Forget to give subagents scoped permissions
- Delegate without clear success criteria

---

### Practice 4: Command Design

**✅ Do:**
- One command = one clear purpose
- Include examples in command descriptions
- Use restrictive tools in commands
- Version control commands alongside code

**❌ Don't:**
- Create overly complex commands (split instead)
- Use commands without documentation
- Allow unrestricted bash in commands
- Commit commands with hardcoded values

---

### Practice 5: Cost Optimization

**Use `/usage` to monitor costs:**

| Task | Recommended Model | Reason |
|------|-------------------|--------|
| Complex planning, design | `claude-opus-4.1` | Most capable |
| Routine coding, refactoring | `claude-sonnet-4.1` | Good balance |
| Subagents, parallelizable tasks | `claude-haiku-4` | Fast, cheap |
| Code review, linting | `claude-haiku-4` | Pattern matching |
| Security audit | `claude-opus-4.1` | Needs reasoning |

**Strategy:**

```bash
> /model claude-opus-4.1              # For main task
[... plan complex feature ...]
> /model claude-sonnet-4.1            # For implementation
[... code the solution ...]
> Have SecurityAuditor review (uses haiku-4 by default)
```

---

### Practice 6: Error Recovery

**When Claude makes a mistake:**

```bash
> /rewind 2
# Back to the last correct state

> [Provide correction]
> Continue with [new approach]
```

**When context is corrupted:**

```bash
> /clear
> /catchup              # Re-sync with project state
> [Resume work]
```

---

## APPENDIX: COMMAND RECIPES & EXAMPLES

### Recipe 1: The Full CI/CD Validation Pipeline

**File: `.claude/commands/ci-full.md`**

```markdown
---
name: ci-full
description: Run complete CI validation (linting, types, tests)
model: sonnet
tools:
  - Read
  - Bash(npm *, git *)
---

# Full CI Pipeline

Run all checks that would run in CI:

## 1. Lint
{cmd:npm run lint}

## 2. Type Check
{cmd:npm run typecheck}

## 3. Unit Tests
{cmd:npm test}

## 4. Build
{cmd:npm run build}

## 5. E2E Tests (if applicable)
{cmd:npm run test:e2e || echo "No E2E tests"}

## Summary
Report all failures with suggested fixes.
```

---

### Recipe 2: The "Rubber Duck" Debugging Command

**File: `.claude/commands/rubber-duck.md`**

```markdown
---
name: rubber-duck
description: Explain code to me like I'm not a programmer
model: opus
tools:
  - Read
---

# Rubber Duck Debugging

Explain this code in simple terms, as if explaining to someone who doesn't know programming:

{file:{{args}}}

## What to include:
1. What does this do in plain English?
2. Why would we need this?
3. How does it work step-by-step?
4. What could go wrong?
5. Is there a simpler way to do this?
```

---

### Recipe 3: The Documentation Generator

**File: `.claude/commands/doc-generate.md`**

```markdown
---
name: doc-generate
description: Auto-generate documentation from code
model: sonnet
---

# Documentation Generator

Generate comprehensive documentation for:

{file:{{args}}}

## Generate:
1. **Function/Class Description**
2. **Parameters** (types, descriptions)
3. **Return Value** (type, description)
4. **Usage Examples** (2-3 real-world examples)
5. **Related Functions** (what else might you use)
6. **Performance Notes** (if relevant)
7. **Gotchas** (common mistakes)
```

---

### Recipe 4: The Dependency Updater

**File: `.claude/commands/deps-update.md`**

```markdown
---
name: deps-update
description: Safely update dependencies with security checks
model: opus
tools:
  - Read
  - Write(package.json, package-lock.json)
  - Bash(npm *, git *)
  - MCP(snyk)
---

# Safe Dependency Update

## 1. Current Status
{cmd:npm outdated}

## 2. Security Audit
{cmd:npm audit}

Use MCP(snyk) for deeper analysis.

## 3. Identify Updates
- Major versions (breaking changes)
- Minor versions (new features, safe)
- Patch versions (bug fixes, safest)

## 4. Update Strategy
- Update all patch versions
- Propose minor version updates
- Warn on major version updates

## 5. Test
{cmd:npm test}

## 6. Commit
Create semantic commit: `chore(deps): update dependencies`
```

---

## TOP COMMUNITY REPOSITORIES

### Essential Command Recipes

These are specific high-value commands you should implement in your `.claude/commands/` directory:

#### The Sanity Commit (`/commit`)

**Goal:** Prevent bad code from entering history.

**Mechanism:** Runs `git diff`, checks for TODO/FIXME/console.log, and generates a semantic commit message.

**Workflow:**
1. User types `/commit` [optional context]
2. Claude reads staged files
3. If blockers like debug prints exist → Aborts with warning
4. If clean → Generates Conventional Commit message, executes `git commit`

---

#### The Context Refresher (`/catchup`)

**Goal:** Re-sync Claude after a `/clear` or long session.

**Mechanism:** Reads `git status` and uncommitted changes to catch up on what happened since context was wiped.

**Workflow:** `/clear` → `/catchup` → Claude is back in context without re-reading the whole repo.

---

#### Ticket Manager (`/ticket`)

**Goal:** Turn a Jira/GitHub issue into code.

**Mechanism:** Uses GitHub MCP or Jira MCP.

**Workflow:**
1. `/ticket PROJ-123`
2. Claude fetches issue details via MCP
3. Create branch `feat/PROJ-123`
4. Implements changes based on acceptance criteria

---

#### Project Scaffolding (`/project:new`)

**Goal:** Standardized file creation (Namespaced).

**Location:** `.claude/commands/project/new.md`

**Invoked as:** `/project:new`

**Workflow:** Prompts for parameters (component name, type) and creates file + test + storybook entry simultaneously.

---

### Top Repositories & Command Suites

The following repositories contain curated collections of commands, sub-agents, and workflow templates:

| Repository | Focus | Best For |
|------------|-------|----------|
| `awesome-claude-code` (Various authors) | Curated Lists | Finding the latest tools, MCP servers, and community guides |
| `VoltAgent/awesome-claude-code-subagents` | Specialized Agents | Sub-agents designed for specific domains (e.g., security audit, QA) |
| `ruvnet/claude-flow` | CLAUDE.md Templates | Standardizing project context. Contains templates for React, Python, etc. |
| `wshobson/commands` | Production Commands | 57+ production-ready command workflows |
| `davepoon/claude-code-subagents-collection` | Mixed Agents + Commands + UI | Browsing & installing via web UI |
| `quemsah/awesome-claude-plugins` | Metrics & Discovery | Automated tracking of popular plugins and tools across GitHub |

**Note:** Awesome lists are community-driven. The `jqueryscript` and `awesome-claude.ai` forks are popular entry points.

---

## CONCLUSION

Claude Code has evolved into a sophisticated **multi-agent coordination platform**. The three layers—**slash commands**, **custom commands**, and **subagent orchestration**—work together to create a powerful development experience.

**Key takeaways:**

1. Built-in slash commands control the session
2. Custom commands codify team workflows
3. Subagents parallelize work and preserve context
4. MCP servers extend Claude's reach
5. CLAUDE.md encodes project conventions
6. Permissions enforce safety boundaries

The future of AI-assisted development isn't about a single AI doing everything—it's about orchestrating multiple specialized agents working in concert.

The most effective setups combine official features with curated community suites of commands and subagents, orchestrated via clear workflows and role-specific configurations.

---

## REFERENCES

- [Anthropic Claude Code Official Docs](https://code.claude.com/docs)
- [Model Context Protocol Hub](https://modelcontextprotocol.io)
- [Skywork.ai Claude Code SDK Reference](https://skywork.ai/blog/claude-code-sdk-command-list-latest-reference/)
- [PubNub: Best Practices for Claude Code Subagents](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)
- [Anthropic: Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [GitHub: Awesome Claude Code](https://github.com/topics/claude-code)

---

**Document Version:** 2.0 (In-Depth Research Edition)  
**Last Updated:** January 13, 2026  
**Status:** Comprehensive, production-ready reference
