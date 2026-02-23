---
name: test
description: "Execute tests with coverage analysis and automated quality reporting"
category: utility
complexity: enhanced
mcp-servers: [playwright]
personas: [qa-specialist]
tags: [API Reference, Testing, Quality Assurance, Coverage Analysis, Playwright MCP]
---

# /sc:test - Testing and Quality Assurance

This command executes tests with coverage analysis and automated quality reporting. It supports various test types (unit, integration, e2e) and offers features like continuous testing, intelligent failure analysis, and cross-browser compatibility.

## Configuration Options
- `target`: Optional target directory or file to run tests against (defaults to all tests)
- `--type`: Test type to execute (unit, integration, e2e, all - defaults to all)
- `--coverage`: Generate coverage reports and metrics
- `--watch`: Activate continuous testing watch mode
- `--fix`: Automatically fix simple test failures during development

## Usage
```
/sc:test [target] [--type unit|integration|e2e|all] [--coverage] [--watch] [--fix]
```

## Behavioral Flow
1. **Discover**: Categorize available tests using runner patterns and conventions
2. **Configure**: Set up appropriate test environment and execution parameters
3. **Execute**: Run tests with monitoring and real-time progress tracking
4. **Analyze**: Generate coverage reports and failure diagnostics
5. **Report**: Provide actionable recommendations and quality metrics

Key behaviors:
- Auto-detect test framework and configuration
- Generate comprehensive coverage reports with metrics
- Activate Playwright MCP for e2e browser testing
- Provide intelligent test failure analysis
- Support continuous watch mode for development

## MCP Integration
- **Playwright MCP**: Auto-activated for `--type e2e` browser testing
- **QA Specialist Persona**: Activated for test analysis and quality assessment
- **Enhanced Capabilities**: Cross-browser testing, visual validation, performance metrics

## Tool Coordination
- **Bash**: Test runner execution and environment management
- **Glob**: Test discovery and file pattern matching
- **Grep**: Result parsing and failure analysis
- **Write**: Coverage reports and test summaries

## Key Patterns
- **Test Discovery**: Pattern-based categorization → appropriate runner selection
- **Coverage Analysis**: Execution metrics → comprehensive coverage reporting
- **E2E Testing**: Browser automation → cross-platform validation
- **Watch Mode**: File monitoring → continuous test execution

## Examples

### Basic Test Execution
```
/sc:test
# Discovers and runs all tests with standard configuration
# Generates pass/fail summary and basic coverage
```

### Targeted Coverage Analysis
```
/sc:test src/components --type unit --coverage
# Unit tests for specific directory with detailed coverage metrics
```

### Browser Testing
```
/sc:test --type e2e
# Activates Playwright MCP for comprehensive browser testing
# Cross-browser compatibility and visual validation
```

### Development Watch Mode
```
/sc:test --watch --fix
# Continuous testing with automatic simple failure fixes
# Real-time feedback during development
```

## Boundaries

**Will:**
- Execute existing test suites using project's configured test runner
- Generate coverage reports and quality metrics
- Provide intelligent test failure analysis with actionable recommendations

**Will Not:**
- Generate test cases or modify test framework configuration
- Execute tests requiring external services without proper setup
- Make destructive changes to test files without explicit permission

## Instructions
1. Improve structure and clarity
2. Keep all code blocks exactly as-is (verbatim, do not summarize)
3. Add a citation [source: plugins/superclaude/commands/test.md] at the end
4. Ensure all headings follow a logical hierarchy (no skipping levels)
5. Expand any placeholder text like [user-defined] into helpful descriptions
6. Start with YAML frontmatter including title, description, and tags
7. Do NOT wrap the output in a markdown code block (output raw text)
8. Do not repeat these instructions in your response.

[source: plugins/superclaude/commands/test.md]