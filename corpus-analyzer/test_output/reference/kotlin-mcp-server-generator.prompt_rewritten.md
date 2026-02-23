---
mode: agent
description: 'Generate a complete Kotlin MCP server project with proper structure, dependencies, and implementation using the official io.modelcontextprotocol:kotlin-sdk library.'
---

## Classification Insights
- Primary Category: reference (confidence: 0.80)
- Secondary Category: howto (confidence: 0.79)
- Key Features: api_patterns (0.20), code_examples (0.30)

## Kotlin MCP Server Project Generator

Generate a complete, production-ready Model Context Protocol (MCP) server project in Kotlin.

### Project Requirements

You will create a Kotlin MCP server with:

1. **Project Structure**: Gradle-based Kotlin project layout
2. **Type Safety**: Utilize data classes and kotlinx.serialization for JSON handling
3. **Coroutines**: All operations should be suspending functions
4. **Error Handling**: Implement Kotlin exceptions and validation
5. **JSON Schemas**: Use `buildJsonObject` for tool schemas
6. **Testing**: Include coroutine test utilities
7. **Logging**: Use kotlin-logging for structured logging
8. **Configuration**: Employ data classes and environment variables
9. **Documentation**: KDoc comments for public APIs
10. **Best Practices**: Follow Kotlin coding conventions and guidelines

### Transport Options

#### Stdio Transport
```kotlin
val transport = StdioServerTransport()
server.connect(transport)
```

#### SSE Transport (Ktor)
```kotlin
embeddedServer(Netty, port = 8080) {
    mcp {
        Server(/*...*/) { "Description" }
    }
}.start(wait = true)
```

### Multiplatform Configuration

For multiplatform projects, add to `build.gradle.kts`:

```kotlin
kotlin {
    jvm()
    js(IR) { nodejs() }
    wasmJs()

    sourceSets {
        commonMain.dependencies {
            implementation("io.modelcontextprotocol:kotlin-sdk:0.7.2")
        }
    }
}
```

[source: prompts/kotlin-mcp-server-generator.prompt.md]