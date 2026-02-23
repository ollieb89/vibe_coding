---
type: reference
---

# Parse Music Notation

This function takes a string representing musical notes in a special ASCII format and returns a list of integers corresponding to how many beats each note lasts.

## Function Signature
```python
def parse_music(music_string: str) -> List[int]:
```

## Parameter Descriptions and Types
- `music_string` (str): A string representing musical notes in a special ASCII format.

## Return Values and Exceptions
The function returns a list of integers, where each integer represents the number of beats that the corresponding note lasts. If the input is an empty string, an empty list is returned.

## Usage Examples
```python
parse_music('o o| .| o| o| .| .| .| .| o o')
# Returns: [4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 4]
```

## Success Criteria
- The function correctly parses the musical notation and returns a list of integers representing the number of beats each note lasts.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/17.py]