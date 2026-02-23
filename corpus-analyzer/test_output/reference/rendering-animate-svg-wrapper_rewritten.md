---
title: Animate SVG Wrapper Instead of SVG Element
description: A best practice for improving performance by enabling hardware acceleration through animating an SVG wrapper instead of the SVG element directly.
tags: reference, rendering, svg, css, animation, performance
---

# Animate SVG Wrapper Instead of SVG Element

Many browsers do not provide hardware acceleration for CSS3 animations on SVG elements. To overcome this limitation, wrap the SVG in a `<div>` and animate the wrapper instead.

## Incorrect (animating SVG directly - no hardware acceleration)

```tsx
function LoadingSpinner() {
  return (
    <svg
      className="animate-spin"
      width="24"
      height="24"
      viewBox="0 0 24 24"
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" />
    </svg>
  )
}
```

## Correct (animating wrapper div - hardware accelerated)

```tsx
function LoadingSpinner() {
  return (
    <div className="animate-spin">
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
      >
        <circle cx="12" cy="12" r="10" stroke="currentColor" />
      </svg>
    </div>
  )
}
```

This technique applies to all CSS transforms and transitions (`transform`, `opacity`, `translate`, `scale`, `rotate`). Wrapping the SVG in a div allows browsers to utilize GPU acceleration for smoother animations.

## Usage Examples
- Animate SVG Wrapper Instead of SVG Element: [source: skills/react-best-practices/rules/rendering-animate-svg-wrapper.md#animate-svg-wrapper-instead-of-svg-element]

```markdown
[user-defined]: This placeholder text has been expanded into helpful descriptions in the rewritten document.
```

[source: skills/react-best-practices/rules/rendering-animate-svg-wrapper.md]