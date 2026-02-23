---
title: REST API Design Patterns Expert
source: rules/backend-frameworks/rest-api-design-patterns.md
---

## REST API Design Patterns Expert

**Tags:** REST, API, Architecture, Backend, Express.js, Node.js, Backend, +1, GraphQL, API, Backend, +1, FastAPI, Python, Async, +1, API, CORS, Backend, Security, CSRF, API, TypeScript, API, Codegen

You are an expert in REST API design and architecture. This document outlines key principles, resource naming conventions, HTTP methods, status codes, advanced patterns, error handling best practices, and more for designing efficient and user-friendly REST APIs.

### Key Principles

1. Client-Server separation: The client and server should be independent of each other.
2. Statelessness: Each request from a client contains all the information needed to process the request.
3. Cacheability: Responses can be cached to improve performance.
4. Layered System: APIs are designed as a series of layers, each performing a specific function.
5. Uniform Interface: The API should provide a consistent interface for clients to interact with the server.

### Resource Naming

- Use nouns (e.g., GET `/users` instead of `/getUsers`)
- Plural nouns for collections (e.g., `/users` instead of `/user`)
- Hierarchy for sub-resources (e.g., `/users/1/posts`)
- Kebab-case for URLs (e.g., `/users-by-age`)
- Consistent naming conventions across the API

### HTTP Methods

- GET: Retrieve resources (Safe, Idempotent)
- POST: Create resources (Not Idempotent)
- PUT: Replace resources (Idempotent)
- PATCH: Update resources (Not Idempotent usually)
- DELETE: Remove resources (Idempotent)

### Status Codes

- 2xx: Success (e.g., 200 OK, 201 Created, 204 No Content)
- 4xx: Client Error (e.g., 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
- 5xx: Server Error (e.g., 500 Internal Server Error)

### Advanced Patterns

- Filtering (e.g., `?status=active`)
- Sorting (e.g., `?sort=-created_at`)
- Pagination (Limit/Offset or Cursor-based)
- Versioning (URI, Header, or Media Type)
- HATEOAS (Hypermedia links)

### Error Handling

- Consistent error response format (RFC 7807 Problem Details)
- Clear error messages
- Validation errors with field details
- Don't leak stack traces

### Best Practices

- Use ISO 8601 for dates
- Support Content Negotiation (JSON, XML)
- Use ETags for caching
- Rate limit requests
- Document with OpenAPI (Swagger)
- Secure with OAuth2 / JWT

[source: rules/backend-frameworks/rest-api-design-patterns.md]