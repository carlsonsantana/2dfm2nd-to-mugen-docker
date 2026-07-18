"""Tests for the indexed BMP -> 8-bit PNG conversion (fm2nd2mugen.bmp_to_png)."""

from pathlib import Path

import pytest
from PIL import Image

from fm2nd2mugen.bmp_to_png import convert_image_folder, convert_indexed_bmp_to_png


def _write_indexed_bmp(path: Path, size: tuple[int, int]) -> Image.Image:
    """Create a small 8-bit indexed BMP with a known palette + pixel indices."""
    width, height = size
    image = Image.new("P", size)
    # A distinctive, non-greyscale palette so a mangled table is obvious.
    palette = []
    for i in range(256):
        palette.extend([i, (255 - i), (i * 2) % 256])
    image.putpalette(palette)
    image.putdata([(x + y) % 256 for y in range(height) for x in range(width)])
    image.save(path, format="BMP")
    return image


def test_conversion_preserves_size_indices_and_palette(tmp_path: Path) -> None:
    bmp = tmp_path / "0000.bmp"
    source = _write_indexed_bmp(bmp, (7, 5))

    png = tmp_path / "0000.png"
    convert_indexed_bmp_to_png(bmp, png)

    with Image.open(png) as result:
        assert result.mode == "P"
        assert result.size == source.size
        assert result.tobytes() == source.tobytes()  # identical pixel indices
        assert result.getpalette()[:768] == source.getpalette()[:768]


def test_rejects_non_indexed_image(tmp_path: Path) -> None:
    rgb = tmp_path / "truecolor.bmp"
    Image.new("RGB", (4, 4), (10, 20, 30)).save(rgb, format="BMP")

    with pytest.raises(ValueError, match="mode 'P'"):
        convert_indexed_bmp_to_png(rgb, tmp_path / "out.png")


def test_convert_image_folder_maps_every_bmp(tmp_path: Path) -> None:
    bmp_dir = tmp_path / "img"
    bmp_dir.mkdir()
    for name in ("0000.bmp", "0001.bmp", "0002.bmp"):
        _write_indexed_bmp(bmp_dir / name, (3, 3))

    pngs = convert_image_folder(bmp_dir, tmp_path / "png")

    assert [p.name for p in pngs] == ["0000.png", "0001.png", "0002.png"]
    assert all(p.is_file() for p in pngs)


def test_convert_image_folder_errors_when_empty(tmp_path: Path) -> None:
    empty = tmp_path / "img"
    empty.mkdir()

    with pytest.raises(FileNotFoundError, match="no .bmp sprites"):
        convert_image_folder(empty, tmp_path / "png")
