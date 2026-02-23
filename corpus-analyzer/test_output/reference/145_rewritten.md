---
type: reference
---

# Order By Points

This function sorts a given list of integers in ascending order according to the sum of their digits. If there are several items with similar sum of their digits, they are ordered based on their index in the original list.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/145.py]

## Function Signature

```python
def order_by_points(nums):
    ...
```

## Parameters and Types

- `nums`: list of integers

## Return Values and Exceptions

The function returns a sorted list of integers. If the input is not a list or contains non-integer elements, it will raise a `TypeError`.

## Usage Examples

```python
>>> order_by_points([1, 11, -1, -11, -12]) == [-1, -11, 1, -12, 11]
True
>>> order_by_points([]) == []
True
```

## Additional Information

The function uses a helper method `digit_sum(n)` to calculate the sum of the digits of an integer. This method first converts the absolute value of the input into a string, then iterates through each digit in the string and adds or subtracts it based on its position (0 for negative numbers). The total sum is returned at the end.

```python
def digit_sum(n):
    ...