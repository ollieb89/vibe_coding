---
type: reference
---

## Defer State Reads to Usage Point

### Impact
MEDIUM

#### Impact Description
avoids unnecessary subscriptions

### Tags
- rerender
- searchParams
- localStorage
- optimization

### Defer State Reads to Usage Point

Avoid subscribing to dynamic state (searchParams, localStorage) if you only read it inside callbacks. This practice helps reduce unnecessary re-renders and optimizes the application's performance.

#### Incorrect (subscribes to all searchParams changes):

```tsx
function ShareButton({ chatId }: { chatId: string }) {
  const searchParams = useSearchParams()

  const handleShare = () => {
    const ref = searchParams.get('ref')
    shareChat(chatId, { ref })
  }

  return <button onClick={handleShare}>Share</button>
}
```

#### Correct (reads on demand, no subscription):

```tsx
function ShareButton({ chatId }: { chatId: string }) {
  const handleShare = () => {
    const params = new URLSearchParams(window.location.search)
    const ref = params.get('ref')
    shareChat(chatId, { ref })
  }

  return <button onClick={handleShare}>Share</button>
}
```

[source: skills/react-best-practices/rules/rerender-defer-reads.md]