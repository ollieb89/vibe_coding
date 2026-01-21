# CLAUDE_COMMANDS_OVERVIEW.md

> Unified overview of Claude Code built-in slash commands, custom Markdown commands, subagents, MCP-powered commands, and practical workflows. Consolidated from:
> - Claude-Code-Complete-Guide-2026.md
> - Claude_Commands_Updated_2026.md
> - Original CLAUDE_COMMANDS_OVERVIEW.md

---

## 1. Executive Summary

Claude Code is Anthropic’s agentic CLI for deep codebase work. Instead of a fixed binary with hard‑coded subcommands, it exposes a **command fabric** composed of:

| Layer | What it is | Typical examples | Primary value |
| --- | --- | --- | --- |
| **Built‑in slash commands** | First‑class commands compiled into Claude Code | `/clear`, `/compact`, `/permissions`, `/status`, `/agents` | Control session, tools, models, and context |
| **Custom Markdown commands** | `.md` files mapped to slash commands | `/commit`, `/plan`, `/db:migrate`, `/ci-full` | Encode repeatable workflows as prompts + shell + tools |
| **MCP‑provided commands** | Commands surfaced by Model Context Protocol servers | `/github:pr-create`, `/github:review` | Integrate external systems (GitHub, DB, browsers, etc.) |
| **Subagents** | Specialized AI profiles with constrained tools | `SecurityAuditor`, `FrontendDeveloper` | Parallel work, specialization, and safety via scoped capabilities |
| **CLAUDE.md + memory** | Long‑lived project and user context | Tech stack, style guide, routing rules | Makes commands & agents project‑aware and consistent |

The most effective setups treat commands as **versioned infrastructure-as-prompt**: workflow recipes, not ad‑hoc chats. Teams standardize on a small set of built‑ins plus 10–30 well‑designed custom commands and 3–7 subagents, wired together by permissions, MCP servers, and CLAUDE.md.
### **2026 Innovation: Automatic Subagent Delegation**

As of January 2026, Claude Code now **automatically routes work** to specialized subagents based on task complexity and domain sensitivity:

- **Simple fixes & edits** \u2192 Main Claude agent
- **Security-sensitive changes** (auth, crypto, secrets) \u2192 SecurityAuditor subagent
- **Performance analysis & optimization** \u2192 PerformanceAnalyst subagent
- **Frontend component development** \u2192 FrontendSpecialist subagent
- **Backend/API work** \u2192 BackendDeveloper subagent
- **Multi-step complex tasks** \u2192 Auto-chains agents sequentially

This means you describe the goal in natural language, and Claude Code **intelligently orchestrates the right team** without explicit delegation commands. You can still explicitly delegate using `> Have the SecurityAuditor review...`, but auto-delegation makes it unnecessary for routine tasks.
---

## 2. Core Concepts in One View

### 2.1 Command Types

| Type | Definition | Where it lives | How you invoke it |
| --- | --- | --- | --- |
| **Built‑in slash command** | Native Claude Code feature | Inside Claude CLI | Type `/clear`, `/compact`, `/model` in a Claude session |
| **Project custom command** | Markdown workflow file scoped to a repo | `.claude/commands/**.md` | `/deploy`, `/db:migrate`, `/plan`, `/ticket` |
| **User‑level custom command** | Global command available across projects | `~/.claude/commands/**.md` | `/user:commit`, `/user:review`, `/user:security:scan` |
| **MCP dynamic command** | Command exported by an MCP server as a prompt | Defined by MCP server config | `/github:issue-create`, `/github:review` |

### 2.2 High‑leverage primitives

- **Permissions system**: Fine‑grained allow/deny lists for `Read`, `Write`, `Bash`, and each MCP server. Used to create safe profiles (e.g. read‑only security audit vs full‑autonomy local dev).
- **CLAUDE.md**: Single source of truth for:
  - Tech stack
  - Build/test commands
  - Architecture and conventions
  - Subagent routing hints (when to use which specialist)
