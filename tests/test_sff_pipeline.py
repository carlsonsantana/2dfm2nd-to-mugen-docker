"""Wiring test for build_character_sff with a fake Wine runner.

Exercises the SFF stages (convert BMPs -> def -> build -> place) plus the returned
sprite_map, without needing dotnet or Wine. The parse is the orchestrator's job, so
here `resources` is constructed directly.
"""

from pathlib import Path

from fm2nd2mugen import sff_pipeline
from fm2nd2mugen.parser_runner import ExportedResources
from fm2nd2mugen.wine_runner import WineToolResult


def test_build_character_sff_wires_stages(tmp_path, make_indexed_bmp) -> None:
    name = "X"
    work_dir = tmp_path / "work" / name
    img_dir = work_dir / name / "img"
    img_dir.mkdir(parents=True)
    for i in range(3):
        make_indexed_bmp(img_dir / f"{i:04d}.bmp", (3, 3))
    resources = ExportedResources(work_dir / f"{name}.json", work_dir / name, img_dir)

    def _fake_sprmake(exe: Path, args: list[str], cwd: Path) -> WineToolResult:
        # def is <name>-sff.def; sprmake2 would emit <name>.sff beside it
        sff_name = Path(args[0]).stem.removesuffix("-sff")
        assert (cwd / args[0]).is_file()  # def written next to the PNGs
        assert sorted(p.name for p in cwd.glob("*.png")) == [
            "0000.png",
            "0001.png",
            "0002.png",
        ]
        (cwd / f"{sff_name}.sff").write_bytes(b"SFFv2-fake")
        return WineToolResult(0, "", "")

    output_root = tmp_path / "output"
    result = sff_pipeline.build_character_sff(
        resources,
        name,
        work_dir,
        output_root,
        Path("/mugen/sprmake2.exe"),
        run_tool=_fake_sprmake,
    )

    assert result.sff_path == output_root / name / f"{name}.sff"
    assert result.sff_path.read_bytes() == b"SFFv2-fake"
    # sprite_map carries the group explicitly so the AIR side never hardcodes it
    assert result.sprite_map == {0: (0, 0), 1: (0, 1), 2: (0, 2)}
