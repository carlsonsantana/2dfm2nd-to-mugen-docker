"""Tests for build_sff (fm2nd2mugen.sprmake_runner) using a fake Wine runner."""

from pathlib import Path

import pytest

from fm2nd2mugen.sprmake_runner import SprmakeError, build_sff
from fm2nd2mugen.wine_runner import WineToolResult


def _fake_tool_writing(content: bytes):
    """Fake run_tool simulating sprmake2: writes `<name>.sff` next to the def."""

    def _run(exe: Path, args: list[str], cwd: Path) -> WineToolResult:
        name = Path(args[0]).stem.removesuffix("-sff")
        (cwd / f"{name}.sff").write_bytes(content)
        return WineToolResult(0, "", "")

    return _run


def _write_def(tmp_path: Path) -> Path:
    def_file = tmp_path / "X-sff.def"
    def_file.write_text("[Output]\nfilename = X.sff\n")
    return def_file


def test_build_sff_returns_output_when_created(tmp_path: Path) -> None:
    def_file = _write_def(tmp_path)

    result = build_sff(
        def_file, tmp_path / "X.sff", Path("/mugen/sprmake2.exe"),
        run_tool=_fake_tool_writing(b"SFF\0data"),
    )

    assert result == tmp_path / "X.sff"
    assert result.read_bytes() == b"SFF\0data"


def test_build_sff_raises_when_missing(tmp_path: Path) -> None:
    def_file = _write_def(tmp_path)

    def _run(exe, args, cwd) -> WineToolResult:
        return WineToolResult(1, "", "boom")

    with pytest.raises(SprmakeError, match="did not produce"):
        build_sff(def_file, tmp_path / "X.sff", Path("/mugen/sprmake2.exe"), run_tool=_run)


def test_build_sff_raises_when_empty(tmp_path: Path) -> None:
    def_file = _write_def(tmp_path)

    with pytest.raises(SprmakeError, match="did not produce"):
        build_sff(
            def_file, tmp_path / "X.sff", Path("/mugen/sprmake2.exe"),
            run_tool=_fake_tool_writing(b""),
        )
