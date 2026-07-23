"""Run the `fm2ndparser` .NET tool to export a `.player`'s JSON + resources."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExportedResources:
    """Filesystem paths produced by `fm2ndparser -x` for one `.player`.

    `image_dir` holds the global-palette-0 sprites (`0000.bmp`, `0001.bmp`, ...);
    `resource_dir` also contains the palette-swap folders `1/`-`7/` and `snd/`.
    """

    character_json: Path
    resource_dir: Path
    image_dir: Path


class ParserError(RuntimeError):
    """Raised when `fm2ndparser` fails or its expected output is missing."""


def export_player_resources(
    player_file: Path,
    work_dir: Path,
    parser_dll: Path,
) -> ExportedResources:
    """Export `player_file`'s JSON + indexed BMP/WAV resources into `work_dir`.

    `fm2ndparser` writes `<stem>.json` and `<stem>/` relative to its working
    directory, so it is invoked with `cwd=work_dir` (see fm2ndparser
    docs/cli-usage.md). `parser_dll` is injected so the caller owns the path.

    Example:
        >>> export_player_resources(
        ...     Path("/input/ryu.player"),
        ...     Path("/work/ryu"),
        ...     Path("/opt/fm2ndparser/Fm2ndParser.dll"),
        ... )
        ExportedResources(character_json=.../ryu.json, ...)
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    _invoke_parser(player_file, work_dir, parser_dll)
    resources = _resource_paths(player_file.stem, work_dir)
    _verify_export(resources, player_file)
    return resources


def _invoke_parser(player_file: Path, work_dir: Path, parser_dll: Path) -> None:
    """Run `dotnet <parser_dll> <player_file> -x` inside `work_dir`."""
    command = ["dotnet", str(parser_dll), str(player_file), "-x"]
    try:
        result = subprocess.run(command, cwd=work_dir, capture_output=True, text=True)
    except FileNotFoundError as missing:
        raise ParserError(
            f"cannot run fm2ndparser: `dotnet` not found on PATH "
            f"(needed to execute {parser_dll!s})"
        ) from missing
    if result.returncode != 0:
        raise ParserError(
            f"fm2ndparser failed (exit {result.returncode}) for {player_file!s}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def _resource_paths(stem: str, work_dir: Path) -> ExportedResources:
    """Build the expected output paths for a parsed `.player` named `stem`."""
    resource_dir = work_dir / stem
    return ExportedResources(
        character_json=work_dir / f"{stem}.json",
        resource_dir=resource_dir,
        image_dir=resource_dir / "img",
    )


def _verify_export(resources: ExportedResources, player_file: Path) -> None:
    """Fail loudly if the parser did not produce the JSON + image folder."""
    if not resources.character_json.is_file():
        raise ParserError(
            f"fm2ndparser produced no JSON for {player_file!s}: "
            f"expected file {resources.character_json!s}"
        )
    if not resources.image_dir.is_dir():
        raise ParserError(
            f"fm2ndparser produced no image folder for {player_file!s}: "
            f"expected directory {resources.image_dir!s}"
        )
