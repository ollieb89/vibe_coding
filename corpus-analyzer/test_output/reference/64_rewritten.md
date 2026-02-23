---
type: reference
---

# Vowels Count Function

Write a function `vowels_count` which takes a string representing a word as input and returns the number of vowels in the string. Vowels in this case are 'a', 'e', 'i', 'o', 'u'. Here, 'y' is also a vowel, but only when it is at the end of the given word.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/64.py]

## Function Signature
```python
def vowels_count(s):
    ...
```

## Parameters and Types
- `s`: `str` - The input string to be processed.

## Return Values and Exceptions
The function returns an integer representing the count of vowels in the given string. No exceptions are thrown.

## Usage Examples
```python
>>> vowels_count("abcde")
2
>>> vowels_count("ACEDY")
3
```

## Function Description
The function iterates through each character in the input string and checks if it is a vowel. If the character is found in the predefined set of vowels, the count is incremented. Additionally, if the string ends with 'y' or 'Y', an extra vowel count is added to the total.

## Example Implementation
```python
def vowels_count(s):
    vowels = 'aeiouAEIOU'
    count = 0
    for char in s:
        if char in vowels:
            count += 1
    if s and s[-1] in 'yY':
        count += 1
    return count