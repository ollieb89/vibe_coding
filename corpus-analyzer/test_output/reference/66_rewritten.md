---
type: reference
---

# Digit Sum Function Reference

This function takes a string as input and returns the sum of the ASCII codes for the uppercase characters in the string.

## Configuration Options
- `None`: This function does not require any configuration options.

## Function Signature
```python
def digitSum(s):
    """..."""
```

## Parameter Descriptions and Types
- `s` (string): The input string to be processed.

## Return Values and Exceptions
The function returns an integer representing the sum of the ASCII codes for the uppercase characters in the input string. If the input is not a string, a `TypeError` will be raised.

## Usage Examples
```python
digitSum("")  # Returns: 0
digitSum("abAB")  # Returns: 131
digitSum("abcCd")  # Returns: 67
digitSum("helloE")  # Returns: 69
digitSum("woArBld")  # Returns: 131
digitSum("aAaaaXa")  # Returns: 153
```

## Output Format / Reports
No specific output format is associated with this function.

## Success Criteria
- The function correctly calculates the sum of the ASCII codes for the uppercase characters in the input string.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/66.py]