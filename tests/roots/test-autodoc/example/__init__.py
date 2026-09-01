"""Example module for autodoc tests."""

from __future__ import annotations

from typing import ClassVar

from example.catalog.category import Category
from example.catalog.product import Product


class Greeter:
    """A friendly greeter.

    :icon: hand-wave
    :param name: The display name of the greeter.
    :param polite: Whether to use polite forms.
    """

    product: Product
    """Current product."""
    category: Category
    """Active category."""
    schema_version: ClassVar[str]

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
