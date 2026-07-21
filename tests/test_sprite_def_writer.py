"""Tests for the sprmake2 def writer (fm2nd2mugen.sprite_def_writer)."""

from pathlib import Path

import pytest

from fm2nd2mugen.sprite_def_writer import (
    SpriteEntry,
    build_sprite_entries,
    render_sprite_def,
    write_sprite_def,
)


def test_build_entries_number_by_stem() -> None:
    pngs = [Path("png/0000.png"), Path("png/0007.png"), Path("png/0042.png")]

    entries = build_sprite_entries(pngs)

    assert entries == [
        SpriteEntry(0, 0, "0000.png", 0, 0),
        SpriteEntry(0, 7, "0007.png", 0, 0),
        SpriteEntry(0, 42, "0042.png", 0, 0),
    ]


def test_build_entries_rejects_non_numeric_name() -> None:
    with pytest.raises(ValueError, match="numeric index"):
        build_sprite_entries([Path("png/portrait.png")])


def test_build_entries_rejects_empty() -> None:
    with pytest.raises(ValueError, match="no sprite PNGs"):
        build_sprite_entries([])


def test_render_has_faithful_options_and_sprite_lines() -> None:
    entries = [SpriteEntry(0, 0, "0000.png", 0, 0), SpriteEntry(0, 1, "0001.png", 0, 0)]

    text = render_sprite_def(entries, "char.sff", Path("/work/png"))

    assert "[Output]\nfilename = char.sff" in text
    assert "input.dir = /work/png" in text
    assert "sprite.autocrop = 0" in text  # no cropping -> faithful dimensions
    assert "sprite.usepal = -1" in text  # each sprite keeps its own palette
    assert "sprite.compress.8 = none" in text
    assert "0, 0, 0000.png, 0, 0" in text
    assert "0, 1, 0001.png, 0, 0" in text


def test_render_omits_input_dir_by_default() -> None:
    text = render_sprite_def([SpriteEntry(0, 0, "0000.png", 0, 0)], "char.sff")

    assert "input.dir" not in text  # defaults to the def file's own directory
    assert "sprite.autocrop = 0" in text


def test_write_creates_file(tmp_path: Path) -> None:
    entries = [SpriteEntry(0, 0, "0000.png", 0, 0)]
    def_path = tmp_path / "build" / "char-sff.def"

    write_sprite_def(entries, def_path, "char.sff", tmp_path / "png")

    assert def_path.is_file()
    assert def_path.read_text().endswith("0, 0, 0000.png, 0, 0\n")
