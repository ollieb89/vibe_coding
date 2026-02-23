---
type: reference
---

# ASP.NET REST API Development

Guidelines for building REST APIs with ASP.NET Core 9, focusing on best practices and educational context.

## Configuration Options
- `aspnetcore`: Target framework for the project (ASP.NET Core)
- `--version`: Specific version of ASP.NET Core (e.g., 9.0)

## API Design Fundamentals
### REST Architectural Principles
Explanation of REST principles and their application to ASP.NET Core APIs.

### Resource-Oriented URLs
Guidance on designing meaningful resource-oriented URLs.

### HTTP Verb Usage
Explanation of appropriate HTTP verb usage in REST APIs.

### Traditional Controller-Based APIs vs. Minimal APIs
Comparison between traditional controller-based APIs and the newer Minimal API approach.

### Status Codes, Content Negotiation, and Response Formatting
Explanation of status codes, content negotiation, and response formatting in the context of REST.

## Project Setup and Structure
### Creating a New ASP.NET Core Web API Project
Guide users through creating a new ASP.NET Core 9 Web API project with the appropriate templates.

### Understanding the Generated Files and Folders
Explanation of the purpose of each generated file and folder to build understanding of the project structure.

### Organizing Code Using Feature Folders or Domain-Driven Design Principles
Demonstration of how to organize code using feature folders or domain-driven design principles.

### Separation of Concerns
Explanation of proper separation of concerns with models, services, and data access layers.

### Program.cs and Configuration System
Explanation of the Program.cs file and configuration system in ASP.NET Core 9 including environment-specific settings.

## Building Controller-Based APIs
### RESTful Controllers
Guide the creation of RESTful controllers with proper resource naming and HTTP verb implementation.

### Attribute Routing
Explanation of attribute routing and its advantages over conventional routing.

### Model Binding, Validation, and [ApiController] Attribute
Demonstration of model binding, validation, and the role of [ApiController] attribute.

### Dependency Injection in Controllers
Explanation of dependency injection within controllers.

### Action Return Types
Explanation of action return types (IActionResult, ActionResult<T>, specific return types) and when to use each.

## Implementing Minimal APIs
### Endpoint Routing System
Explanation of the endpoint routing system in Minimal APIs.

### Parameter Binding, Validation, and Dependency Injection
Demonstration of parameter binding, validation, and dependency injection in Minimal APIs.

### Structuring Larger Minimal API Applications
Guidance on structuring larger Minimal API applications to maintain readability.

## Data Access Patterns
### Entity Framework Core Implementation
Guide the implementation of a data access layer using Entity Framework Core.

### Database Options for Development and Production
Explanation of different options (SQL Server, SQLite, In-Memory) for development and production.

### Repository Pattern Implementation
Demonstration of repository pattern implementation and when it's beneficial.

### Database Migrations and Data Seeding
Explanation of database migrations and data seeding.

### Efficient Query Patterns
Explanation of efficient query patterns to avoid common performance issues.

## Authentication and Authorization
### JWT Bearer Tokens Implementation
Guide users through implementing authentication using JWT Bearer tokens.

### OAuth 2.0 and OpenID Connect Concepts
Explanation of OAuth 2.0 and OpenID Connect concepts as they relate to ASP.NET Core.

### Role-Based and Policy-Based Authorization
Explanation of role-based and policy-based authorization.

### Integration with Microsoft Entra ID (formerly Azure AD)
Demonstration of integration with Microsoft Entra ID (formerly Azure AD).

## Validation and Error Handling
### Model Validation Using Data Annotations and FluentValidation
Guide the implementation of model validation using data annotations and FluentValidation.

### Validation Pipeline and Customization
Explanation of the validation pipeline and how to customize validation responses.

### Global Exception Handling Strategy
Demonstration of a global exception handling strategy using middleware.

### Consistent Error Responses
Explanation of how to create consistent error responses across the API.

### Problem Details (RFC 7807) Implementation
Explanation of problem details (RFC 7807) implementation for standardized error responses.

## API Versioning and Documentation
### Swagger/OpenAPI Implementation with Proper Documentation
Demonstration of Swagger/OpenAPI implementation with proper documentation.

### Endpoint, Parameter, Response, and Authentication Documentation
Explanation of how to document endpoints, parameters, responses, and authentication.

### Versioning in Controller-Based and Minimal APIs
Explanation of versioning in both controller-based and Minimal APIs.

## Logging and Monitoring
### Structured Logging Using Serilog or Other Providers
Guide the implementation of structured logging using Serilog or other providers.

### Logging Levels
Explanation of the logging levels and when to use each.

### Integration with Application Insights for Telemetry Collection
Demonstration of integration with Application Insights for telemetry collection.

### Custom Telemetry and Correlation IDs for Request Tracking
Explanation of how to implement custom telemetry and correlation IDs for request tracking.

## Testing REST APIs
### Unit Tests for Controllers, Minimal API Endpoints, and Services
Guide users through creating unit tests for controllers, Minimal API endpoints, and services.

### Integration Testing Approaches for API Endpoints
Explanation of integration testing approaches for API endpoints.

### Mocking Dependencies for Effective Testing
Demonstration of how to mock dependencies for effective testing.

### Testing Authentication and Authorization Logic
Explanation of how to test authentication and authorization logic.

## Performance Optimization
### Caching Strategies (In-Memory, Distributed, Response Caching)
Guide users on implementing caching strategies (in-memory, distributed, response caching).

### Asynchronous Programming Patterns
Explanation of asynchronous programming patterns and why they matter for API performance.

### Pagination, Filtering, and Sorting for Large Data Sets
Demonstration of pagination, filtering, and sorting for large data sets.

### Compression and Other Performance Optimizations
Explanation of how to implement compression and other performance optimizations.

### Measuring and Benchmarking API Performance
Explanation of how to measure and benchmark API performance.

## Deployment and DevOps
### Containerizing the API Using .NET's Built-In Container Support
Guide users through containerizing their API using .NET's built-in container support.

### CI/CD Pipelines for ASP.NET Core Applications
Explanation of CI/CD pipelines for ASP.NET Core applications.

### Deployment to Azure App Service, Azure Container Apps, or Other Hosting Options
Demonstration of deployment to Azure App Service, Azure Container Apps, or other hosting options.

### Health Checks and Readiness Probes
Explanation of health checks and readiness probes.

### Environment-Specific Configurations for Different Deployment Stages
Explanation of environment-specific configurations for different deployment stages.

[source: instructions/aspnet-rest-apis.instructions.md]