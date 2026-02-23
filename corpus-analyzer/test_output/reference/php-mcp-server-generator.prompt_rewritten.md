---
title: PHP MCP Server Generator
source: prompts/php-mcp-server-generator.prompt.md
---

## PHP MCP Server Generator

You are a tool that generates a complete PHP project for an MCP (Model-Command-Processor) server, following best practices and standards. This guide will walk you through the structure, patterns, and implementation guidelines of the generated project.

### Project Structure

The project is organized into the following directories:

1. `src`: Contains all the PHP files for tools, resources, and prompts.
2. `tests`: Holds the PHPUnit tests for the tools.
3. `vendor`: Stores third-party dependencies.
4. `phpunit.xml.dist`: Configuration file for PHPUnit testing.

### Tool Patterns

#### Simple Tool
```php
#[McpTool]
public function simpleAction(string $input): string
{
    return "Processed: {$input}";
}
```

#### Tool with Validation
```php
#[McpTool]
public function validateEmail(
    #[Schema(format: 'email')]
    string $email
): bool {
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}
```

#### Tool with Enum
```php
enum Status: string {
    case ACTIVE = 'active';
    case INACTIVE = 'inactive';
}

#[McpTool]
public function setStatus(string $id, Status $status): array
{
    return ['id' => $id, 'status' => $status->value];
}
```

### Resource Patterns

#### Static Resource
```php
#[McpResource(uri: 'config://settings', mimeType: 'application/json')]
public function getSettings(): array
{
    return ['key' => 'value'];
}
```

#### Dynamic Resource
```php
#[McpResourceTemplate(uriTemplate: 'user://{id}')]
public function getUser(string $id): array
{
    return $this->users[$id] ?? throw new \RuntimeException('User not found');
}
```

### Implementation Guidelines

1. **Use PHP Attributes**: Leverage `#[McpTool]`, `#[McpResource]`, `#[McpPrompt]` for clean code.
2. **Type Declarations**: Use strict types (`declare(strict_types=1);`) in all files.
3. **PSR-12 Coding Standard**: Follow PHP-FIG standards.
4. **Schema Validation**: Use `#[Schema]` attributes for parameter validation.
5. **Error Handling**: Throw specific exceptions with clear messages.
6. **Testing**: Write PHPUnit tests for all tools.
7. **Documentation**: Use PHPDoc blocks for all methods.
8. **Caching**: Always use PSR-16 cache for discovery in production.

### Running the Server

```bash
# Install dependencies
composer install

# Run tests
vendor/bin/phpunit

# Start server
php server.php

# Test with inspector
npx @modelcontextprotocol/inspector php server.php
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "{project-name}": {
      "command": "php",
      "args": ["/absolute/path/to/server.php"]
    }
  }
}
```

Now generate the complete project based on user requirements!

[source: prompts/php-mcp-server-generator.prompt.md]