---
title: PM Agent: Upstream vs Clean Architecture Comparison
source: docs/architecture/PM_AGENT_COMPARISON.md
---

# Comparison of Upstream and This PR's PM Agent Implementation

This document compares the key differences between the original [Upstream](#footnote1) implementation of the Personal Memory (PM) Agent and the current implementation in this PR. The comparison covers various aspects such as implementation, configuration, performance, and compatibility.

## Key Differences

| Category | Upstream | This PR |
| --- | --- | --- |
| **Implementation** | Markdown + Python hooks | Pure Python |
| **Configuration** | ~/.claude/skills/ | site-packages/ |
| **Activation** | Auto (session start) | On-demand (import) |
| **Token Usage** | 12.4K | 6K (-52%) |
| **Test Coverage** | Partial | 79 tests |
| **Auto-activation** | ✅ | ❌ |
| **PDCA Docs Generation** | ✅ Auto | ❌ Manual |
| **Pytest Fixtures** | ❌ | ✅ |

## Compatibility

### Mutual Benefits

Both implementations have their unique advantages, and it's possible to leverage the benefits of both by using them together.

- Core (This PR): Ideal for developers who prefer Pytest-driven development and want to minimize token usage.
- Skills (Upstream): Suitable for users who value Auto-activation and Claude Code integration.

### Preserving Upstream's Features

Maintaining the original implementation of the PM Agent offers several benefits:

1. **Auto-activation**: Automatically activates at session start, making it more convenient for users.
2. **PDCA Docs Generation**: Generates PDCA cycle documentation automatically, simplifying documentation management.
3. **Claude Code Integration**: Seamlessly integrates with Claude Code for enhanced functionality and workflow.

## Recommendations

### Best Practices: Coexistence

The recommended approach is to use both implementations together (Option 1):

- Core (This PR): Utilize it for Pytest-driven development and minimizing token usage.
- Skills (Upstream): Leverage it for Auto-activation, Claude Code integration, and daily usage.

By using both implementations, you can enjoy the benefits of each while still maintaining compatibility with the original PM Agent.

---

## Footnote
<a id="footnote1">1</a> Upstream refers to the original implementation of the Personal Memory (PM) Agent available in Claude Code's repository. [source: docs/architecture/PM_AGENT_COMPARISON.md]