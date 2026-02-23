---
type: reference
---

# C# Application Development Guidelines by @tsubakimoto [source: instructions/csharp-ja.instructions.md]

## C# Best Practices
- Always use the latest version of C#, currently C# 13.
- Write clear and concise comments for each function.

## General Guidelines
- Only make confident proposals during code review.
- Include reasons for design decisions in comments, adhering to maintainable practices.
- Handle edge cases and write clear exception handling.
- Comment on the purpose and usage of libraries and external dependencies.

## Naming Conventions
- Use PascalCase for component names, method names, and public members.
- Use camelCase for private fields and local variables.
- Prefix interface names with "I" (e.g., IUserService).

## Formatting
- Apply code formatting styles defined in .editorconfig.
- Recommend using file scope namespace declarations and one line of `using` directives.
- Insert a newline before the opening brace of any control structure (if, for, while, foreach, using, try, etc.).
- Place the final return statement on a separate line.
- Use pattern matching and switch statements where possible.
- Use `nameof` instead of string literals for member name references.
- Create XML documentation comments for all public API members, including `<example>` and `<code>` when possible.

## Project Setup and Configuration
- Provide step-by-step instructions for creating a new .NET project using appropriate templates.
- Describe the purpose of each generated file and folder, helping to understand the project structure.
- Show organization methods using feature folders or Domain-Driven Design (DDD).
- Demonstrate responsibility separation between models, services, and data access layers.
- Explain ASP.NET Core 9's Program.cs and configuration system, as well as environment-specific settings.

## Nullable Reference Types
- Declare variables as non-null and check for `null` at entry points.
- Use `is null` or `is not null` instead of `== null` or `!= null`.
- Trust C#'s null annotations, avoiding unnecessary null checks when the type system guarantees a non-null value.

## Data Access Patterns
- Implement data access layer using Entity Framework Core.
- Discuss options for development and production (SQL Server, SQLite, In-Memory).
- Demonstrate implementation of Repository pattern and situations where it is effective.
- Explain database migration and seeding methods.
- Describe common performance issues and efficient query patterns.

## Authentication and Authorization
- Implement JWT Bearer Token authentication.
- Explain concepts related to OAuth 2.0 and OpenID Connect in ASP.NET Core.
- Show role-based and policy-based authorization implementation methods.
- Demonstrate integration with Microsoft Entra ID (formerly Azure AD).
- Describe methods for securing Controller-based API and Minimal APIs consistently.

## Validation and Error Handling
- Implement data annotations and FluentValidation for model validation.
- Explain validation pipelines and custom validation response methods.
- Show middleware-based global exception handling strategies.
- Describe consistent error responses across the entire API.
- Explain implementation of Problem Details (RFC 7807) for standardized error responses.

## API Versioning and Documentation
- Discuss API versioning strategy and its explanation.
- Show Swagger / OpenAPI implementation with appropriate documentation.
- Describe endpoint, parameter, response, authentication documentation methods.
- Explain versioning for Controller-based API and Minimal APIs.
- Provide helpful API documentation for users.

## Logging and Monitoring
- Implement structured logging using Serilog or similar tools.
- Explain log levels and situations where each should be used.
- Show Application Insights integration for telemetry collection.
- Describe custom telemetry and correlation ID implementation methods.
- Discuss API performance, error, usage pattern monitoring methods.

## Testing
- Include test cases for important application routes.
- Provide instructions for creating unit tests.
- Omit "Act", "Arrange", "Assert" comments in the response.
- Follow existing style conventions (test method names, case sensitivity) for nearby files.
- Describe integration testing methods for API endpoints.
- Show dependency mocking methods for efficient testing.
- Explain testing methods for authentication and authorization logic.
- Discuss Test-Driven Development (TDD) principles applicable to API development.

## Performance Optimization
- Implement caching strategies (in-memory, distributed, response caching).
- Explain the importance of asynchronous programming patterns for API performance.
- Show large dataset pagination, filtering, and sorting methods.
- Describe compression and other performance optimization implementation methods.
- Discuss API performance measurement and benchmarking methods.

## Deployment and DevOps
- Use .NET's built-in container support (`dotnet publish --os linux --arch x64 -p:PublishProfile=DefaultContainer`) for containerizing APIs.
- Explain the differences between manual Dockerfile creation and .NET's container publishing features.
- Describe CI/CD pipelines for .NET applications.
- Discuss hosting options such as Azure App Service, Azure Container Apps, etc.
- Show health checks and Readiness Probe implementation methods.
- Explain environment-specific configuration at each deployment stage.