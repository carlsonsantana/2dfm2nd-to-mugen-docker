"""Round-trip integration test: .player -> .sff -> sff2png PNGs vs reference BMPs.

Runs the real pipeline (dotnet fm2ndparser + Wine sprmake2), explodes the built
SFF with the official MUGEN `sff2png` tool, and asserts each PNG matches the
sprite fm2ndparser originally exported. Requires the container toolchain and a
MUGEN install mounted at /mugen; opt in with `pytest --run-integration`.
"""

import os
import shutil
from pathlib import Path

import pytest

from _roundtrip_compare import assert_png_matches_reference, parse_sprite_def
from fm2nd2mugen.character_pipeline import convert_player_to_character
from fm2nd2mugen.wine_runner import run_windows_tool

FIXTURES = Path(__file__).parent / "fixtures" / "roundtrip"
PLAYER = FIXTURES / "character.player"
EXPECTED_SPRITE_COUNT = 2  # character.player exports exactly two images


def _tool_path(env_var: str, default: str) -> Path:
    """Resolve a MUGEN/parser tool path from env, failing loudly if absent.

    The test only runs under `--run-integration`, so a missing tool is a hard
    error (you opted in) rather than a silent skip.
    """
    path = Path(os.environ.get(env_var, default))
    if not path.is_file():
        raise FileNotFoundError(
            f"{env_var} tool not found at {path!s}; mount /mugen and the parser "
            f"(or set {env_var}) — required when running with --run-integration"
        )
    return path


@pytest.mark.integration
def test_sff_roundtrip_matches_reference_bmps(tmp_path: Path) -> None:
    parser_dll = _tool_path("FM2ND_PARSER_DLL", "/opt/fm2ndparser/Fm2ndParser.dll")
    sprmake2_exe = _tool_path("FM2ND_SPRMAKE2", "/mugen/sprmake2.exe")
    sff2png_exe = _tool_path("FM2ND_SFF2PNG", "/mugen/sff2png.exe")

    artifacts = convert_player_to_character(
        PLAYER, tmp_path / "work", tmp_path / "out", parser_dll, sprmake2_exe
    )
    sff = artifacts.sff_path

    # the same run also emits the .air beside the .sff
    assert artifacts.air_path.is_file()
    assert "[Begin Action" in artifacts.air_path.read_text(encoding="utf-8")

    explode_dir = tmp_path / "rt"
    pngs = _explode_sff(sff, sff2png_exe, explode_dir)
    assert len(pngs) == EXPECTED_SPRITE_COUNT, (
        f"expected {EXPECTED_SPRITE_COUNT} exploded PNGs, "
        f"got {sorted(p.name for p in pngs)}"
    )

    for sprite in parse_sprite_def(explode_dir / "spr-sff.def"):
        assert_png_matches_reference(
            explode_dir / sprite.png_name, FIXTURES / f"{sprite.image:04d}.bmp"
        )


def _explode_sff(sff: Path, sff2png_exe: Path, out_dir: Path) -> list[Path]:
    """Run sff2png on a local copy of the SFF, keeping all paths relative.

    Mirrors the sprmake2 pattern: run from the tool's own cwd with bare
    filenames so no Unix<->Wine path translation is needed. sff2png writes
    `spr<NNN>.png` plus a `spr-sff.def` describing each PNG's (group, image).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    local_sff = out_dir / sff.name
    shutil.copy2(sff, local_sff)
    run_windows_tool(sff2png_exe, [local_sff.name, "spr"], out_dir)
    return sorted(out_dir.glob("spr*.png"))
