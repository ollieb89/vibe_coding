---
type: reference
---

# remove_vowels Function Reference

The `remove_vowels` function takes a string as input and returns a new string with all vowels removed.

## Function Signature
```python
def remove_vowels(text):
    pass
```

## Parameters
- `text`: A string to be processed by the function.

## Return Value
The function returns a new string without any vowels.

## Exceptions
None.

## Usage Examples
```python
>>> remove_vowels('')
''
>>> remove_vowels("abcdef\nghijklm")
'bcdf\nghjklm'
>>> remove_vowels('abcdef')
'bcdf'
>>> remove_vowels('aaaaa')
''
>>> remove_vowels('aaBAA')
'B'
>>> remove_vowels('zbcd')
'zbcd'
```

## Implementation Details
The function uses a predefined string `vowels` to filter out the vowels from the input text.

```python
def remove_vowels(text):
    vowels = 'aeiouAEIOU'
    return ''.join(char for char in text if char not in vowels)
```

## Citation
[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/51.py]