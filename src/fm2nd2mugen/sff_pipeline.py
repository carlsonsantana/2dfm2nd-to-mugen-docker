"""Orchestrate one `.player` -> MUGEN `.sff`: parse, convert, build, place output."""

import shutil
from pathlib import Path

from fm2nd2mugen.bmp_to_png import convert_image_folder
from fm2nd2mugen.parser_runner import export_player_resources
from fm2nd2mugen.sprite_def_writer import build_sprite_entries, write_sprite_def
from fm2nd2mugen.sprmake_runner import build_sff
from fm2nd2mugen.wine_runner import RunWindowsTool, run_windows_tool


def convert_player_to_sff(
    player_file: Path,
    work_root: Path,
    output_root: Path,
    parser_dll: Path,
    sprmake2_exe: Path,
    run_tool: RunWindowsTool = run_windows_tool,
) -> Path:
    """Convert `player_file` into `<output_root>/<name>/<name>.sff`, returned.

    All intermediates land under `work_root/<name>/`; the def + PNGs share one
    directory so sprmake2's relative paths resolve cleanly under Wine.
    """
    name = player_file.stem
    work_dir = work_root / name
    resources = export_player_resources(player_file, work_dir, parser_dll)

    build_dir = work_dir / "png"
    pngs = convert_image_folder(resources.image_dir, build_dir)
    built_sff = _build_sff_in(build_dir, name, pngs, sprmake2_exe, run_tool)

    return _place_output(built_sff, output_root / name / f"{name}.sff")


def _build_sff_in(build_dir, name, pngs, sprmake2_exe, run_tool) -> Path:
    """Write the def next to the PNGs and build `<name>.sff` in `build_dir`."""
    def_file = build_dir / f"{name}-sff.def"
    write_sprite_def(build_sprite_entries(pngs), def_file, f"{name}.sff")
    return build_sff(def_file, build_dir / f"{name}.sff", sprmake2_exe, run_tool)


def _place_output(built_sff: Path, output_sff: Path) -> Path:
    """Copy the built SFF into the MUGEN character folder under /output."""
    output_sff.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_sff, output_sff)
    return output_sff
