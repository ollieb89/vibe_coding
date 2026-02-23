---
title: Loading & Error States Guidelines
description: Best practices for handling loading and error states in React applications, focusing on Suspense, LoadingOverlay, Skeleton, and error handling with MUI Snackbar and custom components.
tags: react, frontend, performance, best-practices
---

# Loading States

## Preferred Method: SuspenseLoader + useSuspenseQuery (Modern Pattern)

```typescript
// ...
```

## Acceptable Method: LoadingOverlay (Legacy Pattern)

```typescript
// ...
```

## Ok Method: Skeleton with Same Layout

```typescript
// ...
```

## Never Method: Early Returns or Conditional Layout

```typescript
// ...
```

# Error Handling

## Always Method: Use MUI Snackbar for User Feedback

```typescript
// ...
```

## Never Method: react-toastify

```typescript
// ...
```

## Use onError Callbacks in Queries/Mutations

```typescript
// ...
```

## Error Boundaries for Component-Level Errors

```typescript
// ...
```

# Complete Examples

[...]

# Loading State Anti-Patterns

[...]

# Skeleton Loading (Alternative)

[...]

# Summary

[...]

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: skills/frontend-dev-guidelines/resources/loading-and-error-states.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.