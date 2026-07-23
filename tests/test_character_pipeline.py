"""Offline wiring test for convert_player_to_character (SFF + AIR).

Fakes the two external boundaries (dotnet parser, Wine sprmake2) so the whole
orchestration — parse -> SFF + sprite_map -> AIR beside the SFF — runs on the host.
"""

import json
from pathlib import Path

from fm2nd2mugen import character_pipeline
from fm2nd2mugen.fm2nd.parser_runner import ExportedResources
from fm2nd2mugen.common.wine_runner import WineToolResult

_CHARACTER_JSON = {
    "skills": [
        {
            "index": 5,
            "name": "Idle",
            "blocks": [
                {"index": 0, "type": "Settings"},
                {
                    "index": 1,
                    "type": "I",
                    "i": 0,
                    "x": 0,
                    "y": 0,
                    "wait": 10,
                    "turnX": False,
                    "turnY": False,
                    "ignoreDirection": False,
                },
                {
                    "index": 2,
                    "type": "I",
                    "i": 1,
                    "x": 2,
                    "y": -3,
                    "wait": 5,
                    "turnX": True,
                    "turnY": False,
                    "ignoreDirection": False,
                },
            ],
        },
        {"index": 9, "name": "Logic", "blocks": [{"index": 0, "type": "C"}]},
    ]
}


def test_convert_player_to_character_writes_sff_and_air(
    tmp_path, monkeypatch, make_indexed_bmp
) -> None:
    player = tmp_path / "input" / "PL.player"
    player.parent.mkdir()
    player.write_bytes(b"stub")

    def _fake_export(player_file: Path, work_dir: Path, parser_dll: Path):
        stem = player_file.stem
        img_dir = work_dir / stem / "img"
        img_dir.mkdir(parents=True)
        for i in range(3):
            make_indexed_bmp(img_dir / f"{i:04d}.bmp", (3, 3))
        character_json = work_dir / f"{stem}.json"
        character_json.write_text(json.dumps(_CHARACTER_JSON), encoding="utf-8")
        return ExportedResources(character_json, work_dir / stem, img_dir)

    def _fake_sprmake(exe: Path, args: list[str], cwd: Path) -> WineToolResult:
        sff_name = Path(args[0]).stem.removesuffix("-sff")
        (cwd / f"{sff_name}.sff").write_bytes(b"SFFv2-fake")
        return WineToolResult(0, "", "")

    monkeypatch.setattr(character_pipeline, "export_player_resources", _fake_export)
    output_root = tmp_path / "output"

    artifacts = character_pipeline.convert_player_to_character(
        player,
        tmp_path / "work",
        output_root,
        Path("/opt/fm2ndparser/Fm2ndParser.dll"),
        Path("/mugen/sprmake2.exe"),
        run_tool=_fake_sprmake,
    )

    assert artifacts.sff_path == output_root / "PL" / "PL.sff"
    assert artifacts.air_path == output_root / "PL" / "PL.air"
    assert artifacts.sff_path.read_bytes() == b"SFFv2-fake"

    air = artifacts.air_path.read_text(encoding="utf-8")
    assert '; Skill "Idle" (index 5)' in air
    assert "[Begin Action 5]" in air
    assert "0, 0, 0, 0, 6" in air  # i=0, wait 10 -> 6 ticks, no flip
    assert "0, 1, 2, -3, 3, H" in air  # i=1, wait 5 -> 3 ticks, turnX -> H
    assert '; Skill "Logic" (index 9): no frames, skipped' in air
