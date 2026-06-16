"""Category types for autodoc tests."""

from __future__ import annotations

from example.catalog.product import Product


class Category:
    """A product category."""

    featured: Product
    """The featured product for this category."""
