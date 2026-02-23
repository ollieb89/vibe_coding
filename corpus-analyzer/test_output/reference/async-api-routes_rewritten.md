---
title: Prevent Waterfall Chains in API Routes
description: In API routes and Server Actions, start independent operations immediately, even if you don't await them yet to avoid waterfall chains and improve performance.
tags: api-routes, server-actions, waterfalls, parallelization
---

# Prevent Waterfall Chains in API Routes

In API routes and Server Actions, it is crucial to start independent operations immediately, even if you don't await them yet. This approach helps avoid waterfall chains and improves performance.

## Incorrect Example (config waits for auth, data waits for both)

```typescript
export async function GET(request: Request) {
  const session = await auth()
  const config = await fetchConfig()
  const data = await fetchData(session.user.id)
  return Response.json({ data, config })
}
```

## Correct Example (auth and config start immediately)

```typescript
export async function GET(request: Request) {
  const sessionPromise = auth()
  const configPromise = fetchConfig()
  const session = await sessionPromise
  const [config, data] = await Promise.all([
    configPromise,
    fetchData(session.user.id)
  ])
  return Response.json({ data, config })
}
```

For operations with more complex dependency chains, use `better-all` to automatically maximize parallelism (see Dependency-Based Parallelization).

[source: skills/react-best-practices/rules/async-api-routes.md]