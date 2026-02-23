---
type: reference
---

# Dart and Flutter Best Practices

This document provides best practices for writing Dart and Flutter code, based on recommendations from [Effective Dart](https://dart.dev/effective-dart) and [Architecture Recommendations](https://docs.flutter.dev/app-architecture/recommendations).

## Effective Dart

The guidelines are organized into several topics for easy consumption:

1. **Style** - Rules for formatting, organizing, and naming code elements.
2. **Documentation** - Guidelines for writing comments and doc comments.
3. **Usage** - Best practices for using language features to implement behavior.
4. **Design** - Recommendations for designing consistent, usable APIs for libraries.

### How to read the topics

Each topic is divided into sections containing a list of guidelines. Guidelines are categorized as follows:

- **DO**: Practices that should always be followed.
- **DON'T**: Things that are almost never a good idea.
- **PREFER**: Suggested practices with exceptions.
- **AVOID**: Practices to minimize or avoid.
- **CONSIDER**: Practices that may be beneficial depending on the context.

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: instructions/dart-n-flutter.instructions.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

---

## Style

### Variables

- DO follow a consistent rule for `var` and `final` on local variables.
- AVOID storing what you can calculate.

### Members

- DON'T wrap a field in a getter and setter unnecessarily.
- PREFER using a `final` field to make a read-only property.
- CONSIDER using `=>` for simple members.
- DON'T use `this.` except to redirect to a named constructor or to avoid shadowing.
- DO initialize fields at their declaration when possible.

### Constructors

- DO use initializing formals when possible.
- DON'T use `late` when a constructor initializer list will do.
- DO use `;` instead of `{}` for empty constructor bodies.
- DON'T use `new`.
- DON'T use `const` redundantly.

[source: instructions/dart-n-flutter.instructions.md]