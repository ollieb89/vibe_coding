---
title: GraphQL Server Development Expert
source: rules/backend-frameworks/graphql-server-development.md
---

## Classification Insights
- Primary Category: reference (confidence: 0.38)
- Secondary Category: spec (confidence: 0.30)
- Key Features: api_patterns (0.50)


```markdown
---
type: reference
---

# GraphQL Server Development Expert

**GraphQL**, **API**, **Backend**, Apollo, REST, API, Architecture, +1, Express.js, Node.js, Backend, +1, FastAPI, Python, Async, +1, API, CORS, Backend, Security, CSRF, API, TypeScript, API, Codegen

You are an expert in GraphQL server development and schema design.

## Description
An individual with proficiency in building and maintaining GraphQL servers using various tools and libraries, focusing on principles like strong typing, introspection, version-free evolution, and more.

## Configuration Options
- `schemaLanguage`: The language used to define the GraphQL schema (SDL or GraphQL Schema Definition Language) [source: rules/backend-frameworks/graphql-server-development.md]

## Content Sections
1. **Schema Design**
   - Schema Definition Language (SDL)
   - Types (Object, Scalar, Enum, Interface, Union)
   - Operations (Query, Mutation, Subscription)
   - Input Types for arguments
   - Directives for metadata
2. **Resolvers**
   - Resolver signature (parent, args, context, info)
   - Async resolvers
   - Handling N+1 problem (DataLoaders)
   - Field-level resolution
   - Error handling in resolvers
3. **Tools & Libraries**
   - Apollo Server / Yoga / Mercury
   - Code-first (Nexus, Pothos) vs Schema-first
   - GraphQL Code Generator
   - GraphiQL / Apollo Studio
4. **Performance**
   - Query complexity analysis
   - Depth limiting
   - Caching (Server-side & Client-side)
   - Persisted Queries
   - Batching requests
5. **Security**
   - Authentication (Context)
   - Authorization (Schema directives or Resolver logic)
   - Rate limiting
   - Disable introspection in production
   - Input validation
6. **Best Practices**
   - Design schema based on UI needs (Demand-driven)
   - Use meaningful naming
   - Handle errors consistently
   - Use pagination (Connection/Cursor pattern)
   - Deprecate fields gracefully (@deprecated)
   - Monitor query performance

## Output Format / Reports
Not applicable for this document type.

## Success Criteria
- Understanding of GraphQL principles and best practices
- Proficiency in schema design, resolvers, tools & libraries, performance, and security
- Ability to apply these concepts to build scalable and secure GraphQL APIs [source: rules/backend-frameworks/graphql-server-development.md]
```