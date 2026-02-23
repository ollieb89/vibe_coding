---
type: reference
---

# Parse Nested Parentheses (parse_nested_parens)

This function takes a string as input, where each group of nested parentheses is separated by spaces. The function returns a list containing the deepest level of nesting for each group of parentheses.

## Configuration Options
- `paren_string`: A string representing multiple groups for nested parentheses separated by spaces.

## Function Signature
```python
def parse_nested_parens(paren_string: str) -> List[int]:
    ...
```

## Parameter Descriptions and Types
- `paren_string` (str): A string representing multiple groups for nested parentheses separated by spaces.
- Return Value (List[int]): A list containing the deepest level of nesting for each group of parentheses.

## Usage Examples
```python
parse_nested_parens('(()()) ((())) () ((())()())')  # Returns [2, 3, 1, 3]
```

## Exceptions
The function does not throw any exceptions in the provided code.

## Return Values
The function returns a list containing the deepest level of nesting for each group of parentheses.

## Output Format / Reports
Not applicable as this is a standalone function and does not produce reports or outputs.

## Success Criteria
- The function correctly identifies the deepest level of nesting for each group of parentheses in the input string.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/6.py]