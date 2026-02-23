---
title: Trigger Types - Complete Guide
source: skills/skill-developer/TRIGGER_TYPES.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.67)
- Secondary Category: tutorial (confidence: 0.54)
- Key Features: api_patterns (0.20), code_examples (0.30)

---

```markdown
# Trigger Types - Complete Guide [source: skills/skill-developer/TRIGGER_TYPES.md]

A comprehensive guide for configuring skill triggers in Claude Code's skill auto-activation system.

## Table of Contents

1. [Keyword Triggers (Explicit)](#keyword-triggers)
2. [Intent Pattern Triggers (Implicit)](#intent-pattern-triggers)
3. [File Path Triggers](#file-path-triggers)
4. [Content Pattern Triggers](#content-pattern-triggers)
5. [Best Practices Summary](#best-practices-summary)

---

## Keyword Triggers (Explicit)

### How It Works

Case-insensitive substring matching in user's prompt.

### Use For

Topic-based activation where user explicitly mentions the subject.

### Configuration

```json
"promptTriggers": {
  "keywords": ["layout", "grid", "toolbar", "submission"]
}
```

### Example

- User prompt: "how does the **layout** system work?"
- Matches: "layout" keyword
- Activates: `project-catalog-developer`

### Best Practices

- Use specific, unambiguous terms
- Include common variations ("layout", "layout system", "grid layout")
- Avoid overly generic words ("system", "work", "create")
- Test with real prompts

---

## Intent Pattern Triggers (Implicit)

### How It Works

Regex pattern matching to detect user's intent even when they don't mention the topic explicitly.

### Use For

Action-based activation where user describes what they want to do rather than the specific topic.

### Configuration

```json
"promptTriggers": {
  "intentPatterns": [
    "(create|add|implement).*?(feature|endpoint)",
    "(how does|explain).*?(layout|workflow)"
  ]
}
```

### Examples

**Database Work:**
- User prompt: "add user tracking feature"
- Matches: `(add).*?(feature)`
- Activates: `database-verification`, `error-tracking`

**Component Creation:**
- User prompt: "create a dashboard widget"
- Matches: `(create).*?(component)` (if component in pattern)
- Activates: `frontend-dev-guidelines`

### Best Practices

- Capture common action verbs: `(create|add|modify|build|implement)`
- Include domain-specific nouns: `(feature|endpoint|component|workflow)`
- Use non-greedy matching: `.*?` instead of `.*`
- Test patterns thoroughly with regex tester (https://regex101.com/)
- Don't make patterns too broad (causes false positives)
- Don't make patterns too specific (causes false negatives)

### Common Pattern Examples

```regex
# Database Work
(add|create|implement).*?(user|login|auth|feature)

# Explanations
(how does|explain|what is|describe).*?

# Frontend Work
(create|add|make|build).*?(component|UI|page|modal|dialog)

# Error Handling
(fix|handle|catch|debug).*?(error|exception|bug)

# Workflow Operations
(create|add|modify).*?(workflow|step|branch|condition)
```

---

## File Path Triggers

### How It Works

Glob pattern matching against the file path being edited.

### Use For

Domain/area-specific activation based on file location in the project.

### Configuration

```json
"fileTriggers": {
  "pathPatterns": [
    "frontend/src/**/*.tsx",
    "form/src/**/*.ts"
  ],
  "pathExclusions": [
    "**/*.test.ts",
    "**/*.spec.ts"
  ]
}
```

### Glob Pattern Syntax

- `**` = Any number of directories (including zero)
- `*` = Any characters within a directory name
- Examples:
  - `frontend/src/**/*.tsx` = All .tsx files in frontend/src and subdirs
  - `/path/to/file.txt` = Exact match for the specified file path

### Best Practices

- Match broadly for file paths
- Add exclusions for test files
- Make patterns specific enough to avoid false matches

---

## Content Pattern Triggers

### How It Works

Regex pattern matching against the content of the file being edited.

### Use For

Activation based on specific code patterns within a file.

### Configuration

```json
"contentTriggers": {
  "patterns": [
    {
      "name": "Prisma",
      "regex": "(import.*[Pp]risma|PrismaService|prisma\\.)"
    },
    {
      "name": "Controllers",
      "regex": "export.*React\\.FC|export default function.*|useState|useEffect"
    }
  ]
}
```

### Best Practices

- Match specific code patterns
- Escape special characters in content patterns
- Test against real file content
- Make patterns specific enough to avoid false matches

---

## Best Practices Summary

### DO:
✅ Use specific, unambiguous keywords
✅ Test all patterns with real examples
✅ Include common variations
✅ Use non-greedy regex: `.*?`
✅ Escape special characters in content patterns
✅ Add exclusions for test files
✅ Make file path patterns narrow and specific

### DON'T:
❌ Use overly generic keywords ("system", "work")
❌ Make intent patterns too broad (false positives)
❌ Make patterns too specific (false negatives)
❌ Forget to test with regex tester (https://regex101.com/)
❌ Use greedy regex: `.*` instead of `.*?`
❌ Match too broadly in file paths

### Testing Your Triggers

**Test keyword/intent triggers:**
```bash
echo '{"session_id":"test","prompt":"your test prompt"}' | \
  npx tsx .claude/hooks/skill-activation-prompt.ts
```

**Test file path/content triggers:**
```bash
cat <<'EOF' | npx tsx .claude/hooks/skill-verification-guard.ts
{
  "session_id": "test",
  "tool_name": "Edit",
  "tool_input": {"file_path": "/path/to/test/file.ts"}
}
EOF
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main skill guide
- [SKILL_RULES_REFERENCE.md](SKILL_RULES_REFERENCE.md) - Complete skill-rules.json schema
- [PATTERNS_LIBRARY.md](PATTERNS_LIBRARY.md) - Ready-to-use pattern library
```
```