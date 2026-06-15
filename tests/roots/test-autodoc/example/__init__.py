"""Example module for autodoc tests."""

from __future__ import annotations

from example.nested.config import Config
from example.nested.settings import Settings


class Greeter:
    """A friendly greeter.

    :param name: The display name of the greeter.
    :param polite: Whether to use polite forms.
    """

    config: Config
    """Current client configuration."""
    settings: Settings
    """Active settings."""

    def __init__(self, name: str, polite: bool = True) -> None:
        self.name = name
        self.polite = polite

    def greet(self, target: str) -> str:
        """Greet a target.

        :param target: Who to greet.
        :returns: A greeting string.
        :raises ValueError: If target is empty.
        """
        if not target:
            raise ValueError("empty target")
        return f"Hello, {target}!"


def add(a: int, b: int) -> int:
    """Add two integers.

    :param a: First number.
    :param b: Second number.
    :returns: The sum.
    """
    return a + b
