---
title: Rust MCP Server Development Best Practices
description: 'Best practices for building Model Context Protocol servers in Rust using the official rmcp SDK with async/await patterns'
tags: [Rust, MCP, Server, Development]
source: instructions/rust-mcp-server.instructions.md
---

## Table of Contents
1. [Introduction](#introduction)
2. [Project Setup](#project-setup)
3. [Tool Implementation](#tool-implementation)
    - [Analyzing Code](#analyzing-code)
    - [Validating Parameters](#validating-parameters)
4. [Prompt Implementation](#prompt-implementation)
    - [Listing Prompts](#listing-prompts)
    - [Getting a Prompt](#getting-a-prompt)
5. [Resource Implementation](#resource-implementation)
    - [Listing Resources](#listing-resources)
    - [Reading a Resource](#reading-a-resource)
6. [Transport Options](#transport-options)
    - [Stdio Transport](#stdio-transport)
    - [SSE (Server-Sent Events) Transport](#sse--server-sent-events--transport)
    - [Streamable HTTP Transport](#streamable-http-transport)
    - [Custom Transports](#custom-transports)
7. [Error Handling](#error-handling)
    - [ErrorData Usage](#errordata-usage)
    - [Anyhow Integration](#anyhow-integration)
8. [Testing](#testing)
    - [Unit Tests](#unit-tests)
9. [Conclusion](#conclusion)

## Introduction
This guide provides best practices for developing a Model Context Protocol (MCP) server in Rust using the official rmcp SDK with async/await patterns.

## Project Setup
To get started, you'll need to have Rust and Cargo installed on your system. You can follow the [official Rust installation guide](https://www.rust-lang.org/tools/install) if you haven't already. Once you have Rust installed, create a new project using Cargo:

```sh
$ cargo new my_mcp_server --lib
```

## Tool Implementation
Tools in an MCP server are responsible for executing tasks and returning results. Here's an example of analyzing code for best practices:

### Analyzing Code
```rust
use rmcp::model::{Tool, ToolResponseContent};

#[derive(Serialize)]
struct CodeParams {
    filename: String,
}

#[tool]
async fn analyze_code(params: Parameters<CodeParams>) -> ToolResponseContent {
    // ... Analyze code for best practices and suggest improvements ...

    ToolResponseContent::from(vec![
        TextContent::text(format!("Analysis of {}:", params.inner().filename)),
        TextContent::text("No issues found."),
    ])
}
```

### Validating Parameters
When validating parameters, you can use the `validate_params` function that returns a Result wrapping an MCP error:

```rust
use rmcp::ErrorData;

fn validate_params(value: &str) -> Result<(), ErrorData> {
    if value.is_empty() {
        return Err(ErrorData::invalid_params("Value cannot be empty"));
    }
    Ok(())
}
```

## Prompt Implementation
Prompts are used to interact with users or other systems during the execution of tasks. Here's an example of listing and getting prompts:

### Listing Prompts
```rust
use rmcp::model::{Prompt, PromptArgument, PromptMessage, GetPromptResult};

async fn list_prompts(
    &self,
    _request: Option<PaginatedRequestParam>,
    _context: RequestContext<RoleServer>,
) -> Result<ListPromptsResult, ErrorData> {
    let prompts = vec![
        Prompt {
            name: "code-review".to_string(),
            description: Some("Review code for best practices".to_string()),
            arguments: Some(vec![
                PromptArgument {
                    name: "language".to_string(),
                    description: Some("Programming language".to_string()),
                    required: Some(true),
                },
            ]),
        },
    ];
    
    Ok(ListPromptsResult { prompts })
}
```

### Getting a Prompt
```rust
async fn get_prompt(
    &self,
    request: GetPromptRequestParam,
    _context: RequestContext<RoleServer>,
) -> Result<GetPromptResult, ErrorData> {
    match request.name.as_str() {
        "code-review" => {
            let language = request.arguments
                .as_ref()
                .and_then(|args| args.get("language"))
                .ok_or_else(|| ErrorData::invalid_params("language required"))?;
            
            Ok(GetPromptResult {
                description: Some("Code review prompt".to_string()),
                messages: vec![
                    PromptMessage::user(format!(
                        "Review this {} code for best practices and suggest improvements",
                        language
                    )),
                ],
            })
        }
        _ => Err(ErrorData::invalid_params("Unknown prompt")),
    }
}
```

## Resource Implementation
Resources are used to store and retrieve data in an MCP server. Here's an example of listing and reading resources:

### Listing Resources
```rust
async fn list_resources(
    &self,
    _request: Option<PaginatedRequestParam>,
    _context: RequestContext<RoleServer>,
) -> Result<ListResourcesResult, ErrorData> {
    let resources = vec![
        Resource {
            uri: "file:///data/config.json".to_string(),
            name: "Configuration".to_string(),
            description: Some("Server configuration".to_string()),
            mime_type: Some("application/json".to_string()),
        },
    ];

    Ok(ListResourcesResult { resources })
}
```

### Reading a Resource
```rust
async fn read_resource(
    &self,
    request: ReadResourceRequestParam,
    _context: RequestContext<RoleServer>,
) -> Result<ReadResourceResult, ErrorData> {
    match request.uri.as_str() {
        "file:///data/config.json" => {
            let content = r#"{"version": "1.0", "enabled": true}"#;
            Ok(ReadResourceResult {
                contents: vec![
                    ResourceContents::text(content.to_string())
                        .with_uri(request.uri)
                        .with_mime_type("application/json"),
                ],
            })
        }
        _ => Err(ErrorData::invalid_params("Unknown resource")),
    }
}
```

## Transport Options
MCP servers can use various transports to communicate with clients. Here's an example of using Stdio, SSE (Server-Sent Events), Streamable HTTP, and custom transports:

### Stdio Transport
```rust
let transport = rmcp::transport::StdioTransport::new();
let server = Server::builder()
    .with_handler(handler)
    .build(transport)?;
```

### SSE (Server-Sent Events) Transport
```rust
use rmcp::transport::SseServerTransport;
use std::net::SocketAddr;

let addr: SocketAddr = "127.0.0.1:8000".parse()?;
let transport = SseServerTransport::new(addr);

let server = Server::builder()
    .with_handler(handler)
    .build(transport)?;

server.run(signal::ctrl_c()).await?;
```

### Streamable HTTP Transport
```rust
use rmcp::transport::StreamableHttpTransport;
use axum::{Router, routing::post};

let transport = rmcp::transport::StreamableHttpTransport::new();
let app = Router::new()
    .route("/mcp", post(transport.handler()));

let listener = tokio::net::TcpListener::bind("127.0.0.1:3000").await?;
axum::serve(listener, app).await?;
```

### Custom Transports
Custom transports can be implemented for TCP, Unix Socket, WebSocket, or other protocols. See examples/transport/ for more details.

## Error Handling
Proper error handling is crucial in an MCP server. Here's an example of using `ErrorData` and `anyhow`:

### ErrorData Usage
```rust
use rmcp::ErrorData;

fn validate_params(value: &str) -> Result<(), ErrorData> {
    if value.is_empty() {
        return Err(ErrorData::invalid_params("Value cannot be empty"));
    }
    Ok(())
}
```

### Anyhow Integration
```rust
use rmcp::ErrorData;
use std::convert::From;
use anyhow::{Context, Result};

fn validate_params(value: &str) -> Result<(), ErrorData> {
    if value.is_empty() {
        Err(ErrorData::invalid_params("Value cannot be empty"))
            .context("Failed to validate parameters")?
    } else {
        Ok(())
    }
}
```

## Testing
Unit tests can help ensure the correctness of your MCP server implementation. Here's an example of testing a tool:

### Unit Tests
```rust
use super::*;

#[tokio::test]
async fn test_analyze_code() {
    let handler = Handler::new();
    let request = Request::new(
        Method::Post,
        "/mcp/tools/analyze-code",
        Body::from_json(&AnalyzeCodeRequest {
            filename: "example.rs".to_string(),
        })?,
    );

    let response = handler.handle(request).await;
    assert!(response.is_ok());

    // ... Assert the response contains expected data ...
}
```

## Conclusion
This guide provides a comprehensive overview of developing an MCP server in Rust using the official rmcp SDK with async/await patterns. By following these best practices, you can create robust and efficient servers that meet your needs. Happy coding!