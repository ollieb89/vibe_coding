# CLAUDE CODE & GEMINI CLI AGENTS - COMPREHENSIVE OVERVIEW

> **Research Date:** January 13, 2026  
> **Total Agent Types Researched:** 100+ Claude Code Subagents | Gemini CLI Multi-Agent Patterns  
> **Key Repositories Analyzed:** 15+ including VoltAgent/awesome-claude-code-subagents (7.5k stars)

---

## TABLE OF CONTENTS

### PART 1: CLAUDE CODE AGENTS
1. [Introduction to Claude Code Subagents](#claude-code-subagents-introduction)
2. [Built-in Subagents](#built-in-subagents)
3. [Creating Custom Subagents](#creating-custom-subagents)
4. [Subagent Configuration](#subagent-configuration)
5. [100+ Community Subagents Library](#community-subagents-library)
6. [Advanced Patterns & Best Practices](#claude-code-advanced-patterns)

### PART 2: GEMINI CLI AGENTS
7. [Gemini CLI Agent Architecture](#gemini-cli-agents-introduction)
8. [ADK (Agent Development Kit)](#google-adk-agent-development-kit)
9. [Custom Agent Patterns](#gemini-cli-custom-agents)
10. [Multi-Agent Orchestration](#gemini-cli-multi-agent-orchestration)
11. [Comparison: Claude Code vs Gemini CLI Agents](#comparison-table)

---

# PART 1: CLAUDE CODE AGENTS

## CLAUDE CODE SUBAGENTS INTRODUCTION

### What Are Claude Code Subagents?

Claude Code subagents are **specialized AI assistants** that enhance Claude Code's capabilities by providing task-specific expertise. They transform Claude from a single assistant into a **coordinator of specialized agents**.

**Key Architecture:**
```
User Request → Main Agent → Task Analysis → Specialized Sub-Agent Execution → Unified Output
```

### Core Benefits

| Benefit | Description |
|---------|-------------|
| **Independent Context Windows** | Each subagent operates in isolated context, preventing cross-contamination |
| **Domain-Specific Intelligence** | Tailored instructions for specialized tasks yield better performance |
| **Memory Efficiency** | Main conversation stays clean; verbose output isolated in subagent contexts |
| **Enhanced Accuracy** | Specialized prompts lead to better domain-specific results |
| **Workflow Consistency** | Share subagents across team for uniform development practices |
| **Security Control** | Granular tool permissions per subagent |
| **Cost Control** | Route tasks to faster/cheaper models (Haiku vs Opus) |

### How Subagents Work

**Technical Details:**
- Each subagent = separate API request to Anthropic
- Own context window (doesn't share memory with main agent or other subagents)
- Main Claude formulates the prompt for subagent (initial user message)
- Subagent returns summary of results to main Claude
- Main agent integrates reports and derives coherent understanding

**Execution Modes:**
- **Foreground (Blocking):** Waits for completion, passes permission prompts to user
- **Background (Concurrent):** Runs while you continue working, inherits parent permissions, auto-denies unapproved requests

---

## BUILT-IN SUBAGENTS

Claude Code includes three built-in subagents that activate automatically:

### 1. Explore Agent
**Model:** Haiku (fast, low-latency)  
**Tools:** Read-only (denied Write/Edit access)  
**Purpose:** File discovery, code search, codebase exploration  

**Search Modes:**
- `quick` - Targeted lookups
- `medium` - Balanced exploration  
- `very thorough` - Comprehensive analysis

### 2. Plan Agent
**Tools:** Planning and architectural analysis  
**Purpose:** Strategic planning and system design

### 3. General-Purpose Agent
**Tools:** All available tools  
**Purpose:** Versatile execution for non-specialized tasks

---

## CREATING CUSTOM SUBAGENTS

### Method 1: Interactive Creation with `/agents`

**Step-by-Step:**

1. **Launch Interface:** `/agents`

2. **Create New Agent:**
   - Select "Create new agent"
   - Choose scope:
     - **Project-level:** `.claude/agents/` (current project only)
     - **User-level:** `~/.claude/agents/` (all projects)

3. **Generate Configuration:**
   - Option A: **Generate with Claude** (AI-generated)
   - Option B: **Manual configuration** (write your own)

4. **Configure Tools:** Select specific tools or inherit all

5. **Select Model:** `opus`, `sonnet`, `haiku`, or `inherit`

6. **Choose Color:** Visual identifier in UI

7. **Save:** Agent available immediately (no restart needed)

---

### Method 2: Manual Markdown Files

**File Structure:**
```markdown
---
name: subagent-name
description: When this agent should be invoked
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
permissionMode: default
skills: []
hooks: {}
---

You are a [role description and expertise areas]...

[Agent-specific checklists, patterns, and guidelines]...
```

**Storage Locations:**

| Location | Scope | Priority |
|----------|-------|----------|
| `--agents` CLI flag | Current session | 1 (highest) |
| `.claude/agents/` | Current project | 2 |
| `~/.claude/agents/` | All projects | 3 |
| Plugin `agents/` dir | Where plugin enabled | 4 (lowest) |

---

## SUBAGENT CONFIGURATION

### Frontmatter Fields (YAML)

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ Yes | Unique identifier (lowercase, hyphens) |
| `description` | ✅ Yes | When Claude should delegate to this agent |
| `tools` | ❌ No | Allowlist of tools (inherits all if omitted) |
| `disallowedTools` | ❌ No | Denylist of tools to remove |
| `model` | ❌ No | AI model: `sonnet`, `opus`, `haiku`, `inherit` |
| `permissionMode` | ❌ No | Permission handling mode |
| `skills` | ❌ No | Skills to load at startup |
| `hooks` | ❌ No | Lifecycle hooks |

---

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Standard permission checking with prompts |
| `acceptEdits` | Auto-accept file edits |
| `dontAsk` | Auto-deny permission prompts |
| `bypassPermissions` | Skip all permission checks |
| `plan` | Read-only exploration mode |

---

### Tool Access Patterns

**Read-Only Agents:** `Read, Grep, Glob`  
**Research Agents:** `Read, Grep, Glob, WebFetch, WebSearch`  
**Code Writers:** `Read, Write, Edit, Bash, Glob, Grep`  
**Documentation Agents:** `Read, Write, Edit, Glob, Grep, WebFetch, WebSearch`

---

## COMMUNITY SUBAGENTS LIBRARY

**Repository:** https://github.com/VoltAgent/awesome-claude-code-subagents  
**Stars:** 7,500+  
**Categories:** 10  
**Total Subagents:** 100+

### Category 1: Core Development (11 Subagents)

- `api-designer` - REST and GraphQL API architect
- `backend-developer` - Server-side expert
- `frontend-developer` - UI/UX specialist
- `fullstack-developer` - End-to-end features
- `mobile-developer` - Cross-platform mobile
- `microservices-architect` - Distributed systems
- `graphql-architect` - GraphQL expert
- `websocket-engineer` - Real-time communication
- `electron-pro` - Desktop applications
- `wordpress-master` - WordPress expert
- `ui-designer` - Visual design specialist

---

### Category 2: Language Specialists (28 Subagents)

**Popular Languages:**
- `typescript-pro`, `python-pro`, `java-architect`, `golang-pro`, `rust-engineer`
- `javascript-pro`, `csharp-developer`, `cpp-pro`, `php-pro`

**Frameworks:**
- `react-specialist` (React 18+)
- `vue-expert` (Vue 3 Composition API)
- `angular-architect` (Angular 15+)
- `nextjs-developer` (Next.js 14+)
- `laravel-specialist` (Laravel 10+)
- `rails-expert` (Rails 8.1)
- `django-developer` (Django 4+)
- `spring-boot-engineer` (Spring Boot 3+)
- `flutter-expert` (Flutter 3+)

---

### Category 3: Infrastructure (14 Subagents)

- `devops-engineer` - CI/CD automation
- `kubernetes-specialist` - Container orchestration
- `terraform-engineer` - Infrastructure as Code
- `cloud-architect` - AWS/GCP/Azure
- `azure-infra-engineer` - Azure automation
- `database-administrator` - DB management
- `security-engineer` - Infrastructure security
- `sre-engineer` - Site reliability
- `network-engineer` - Network infrastructure
- `platform-engineer` - Platform architecture
- `deployment-engineer` - Deployment automation
- `windows-infra-admin` - Active Directory, GPO

---

### Category 4: Quality & Security (12 Subagents)

- `code-reviewer` - Code quality guardian
- `security-auditor` - Vulnerability expert
- `penetration-tester` - Ethical hacking
- `qa-expert` - Test automation
- `test-automator` - Test frameworks
- `debugger` - Root cause analysis
- `performance-engineer` - Optimization
- `accessibility-tester` - A11y compliance
- `architect-reviewer` - Architecture review
- `compliance-auditor` - Regulatory compliance
- `chaos-engineer` - Resilience testing
- `error-detective` - Error resolution

---

### Category 5: Data & AI (12 Subagents)

- `data-scientist` - Analytics, insights
- `data-engineer` - Data pipelines
- `machine-learning-engineer` - ML systems
- `ml-engineer` - Model development
- `mlops-engineer` - Model deployment
- `ai-engineer` - AI system design
- `llm-architect` - LLM integration
- `nlp-engineer` - NLP systems
- `prompt-engineer` - Prompt optimization
- `database-optimizer` - Query tuning
- `postgres-pro` - PostgreSQL expert
- `data-analyst` - BI and dashboards

---

### Category 6: Developer Experience (12 Subagents)

- `documentation-engineer` - Technical docs
- `dx-optimizer` - Developer experience
- `refactoring-specialist` - Code refactoring
- `legacy-modernizer` - Legacy code updates
- `build-engineer` - Build systems
- `cli-developer` - CLI tools
- `dependency-manager` - Package management
- `git-workflow-manager` - Git strategies
- `tooling-engineer` - Dev tooling
- `mcp-developer` - MCP servers
- `powershell-ui-architect` - PowerShell UI
- `slack-expert` - Slack integrations

---

### Category 7: Specialized Domains (12 Subagents)

- `blockchain-developer` - Web3, smart contracts
- `game-developer` - Game engines
- `embedded-systems` - Microcontrollers, RTOS
- `iot-engineer` - IoT systems
- `fintech-engineer` - Payment systems
- `payment-integration` - Stripe, PayPal
- `mobile-app-developer` - Native mobile
- `api-documenter` - API documentation
- `quant-analyst` - Financial modeling
- `risk-manager` - Risk assessment
- `seo-specialist` - SEO optimization
- `m365-admin` - Microsoft 365

---

### Category 8: Business & Product (10 Subagents)

- `product-manager` - Product strategy
- `project-manager` - Agile, Scrum
- `business-analyst` - Requirements
- `scrum-master` - Sprint planning
- `technical-writer` - User guides
- `ux-researcher` - User research
- `content-marketer` - Content strategy
- `customer-success-manager` - Customer success
- `sales-engineer` - Technical sales
- `legal-advisor` - Legal compliance

---

### Category 9: Meta & Orchestration (9 Subagents)

- `multi-agent-coordinator` - Advanced orchestration
- `agent-organizer` - Agent coordination
- `task-distributor` - Task allocation
- `workflow-orchestrator` - Complex workflows
- `context-manager` - Context optimization
- `error-coordinator` - Error handling
- `knowledge-synthesizer` - Information synthesis
- `performance-monitor` - Agent optimization
- `pied-piper` - SDLC orchestration

---

### Category 10: Research & Analysis (6 Subagents)

- `research-analyst` - Comprehensive research
- `search-specialist` - Information retrieval
- `trend-analyst` - Emerging trends
- `competitive-analyst` - Competitive intelligence
- `market-researcher` - Market analysis
- `data-researcher` - Dataset exploration

---

## CLAUDE CODE ADVANCED PATTERNS

### Pattern 1: Isolate High-Volume Operations

**Problem:** Test runs, logs consume main context

**Solution:** Use subagent to isolate verbose output

### Pattern 2: Parallel Research

**Problem:** Multiple investigations needed

**Solution:** Spawn multiple subagents for concurrent research

### Pattern 3: Sequential Chaining

**Problem:** Multi-step workflows with dependencies

**Solution:** Chain subagents through main agent

### Pattern 4: Resume Subagents

**Problem:** Continue previous work

**Solution:** Resume subagent with full conversation history

### Pattern 5: Background Execution

**Solution:** Run subagent in background (Ctrl+B)

### Pattern 6: Slash Commands Invoke Subagents

**New Feature (v1.0.123):** Claude can automatically execute slash commands

**Pattern:** Subagent → SlashCommand Tool → Another Subagent (indirect delegation)

---

# PART 2: GEMINI CLI AGENTS

## GEMINI CLI AGENTS INTRODUCTION

### Architecture Overview

Gemini CLI is fundamentally different from Claude Code. It's **not** a built-in multi-agent system but provides **building blocks** for creating agent orchestration.

**Building Blocks:**
1. Custom slash commands
2. MCP servers
3. Shell command invocation (`run_shell_command`)
4. Google ADK (Agent Development Kit)
5. File-system-as-state pattern

---

### Core Philosophy: File System as State

**Pattern:** Entire state lives in structured directory

**Directory Structure:**
```
.gemini/
├── agents/
│   ├── tasks/       # Task queue (JSON files)
│   ├── plans/       # Long-term context
│   ├── logs/        # Agent execution logs
│   └── workspace/   # Scratchpad for files
└── commands/        # Custom slash commands
```

---

### Gemini CLI Agent Capabilities

**Available Tools:**
- `glob`, `write_todos`, `write_file`, `google_web_search`
- `web_fetch`, `replace`, `run_shell_command` ⭐
- `search_file_content`, `read_many_files`, `read_file`
- `list_directory`, `save_memory`

**Available Models:**
- **Pro:** `gemini-3-pro-preview`, `gemini-2.5-pro`
- **Flash:** `gemini-2.5-flash`
- **Flash-Lite:** `gemini-2.5-flash-lite`

---

## GOOGLE ADK AGENT DEVELOPMENT KIT

### What is ADK?

**Agent Development Kit (ADK)** is Google's framework for building multi-agent AI applications.

**Key Features:**
- Visual agent blueprint designer
- Code generation from high-level plans
- Multi-agent orchestration
- Automatic deployment

---

### ADK Agent Types

1. **LlmAgent** - Single LLM-powered agent
2. **SequentialAgent** - Execute agents in sequence
3. **LoopAgent** - Iterative execution
4. **ParallelAgent** - Concurrent execution
5. **CustomAgent (BaseAgent)** - Arbitrary orchestration

---

### ADK Development Workflow with Gemini CLI

**Step 1:** Download ADK context (`llms-full.txt`)

**Step 2:** Plan with Gemini CLI
```
I want to build an AI agent to label GitHub issues. @llms-full.txt
```

**Step 3:** Generate code
```
Generate the code for this plan using Python ADK. @llms-full.txt
```

**Step 4:** Iterate
```
Add a new label called "some_new_label" to the agent
```

---

### ADK Extension for Gemini CLI

**Install:**
```bash
gemini extensions install https://github.com/simonliu-ai-product/adk-agent-extension
```

**Commands:**
- `list_adks` - List available ADKs
- `list_adk_agents` - List agents
- `create_session` - Create agent session
- `send_message_to_agent` - Interact with agent

---

## GEMINI CLI CUSTOM AGENTS

### Method 1: Custom Slash Commands as Agents

**File:** `.gemini/commands/coder-agent.toml`
```toml
description = "Specialized coding agent"
prompt = """
You are the coder-agent. Your role is to:
1. Write clean, production-ready code
2. Follow project standards
3. Run tests after implementation

Your current task: {{args}}
"""
```

---

### Method 2: Multi-Agent Orchestration via Shell Commands

**Architecture:**
```
Main Orchestrator (Gemini CLI)
  ↓ run_shell_command
  ↓
Spawn Sub-Agent (new Gemini CLI instance)
  ↓
gemini -e <agent> --yolo -p "Task: ..."
```

---

### Method 3: Agent Identity Crisis Fix

**Bad Prompt:**
```bash
gemini -e coder-agent -p "Task: Create fibonacci guide"
```

**Fixed Prompt:**
```bash
gemini -e coder-agent -p "You are the coder-agent. Task ID: task_001. Your task is to: Create fibonacci guide. Execute this yourself."
```

---

### Example Multi-Agent System

**Repository:** https://github.com/pauldatta/gemini-cli-commands-demo

**Components:**
1. Task Queue (`.gemini/agents/tasks/`)
2. Agent Definitions (Gemini CLI Extensions)
3. Orchestrator Commands
4. Workflow automation

---

## GEMINI CLI MULTI-AGENT ORCHESTRATION

### Pattern 1: Parallel Agents with git worktree

**Solution:** Use `git worktree` for isolated filesystems per agent

### Pattern 2: GitHub Actions Multi-Agent

**Use Case:** Automated issue triage, PR reviews, feature implementation

### Pattern 3: CI/CD Agent Pipeline

**Stages:** Code Quality → Security → Testing → Deployment

### Pattern 4: Agentic Marketing Campaign (ADK)

**Architecture:** Campaign Orchestrator → Market Research, Content, Design, Distribution

### Pattern 5: Gemini CLI as Claude Code Subagent

**Use Case:** Leverage Gemini's 1M token window from Claude Code

---

## COMPARISON TABLE

| Feature | Claude Code | Gemini CLI |
|---------|-------------|------------|
| **Native Agents** | ✅ Built-in | ❌ Manual |
| **Isolation** | ✅ Separate contexts | 🔶 Via CLI instances |
| **Auto Delegation** | ✅ Yes | ❌ Manual |
| **Context Window** | ~200k tokens | ✅ 1M tokens |
| **Cost (Free)** | $20/month | ✅ Free (1k/day) |
| **Model Switching** | ✅ Per-subagent | 🔶 Via flags |
| **Tool Restrictions** | ✅ Native | 🔶 Via flags |
| **Hooks** | ✅ Yes | ❌ No |
| **Background Exec** | ✅ Ctrl+B | 🔶 Shell jobs |
| **Resume Context** | ✅ Yes | ❌ Fresh each time |
| **Setup Complexity** | ✅ Simple | 🔶 Moderate |

---

## BEST PRACTICES SUMMARY

### Claude Code Subagents

**✅ DO:**
- Use project-level subagents for team sharing
- Commit configs to version control
- Create read-only agents for reviews
- Use Haiku for cheap validation
- Resume subagents to continue context

**❌ DON'T:**
- Give unnecessary tool access
- Nest subagents
- Use for quick iterations
- Mix permission modes carelessly

---

### Gemini CLI Agents

**✅ DO:**
- Use file-system-as-state pattern
- Establish clear agent identity in prompts
- Use appropriate models
- Leverage ADK for complex systems

**❌ DON'T:**
- Let agents spawn sub-agents
- Use expensive models for simple tasks
- Allow uncoordinated file writes

---

## RESOURCES

### Claude Code
- VoltAgent Library: https://github.com/VoltAgent/awesome-claude-code-subagents
- Official Docs: https://code.claude.com/docs/en/sub-agents

### Gemini CLI
- Multi-Agent Demo: https://github.com/pauldatta/gemini-cli-commands-demo
- ADK Docs: https://google.github.io/adk-docs/
- Official Docs: https://geminicli.com/docs/

---

**End of Document**
