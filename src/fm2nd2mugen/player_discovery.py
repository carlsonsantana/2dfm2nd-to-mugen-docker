"""Discover the FM2nd `.player` files to convert inside the input volume."""

from pathlib import Path


def find_player_files(input_dir: Path) -> list[Path]:
    """Return every FM2nd `.player` file under `input_dir`, sorted by path.

    Matches case-insensitively and searches recursively, honouring the volume
    contract that "every `.player` found in /input is processed".

    Example:
        >>> find_player_files(Path("/input"))
        [PosixPath('/input/ryu.player')]
    """
    if not input_dir.is_dir():
        raise NotADirectoryError(
            f"input dir is not a directory: {input_dir!s} "
            f"(expected a readable directory of .player files)"
        )
    players = [path for path in input_dir.rglob("*") if _is_player_file(path)]
    return sorted(players)


def _is_player_file(path: Path) -> bool:
    """True when `path` is a regular file with a `.player` extension (any case)."""
    return path.is_file() and path.suffix.lower() == ".player"
