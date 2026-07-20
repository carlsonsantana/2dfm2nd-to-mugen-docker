"""Build a MUGEN SFF v2 file by driving sprmake2.exe under Wine."""

from pathlib import Path

from fm2nd2mugen.wine_runner import RunWindowsTool, run_windows_tool


class SprmakeError(RuntimeError):
    """Raised when sprmake2 does not produce a usable SFF file."""


def build_sff(
    def_file: Path,
    expected_sff: Path,
    sprmake2_exe: Path,
    run_tool: RunWindowsTool = run_windows_tool,
) -> Path:
    """Run sprmake2 on `def_file` and return the built `expected_sff`.

    sprmake2 is invoked from the def file's own directory with the def's bare
    filename, so both the sprite lookups and the relative `[Output] filename` in
    the def resolve there (avoiding Unix<->Wine path issues). `run_tool` is
    injected so tests can substitute a fake. Wine's own exit code is unreliable,
    so success is judged by a non-empty output file.

    Example:
        >>> build_sff(build/"X-sff.def", build/"X.sff", Path("/mugen/sprmake2.exe"))
        PosixPath('.../X.sff')
    """
    result = run_tool(sprmake2_exe, [def_file.name], def_file.parent)
    if not expected_sff.is_file() or expected_sff.stat().st_size == 0:
        raise SprmakeError(
            f"sprmake2 did not produce {expected_sff!s} from {def_file!s} "
            f"(exit {result.returncode}). stdout: {result.stdout.strip()!r} "
            f"stderr: {result.stderr.strip()!r}"
        )
    return expected_sff
