---
type: reference
---

# Self-explanatory Code Commenting Instructions [source: instructions/self-explanatory-code-commenting.instructions.md]

## Description
Guidelines for writing comments to achieve self-explanatory code with minimal comments. Examples are in JavaScript but should work on any language that has comments.

## Configuration Options
- `applyTo`: The scope of the guidelines (e.g., ** for all files)

## Content Sections
### Core Principle
**Write code that speaks for itself. Comment only when necessary to explain WHY, not WHAT.** We do not need comments most of the time.

### Commenting Guidelines
#### ❌ AVOID These Comment Types
- **Obvious Comments**: States the obvious
- **Redundant Comments**: Repeats the code
- **Outdated Comments**: Doesn't match the code

#### ✅ WRITE These Comment Types
- **Complex Business Logic**
- **Non-obvious Algorithms**
- **Regex Patterns**
- **API Constraints or Gotchas**

### Decision Framework
Before writing a comment, ask:
1. Is the code self-explanatory? → No comment needed
2. Would a better variable/function name eliminate the need? → Refactor instead
3. Does this explain WHY, not WHAT? → Good comment
4. Will this help future maintainers? → Good comment

### Special Cases for Comments
- Public APIs
- Configuration and Constants
- Annotations

### Anti-Patterns to Avoid
- Dead Code Comments
- Changelog Comments
- Divider Comments

## Quality Checklist
Before committing, ensure your comments:
- Explain WHY, not WHAT
- Are grammatically correct and clear
- Will remain accurate as code evolves
- Add genuine value to code understanding
- Are placed appropriately (above the code they describe)
- Use proper spelling and professional language

## Success Criteria
- The comments are concise, informative, and self-explanatory.