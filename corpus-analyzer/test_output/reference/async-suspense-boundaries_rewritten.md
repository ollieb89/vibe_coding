---
type: reference
---

## Strategic Suspense Boundaries

### Impact
- High impact on faster initial paint

### Tags
- async
- suspense
- streaming
- layout-shift

### Description
Instead of awaiting data in async components before returning JSX, use Suspense boundaries to show the wrapper UI faster while data loads.

### Configuration Options
<!-- None for this topic -->

### Content Sections
#### Correct Usage Example

The correct usage example demonstrates how to use Suspense boundaries to improve performance by only blocking the component that requires the data, allowing other parts of the page to render immediately.

```tsx
function Page() {
  return (
    <div>
      <div>Sidebar</div>
      <div>Header</div>
      <div>
        <Suspense fallback={<Skeleton />}>
          <DataDisplay />
        </Suspense>
      </div>
      <div>Footer</div>
    </div>
  )
}

async function DataDisplay() {
  const data = await fetchData() // Only blocks this component
  return <div>{data.content}</div>
}
```

#### Alternative Usage Example

The alternative usage example shows how to share a promise across components, allowing them to wait together while still improving performance by only blocking the necessary components.

```tsx
function Page() {
  // Start fetch immediately, but don't await
  const dataPromise = fetchData()

  return (
    <div>
      <div>Sidebar</div>
      <div>Header</div>
      <Suspense fallback={<Skeleton />}>
        <DataDisplay dataPromise={dataPromise} />
        <DataSummary dataPromise={dataPromise} />
      </Suspense>
      <div>Footer</div>
    </div>
  )
}

function DataDisplay({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise) // Unwraps the promise
  return <div>{data.content}</div>
}

function DataSummary({ dataPromise }: { dataPromise: Promise<Data> }) {
  const data = use(dataPromise) // Reuses the same promise
  return <div>{data.summary}</div>
}
```

#### When Not to Use This Pattern

- Critical data needed for layout decisions (affects positioning)
- SEO-critical content above the fold
- Small, fast queries where suspense overhead isn't worth it
- When you want to avoid layout shift (loading → content jump)

#### Trade-off
Faster initial paint vs potential layout shift. Choose based on your UX priorities.

### Output Format / Reports
<!-- None for this topic -->

### Success Criteria
- Improve performance by only blocking the necessary components during data fetching

[source: skills/react-best-practices/rules/async-suspense-boundaries.md]