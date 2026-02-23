---
title: Subscribe to Derived State
description: Learn how to subscribe to derived boolean state instead of continuous values to reduce re-render frequency in React applications.
tags: rerender, derived-state, media-query, optimization
impact: MEDIUM
impactDescription: reduces re-render frequency
---

## Subscribe to Derived State

Subscribing to derived boolean state instead of continuous values can help reduce the frequency of unnecessary re-renders in React applications.

### Incorrect (re-renders on every pixel change)

```tsx
function Sidebar() {
  const width = useWindowWidth()  // updates continuously
  const isMobile = width < 768
  return <nav className={isMobile ? 'mobile' : 'desktop'}>
}
```

### Correct (re-renders only when boolean changes)

```tsx
function Sidebar() {
  const isMobile = useMediaQuery('(max-width: 767px)')
  return <nav className={isMobile ? 'mobile' : 'desktop'}>
}
```

[source: skills/react-best-practices/rules/rerender-derived-state.md]