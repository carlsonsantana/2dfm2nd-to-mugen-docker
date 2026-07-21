"""Shared test fixtures."""

from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

MakeIndexedBmp = Callable[..., Image.Image]


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add `--run-integration` so the container-only tests are opt-in."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests needing Wine/dotnet/MUGEN tools (container only)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip `@pytest.mark.integration` tests unless `--run-integration` is passed.

    They only pass inside the built image (real dotnet parser + Wine sprmake2 /
    sff2png with `/mugen` mounted), so the default host run auto-skips them.
    """
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(reason="needs --run-integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


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
