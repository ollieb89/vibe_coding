---
type: reference
---

# Car Race Collision

This function simulates a car race where n cars are driving left to right and another set of n cars are driving right to left on an infinitely long straight road. The function calculates the number of collisions that occur between these two sets of cars.

## Function Signature
```python
def car_race_collision(n: int) -> int:
    ...
```

## Parameters and Types
- `n`: An integer representing the number of cars in each direction.

## Return Values and Exceptions
- The function returns an integer, which is the total number of collisions that occur during the simulation.

## Usage Examples
1. To find the number of collisions when there are 5 cars in each direction:
```python
car_race_collision(5)
```

## Output Format / Reports
The function returns a single integer representing the total number of collisions.

## Success Criteria
- The output should be an integer that accurately represents the number of collisions based on the input value for `n`.

[source: skills/loki-mode/benchmarks/results/2026-01-05-00-49-17/humaneval-solutions/41.py]