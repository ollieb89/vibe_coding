---
title: Loki Mode - Autonomous Runner
source: skills/loki-mode/autonomy/README.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.95)
- Key Features: code_examples (0.70), function_signatures (0.60), parameter_descriptions (0.80), return_values (0.40), exceptions (0.30), usage_examples (0.90)

---
type: reference
---

# Loki Mode - Autonomous Runner

A single script that handles everything: prerequisites, setup, Vibe Kanban monitoring, and autonomous execution with auto-resume.

## Function Signatures

### `run.sh`
```bash
./autonomy/run.sh [SKILL_FILE]
```

#### Parameters
- **SKILL_FILE**: The path to the SKILL.md file (mandatory).

#### Return Values
- Exit code: 0 on success, non-zero on failure.

#### Exceptions
- If prerequisites are not met, the script will exit with an error message.

## Usage Examples

### Quick Start

```bash
# Run with a PRD
./autonomy/run.sh ./docs/requirements.md

# Run interactively
./autonomy/run.sh
```

## Live Output

Claude's output is displayed in real-time - you can see exactly what's happening:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━