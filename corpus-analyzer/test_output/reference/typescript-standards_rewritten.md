---
title: TypeScript Standards
source: skills/frontend-dev-guidelines/resources/typescript-standards.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.80)
- Key Features: api_patterns (0.50), code_examples (0.30)

---

```markdown
# TypeScript Standards for React Frontend Development

Best practices to ensure type safety and maintainability in TypeScript projects, focusing on React components.

---

## Strict Mode

### Configuration

Enable strict mode in the project's `tsconfig.json`.

```json
// tsconfig.json
{
    "compilerOptions": {
        "strict": true,
        "noImplicitAny": true,
        "strictNullChecks": true
    }
}
```

**Explanation:**
- No implicit `any` types
- Null/undefined must be handled explicitly
- Type safety enforced

---

## No `any` Type

### The Rule

Prefer using specific types over the `any` type.

```typescript
// ✅ CORRECT - Explicitly define types
function handleData(data: MyData) {
    return data.something;
}

interface MyData {
    something: string;
}

// ❌ AVOID - Using the `any` type
function handleData(data: any) {
    return data.something;
}
```

**When to use `unknown`:**
- Use `unknown` for truly unknown data (forces type checking)
- Implement type guards to narrow the type
- Document why the type is unknown

---

## Explicit Return Types

### Function Return Types

Specify explicit return types for functions.

```typescript
// ✅ CORRECT - Explicit return type
function getUser(id: number): Promise<User> {
    return apiClient.get(`/users/${id}`);
}

function calculateTotal(items: Item[]): number {
    return items.reduce((sum, item) => sum + item.price, 0);
}

// ❌ AVOID - Implicit return type (less clear)
function getUser(id: number) {
    return apiClient.get(`/users/${id}`);
}
```

### Component Return Types

#### Functional Components

```typescript
export const MyComponent: React.FC<Props> = ({ prop }) => {
    return <div>{prop}</div>;
};
```

#### Custom Hooks

```typescript
function useMyData(id: number): { data: Data; isLoading: boolean } {
    const [data, setData] = useState<Data | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    return { data: data!, isLoading };
}
```

---

## Type Imports

### Use 'type' Keyword

Prefer using the `type` keyword for type imports.

```typescript
// ✅ CORRECT - Explicitly mark as type import
import type { User } from '~types/user';
import type { Post } from '~types/post';
import type { SxProps, Theme } from '@mui/material';

// ❌ AVOID - Mixed value and type imports
import { User } from '~types/user';  // Unclear if type or value
```

**Benefits:**
- Clearly separates types from values
- Better tree-shaking
- Prevents circular dependencies
- TypeScript compiler optimization

---

## Component Prop Interfaces

### Interface Pattern

Define a separate interface for component props.

```typescript
/**
 * Props for MyComponent
 */
interface Props {
    prop: string;
}

export const MyComponent: React.FC<Props> = ({ prop }) => {
    return <div>{prop}</div>;
};
```

### JSDoc Comments on Prop Interfaces

Include JSDoc comments to document the shape of component props.

```typescript
/**
 * Props for MyComponent
 */
interface Props {
    /** The prop value */
    prop: string;
}

export const MyComponent: React.FC<Props> = ({ prop }) => {
    return <div>{prop}</div>;
};
```

---

## Utility Types

### Partial, Pick, Omit, Required, and Record

Use utility types to manipulate interfaces in TypeScript.

```typescript
// ✅ CORRECT - Using utility types
type UserWithoutEmail = Omit<User, 'email'>;
type RequiredUser = Required<User>;
type PartialUser = Partial<User>;
type UserRecord = Record<keyof User, string | number>;
```

---

## Type Guards

Use type guards to help TypeScript narrow the type of a value.

```typescript
function isUser(value: any): value is User {
    return (typeof value === 'object' && value !== null) && 'id' in value;
}

const user = {} as User;
if (isUser(user)) {
    // user is of type User here
}
```

---

## Generic Types

### Generic Functions

Create generic functions to work with different data types.

```typescript
function getById<T>(items: T[], id: number): T | undefined {
    return items.find(item => (item as any).id === id);
}

// Usage with type inference
const users: User[] = [...];
const user = getById(users, 123);  // Type: User | undefined
```

### Generic Components

Create generic components to work with different data types.

```typescript
interface ListProps<T> {
    items: T[];
    renderItem: (item: T) => React.ReactNode;
}

export function List<T>({ items, renderItem }: ListProps<T>): React.ReactElement {
    return (
        <div>
            {items.map((item, index) => (
                <div key={index}>{renderItem(item)}</div>
            ))}
        </div>
    );
}

// Usage
<List<User>
    items={users}
    renderItem={(user) => <UserCard user={user} />}
/>
```

---

## Type Assertions (Use Sparingly)

### When to Use

Use type assertions when you know more about the value than TypeScript.

```typescript
// ✅ OK - When you know more than TypeScript
const element = document.getElementById('my-element') as HTMLInputElement;
const value = element.value;

// ✅ OK - API response that you've validated
const response = await api.getData();
const user = response.data as User;  // You know the shape
```

### When NOT to Use

Avoid using type assertions when they circumvent type safety or introduce potential errors.

```typescript
// ❌ AVOID - Circumventing type safety
const data = getData() as any;  // WRONG - defeats TypeScript

// ❌ AVOID - Unsafe assertion
const value = unknownValue as string;  // Might not actually be string
```

---

## Null/Undefined Handling

### Optional Chaining

Use optional chaining to access nested properties without causing errors when one or more levels are `null` or `undefined`.

```typescript
// ✅ CORRECT
const name = user?.profile?.name;

// Equivalent to:
const name = user && user.profile && user.profile.name;
```

### Nullish Coalescing

Use nullish coalescing to provide a default value when a property is `null` or `undefined`.

```typescript
// ✅ CORRECT
const displayName = user?.name ?? 'Anonymous';

// Only uses default if null or undefined
// (Different from || which triggers on '', 0, false)
```

### Non-Null Assertion (Use Carefully)

Use the non-null assertion operator `!` to tell TypeScript that a value is definitely not `null` or `undefined`.

```typescript
// ✅ OK - When you're certain value exists
const data = queryClient.getQueryData<Data>(['data'])!;

// ⚠️ CAREFUL - Only use when you KNOW it's not null
// Better to check explicitly:
const data = queryClient.getQueryData<Data>(['data']);
if (data) {
    // Use data
}
```

---

## Summary

**TypeScript Checklist:**
- ✅ Strict mode enabled
- ✅ No `any` type (use `unknown` if needed)
- ✅ Explicit return types on functions
- ✅ Use `import type` for type imports
- ✅ JSDoc comments on prop interfaces
- ✅ Utility types (Partial, Pick, Omit, Required, Record)
- ✅ Type guards for narrowing
- ✅ Optional chaining and nullish coalescing
- ❌ Avoid type assertions unless necessary

**See Also:**
- [component-patterns.md](component-patterns.md) - Component typing
- [data-fetching.md](data-fetching.md) - API typing

---

[source: skills/frontend-dev-guidelines/resources/typescript-standards.md]