---
type: reference
---

# check_if_last_char_is_a_letter

Create a function that returns `True` if the last character of a given string is an alphabetical character and is not part of a word, and `False` otherwise. Note: "word" is a group of characters separated by space.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/134.py]

## Function Signature
```python
def check_if_last_char_is_a_letter(txt: str) -> bool:
    ...
```

## Parameters
- `txt (str)`: The input string to be checked.

## Return Values
- `True` if the last character of the input string is an alphabetical character and not part of a word, otherwise `False`.

## Exceptions
None

## Usage Examples
```python
check_if_last_char_is_a_letter("apple pie") ➞ False
check_if_last_char_is_a_letter("apple pi e") ➞ True
check_if_last_char_is_a_letter("apple pi e ") ➞ False
check_if_last_char_is_a_letter("") ➞ False
```

## Function Body
```python
def check_if_last_char_is_a_letter(txt):
    if len(txt) == 0:
        return False

    last_char = txt[-1]

    if not last_char.isalpha():
        return False

    if len(txt) == 1:
        return True

    second_last_char = txt[-2]

    return second_last_char == ' '
```