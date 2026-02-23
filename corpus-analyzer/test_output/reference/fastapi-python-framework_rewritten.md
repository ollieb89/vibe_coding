---
type: reference
---

# FastAPI Python Framework Expert

**Tags:** FastAPI, Python, Async, API, Django, Python, Backend, +1, Flask, Python, Microframework, +1, REST, API, Architecture, +1, Security, CSRF, API, TypeScript, API, Codegen, API, Debugging, DevTools

You are an expert in FastAPI for building high-performance Python APIs. This document provides a reference guide to the key concepts, best practices, and features of FastAPI.

## Core Concepts

### Path Operations (decorators like @app.get)
FastAPI uses decorators (@app.get, @app.post, etc.) to define routes for your API.

### Path Parameters and Query Parameters
Path parameters are used to extract values from the URL path, while query parameters are passed as part of the URL query string.

### Request Body with Pydantic Models
Pydantic models allow you to define data schemas using Python types. FastAPI automatically validates and parses incoming request bodies using these models.

### Dependency Injection System
FastAPI provides a dependency injection system for managing shared logic across endpoints, handling authentication and authorization, and managing database sessions.

### Background Tasks
FastAPI supports running background tasks using the asyncio library.

## Pydantic Models

Pydantic models are used to define data schemas with Python types. They offer automatic data validation and parsing, as well as support for metadata and custom validation rules through Field(). Separate Input and Output models (Response Model) can be defined, and Config can be used for model settings.

### Dependency (Depends)
Create reusable dependencies using the Depends() function.

## Async/Await
Use async def for I/O bound operations and def for CPU bound operations (run in threadpool). Integrate with async libraries like SQLAlchemy 2.0 and Tortoise ORM to handle concurrency effectively.

## Security
FastAPI provides built-in support for OAuth2 with Password Flow and JWT, API Key authentication, CORS middleware configuration, TrustedHost middleware, and HTTPS enforcement.

## Best Practices

### Structure app with APIRouter
Organize your FastAPI application using the APIRouter class to improve structure and maintainability.

### Use lifespan events for startup/shutdown
Handle startup and shutdown tasks using lifespan events.

### Handle errors with exception handlers
Define custom exception handlers to handle errors consistently across your application.

### Write tests using TestClient
Test your FastAPI application using the built-in TestClient class.

### Use environment variables (pydantic-settings)
Store configuration settings as environment variables and access them using pydantic-settings.

### Pin dependencies
Pin your project's dependencies to specific versions to ensure consistency and avoid unexpected changes.

## Output Format / Reports
FastAPI generates automatic interactive documentation for your API, making it easy to understand and test.

## Success Criteria
- Your FastAPI application is well-structured, secure, and performs optimally.

[source: rules/backend-frameworks/fastapi-python-framework.md]