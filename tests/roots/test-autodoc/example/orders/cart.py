"""Cart types for autodoc tests."""

from __future__ import annotations

from example.catalog.product import Product


class Cart:
    """A shopping cart."""

    last_added: Product
    """The most recently added product."""
