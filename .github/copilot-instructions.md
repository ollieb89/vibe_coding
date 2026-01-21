# AI Coding Agent Instructions for vibe_coding

## Project Purpose
**vibe_coding** is a comprehensive research & documentation repository documenting AI coding agent ecosystems (Claude Code, Gemini CLI, extensions, custom commands, subagents, and MCP servers). It serves as a knowledge base for guiding AI agents in productive workflows across different platforms.

## Architecture & Key Files

### Content Organization
- **[research/commands/CLAUDE_COMMANDS_OVERVIEW.md](../research/commands/CLAUDE_COMMANDS_OVERVIEW.md)**: Master reference for Claude Code command ecosystem (slash commands, custom commands, MCP servers, subagent orchestration)
- **[research/agents/AGENTS_OVERVIEW.md](../research/agents/AGENTS_OVERVIEW.md)**: 100+ subagent patterns and multi-agent orchestration for Claude Code & Gemini CLI
- **[research/GEMINI_CLI_MASTER.md](../research/GEMINI_CLI_MASTER.md)**: 287+ Gemini CLI extensions, custom commands, agent architecture, and workflows
- **[research/extensions/CLAUDE_PLUGINS_OVERVIEW.md](../research/extensions/CLAUDE_PLUGINS_OVERVIEW.md)**: Plugin ecosystem and integration patterns
- **[MERGE_SUMMARY.md](../MERGE_SUMMARY.md)**: Tracks recent content consolidations and updates (source of truth for what was merged when)

### Search Strategy
When asked to research AI agent features:
1. Check **CLAUDE_COMMANDS_OVERVIEW.md** for Claude Code slash commands, custom command patterns, and permission system details
2. Check **AGENTS_OVERVIEW.md** for subagent patterns, delegation workflows, and multi-agent orchestration
3. Check **GEMINI_CLI_MASTER.md** for Gemini CLI extension ecosystem and agent architecture comparisons
4. Cross-reference **MERGE_SUMMARY.md** to understand recent content updates and consolidations

## Key Patterns & Conventions

### Documentation Structure
Each major research file follows this pattern:
- **Executive Summary** with 2026+ innovations (e.g., automatic subagent delegation)
- **Core Concepts** section defining key terms (slash commands, custom commands, MCP servers, subagents, CLAUDE.md)
- **Practical Reference Sections** with command examples, configuration patterns, and common workflows
- **Advanced Patterns** section with production-ready orchestration examples
- **Best Practices** with decision matrices ("when to use each feature")

### Command Ecosystem Hierarchy
Projects using these agents typically layer commands:
1. **Built-in slash commands** (`/clear`, `/permissions`, `/status`, `/agents`) — session control
2. **Custom commands** (`.claude/commands/*.md`, `.gemini/commands/*.md`) — project-specific workflows
3. **MCP servers** (GitHub, Postgres, Jira, etc.) — external system integration
4. **Subagents** (SecurityAuditor, FrontendSpecialist, etc.) — specialized task delegation
5. **CLAUDE.md/GEMINI.md** — project context tying it all together

**Important:** Commands are treated as "versioned infrastructure-as-prompt" — teams standardize 10–30 custom commands + 3–7 subagents rather than ad-hoc interactions.

### Permission System
Claude Code & Gemini CLI share a permission model with three key mechanics:
- **Pattern-based grants**: `Write(src/**, !src/test/**)`, `Bash(git *, npm test)`, `MCP(github)`
- **Interactive approval prompts** during sessions with `[y/n/always/deny]` options
- **Profiles** for different roles (full-autonomy dev, read-only audit, safe migrations)

See CLAUDE_COMMANDS_OVERVIEW.md §3.2 for full pattern reference.

### 2026 Innovations
Document reflects January 2026 state:
- **Automatic subagent delegation** — Claude Code routes security checks, performance analysis, and complex tasks to specialized subagents without explicit user direction
- **Advanced orchestration patterns** — Sequential pipelines, parallel specialization, recursive delegation with visual ASCII diagrams
- **Comprehensive cost/token tracking** — `/usage` and `/cost` commands with 30-day projections

## Maintenance Guidelines

### When Updating Content
- **Preserve the hierarchy**: Keep Core Concepts → Reference → Advanced Patterns → Best Practices structure
- **Use decision matrices**: When documenting "when to use X vs Y", use tables (see CLAUDE_COMMANDS_OVERVIEW.md §3.2 pattern reference)
- **Include concrete examples**: Every major feature should have 2–3 real examples from the docs themselves
- **Update MERGE_SUMMARY.md**: Track when you consolidate or add sections, include date and what was merged where
- **Cross-reference liberally**: Link between CLAUDE_COMMANDS_OVERVIEW.md ↔ AGENTS_OVERVIEW.md ↔ GEMINI_CLI_MASTER.md

### Common Tasks
- **Merging duplicate content**: Check MERGE_SUMMARY.md first; consolidate into the main reference file for the feature area, update MERGE_SUMMARY.md with consolidation details
- **Adding new extensions**: Add to appropriate section in GEMINI_CLI_MASTER.md, include use case, typical MCP tools, and common workflows
- **Documenting new subagents**: Add to AGENTS_OVERVIEW.md with model, tools, purpose; reference orchestration patterns in CLAUDE_COMMANDS_OVERVIEW.md
- **Updating command patterns**: Change the reference table in CLAUDE_COMMANDS_OVERVIEW.md §3 and update examples in both main file and AGENTS_OVERVIEW.md

## Notes for AI Agents
- This project documents **how to document agent workflows**, not a runnable application — edits are research/documentation updates, not code changes
- Files are cross-referenced but independent — updates to one should trigger checks in others (use MERGE_SUMMARY.md to track)
- Test documentation claims against the actual Claude Code/Gemini CLI release notes when available
- When writing new sections, match the verbose-yet-concise style: detailed enough to implement from, but organized for quick reference
