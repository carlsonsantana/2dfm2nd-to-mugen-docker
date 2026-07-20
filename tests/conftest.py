"""Shared test fixtures."""

from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

MakeIndexedBmp = Callable[..., Image.Image]


@pytest.fixture
def make_indexed_bmp() -> MakeIndexedBmp:
    """Return a factory that writes a small 8-bit indexed BMP with a known palette."""

    def _make(path: Path, size: tuple[int, int] = (4, 4)) -> Image.Image:
        width, height = size
        image = Image.new("P", size)
        palette: list[int] = []
        for i in range(256):
            palette.extend([i, (255 - i), (i * 2) % 256])
        image.putpalette(palette)
        image.putdata([(x + y) % 256 for y in range(height) for x in range(width)])
        image.save(path, format="BMP")
        return image

    return _make