- **Subagents**: YAML‑configured agents in `.claude/agents/` with their own instructions, model, tools, and permission scopes.
- **MCP servers**: External backends (GitHub, Postgres, Playwright, Sentry, Jira, etc.) that expose tools and sometimes ready‑made prompts.

---

## 3. Built‑in Slash Commands

Built‑ins are always available and form the operational backbone of Claude Code.

### 3.1 Context Management

| Command | Purpose | Typical usage |
| --- | --- | --- |
| `/clear` | Wipe entire conversation history | Hard reset when context is corrupted or switching projects mid‑session |
| `/compact [focus]` | Summarize prior turns, keep a compressed context | Preserve decisions while freeing tokens (e.g. after long debugging sessions) |
| `/rewind [steps]` | Remove the last N turns from context | Undo a few bad turns before they pollute the rest of the session |
| `/catchup` | Re‑sync Claude with repo state after a reset | Run after `/clear` to re‑ingest current Git status and uncommitted changes |

**Recommended habits**

- Prefer `/compact` every 30–50 turns instead of over‑using `/clear`.
- Use `/rewind` right after a misstep to avoid “reasoning on bad facts”.
- Use `/catchup` as your standard bridge from a fresh context back to the repo.

---

### 3.2 Configuration

| Command | What it configures | Notes |
| --- | --- | --- |
| `/permissions` | Which tools are allowed (and where) | Backed by `~/.claude/settings.json` permission profiles |
| `/model [name]` | Active Claude model for this session | Typical strategy: Opus for planning, Sonnet for implementation, Haiku for subagents |
| `/config` | Interactive wizard for models, directories, MCP, permissions, memory | Fastest way to bootstrap a new environment |

**Example permission profile (code review mode)**

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

**Interactive Permission Configuration During a Session**

When Claude Code attempts to use a tool not in your permission profile, you're prompted:

```
Claude wants to write to: src/components/Button.tsx
Pattern: Write(src/components/**)

Current permission: Not configured
Allow this write? [y/n/always/deny]: always
→ Added Write(src/components/**) to allowedTools
```

Choose:
- `y` – Allow this specific use (not saved)
- `n` – Deny this use
- `always` – Allow and save to permissions profile
- `deny` – Deny and save to denylist

**Permission Pattern Reference**

| Pattern | Matches | Blocks |
| --- | --- | --- |
| `Write(src/**)` | All files in `src/` | Nothing in `src/` |
| `Write(src/**, !src/test/**)` | Files in `src/` except tests | Test files |
| `Bash(git *, npm *)` | Git and npm commands | All other bash |
| `Bash(!rm *, !sudo *)` | Everything except rm/sudo | Destructive commands |
| `MCP(github)` | All GitHub MCP tools | Other MCPs |
| `MCP(github, postgres)` | GitHub and Postgres MCPs | Other MCPs |

---

### 3.3 Navigation & Session State

| Command | Purpose |
| --- | --- |
| `/add-dir [paths...]` | Attach additional working directories (monorepos, multi‑service repos) |
| `/status` | Show current model, directories, MCP servers, permissions, memory state, token usage |
| `/agents` | List built‑in and custom subagents, their tools, and when they are auto‑delegated |
| `/memory` | View, add, and clear persistent memory items |

Patterns:
- Use `/add-dir` instead of starting separate sessions per package in a monorepo.
- Use `/memory` for cross‑session facts (style guides, API invariants, architectural constraints).

---

### 3.4 Utility & Operations

| Command | Purpose |
| --- | --- |
| `/help` | List built‑in and discovered custom slash commands with descriptions |
| `/doctor` | Health check: CLI version, API key, MCP connectivity, permissions, shell integration |
| `/terminal-setup [shell]` | Install aliases (`claude`, `claude-continue`, etc.) and shell completions |
| `/hooks` | Configure lifecycle hooks (pre/post tool use, subagent delegation/return) via `~/.claude/hooks.yaml` |
| `/usage` and `/cost` | Inspect token usage and estimated spend per model and session |

