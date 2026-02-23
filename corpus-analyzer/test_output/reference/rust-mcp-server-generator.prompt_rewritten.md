---
title: Rust MCP Server Generator
source: prompts/rust-mcp-server-generator.prompt.md
---

# Rust MCPL Server Generator: A Template for Creating an AI-Powered MCPL Server Using the `rmcp` Crate

This template provides a starting point for creating an AI-powered Multiplayer Chat Protocol (MCPL) server using the `rmcp` crate. The generated code includes a basic server setup, tool implementations, and test cases.

## Prerequisites

- Rust 1.56 or later
- Cargo 1.56 or later

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/my-mcp-server.git
cd my-mcp-server
```

2. Add the `rmcp` crate to your project's `Cargo.toml`:

```toml
[dependencies]
rmcp = "0.9"
```

3. Run `cargo build --release` to compile the server and its dependencies.

## Server Structure

The server consists of several main components:

- `src/main.rs`: The entry point for the server.
- `Cargo.toml`: The project's configuration file.
- `src/mod.rs`: The main module containing the server's implementation.
- `src/handler.rs`: Contains the server's handlers for handling MCPL messages.
- `src/tools/`: Directory containing tool implementations.
- `tests/`: Directory containing test cases for the server and tools.

## Implementing a Tool

To create a new tool, follow these steps:

1. Define a new struct for the tool's parameters in the appropriate `tools/` module file.
2. Annotate the struct with `#[derive(Debug, Deserialize, JsonSchema)]`.
3. Use the `#[tool]` macro to define the tool, specifying its name and description.
4. Implement the tool as an async function that takes a `Parameters<T>` argument, where `T` is the struct defined in step 1.
5. Return the result of the tool as a `Result<String, String>`.
6. Optionally, add tests for the new tool in the `tests/` directory.

## Example Tool Patterns

### Simple Read-Only Tool

```rust
#[derive(Debug, Deserialize, JsonSchema)]
pub struct GreetParams {
    pub name: String,
}

#[tool(
    name = "greet",
    description = "Greets a user by name",
    annotations(read_only_hint = true, idempotent_hint = true)
)]
async fn greet(params: Parameters<GreetParams>) -> String {
    format!("Hello, {}!", params.inner().name)
}
```

### Tool with Error Handling

```rust
#[derive(Debug, Deserialize, JsonSchema)]
pub struct DivideParams {
    pub a: f64,
    pub b: f64,
}

#[tool(name = "divide", description = "Divides two numbers")]
async fn divide(params: Parameters<DivideParams>) -> Result<String, String> {
    if params.inner().b == 0.0 {
        return Err("Cannot divide by zero".to_string());
    }

    let result = params.inner().a / params.inner().b;
    Ok(format!("Result: {}", result))
}
```

## Running the Server

1. Build the server with `cargo build --release`.
2. Run the compiled binary with `./target/release/my-mcp-server`.
3. Connect to the server using an MCPL client, such as [mcpl-cli](https://github.com/rmcp-rs/mcpl-cli).

## Citation

This template is based on the [prompts/rust-mcp-server-generator.prompt.md](https://gist.github.com/jayphelps/348b2a6e190c5f7d048476c656311a18) prompt by Jay Phelps.