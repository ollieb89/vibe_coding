---
title: Production-ready REST API template using FastAPI.
source: backend-development/skills/api-design-principles/assets/rest-api-template.py
---

## Production-ready REST API template using FastAPI
A comprehensive template for building production-ready APIs with FastAPI, including pagination, filtering, error handling, and best practices.

### Configuration Options
- `title`: The title of the API (default: "API Template")
- `version`: The version number of the API (default: "1.0.0")
- `docs_url`: The URL for the API documentation (default: "/api/docs")

### Content Sections
#### Models
- `UserStatus`: An enumeration representing user statuses (ACTIVE, INACTIVE, SUSPENDED)
- `UserBase`, `UserCreate`, `UserUpdate`, and `User`: Pydantic models for handling user data

#### Pagination
- `PaginationParams`: A model for handling pagination parameters
- `PaginatedResponse`: A response model for returning paginated results

#### Error Handling
- `ErrorDetail`: A model for error details in the API responses
- `ErrorResponse`: The main error response model for the API
- `http_exception_handler`: An exception handler for HTTP exceptions

#### Endpoints
- List users with pagination and filtering (`/api/users`)
- Create a new user (`/api/users`)
- Get user by ID (`/api/users/{user_id}`)
- Partially update user (`/api/users/{user_id}`)
- Delete user (`/api/users/{user_id}`)

### Output Format / Reports
Not applicable in this case as it's a reference document.

### Success Criteria
- The API should adhere to the provided design principles and best practices.

[source: backend-development/skills/api-design-principles/assets/rest-api-template.py]