---
type: reference
---

# LangChain Python Instructions

These instructions guide GitHub Copilot in generating code and documentation for LangChain applications in Python. Focus on LangChain-specific patterns, APIs, and best practices.

## Configuration Options
- `api_key`: Your API key for the chat model provider (e.g., OpenAI)
- `base_url`: The base URL for the chat model provider's API
- `model`: The specific model to use (e.g., `gpt-4o`, `gpt-3.5-turbo`)
- `temperature`: Randomness control (0.0 deterministic — 1.0 creative)
- `timeout`: Seconds to wait before canceling a request
- `max_tokens`: Response token limit
- `stop`: Stop sequences for the model
- `max_retries`: Retry attempts for network/limit failures
- `rate_limiter`: Optional BaseRateLimiter to space requests and avoid provider quota errors

## Runnable Interface (LangChain-specific)

LangChain's `Runnable` interface is the foundation for composing and executing chains, chat models, output parsers, retrievers, and LangGraph graphs. It provides a unified API for invoking, batching, streaming, inspecting, and composing components.

**Key LangChain-specific features:**

- All major LangChain components (chat models, output parsers, retrievers, graphs) implement the Runnable interface.
- Supports synchronous (`invoke`, `batch`, `stream`) and asynchronous (`await invoke`, `await batch`, `stream`) execution.
- Built-in support for tool calling with strict input/output typing.
- Observability: log request_id, model name, latency, and other metadata.

## Chat Models

LangChain offers a consistent interface for chat models with additional features for monitoring, debugging, and optimization.

### Integrations

Integrations are either:

1. Official: packaged `langchain-<provider>` integrations maintained by the LangChain team or provider.
2. Community: contributed integrations (in `langchain-community`)

Chat models typically follow a naming convention with a `Chat` prefix (e.g., `ChatOpenAI`, `ChatAnthropic`, `ChatOllama`). Models without the `Chat` prefix (or with an `LLM` suffix) often implement the older string-in/string-out interface and are less preferred for modern chat workflows.

### Interface

Chat models implement `BaseChatModel` and support the Runnable interface: streaming, async, batching, and more. Many operations accept and return LangChain `messages` (roles like `system`, `user`, `assistant`). See the BaseChatModel API reference for details.

Key methods include:

- `invoke(messages, ...)` — send a list of messages and receive a response.
- `stream(messages, ...)` — stream partial outputs as tokens arrive.
- `batch(inputs, ...)` — batch multiple requests.
- `bind_tools(tools)` — attach tool adapters for tool calling.
- `with_structured_output(schema)` — helper to request structured responses.

### Inputs and outputs

- LangChain supports its own message format and OpenAI's message format; pick one consistently in your codebase.
- Messages include a `role` and `content` blocks; content can include structured or multimodal payloads where supported.

### Standard parameters

Commonly supported parameters (provider-dependent):

- `model`: model identifier (e.g., `gpt-4o`, `gpt-3.5-turbo`)
- `temperature`: randomness control (0.0 deterministic — 1.0 creative)
- `timeout`: seconds to wait before canceling
- `max_tokens`: response token limit
- `stop`: stop sequences
- `max_retries`: retry attempts for network/limit failures
- `api_key`, `base_url`: provider auth and endpoint configuration
- `rate_limiter`: optional BaseRateLimiter to space requests and avoid provider quota errors

> Note: Not all parameters are implemented by every provider. Always consult the provider integration docs.

### Tool calling

Chat models can call tools (APIs, DBs, system adapters). Use LangChain's tool-calling APIs to:

- Register tools with strict input/output typing.
- Observe and log tool call requests and results.
- Validate tool outputs before passing them back to the model or executing side effects.

See the tool-calling guide in the LangChain docs for examples and safe patterns.

### Structured outputs

Use `with_structured_output` or schema-enforced methods to request JSON or typed outputs from the model. Structured outputs are essential for reliable extraction and downstream processing (parsers, DB writes, analytics).

### Multimodality

Some models support multimodal inputs (images, audio). Check provider docs for supported input types and limitations. Multimodal outputs are rare — treat them as experimental and validate rigorously.

### Context window

Models have a finite context window measured in tokens. When designing conversational flows:

- Keep messages concise and prioritize important context.
- Trim old context (summarize or archive) outside the model when it exceeds the window.
- Use a retriever + RAG pattern to surface relevant long-form context instead of pasting large documents into the chat.

## Advanced topics

### Rate-limiting

- Use `rate_limiter` when initializing chat models to space calls.
- Implement retry with exponential backoff and consider fallback models or degraded modes when throttled.

### Caching

- Exact-input caching for conversations is often ineffective. Consider semantic caching (embedding-based) for repeated meaning-level queries.
- Semantic caching introduces dependency on embeddings and is not universally suitable.
- Cache only where it reduces cost and meets correctness requirements (e.g., FAQ bots).

## Best practices

- Use type hints and dataclasses for public APIs.
- Validate inputs before calling LLMs or tools.
- Load secrets from secret managers; never log secrets or unredacted model outputs.
- Deterministic tests: mock LLMs and embedding calls.
- Cache embeddings and frequent retrieval results.
- Observability: log request_id, model name, latency, and other metadata.

[source: instructions/langchain-python.instructions.md]