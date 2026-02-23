---
type: reference
---

# separate_paren_groups Function Reference [source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/1.py]

This function takes a string containing multiple groups of nested parentheses and returns a list of those groups, separated and properly balanced. The input string ignores any spaces.

## Function Signature
```python
def separate_paren_groups(paren_string: str) -> List[str]:
```

## Parameters
- `paren_string` (str): A string containing multiple groups of nested parentheses, ignoring spaces.

## Return Value
A list of strings containing the separated and properly balanced groups of parentheses.

## Exceptions
None in this implementation.

## Usage Example
```python
separate_paren_groups('( ) (( )) (( )( ))')  # Returns ['()', '(())', '(()())']
```

## Function Description
The function iterates through the input string, keeping track of the current group and its depth. When a closing parenthesis is encountered, if the depth reaches zero, the current group is added to the result list, and a new empty group is started. If the depth does not reach zero, the current group and the closing parenthesis are added to the current group.