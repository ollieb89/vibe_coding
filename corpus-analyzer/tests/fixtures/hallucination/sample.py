"""Sample Python file for testing chunking."""

import os
from typing import Any


class SampleClass:
    """A sample class for testing."""

    def __init__(self, value: int) -> None:
        """Initialize with a value."""
        self.value = value

    def get_value(self) -> int:
        """Return the value."""
        return self.value


def sample_function(x: int) -> int:
    """A sample function."""
    return x * 2


if __name__ == "__main__":
    obj = SampleClass(10)
    print(obj.get_value())
