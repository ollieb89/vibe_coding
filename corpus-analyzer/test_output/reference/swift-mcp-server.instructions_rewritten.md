---
type: reference
---

# Swift MCP Server Development Guidelines [source: instructions/swift-mcp-server.instructions.md]

Best practices and patterns for building Model Context Protocol (MCP) servers in Swift using the official MCP Swift SDK package.

## Configuration Options
- `name`: The server's name
- `version`: The server's version number

## Server Setup

Create an MCP server using the `Server` class with capabilities:

```swift
import ModelContextProtocolSwiftSDK

let capabilities = [.tools, .sampling]
let server = Server(name: "MyMCPServer", version: "1.0.0", capabilities: capabilities)
```

## Initializing the Server

Initialize the server with a transport and an optional initialize hook:

```swift
import ModelContextProtocolSwiftSDK
import Foundation

let transport = StdioTransport()
let initializeHook: (ClientInfo, ClientCapabilities) async throws -> Void = { clientInfo, clientCapabilities in
    // Validate client and perform any necessary setup
}

try await server.start(transport: transport, initializeHook: initializeHook)
```

## Handling Tool Requests

Implement the `CallTool` protocol to handle tool requests:

```swift
struct CallTool {
    struct Params {
        let name: String
        let arguments: [String: Any]?
    }

    static func request(_ params: Params) -> Request<CallTool.Result> {
        // Create and return a new request with the provided parameters
    }
}
```

## Processing Tool Requests

Process tool requests using the `Client` class:

```swift
import ModelContextProtocolSwiftSDK

let client = Client(name: "MyClient", version: "1.0.0")

do {
    let result = try await client.callTool(CallTool.request(.init(name: "process", arguments: ["id": 1])))
    print(result.content)
} catch {
    print("Error processing tool request: \(error)")
}
```

## Shutdown and Graceful Termination

Use the `ServiceLifecycle` library for graceful shutdown:

```swift
import ModelContextProtocolSwiftSDK
import ServiceLifecycle

struct MCPService: Service {
    let server: Server
    let transport: Transport

    func run() async throws {
        try await server.start(transport: transport)
        try await Task.sleep(for: .days(365 * 100))
    }

    func shutdown() async throws {
        try await server.stop()
    }
}

let logger = Logger(label: "com.example.mcp-server")
let transport = StdioTransport(logger: logger)
let mcpService = MCPService(server: server, transport: transport)

let serviceGroup = ServiceGroup(
    services: [mcpService],
    configuration: .init(
        gracefulShutdownSignals: [.sigterm, .sigint]
    ),
    logger: logger
)

try await serviceGroup.run()
```

## Testing the Server

Test your server using XCTest:

```swift
import XCTest
@testable import MyMCPServer

final class ServerTests: XCTestCase {
    func testToolCall() async throws {
        let server = createTestServer()

        // Test tool call logic
        let params = CallTool.Params(name: "process", arguments: ["id": 1])

        // Verify behavior
        XCTAssertNoThrow(try await processToolCall(params))
    }
}