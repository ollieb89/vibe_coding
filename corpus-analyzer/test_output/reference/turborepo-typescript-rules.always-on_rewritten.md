---
type: reference
---

# Turborepo + TypeScript Rules

## Description
This rule enforces standardization of TypeScript configuration and builds within a Turborepo project.

[source: rules/architecture/turborepo-typescript-rules.always-on.md]

---

## Configuration Options
- `always_on`: Enables the rule to run on every commit (default: true)

---

## Content Sections
### Mandatory Usage
- Use shared TypeScript configuration packages
- Packages extend shared configs

### Prohibited Usage
- Root-level `tsconfig.json`

---

## Tasks
- `build`: cacheable
- `typecheck`: cacheable

---

## Output Format / Reports
Not applicable for this rule.

---

## Success Criteria
- All packages use shared TypeScript configuration
- No root-level `tsconfig.json` is present in any package