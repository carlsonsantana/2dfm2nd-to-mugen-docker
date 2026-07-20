"""Wiring test for convert_player_to_sff with fake parser + Wine runner.

Exercises the full orchestration (parse -> convert -> def -> build -> place) without
needing dotnet or Wine, by faking those two boundaries.
"""

from pathlib import Path

from fm2nd2mugen import sff_pipeline
from fm2nd2mugen.parser_runner import ExportedResources
from fm2nd2mugen.wine_runner import WineToolResult


def test_convert_player_to_sff_wires_stages(tmp_path, monkeypatch, make_indexed_bmp) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    player = input_dir / "X.player"
    player.write_bytes(b"stub")

    def _fake_export(player_file: Path, work_dir: Path, parser_dll: Path):
        img_dir = work_dir / player_file.stem / "img"
        img_dir.mkdir(parents=True)
        for i in range(3):
            make_indexed_bmp(img_dir / f"{i:04d}.bmp", (3, 3))
        return ExportedResources(work_dir / "X.json", work_dir / "X", img_dir)

    def _fake_sprmake(exe: Path, args: list[str], cwd: Path) -> WineToolResult:
        # def is <name>-sff.def; sprmake2 would emit <name>.sff beside it
        name = Path(args[0]).stem.removesuffix("-sff")
        assert (cwd / args[0]).is_file()  # def written next to the PNGs
        assert sorted(p.name for p in cwd.glob("*.png")) == ["0000.png", "0001.png", "0002.png"]
        (cwd / f"{name}.sff").write_bytes(b"SFFv2-fake")
        return WineToolResult(0, "", "")

    monkeypatch.setattr(sff_pipeline, "export_player_resources", _fake_export)

    output_root = tmp_path / "output"
    sff = sff_pipeline.convert_player_to_sff(
        player,
        tmp_path / "work",
        output_root,
        Path("/opt/fm2ndparser/Fm2ndParser.dll"),
        Path("/mugen/sprmake2.exe"),
        run_tool=_fake_sprmake,
    )

    assert sff == output_root / "X" / "X.sff"
    assert sff.read_bytes() == b"SFFv2-fake"
