---
mode: 'agent'
tools: ['changes', 'search/codebase', 'edit/editFiles', 'problems', 'search']
description: 'Get best practices for XUnit unit testing, including data-driven tests'
---

## Classification Insights
- Primary Category: reference (confidence: 0.12)
- Key Features: api_patterns (0.15)

# XUnit Best Practices

This document provides guidelines for writing effective unit tests with XUnit, covering both standard and data-driven testing approaches.

## Project Setup

- Create a separate test project named `[ProjectName].Tests`
- Add references to the following NuGet packages: Microsoft.NET.Test.Sdk, xunit, and xunit.runner.visualstudio
- Organize test classes that match the classes being tested (e.g., `CalculatorTests` for `Calculator`)
- Use .NET SDK test commands: `dotnet test` to run tests

[source: prompts/csharp-xunit.prompt.md]

## Test Structure

- No test class attributes required (unlike MSTest/NUnit)
- Use fact-based tests with `[Fact]` attribute for simple tests
- Adhere to the Arrange-Act-Assert (AAA) pattern
- Name tests using the pattern `MethodName_Scenario_ExpectedBehavior`
- Use constructor for setup and `IDisposable.Dispose()` for teardown
- Utilize `IClassFixture<T>` for shared context between tests in a class
- Utilize `ICollectionFixture<T>` for shared context between multiple test classes

## Standard Tests

- Keep tests focused on a single behavior
- Avoid testing multiple behaviors in one test method
- Use clear assertions that express intent
- Include only the assertions needed to verify the test case
- Make tests independent and idempotent (can run in any order)
- Minimize test interdependencies

## Data-Driven Tests

- Use `[Theory]` combined with data source attributes
- Utilize `[InlineData]` for inline test data
- Use `[MemberData]` for method-based test data
- Use `[ClassData]` for class-based test data
- Create custom data attributes by implementing `DataAttribute`
- Employ meaningful parameter names in data-driven tests

## Assertions

- Use `Assert.Equal` for value equality
- Use `Assert.Same` for reference equality
- Use `Assert.True`/`Assert.False` for boolean conditions
- Use `Assert.Contains`/`Assert.DoesNotContain` for collections
- Use `Assert.Matches`/`Assert.DoesNotMatch` for regex pattern matching
- Utilize `Assert.Throws<T>` or `await Assert.ThrowsAsync<T>` to test exceptions
- Consider using fluent assertions library for more readable assertions

## Mocking and Isolation

- Contemplate using Moq or NSubstitute alongside XUnit
- Mock dependencies to isolate units under test
- Use interfaces to facilitate mocking
- Consider using a DI container for complex test setups

## Test Organization

- Organize tests by feature or component
- Utilize `[Trait("Category", "CategoryName")]` for categorization
- Group tests with shared dependencies using collection fixtures
- Contemplate output helpers (`ITestOutputHelper`) for test diagnostics
- Skip tests conditionally with `Skip = "reason"` in fact/theory attributes