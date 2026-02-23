---
type: reference
---

# Lightweight Connection Handling for MCP Servers

This module provides a base class for handling connections to MCP servers, along with three specific connection types: stdio (standard input/output), SSE (Server-Sent Events), and HTTP.

## Configuration Options
- `transport`: Connection type ("stdio", "sse", or "http") [source: skills/mcp-builder/scripts/connections.py]
- `command`: Command to run (stdio only)
- `args`: Command arguments (stdio only)
- `env`: Environment variables (stdio only)
- `url`: Server URL (sse and http only)
- `headers`: HTTP headers (sse and http only)

## Base Class: MCPConnection
```

### MCPConnection

```python
class MCPConnection(ABC):
    # ... (method signatures, parameter descriptions, return values, exceptions, and usage examples omitted for brevity)
```

## Subclasses

### MCPConnectionStdio

```python
class MCPConnectionStdio(MCPConnection):
    # ... (method signatures, parameter descriptions, return values, exceptions, and usage examples omitted for brevity)
```

### MCPConnectionSSE

```python
class MCPConnectionSSE(MCPConnection):
    # ... (method signatures, parameter descriptions, return values, exceptions, and usage examples omitted for brevity)
```

### MCPConnectionHTTP

```python
class MCPConnectionHTTP(MCPConnection):
    # ... (method signatures, parameter descriptions, return values, exceptions, and usage examples omitted for brevity)
```

## Factory Function: create_connection

```python
def create_connection(
    transport,
    command=None,
    args=None,
    env=None,
    url=None,
    headers=None,
):
    # ... (method signature, parameter descriptions, return values, exceptions, and usage examples omitted for brevity)
```

## Output Format / Reports
Not applicable.

## Success Criteria
- A valid `MCPConnection` instance is returned when the provided transport type is supported.