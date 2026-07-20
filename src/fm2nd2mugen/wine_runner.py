"""Thin project-owned wrapper for running the Windows MUGEN tools under Wine.

Isolating Wine behind one small interface keeps subprocess/Wine details out of the
pipeline and lets callers inject a fake in tests (see `RunWindowsTool`).
"""

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WineToolResult:
    """Captured outcome of one Wine tool invocation."""

    returncode: int
    stdout: str
    stderr: str


# Callable signature the pipeline depends on; `run_windows_tool` is the real impl.
RunWindowsTool = Callable[[Path, list[str], Path], WineToolResult]


def run_windows_tool(exe: Path, args: list[str], cwd: Path) -> WineToolResult:
    """Run `wine <exe> <args...>` in `cwd`, inheriting the image's Wine env.

    The container sets WINEPREFIX/HOME/WINEDEBUG/XDG_RUNTIME_DIR, so the child
    process inherits them; `cwd` is where the tool resolves relative paths.

    Example:
        >>> run_windows_tool(Path("/mugen/sprmake2.exe"), ["char-sff.def"], build_dir)
        WineToolResult(returncode=0, stdout=..., stderr=...)
    """
    command = ["wine", str(exe), *args]
    try:
        completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError as missing:
        raise RuntimeError(
            f"cannot run Wine: `wine` not found on PATH (needed to execute {exe!s})"
        ) from missing
    return WineToolResult(completed.returncode, completed.stdout, completed.stderr)
