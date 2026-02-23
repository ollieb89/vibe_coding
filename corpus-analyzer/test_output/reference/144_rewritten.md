---
type: reference
---

# Simplify Function

This function takes two fractions represented as strings and returns `True` if their product is a whole number, otherwise it returns `False`. Both fractions have the following format: `<numerator>/<denominator>`, where both numerator and denominator are positive whole numbers. It's assumed that the given fractions are valid and do not have zero as the denominator.

## Function Signature
```python
def simplify(x, n):
    # ... (function body)
```

## Parameters
- `x`: A string representation of a fraction in the format `<numerator>/<denominator>`.
- `n`: A string representation of another fraction in the format `<numerator>/<denominator>`.

## Return Value
The function returns `True` if the product of the two input fractions is a whole number, otherwise it returns `False`.

## Exceptions
None. The function does not throw any exceptions.

## Usage Example
```python
simplify("1/5", "5/1")  # Returns True
simplify("1/6", "2/1")  # Returns False
simplify("7/10", "10/2")  # Returns False
```

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/144.py]