---
title: Store Event Handlers in Refs
description: Best practice for optimizing event handling in React by storing callbacks in refs to prevent unnecessary re-subscriptions.
tags: advanced, hooks, refs, event-handlers, optimization
impact: LOW (stable subscriptions)
---

# Store Event Handlers in Refs

To avoid unnecessary re-subscriptions when using effects with event handlers, store callbacks in refs.

## Incorrect Example (re-subscribes on every render):

```tsx
function useWindowEvent(event: string, handler: () => void) {
  useEffect(() => {
    window.addEventListener(event, handler)
    return () => window.removeEventListener(event, handler)
  }, [event, handler])
}
```

## Correct Example (stable subscription):

```tsx
function useWindowEvent(event: string, handler: () => void) {
  const handlerRef = useRef(handler)
  useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  useEffect(() => {
    const listener = () => handlerRef.current()
    window.addEventListener(event, listener)
    return () => window.removeEventListener(event, listener)
  }, [event])
}
```

## Alternative: Use `useEffectEvent` if you're on latest React:

```tsx
import { useEffectEvent } from 'react'

function useWindowEvent(event: string, handler: () => void) {
  const onEvent = useEffectEvent(handler)

  useEffect(() => {
    window.addEventListener(event, onEvent)
    return () => window.removeEventListener(event, onEvent)
  }, [event])
}
```

`useEffectEvent` offers a cleaner API for the same pattern: it creates a stable function reference that always calls the latest version of the handler.

[source: skills/react-best-practices/rules/advanced-event-handler-refs.md]