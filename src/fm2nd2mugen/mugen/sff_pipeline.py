"""Build a MUGEN `.sff` from a parsed `.player`'s sprites (SFF only).

Parsing the `.player` and assembling the rest of the character folder belong to
the orchestrator (`character_pipeline`); this module only turns exported sprites
into an SFF and reports the sprite lookup the `.air` writer needs.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from fm2nd2mugen.common.bmp_to_png import convert_image_folder
from fm2nd2mugen.common.wine_runner import RunWindowsTool, run_windows_tool
from fm2nd2mugen.fm2nd.parser_runner import ExportedResources
from fm2nd2mugen.mugen.sprite_def_writer import (
    SpriteEntry,
    build_sprite_entries,
    build_sprite_map,
    write_sprite_def,
)
from fm2nd2mugen.mugen.sprmake_runner import build_sff


@dataclass(frozen=True)
class SffBuildResult:
    """The built SFF plus the sprite lookup the `.air` writer consumes.

    `sprite_map` is `fm2nd_image_index -> (group, image)`; the AIR writer reads
    group/image from it so sprite numbering is never hardcoded downstream.
    """

    sff_path: Path
    sprite_map: dict[int, tuple[int, int]]


def build_character_sff(
    resources: ExportedResources,
    name: str,
    work_dir: Path,
    output_root: Path,
    sprmake2_exe: Path,
    run_tool: RunWindowsTool = run_windows_tool,
) -> SffBuildResult:
    """Build `<output_root>/<name>/<name>.sff` from already-parsed `resources`.

    Intermediates (PNGs + the sprmake2 def) land under `work_dir/png` so the def's
    relative paths resolve cleanly under Wine.

    Example:
        >>> build_character_sff(resources, "ryu", work, out, Path("/mugen/sprmake2.exe"))
        SffBuildResult(sff_path=.../ryu.sff, sprite_map={0: (0, 0), ...})
    """
    build_dir = work_dir / "png"
    pngs = convert_image_folder(resources.image_dir, build_dir)
    entries = build_sprite_entries(pngs)
    built_sff = _build_sff_in(build_dir, name, entries, sprmake2_exe, run_tool)
    sff_path = _place_output(built_sff, output_root / name / f"{name}.sff")
    return SffBuildResult(sff_path, build_sprite_map(entries))


def _build_sff_in(
    build_dir: Path,
    name: str,
    entries: list[SpriteEntry],
    sprmake2_exe: Path,
    run_tool: RunWindowsTool,
) -> Path:
    """Write the def next to the PNGs and build `<name>.sff` in `build_dir`."""
    def_file = build_dir / f"{name}-sff.def"
    write_sprite_def(entries, def_file, f"{name}.sff")
    return build_sff(def_file, build_dir / f"{name}.sff", sprmake2_exe, run_tool)


def _place_output(built_sff: Path, output_sff: Path) -> Path:
    """Copy the built SFF into the MUGEN character folder under /output."""
    output_sff.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_sff, output_sff)
    return output_sff
