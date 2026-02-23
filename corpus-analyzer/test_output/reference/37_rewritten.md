---
type: reference
---

# sort_even Function Reference

This function takes a list `l` and returns a new list `l'`, such that `l'` is identical to `l` in odd indices, while its values at even indices are equal to the values of the even indices of `l`, but sorted.

## Function Signature
```python
def sort_even(l: list) -> list:
    ...
```

## Parameters
- `l` (list): The input list to be sorted.

## Return Value
A new list `l'` with the specified sorting criteria applied.

## Exceptions
None.

## Usage Examples
```python
>>> sort_even([1, 2, 3])
[1, 2, 3]
>>> sort_even([5, 6, 3, 4])
[3, 6, 5, 4]
```

## Description
The function first sorts the even values of the input list and then replaces the even indices of the original list with the sorted even values.

## Output Format / Reports
No specific output format is defined for this function.

## Success Criteria
- The function should correctly sort the even values in the input list while preserving the odd values.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/37.py]