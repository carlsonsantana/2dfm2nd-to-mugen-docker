"""Compare sff2png output PNGs against fm2ndparser's reference BMPs.

Round-trip verification helpers for test_sff_roundtrip.py. sff2png writes no
tRNS chunk and FM2nd uses the top-right-corner color as transparent, so the
transparent region is ignored; every other pixel must match within the 5-bit
color step. See docs/sff2png-usage.md and fm2ndparser/docs/output-formats.md.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

# Max per-channel difference for opaque pixels. FM2nd stores 5-bit channels
# (multiples of 8; white is 248 not 255), and PNG round-tripping through sff2png
# may expand them, so a logical color can shift by up to one 5-bit step. Mirrors
# ColorTolerance in fm2ndparser/Fm2ndParser.Tests/PlayerExportTests.cs.
COLOR_TOLERANCE = 8

Rgb = tuple[int, int, int]


@dataclass(frozen=True)
class SpriteRef:
    """One `[Sprite]` line from an sff2png `-sff.def`: group, image, PNG name."""

    group: int
    image: int
    png_name: str


def parse_sprite_def(def_path: Path) -> list[SpriteRef]:
    """Map each PNG back to its (group, image) from sff2png's `-sff.def`.

    Never assume `spr000.png` is image 0 — sff2png numbers PNGs in SFF storage
    order and records the real (group, image) in the `[Sprite]` section.

    Example:
        >>> parse_sprite_def(Path("rt/spr-sff.def"))
        [SpriteRef(group=0, image=0, png_name='spr000.png'), ...]
    """
    sprites: list[SpriteRef] = []
    in_sprites = False
    for raw in def_path.read_text().splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            in_sprites = line.lower() == "[sprite]"
            continue
        if in_sprites:
            sprites.append(_parse_sprite_line(line, def_path))
    if not sprites:
        raise ValueError(f"no [Sprite] entries found in {def_path!s}")
    return sprites


def _parse_sprite_line(line: str, def_path: Path) -> SpriteRef:
    """Parse a `group, image, fname, axisx, axisy` line into a SpriteRef."""
    fields = [f.strip() for f in line.split(",")]
    if len(fields) < 3:
        raise ValueError(
            f"malformed [Sprite] line {line!r} in {def_path!s} "
            f"(expected 'group, image, fname, axisx, axisy')"
        )
    return SpriteRef(int(fields[0]), int(fields[1]), Path(fields[2]).name)


def assert_png_matches_reference(actual_png: Path, reference_bmp: Path) -> None:
    """Assert sff2png PNG matches the reference BMP, ignoring transparent pixels.

    Same width/height required; opaque pixels must match within COLOR_TOLERANCE
    per channel; pixels whose reference color equals the top-right corner (the
    FM2nd transparent color) are skipped because sff2png does not preserve them.
    """
    with Image.open(reference_bmp) as ref_img, Image.open(actual_png) as got_img:
        reference = ref_img.convert("RGB")
        actual = got_img.convert("RGB")
    _assert_same_size(reference, actual, actual_png)
    _assert_pixels_close(reference, actual, actual_png)


def _assert_same_size(reference: Image.Image, actual: Image.Image, name: Path) -> None:
    """Fail with both sizes if the exported PNG differs in dimensions."""
    if reference.size != actual.size:
        raise AssertionError(
            f"{name.name}: size mismatch — reference {reference.size}, "
            f"exported {actual.size}"
        )


def _assert_pixels_close(
    reference: Image.Image, actual: Image.Image, name: Path
) -> None:
    """Compare every opaque pixel within tolerance; skip the transparent color."""
    width, height = reference.size
    transparent: Rgb = reference.getpixel((width - 1, 0))  # FM2nd transparent color
    ref_px = reference.load()
    got_px = actual.load()
    for y in range(height):
        for x in range(width):
            expected: Rgb = ref_px[x, y]
            if expected == transparent:
                continue  # sff2png writes no tRNS; transparent region may differ
            got: Rgb = got_px[x, y]
            if any(abs(e - g) > COLOR_TOLERANCE for e, g in zip(expected, got)):
                raise AssertionError(
                    f"{name.name}: pixel mismatch at ({x},{y}) — expected "
                    f"{expected} (±{COLOR_TOLERANCE}), got {got}"
                )