**Lifecycle Hooks (`/hooks`)**

Hooks let you inject custom logic at critical points in Claude Code's execution. Configure via interactive menu or edit `~/.claude/hooks.yaml`:

```yaml
hooks:
  PreToolUse:
    - name: ValidateDestructiveCommands
      pattern: "Bash(rm *, sudo *)"
      action: request_approval
      message: "Destructive command detected. Approve? [y/n]"
  
  PostToolSuccess:
    - name: LogAllWrites
      pattern: "Write(src/**)"
      action: log_to_file
      file: ~/.claude/audit.log
      format: "timestamp | tool | result | operator | changes"

  SubagentDelegation:
    - name: TrackDelegations
      action: log_to_file
      file: ~/.claude/delegations.log
      format: "task | delegated_to | reason"
```

**Available hooks:**
- `PreToolUse` – Before Claude uses any tool (validate, approve, log)
- `PostToolSuccess` – After tool succeeds (record, archive, notify)
- `PostToolFailure` – After tool fails (recover, alert, retry)
- `SubagentDelegation` – Before delegating to a subagent
- `SubagentReturn` – When subagent returns results

**Token Usage & Cost Tracking**

```bash
> /usage
→ Token Usage Summary:
  This session: 24,517 tokens
  Today: 156,280 tokens
  This month: 1,847,291 tokens
  
  By model:
    claude-opus-4.1: 1,200,000 tokens @ $0.015/K = $18.00
    claude-sonnet-4.1: 647,291 tokens @ $0.003/K = $1.94
    claude-haiku-4: 0 tokens (free tier)
  
  Projected monthly cost: $21.21
  
> /cost
→ Cost Breakdown (30-day projection):
  Estimated spend: $21.21
  Most expensive operation: Architectural review (3x Opus runs) = $8.40
  Cheapest operations: Bug fixes with Haiku = $0.12
```

---

## 4. Custom Commands (Markdown‑based)

Custom commands are where teams encode **repeatable workflows**.

### 4.1 Command Locations & Naming

```text
~/.claude/commands/              # User-level (global)
  commit.md                      # /user:commit
  review.md                      # /user:review
  security/scan.md               # /user:security:scan

.claude/commands/                # Project-level (scoped to repo)
  deploy.md                      # /deploy
  test/unit.md                   # /test:unit
  test/e2e.md                    # /test:e2e
  db/migrate.md                  # /db:migrate
  project/new.md                 # /project:new
```

- Folder nesting becomes `:` namespaces: `test/unit.md` → `/test:unit`.
- User‑level commands are ideal for global workflows (semantic commits, generic reviews).
- Project commands should capture repo‑specific tasks (CI pipeline, deploys, DB migrations).

### 4.2 Anatomy of a Command

Each command is a Markdown file with YAML frontmatter and a prompt body:

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
1. Security
2. Performance
3. Maintainability

## Input
```bash
{cmd:git diff HEAD~1}
```

