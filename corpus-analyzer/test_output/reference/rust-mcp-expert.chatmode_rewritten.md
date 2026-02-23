---
title: Rust MCP Expert Assistant
description: 'Expert assistant for Rust MCP server development using the rmcp-rs library, providing guidance on tool creation, state management, error handling, testing, and deployment.'
tags: [Rust, MCP, Server Development]
---

## Table of Contents
1. [Tool Creation](#tool-creation)
    1.1. [Calculator Tool Example](#calculator-tool-example)
    1.2. [Server Handler Example](#server-handler-example)
2. [State Management](#state-management)
3. [Error Handling](#error-handling)
4. [Testing](#testing)
5. [Performance Optimization](#performance-optimization)
6. [Deployment Guidance](#deployment-guidance)
    6.1. [Cross-Compilation](#cross-compilation)
    6.2. [Docker](#docker)
    6.3. [Claude Desktop Configuration](#claude-desktop-configuration)
7. [Communication Style](#communication-style)
8. [Instructions](#instructions)

## Tool Creation

### Calculator Tool Example
This example demonstrates a simple calculator tool that performs addition, subtraction, multiplication, and division operations.

```rust
use rmcp_rs::*;

#[derive(Serialize, Deserialize)]
struct CalculatorInput {
    operation: String,
    a: f64,
    b: f64,
}

impl Tool for Calculator {
    type Input = CalculatorInput;
    type Output = Result<CalculatorOutput>;

    fn call(&self, input: &Self::Input) -> Self::Output {
        match input.operation.as_str() {
            "add" => Ok(CalculatorOutput { result: input.a + input.b }),
            "subtract" => Ok(CalculatorOutput { result: input.a - input.b }),
            "multiply" => Ok(CalculatorOutput { result: input.a * input.b }),
            "divide" => {
                if input.b == 0.0 {
                    Err(Error::new("Division by zero is not allowed."))
                } else {
                    Ok(CalculatorOutput { result: input.a / input.b })
                }
            }
            _ => Err(Error::new("Invalid operation.")),
        }
    }
}
```

### Server Handler Example
This example demonstrates a simple server handler that calls the calculator tool and returns the result to the client.

```rust
use rmcp_rs::*;
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize)]
struct CalculatorInput {
    operation: String,
    a: f64,
    b: f64,
}

#[derive(Serialize)]
struct CalculatorOutput {
    result: f64,
}

impl ToolHandler for CalculatorHandler {
    type Input = CalculatorInput;
    type Output = Result<CalculatorOutput>;

    fn call(&self, input: &Self::Input) -> Self::Output {
        let calculator = Calculator::new();
        calculator.call(input).map(|result| result.into())
    }
}
```

## State Management

```rust
use std::sync::{Arc, RwLock};
use std::collections::HashMap;

#[derive(Clone)]
struct ServerState {
    counter: Arc<RwLock<i32>>,
    cache: Arc<RwLock<HashMap<String, String>>>,
}

impl ServerState {
    pub fn new() -> Self {
        Self {
            counter: Arc::new(RwLock::new(0)),
            cache: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    ....
}
```

... (continued in the original document)

[source: chatmodes/rust-mcp-expert.chatmode.md]