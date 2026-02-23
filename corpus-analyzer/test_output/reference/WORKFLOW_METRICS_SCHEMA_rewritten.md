---
title: Workflow Metrics Schema
source: docs/memory/WORKFLOW_METRICS_SCHEMA.md
---

# Workflow Metrics Schema: Optimizing Efficiency for PM Agent

This document outlines the schema for workflow metrics used by the PM Agent, a tool designed to optimize task execution efficiency. The schema includes data collection points, analysis scripts, visualization examples, expected patterns, and integration details with the PM Agent.

## Overview

The PM Agent automatically records workflow metrics at each execution point, providing valuable insights for continuous optimization and A/B testing.

### Data Collection Points
- Session start (Layer 0)
- Intent classification (Layer 1)
- Progressive loading (Layers 2-5)
- Task completion
- Session end

### No Manual Intervention
All recording is automatic, ensuring transparent operation and privacy preservation.

## Metrics Schema

Each workflow metric record includes the following fields:

- `timestamp`: timestamp of the execution point
- `task_type`: generic classification of the task type (e.g., typo_fix)
- `tokens_used`: number of tokens consumed during the task execution
- `success`: boolean indicating whether the task was successfully completed
- `time_ms`: time taken to complete the task in milliseconds
- `workflow_id`: identifier for the workflow variant used (e.g., progressive_v3_layer2)
- `error_recurrence`: percentage of similar errors encountered during previous executions
- `user_feedback`: user-defined feedback on task execution quality

## Data Storage and Retention

Data is stored locally in the `docs/memory/` directory, with no external transmission. Users can control the retention period as needed.

### File Rotation
Old metrics are archived monthly, while a fresh file is started for new data.

```bash
# Archive old metrics (monthly)
mv docs/memory/workflow_metrics.jsonl \
   docs/memory/archive/workflow_metrics_2025-10.jsonl

# Start fresh
touch docs/memory/workflow_metrics.jsonl
```

### Cleanup
Metrics older than 6 months are removed.

```bash
# Remove metrics older than 6 months
find docs/memory/archive/ -name "workflow_metrics_*.jsonl" \
  -mtime +180 -delete
```

## Analysis and Visualization

### Weekly Analysis
```bash
# Group by task type and calculate averages
python scripts/analyze_workflow_metrics.py --period week

# Output:
# Task Type: typo_fix
#   Count: 12
#   Avg Tokens: 680
#   Avg Time: 1,850ms
#   Success Rate: 100%
```

### A/B Testing Analysis
```bash
# Compare workflow variants
python scripts/ab_test_workflows.py \
  --variant-a progressive_v3_layer2 \
  --variant-b experimental_eager_layer3 \
  --metric tokens_used

# Output:
# Variant A (progressive_v3_layer2):
#   Avg Tokens: 1,250
#   Success Rate: 95%
#
# Variant B (experimental_eager_layer3):
#   Avg Tokens: 2,100
#   Success Rate: 98%
#
# Statistical Significance: p = 0.03 (significant)
# Recommendation: Keep Variant A (better efficiency)
```

### Visualization
#### Token Usage Over Time
```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_json("docs/memory/workflow_metrics.jsonl", lines=True)
df['date'] = pd.to_datetime(df['timestamp']).dt.date

daily_avg = df.groupby('date')['tokens_used'].mean()
plt.plot(daily_avg)
plt.title("Average Token Usage Over Time")
plt.ylabel("Tokens")
plt.xlabel("Date")
plt.show()
```

#### Task Type Distribution
```python
task_counts = df['task_type'].value_counts()
plt.pie(task_counts, labels=task_counts.index, autopct='%1.1f%%')
plt.title("Task Type Distribution")
plt.show()
```

#### Workflow Efficiency Comparison
```python
workflow_efficiency = df.groupby('workflow_id').agg({
    'tokens_used': 'mean',
    'success': 'mean',
    'time_ms': 'mean'
})
print(workflow_efficiency.sort_values('tokens_used'))
```

## Expected Patterns

### Healthy Metrics (After 1 Month)
```yaml
token_efficiency:
  ultra_light: 750-1,050 tokens (63% reduction)
  light: 1,250 tokens (46% reduction)
  medium: 3,850 tokens (47% reduction)
  heavy: 10,350 tokens (40% reduction)

success_rates:
  all_tasks: ≥95%
  ultra_light: 100% (simple tasks)
  light: 98%
  medium: 95%
  heavy: 92%

user_satisfaction:
  satisfied: ≥70%
  neutral: ≤25%
  unsatisfied: ≤5%
```

### Red Flags (Require Investigation)
```yaml
warning_signs:
  - success_rate < 85% for any task type
  - tokens_used > estimated_budget by >30%
  - time_ms > 10 seconds for light tasks
  - user_feedback "unsatisfied" > 10%
  - error_recurrence > 15%
```

## Integration with PM Agent

The PM Agent is designed to work seamlessly with the metrics schema, automatically recording data at each execution point without requiring any manual intervention.

### Privacy and Security

#### Data Retention
- Local storage only (`docs/memory/`)
- No external transmission
- Git-manageable (optional)
- User controls retention period

#### Sensitive Data Handling
- No code snippets logged
- No user input content
- Only metadata (tokens, timing, success)
- Task types are generic classifications

## Maintenance

Regular maintenance tasks include file rotation and cleanup.

### File Rotation
```bash
# Archive old metrics (monthly)
mv docs/memory/workflow_metrics.jsonl \
   docs/memory/archive/workflow_metrics_2025-10.jsonl

# Start fresh
touch docs/memory/workflow_metrics.jsonl
```

### Cleanup
```bash
# Remove metrics older than 6 months
find docs/memory/archive/ -name "workflow_metrics_*.jsonl" \
  -mtime +180 -delete
```

## References
- Specification: `plugins/superclaude/commands/pm.md` (Line 291-355)
- Research: `docs/research/llm-agent-token-efficiency-2025.md`
- Tests: `tests/pm_agent/test_token_budget.py`

```
[source: docs/memory/WORKFLOW_METRICS_SCHEMA.md]