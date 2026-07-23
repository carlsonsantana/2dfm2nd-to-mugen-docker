"""Orchestrate one `.player` -> a MUGEN character folder.

Owns the single parse of the `.player` (the shared source for every stage) and
delegates the artifact builds: SFF to `sff_pipeline`, `.air` to `air_writer`. This
module knows about all stages; each stage module stays about one artifact.

Milestone: SFF + AIR. The `.def`/`.cns`/`.cmd`/`.snd`/`.act` stages extend
`CharacterArtifacts` as they land.
"""

from dataclasses import dataclass
from pathlib import Path

from fm2nd2mugen.common.wine_runner import RunWindowsTool, run_windows_tool
from fm2nd2mugen.fm2nd.parser_runner import export_player_resources
from fm2nd2mugen.fm2nd.skill_reader import load_skills
from fm2nd2mugen.mugen.air_writer import build_actions, write_air
from fm2nd2mugen.mugen.sff_pipeline import build_character_sff


@dataclass(frozen=True)
class CharacterArtifacts:
    """The files produced for one character under `/output/<name>/`."""

    sff_path: Path
    air_path: Path


def convert_player_to_character(
    player_file: Path,
    work_root: Path,
    output_root: Path,
    parser_dll: Path,
    sprmake2_exe: Path,
    run_tool: RunWindowsTool = run_windows_tool,
) -> CharacterArtifacts:
    """Convert `player_file` into `<output_root>/<name>/` (SFF + AIR so far).

    Example:
        >>> convert_player_to_character(
        ...     Path("/input/ryu.player"), Path("/work"), Path("/output"),
        ...     Path("/opt/fm2ndparser/Fm2ndParser.dll"), Path("/mugen/sprmake2.exe"),
        ... )
        CharacterArtifacts(sff_path=.../ryu.sff, air_path=.../ryu.air)
    """
    name = player_file.stem
    work_dir = work_root / name
    resources = export_player_resources(player_file, work_dir, parser_dll)
    sff = build_character_sff(
        resources, name, work_dir, output_root, sprmake2_exe, run_tool
    )
    air_path = _write_character_air(
        resources.character_json, sff.sprite_map, sff.sff_path
    )
    return CharacterArtifacts(sff.sff_path, air_path)


def _write_character_air(
    character_json: Path,
    sprite_map: dict[int, tuple[int, int]],
    sff_path: Path,
) -> Path:
    """Write `<name>.air` beside the built SFF and return its path."""
    air_path = sff_path.with_suffix(".air")
    write_air(build_actions(load_skills(character_json), sprite_map), air_path)
    return air_path
