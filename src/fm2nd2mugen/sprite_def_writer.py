"""Write the sprmake2 SFF definition (`.def`) that assembles the sprite PNGs.

See docs/mugen/sprmake2-usage.md for the def format. For this milestone every sprite
maps to group 0, image = the FM2nd flat index, axis (0,0); frame offsets belong to
the `.air` (a later task). autocrop is off and usepal is -1 so pixels and palette
round-trip faithfully.
"""

from dataclasses import dataclass
from pathlib import Path

SPRITE_GROUP = 0
SPRITE_AXIS_X = 0
SPRITE_AXIS_Y = 0


@dataclass(frozen=True)
class SpriteEntry:
    """One `[Sprite]` line: `group, image, filename, axis_x, axis_y`."""

    group: int
    image: int
    filename: str
    axis_x: int
    axis_y: int


def build_sprite_entries(png_files: list[Path]) -> list[SpriteEntry]:
    """Map `NNNN.png` sprite files to group-0 entries numbered by their index.

    The numeric stem (e.g. `0007.png` -> 7) becomes the MUGEN image number, so the
    FM2nd flat index survives 1:1.
    """
    if not png_files:
        raise ValueError("no sprite PNGs given; cannot build a sprmake2 def")
    return [_entry_for(png_file) for png_file in png_files]


def _entry_for(png_file: Path) -> SpriteEntry:
    """Build a group-0, axis-(0,0) entry from a numerically named PNG."""
    if not png_file.stem.isdigit():
        raise ValueError(
            f"sprite PNG name is not a numeric index: {png_file.name!r} "
            f"(expected e.g. '0007.png')"
        )
    return SpriteEntry(
        group=SPRITE_GROUP,
        image=int(png_file.stem),
        filename=png_file.name,
        axis_x=SPRITE_AXIS_X,
        axis_y=SPRITE_AXIS_Y,
    )


def render_sprite_def(
    entries: list[SpriteEntry],
    sff_filename: str,
    input_dir: Path | None = None,
) -> str:
    """Render the full sprmake2 def text for `entries` (see module docstring).

    When `input_dir` is None the `input.dir` line is omitted, so sprmake2 reads
    sprites from the def file's own directory (its documented default). This keeps
    every path relative and avoids Unix<->Wine path translation.
    """
    options = ["[Option]"]
    if input_dir is not None:
        options.append(f"input.dir = {input_dir}")
    options += ["sprite.compress.8 = none", "sprite.autocrop = 0", "sprite.usepal = -1"]
    header = ["[Output]", f"filename = {sff_filename}", "", *options, "", "[Sprite]"]
    lines = [
        f"{e.group}, {e.image}, {e.filename}, {e.axis_x}, {e.axis_y}" for e in entries
    ]
    return "\n".join(header + lines) + "\n"


def write_sprite_def(
    entries: list[SpriteEntry],
    def_path: Path,
    sff_filename: str,
    input_dir: Path | None = None,
) -> None:
    """Render and write the sprmake2 def to `def_path`.

    Example:
        >>> write_sprite_def(entries, Path("build/png/char-sff.def"), "char.sff")
    """
    def_path.parent.mkdir(parents=True, exist_ok=True)
    def_path.write_text(render_sprite_def(entries, sff_filename, input_dir))
