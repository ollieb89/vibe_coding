---
type: reference
---

# Playwright MCP Server

**Purpose**: Browser automation and End-to-End (E2E) testing with real browser interaction

## Configuration Options
- `browser`: The web browser to use for the test. Supported browsers include Chromium, Firefox, WebKit, and Edge [source: plugins/superclaude/mcp/MCP_Playwright.md]
- `url`: The URL of the web page to be tested. This can be a local or remote URL [source: plugins/superclaude/mcp/MCP_Playwright.md]
- `headless`: A boolean value indicating whether the browser should run in headless mode (without a graphical interface). Default is false [source: plugins/superclaude/mcp/MCP_Playwright.md]
- `viewportSize`: The size of the viewport for the browser window, specified as an array with two integers representing width and height [source: plugins/superclaude/mcp/MCP_Playwright.md]
- `screenshotDir`: The directory where screenshots will be saved during visual testing [source: plugins/superclaude/mcp/MCP_Playwright.md]

## Content Sections
### Triggers
- Browser testing and E2E test scenarios
- Visual testing, screenshot, or UI validation requests
- Form submission and user interaction testing
- Cross-browser compatibility validation
- Performance testing requiring real browser rendering
- Accessibility testing with automated Web Content Accessibility Guidelines (WCAG) compliance

### Choose When
- **For real browser interaction**: When you need actual rendering, not just code analysis
- **Over unit tests**: For integration testing, user journeys, visual validation
- **For E2E scenarios**: Login flows, form submissions, multi-page workflows
- **For visual testing**: Screenshot comparisons, responsive design validation
- **Not for code analysis**: Static code review, syntax checking, logic validation (use Native Claude instead)

### Works Best With
- **Sequential**: Sequential plans test strategy → Playwright executes browser automation
- **Magic**: Magic creates UI components → Playwright validates accessibility and behavior

## Examples
```
"test the login flow" → Playwright (browser automation)
"check if form validation works" → Playwright (real user interaction)
"take screenshots of responsive design" → Playwright (visual testing)
"validate accessibility compliance" → Playwright (automated WCAG testing)
"review this function's logic" → Native Claude (static analysis)
"explain the authentication code" → Native Claude (code review)
```

## Output Format / Reports
Playwright generates detailed reports for each test run, including screenshots and logs. The reports can be found in the project directory [source: plugins/superclaude/mcp/MCP_Playwright.md]

## Success Criteria
- Tests pass with no errors or failures
- Screenshots match expected visual references (for visual testing)
- Accessibility compliance is met (for accessibility testing)