## Output Format
- **File:** path (line)
- **Severity:** Critical / Warning / Info
- **Category:** Security / Performance / Maintainability
- **Description:**
- **Suggestion:**
- **Example:**
```

#### Supported command‑time syntaxes

| Syntax | Meaning |
| --- | --- |
| `{cmd:...}` | Execute a shell command and splice output into the prompt |
| `{file:path}` | Include the contents of a file |
| `{{args}}` | Raw arguments passed after the slash command |
| `{{env:VAR}}` | Substitute an environment variable |

Frontmatter controls **name, description, model override, tool restrictions**, and optionally tags or categories.

---

### 4.3 Essential Command Recipes

These are the “must‑have” commands most teams benefit from immediately.

#### 4.3.1 Semantic Commit (`/commit`)

- **Goal:** Prevent low‑quality or unsafe changes from entering Git history.
- **Behavior:**
  - Runs `git diff --staged` via `{cmd:git diff --staged}`.
  - Scans for debug leftovers (`console.log`, `debugger`, `TODO`, `FIXME`, commented‑out blocks, hard‑coded secrets).
  - If blockers are present → abort with a detailed report.
  - If clean → generate a Conventional Commit message `type(scope): description` and optionally run `git commit`.

Typical flow:

```bash
git add src/**
claude
> /commit
→ Analyzing staged changes…
→ ✓ No debug code found
→ Suggested commit: feat(auth): add OAuth2 login flow
→ Execute this commit? [y/n]
```

#### 4.3.2 Task Planner (`/plan`)

- **Goal:** Turn a vague request into a concrete, ordered implementation plan.
- **Inputs:** Human task description via `{{args}}`.
- **Outputs:**
  - Requirements analysis
  - Architectural approach and trade‑offs
  - Files to create/modify/delete
  - Step‑by‑step checklist with complexity estimate
  - Testing strategy, risks, success criteria

Great as the first step in the **Explore → Plan → Code → Review** cycle.

#### 4.3.3 Ticket Worker (`/ticket` or `/fix-issue`)

- **Goal:** Turn tracked work items (GitHub/Jira) into concrete branches and code changes.
- **Mechanism:**
  - Use MCP GitHub or Jira to fetch issue details.
  - Create a branch (`feat/PROJ-123` or `fix/issue-123`).
  - Optionally call `/plan` internally.
  - Implement changes & run tests.

Example sketch:

```markdown
Issue number: {{args}}

```bash
{cmd:gh issue view {{args}}}
{cmd:git checkout -b fix/issue-{{args}}}
```
```

#### 4.3.4 Project Scaffolder (`/project:new`)

- **Goal:** Enforce consistent structure for new slices of the system.
- **Typical behavior:** Ask for a component/feature name and type, then:
  - Create implementation file
  - Create test file
  - Add Storybook/route entry if applicable

#### 4.3.5 CI / Quality Gate (`/ci-full`)

Runs your full local CI suite:

```markdown
{cmd:npm run lint}
{cmd:npm run typecheck}
{cmd:npm test}
{cmd:npm run build}
{cmd:npm run test:e2e || echo "No E2E tests"}
```

Summarizes failures and suggests fixes. Typically restricted to safe Bash patterns (`Bash(npm *, git *)`).

#### 4.3.6 Rubber‑Duck Debugger (`/rubber-duck`)

Explains a file in plain language and surfaces potential risks, misunderstandings, and simplifications. Very effective for onboarding and for untangling legacy modules.

#### 4.3.7 Documentation Generator (`/doc-generate`)

Reads a file and outputs structured docs: description, parameters, return values, examples, related APIs, performance notes, and gotchas.

#### 4.3.8 Safe Dependency Updater (`/deps-update`)

Combines `npm outdated`, `npm audit`, optional Snyk MCP, and a test run into a safe, explainable dependency upgrade workflow with a single semantic commit at the end.

---

## 5. MCP Servers & Dynamic Commands

MCP (Model Context Protocol) is how Claude Code attaches external capabilities.

### 5.1 Server Types

- **Official servers**: `filesystem`, `github`, `postgres`, `playwright`, `sentry`, etc.
- **Community servers**: `jira`, `slack`, `stripe`, `airtable`, `memory`, and many others.

### 5.2 Installation & Configuration

Via CLI:

```bash
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres postgresql://user:pass@localhost/db
claude mcp add playwright -- npx -y @modelcontextprotocol/server-playwright
```

Via `settings.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxx"
      }
    }
  }
}
```

### 5.3 Dynamic MCP Commands

Many servers expose **prompts** that appear as slash commands, e.g. GitHub MCP:

```bash
/github:pr-create
/github:issue-search
/github:issue-create
/github:review
```

These can be wrapped by your own commands (`/ticket`, `/pr:prepare`, `/release:cut`) to form high‑level workflows.
**Popular MCP Server Commands (Reference)**

| MCP Server | Common Commands | Use Case |
| --- | --- | --- |
| **github** | `/github:pr-create`, `/github:issue-search`, `/github:issue-create`, `/github:review` | Repo management, PR workflows, issue handling |
| **postgres** | `/db:query`, `/db:schema`, `/db:migrate` | Database queries, schema inspection, migrations |
| **sentry** | `/sentry:errors`, `/sentry:trace`, `/sentry:alert` | Error tracking, performance monitoring, alerts |
| **playwright** | `/test:run-browser`, `/test:screenshot`, `/test:visual-regression` | Browser automation, E2E testing, visual regression |
| **jira** | `/jira:create-issue`, `/jira:search`, `/jira:transition` | Issue management, sprint planning |
| **slack** | `/notify:message`, `/notify:thread`, `/notify:channel` | Team notifications, async updates |
| **stripe** | `/stripe:customers`, `/stripe:payments`, `/stripe:refunds` | Payment processing queries |
| **airtable** | `/airtable:fetch`, `/airtable:create`, `/airtable:update` | Database-like data management |

### 5.4 Composing MCP Commands into Workflows

Wrap MCP commands in custom `.claude/commands/*.md` files for higher-level workflows:

**File: `.claude/commands/release/cut.md`**

```markdown
---
name: release:cut
description: Create a release with automated changelog and GitHub release
model: sonnet
tools:
  - Read
  - Write(CHANGELOG.md, package.json)
  - Bash(git *, npm *)
  - MCP(github)
---

# Release Cutter

Automated release workflow.

## Step 1: Fetch Latest Tags

\`\`\`bash
{cmd:git tag --list | tail -5}
\`\`\`

## Step 2: Generate Changelog

\`\`\`bash
{cmd:git log $(git describe --tags --abbrev=0)..HEAD --oneline}
\`\`\`

Using this, create a CHANGELOG entry for the next version.

## Step 3: Update Version

Bump \`package.json\` version using semver logic.

## Step 4: Create GitHub Release

Use \`/github:pr-create\` or direct GitHub API call to publish release notes.
```

**Usage:**

```bash
claude
> /release:cut
→ [Analyzes commits, bumps version, creates release, posts GitHub release]
```
---

## 6. Subagents & Orchestration

Subagents are named specialist agents defined in `.claude/agents/*.md`.

### 6.1 Why Subagents

- Isolate noisy or verbose work streams.
- Restrict tools for safety (e.g. read‑only security auditor).
- Parallelize independent tasks (up to ~10 subagents at once).
- Optimize cost by assigning cheaper models to mechanical tasks.

### 6.2 Defining a Subagent

Example security auditor:

```yaml
---
name: SecurityAuditor
description: Security specialist focused on vulnerability detection
instructions: |
  You are a security-focused code reviewer specializing in OWASP Top 10,
  authentication & authorization, injection attacks, and secrets management.
model: opus
tools:
  - Read
  - MCP(snyk)
  - MCP(github)
permissions:
  allowedTools:
    - Read
    - MCP(snyk)
    - MCP(github)
---
```

Usage:

```bash
> Have the SecurityAuditor review src/auth.ts for vulnerabilities
```

### 6.3 Built‑in Subagents

- **Explore**: Discovery and mapping, limited to `Read` + light `Bash(grep/find/ls)`.
- **Plan**: Architecture and design, often writing ADR‑style docs.
- **General**: Fallback when no specific agent is a better fit.

### 6.4 Orchestration Patterns

**1. Sequential Pipeline**
```
Requirements Analysis
        ↓
    Planning (Architect)
        ↓
   Implementation (Frontend/Backend/DB specialists)
        ↓
   Security Review (SecurityAuditor)
        ↓
   Performance Review (PerformanceAnalyst)
        ↓
   QA & Testing (TestRunner)
```

Useful for: Complex features requiring design review before implementation.

**2. Parallel Specialization**
```
         Main Task
        /    |     \
       /     |      \
   Security | Performance | Architecture
   Audit    | Analysis    | Review
       \     |     /
        \    |    /
    Aggregate Results
```

Useful for: Code reviews, audits, or when multiple concerns need simultaneous analysis.

**3. Recursive Delegation**
```
    Architect Agent
        |
        +-- FrontendSpecialist
        |        |
        |        +-- ComponentBuilder
        |        +-- StyleEngineer
        |
        +-- BackendDeveloper
               |
               +-- APIDesigner
               +-- DatabaseExpert
```

Useful for: Large systems where sub-domains need further specialization.

**4. Auto-delegation (2026 Feature)**

Claude Code now detects task type and automatically routes:

```bash
> Build a login form with OAuth2 integration

→ Detected: Multi-domain task (frontend + auth)
→ Delegating to FrontendSpecialist...
→ Delegating to SecurityAuditor (OAuth2 review)...
→ [Both agents work in parallel]
→ Aggregating results...
→ ✓ Complete
```

You can also **prevent auto-delegation** for a single task:

```bash
> /permissions --no-auto-delegate
> Fix the button alignment issue
→ Using main Claude agent (no auto-delegation)
```

---

## 7. CLAUDE.md & Memory Architecture

### 7.1 Minimum viable CLAUDE.md

- Tech stack and versions
- Build/test/lint/typecheck commands
- Directory layout and naming conventions
- Style guide (patterns to prefer/avoid)
- Known constraints and “gotchas”

This file is auto‑loaded into context at session start, so it should answer “what is this project and how do we work here?” without extra prompting.

### 7.2 Advanced CLAUDE.md with Routing

Add sections like:

- “When to use FrontendSpecialist vs BackendDeveloper vs PerformanceAnalyst vs SecurityAuditor.”
- “Which MCP servers are authoritative for which domains (GitHub vs Jira vs internal API).”
- “What permission profiles to use for dev vs review vs prod‑adjacent tasks.”

Combined with explicit `/agents` and `/permissions` usage, this turns Claude Code into a **policy‑driven multi‑agent system** rather than a single assistant.

---

## 8. Advanced Patterns & Workflows

### 8.1 Workflow: Task Management with Claude Code

For complex multi-step tasks, combine `/plan`, custom commands, and subagents:

```bash
claude
> /plan "Implement two-factor authentication across auth system"
→ [Detailed plan with requirements, architecture, steps, risks]

> /commit  # When staging changes
→ [Semantic commit with safety checks]

> /ci-full  # Before pushing
→ [Runs lint, tests, builds, E2E]

> Have the SecurityAuditor review src/auth/2fa.ts
→ [Security-focused review]

> /github:pr-create
→ [Creates PR with changelog]
```

### 8.2 Workflow: Safe Database Migrations

```bash
# In a project with a custom /db:migrate command

claude
> /db:migrate
→ Analyzing pending migrations...
→ Found: 3 migrations
→ Pre-flight checks: ✓ Pass
→ Estimated time: 45 seconds
→ Proceeding with transaction wrapper...
→ ✓ Migration complete
→ Verified with tests: ✓ Pass
```

### 8.3 Workflow: Parallel Code Review

```bash
claude
> Review src/api/auth.ts in parallel for security, performance, and maintainability

→ Delegating to SecurityAuditor...
→ Delegating to PerformanceAnalyst...
→ Delegating to MaintenanceExpert...

[All three work in parallel]

→ SecurityAuditor: 3 issues (1 critical)
→ PerformanceAnalyst: 2 issues (N+1 query detected)
→ MaintenanceExpert: 1 issue (type safety)

→ Aggregated report:
   Critical: SQL injection risk in query builder
   Performance: Add database index on user_id
   Maintainability: Improve type annotations
```

### 8.4 Workflow: Dependency Updates with Safety Gates

Use `/deps-update` custom command with permission gates:

```bash
> /permissions --profile dependency-updates
→ Profile loaded: Read + Write(package.json) + Bash(npm *) + MCP(snyk)

> /deps-update
→ Running npm audit...
→ Found 2 vulnerabilities
→ Testing updates against full test suite...
→ ✓ All tests pass
→ Proposing commit: chore(deps): update dependencies for security
→ /commit  # Semantic commit with blockers check
```

---

## 9. Best Practices & Optimization

### 9.1 When to Use Each Feature

| Feature | When to use | Avoid when |
| --- | --- | --- |
| **`/compact`** | After 30-50 turns or approaching token limit | You need full conversation history for analysis |
| **`/rewind`** | Immediately after a bad suggestion | The issue is deep in context (use `/compact` instead) |
| **Custom commands** | Task is repeated 3+ times or complex multi-step | One-off task or single command |
| **Subagents** | Need isolation, safety gates, or parallel work | Task is trivial or requires main agent's full context |
| **MCP servers** | Need external system integration (GitHub, DB, etc.) | Everything is in the local repo |
| **Permissions** | Code review, unfamiliar task, or safety-critical work | Solo development with trusted code |
| **Auto-delegation** | Exploring a new codebase or complex domain task | You want full control of which agent runs |

### 9.2 Performance Optimization

**Token efficiency:**
- Use `/compact [focus]` instead of `/clear` to preserve context
- Keep CLAUDE.md concise but comprehensive
- Use `{{args}}` in commands to avoid repeating task descriptions

**Cost optimization:**
- Assign cheaper models (Haiku) to mechanical subagents
- Use Sonnet for balanced work
- Reserve Opus for high-complexity tasks (architecture, design)

**Speed optimization:**
- Parallelize subagent work when possible
- Use lighter permissions profiles to reduce approval prompts
- Cache MCP results (e.g., repository metadata) in CLAUDE.md

### 9.3 Safety & Governance

**Multi-person teams:**
- Create permission profiles for code review vs development
- Use lifecycle hooks (`/hooks`) to log all writes and destructive commands
- Enable approval gates for sensitive areas (auth, payments, production config)

**Compliance & auditing:**
- Store audit logs in `~/.claude/audit.log` via hooks
- Regular review of `/usage` and `/cost` for anomalies
- Archive completed sessions and subagent delegations

**Preventing accidents:**
- Use deny-patterns for critical files: `Write(!.env*, !config/production.*, !secrets/**)`
- Require approval for Bash commands matching `rm *`, `sudo *`, `drop table`
- Use `/hooks` to catch and alert on suspicious patterns

### 9.4 Common Pitfalls & How to Avoid Them

| Pitfall | Symptom | Fix |
| --- | --- | --- |
| **Token bloat** | `/status` shows 180K+ tokens used | Use `/compact focus on current task` every 30 turns |
| **Stale context** | Claude acts like changes don't exist | Use `/catchup` after switching branches or pulling updates |
| **Wrong agent** | Performance advice from SecurityAuditor | Review CLAUDE.md routing hints; improve auto-delegation hints |
| **Over-automation** | Commands become brittle with repo changes | Keep commands stateless; use glob patterns, not absolute paths |
| **Permission nightmares** | Constant approval prompts, productivity loss | Calibrate permission profiles; use `always` option wisely |
| **Cost creep** | Unexpected $50+ monthly bill | Monitor `/cost`; prefer Haiku for subagents; use `/compact` |

---

## 10. CLI Usage & Flags (Shell‑level)

These are commands executed in your shell, not inside a Claude session.

### 10.1 Basics

```bash
# Start interactive REPL
claude

# Start with an initial question
claude "Explain this project structure"

# One-off (print mode)
claude -p "Review src/auth.ts for security issues"

# Continue previous session
claude -c

# Continue and immediately send a new instruction
claude -c -p "Run the tests"

# Resume specific session by ID
claude -r <session-id> "Finish the implementation"
```

### 10.2 Useful Flags

```bash
# Attach extra directories (monorepo support)
claude --add-dir ../api ../lib

# Pre-approve some tools for this run
claude --allowedTools "Read" "Write(src/**)" "Bash(npm *)"

# Replace default system prompt completely
claude --system-prompt "You are a Python expert"

# Append to default system prompt
claude --append-system-prompt "Focus on performance optimization"

# Pipe data into Claude
cat logs.txt | claude -p "Analyze these errors and propose fixes"

# Self-update the CLI
claude update
```

### 10.3 MCP Management via CLI

```bash
claude mcp list
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp remove github
claude mcp test github
```

---

## 11. Practical Setup Strategy (Recommended)

1. **Bootstrap context**
   - Create a solid `CLAUDE.md` using templates (e.g. for Next.js, Django, FastAPI, Go).
   - Add 3–5 explicit memory items via `/memory` for long‑lived rules that transcend repos (commit style, review philosophy, etc.).

2. **Install core MCP servers**
   - Always: `filesystem`, `github`.
   - As needed: `postgres`, `playwright`, `sentry`, `jira`, `stripe`, etc.

3. **Define permission profiles**
   - Full autonomy (local dev).
   - Restricted write (code review).
   - Read‑only audit (security/compliance).
   - Per‑subagent scoped permissions.

4. **Create or import command suites**
   - Global: `/commit`, `/review`, `/plan`, `/rubber-duck`, `/doc-generate`, `/deps-update`, `/ci-full`.
   - Project: `/deploy`, `/db:migrate`, `/ticket`, `/project:new`, stack‑specific commands.

5. **Add 3–7 subagents**
   - SecurityAuditor, PerformanceAnalyst, FrontendSpecialist, BackendDeveloper, TestRunner, DocsWriter, Architect.

6. **Evolve via workflows**
   - Standardize on Explore → Plan → Code → Review cycles.
   - Encode frequently repeated flows as new commands instead of new habits.

---

## 12. Quick Reference Tables

### 12.1 Built‑In Slash Commands (Cheat Sheet)

| Category | Command | One‑line mental model |
| --- | --- | --- |
| Context | `/clear` | Hard reset conversation |
| Context | `/compact [focus]` | Summarize history, keep essentials |
| Context | `/rewind [n]` | Step back N turns |
| Context | `/catchup` | Re‑ingest repo state after a reset |
| Config | `/permissions` | Configure tool access & safety profiles |
| Config | `/model` | Switch active Claude model |
| Config | `/config` | Interactive environment wizard |
| Nav | `/add-dir` | Attach more working directories |
| Nav | `/status` | Show session snapshot |
| Nav | `/agents` | List subagents and capabilities |
| Nav | `/memory` | Manage long‑term memory items |
| Utility | `/help` | Show built‑ins + discovered custom commands |
| Utility | `/doctor` | Diagnose setup issues |
| Utility | `/terminal-setup` | Install shell aliases & completions |
| Utility | `/hooks` | Configure lifecycle hooks |
| Utility | `/usage`, `/cost` | Inspect token and cost usage |

### 12.2 High‑Value Custom Commands to Implement First

| Command | Scope | Purpose |
| --- | --- | --- |
| `/commit` | Global | Semantic, safety‑checked Git commits |
| `/review` | Global | Structured multi‑axis code reviews |
| `/plan` | Global | Turn tasks into concrete plans |
| `/rubber-duck` | Global | Explain and sanity‑check complex files |
| `/doc-generate` | Global | Generate human‑readable documentation from code |
| `/ci-full` | Project | Run full local CI and summarize failures |
| `/db:migrate` | Project | Safe DB migrations with pre‑flight checks and rollback strategy |
| `/deps-update` | Project | Safe dependency upgrades with security scanning |
| `/ticket` or `/fix-issue` | Project | Turn issues/tickets into branches and implementations |
| `/project:new` | Project | Scaffold new features/components in a consistent way |

This overview can be dropped directly into `CLAUDE_COMMANDS_OVERVIEW.md` and extended as your command suite and subagent roster grow.