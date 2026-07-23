"""Convert fm2ndparser's indexed BMP sprites into the 8-bit PNG sprmake2 wants.

fm2ndparser exports 8-bit indexed BMP (global palette 0); `sprmake2` reads 8-bit
`.png`. This rewrites the container only: pixel indices and palette are preserved
unchanged, so the round-trip stays faithful.
"""

from pathlib import Path

from PIL import Image


def convert_indexed_bmp_to_png(bmp_file: Path, png_file: Path) -> None:
    """Rewrite one 8-bit indexed BMP as an 8-bit indexed PNG, palette intact.

    Raises if the source is not 8-bit indexed (Pillow mode ``P``), since that is
    the only format fm2ndparser produces and the only one this pipeline accepts.

    Example:
        >>> convert_indexed_bmp_to_png(Path("img/0000.bmp"), Path("png/0000.png"))
    """
    with Image.open(bmp_file) as image:
        if image.mode != "P":
            raise ValueError(
                f"expected 8-bit indexed BMP (Pillow mode 'P'), got mode "
                f"{image.mode!r} for {bmp_file!s}"
            )
        png_file.parent.mkdir(parents=True, exist_ok=True)
        image.save(png_file, format="PNG")


def convert_image_folder(bmp_dir: Path, png_dir: Path) -> list[Path]:
    """Convert every `NNNN.bmp` in `bmp_dir` to `NNNN.png` in `png_dir`.

    Returns the created PNG paths sorted by their numeric name. The stem is kept
    verbatim so the FM2nd flat index survives into the sprite numbering.
    """
    bmps = sorted(bmp_dir.glob("*.bmp"))
    if not bmps:
        raise FileNotFoundError(
            f"no .bmp sprites found in {bmp_dir!s} (expected fm2ndparser img/ output)"
        )
    pngs = []
    for bmp_file in bmps:
        png_file = png_dir / f"{bmp_file.stem}.png"
        convert_indexed_bmp_to_png(bmp_file, png_file)
        pngs.append(png_file)
    return pngs
