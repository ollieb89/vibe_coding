---
title: Memory System Reference
source: skills/loki-mode/references/memory-system.md
---

# Rewritten Memory System Document

```yaml
title: The Loki Memory System
description: A comprehensive guide to the memory system of the Loki AI, detailing episodic, semantic, and procedural memories, as well as linking, retrieval, ledger, handoff protocols, and maintenance.
tags: loki, ai, memory, system, architecture
source: skills/loki-mode/references/memory-system.md
```

## Introduction

The Loki Memory System is a fundamental component of the Loki AI's architecture that enables learning and adaptation by capturing, organizing, and retrieving various types of memories. This document provides an overview of episodic, semantic, and procedural memories, their interactions, and how they are managed within the system.

## Episodic Memory

Episodic memory stores personal experiences and events in a sequential order. Each episode is represented as a unique event with associated details such as context, outcome, and artifacts.

### Example Episode Representation

```json
{
  "id": "episode-001",
  "timestamp": "2026-01-06T10:30:00Z",
  "context": {
    "task": "Implement POST /api/todos endpoint"
  },
  "outcome": "Success",
  "artifacts": ["src/routes/todos.ts"],
  "notes": "Implemented validation, business logic, and response generation."
}
```

## Semantic Memory

Semantic memory stores general knowledge and concepts that are not tied to a specific event or time. It includes patterns, anti-patterns, and skills that can be applied across various tasks.

### Example Pattern Representation

```json
{
  "id": "sem-001",
  "summary": "Implement API endpoint using OpenAPI specification"
}
```

## Procedural Memory (Skills)

Procedural memory stores reusable action sequences for specific tasks or types of tasks. Each skill is represented as a set of steps, prerequisites, and exit criteria.

### Example Skill Representation

```markdown
# Skill: API Endpoint Implementation

## Prerequisites
- OpenAPI spec exists at .loki/specs/openapi.yaml
- Database schema defined

## Steps
1. Read endpoint spec from openapi.yaml
2. Create route handler in src/routes/{resource}.ts
3. Implement request validation using spec schema
4. Implement business logic
5. Add database operations if needed
6. Return response matching spec schema
7. Write contract tests
8. Run tests, verify passing

## Common Errors & Fixes
- Missing return type: Add `: void` to handler
- Schema mismatch: Regenerate types from spec

## Exit Criteria
- All contract tests pass
- Response matches OpenAPI spec
- No TypeScript errors
```

## Linking

Each memory note can link to related notes, enabling a Zettelkasten-style network of interconnected knowledge. Link relations include `derived_from`, `related_to`, `contradicts`, `elaborates`, `example_of`, `supersedes`, and `superseded_by`.

## Memory Retrieval

The system retrieves relevant memories before executing any task, using semantic similarity, temporal recency, and keyword search. This helps the AI apply appropriate patterns, anti-patterns, and skills to the current context.

### Retrieval Before Task Execution

Before executing any task, retrieve relevant memories:

```python
def before_task_execution(task):
    """
    Inject relevant memories into task context.
    """
    # 1. Retrieve relevant memories
    memories = retrieve_relevant_memory(task)

    # 2. Check for anti-patterns
    anti_patterns = search_anti_patterns(task.action_type)

    # 3. Inject into prompt
    task.context["relevant_patterns"] = [m.summary for m in memories]
    task.context["avoid_these"] = [a.summary for a in anti_patterns]
    task.context["applicable_skills"] = find_skills(task.type)

    return task
```

## Ledger System (Agent Checkpoints)

Each agent maintains its own ledger, recording important information such as the last checkpoint, tasks completed, current task, state, and context.

### Example Agent Ledger Representation

```json
{
  "agent_id": "eng-001-backend",
  "last_checkpoint": "2026-01-06T10:00:00Z",
  "tasks_completed": 12,
  "current_task": "task-042",
  "state": {
    "files_modified": ["src/routes/todos.ts"],
    "uncommitted_changes": true,
    "last_git_commit": "abc123"
  },
  "context": {
    "tech_stack": ["express", "typescript", "sqlite"],
    "patterns_learned": ["sem-001", "sem-005"],
    "current_goal": "Implement CRUD for todos"
  }
}
```

## Handoff Protocol

When switching between agents, a handoff protocol is followed to transfer relevant information:

### Example Handoff Representation

```json
{
  "id": "handoff-001",
  "from_agent": "eng-001-backend",
  "to_agent": "qa-001-testing",
  "timestamp": "2026-01-06T11:00:00Z",
  "context": {
    "what_was_done": "Implemented POST /api/todos endpoint",
    "artifacts": ["src/routes/todos.ts"],
    "git_state": "commit abc123",
    "needs_testing": ["unit tests for validation", "contract tests"],
    "known_issues": [],
    "relevant_patterns": ["sem-001"]
  }
}
```

## Memory Maintenance

### Pruning Old Episodic Memories

The system prunes old episodic memories based on their age and relevance to semantic memories.

### Merging Duplicate Patterns

Duplicate patterns are merged to maintain consistency within the semantic memory network.

[source: skills/loki-mode/references/memory-system.md]