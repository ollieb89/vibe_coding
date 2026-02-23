---
type: reference
---

# Rust Project Scaffolding

Generate complete, idiomatic, and production-ready Rust applications with proper structure, dependency management, testing, and build configuration following Rust best practices. This guide focuses on creating scalable architecture and adhering to Rust idioms for your projects.

## Context

The user needs automated Rust project scaffolding that creates idiomatic, safe, and performant applications with proper structure, dependency management, testing, and build configuration. Focus on Rust idioms and scalable architecture.

## Requirements

- A Rust project setup that follows best practices for organization, error handling, and testing
- Proper documentation and code examples to help users understand the generated project structure

## Instructions

### 1. Analyze Project Type

Determine the project type from user requirements:
- **Binary**: CLI tools, applications, services
- **Library**: Reusable crates, shared utilities
- **Workspace**: Multi-crate projects, monorepos
- **Web API**: Actix/Axum web services, REST APIs
- **WebAssembly**: Browser-based applications

### 2. Initialize Project with Cargo

```bash
# Create binary project
cargo new project-name
cd project-name

# Or create library
cargo new --lib library-name
```

### 3. Generate Binary Project Structure

[source: systems-programming/commands/rust-project.md]

### 4. Generate Library Project Structure

[source: systems-programming/commands/rust-project.md]

### 5. Generate Workspace Structure

[source: systems-programming/commands/rust-project.md]

### 6. Generate Web API Structure (Axum)

[source: systems-programming/commands/rust-project.md]

### 7. Configure Development Tools

[source: systems-programming/commands/rust-project.md]

## Output Format

1. **Project Structure**: Complete directory tree with idiomatic Rust organization
2. **Configuration**: Cargo.toml with dependencies and build settings
3. **Entry Point**: main.rs or lib.rs with proper documentation
4. **Tests**: Unit and integration test structure
5. **Documentation**: README and code documentation
6. **Development Tools**: Makefile, clippy/rustfmt configs

Focus on creating idiomatic Rust projects with strong type safety, proper error handling, and comprehensive testing setup.