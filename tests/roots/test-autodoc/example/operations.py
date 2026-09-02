"""Operation helpers for autodoc tests."""

from __future__ import annotations


def parse_check_image_file(response: object) -> bool:
    """Parse an image-file check response.

    :param response: Response to parse.
    :returns: Whether the image-file check passed.
    """
    return bool(response)
