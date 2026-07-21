"""Entrypoint: convert every `.player` in the input volume into a MUGEN `.sff`.

Paths follow the volume contract (/input, /output, /mugen) and can be overridden
with environment variables for local runs. This milestone builds only the SFF; the
rest of the character folder is assembled by later stages.
"""

import os
import sys
from pathlib import Path

from fm2nd2mugen.player_discovery import find_player_files
from fm2nd2mugen.sff_pipeline import convert_player_to_sff

INPUT_DIR = Path(os.environ.get("FM2ND_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("FM2ND_OUTPUT_DIR", "/output"))
WORK_ROOT = Path(os.environ.get("FM2ND_WORK_DIR", "/tmp/fm2nd-build"))
PARSER_DLL = Path(os.environ.get("FM2ND_PARSER_DLL", "/opt/fm2ndparser/Fm2ndParser.dll"))
SPRMAKE2_EXE = Path(os.environ.get("FM2ND_SPRMAKE2", "/mugen/sprmake2.exe"))


def main() -> int:
    players = find_player_files(INPUT_DIR)
    if not players:
        print(f"no .player files found under {INPUT_DIR}", file=sys.stderr)
        return 1
    print(f"converting {len(players)} character(s) from {INPUT_DIR}")
    for player_file in players:
        _convert_one(player_file)
    return 0


def _convert_one(player_file: Path) -> None:
    """Convert a single `.player`, reporting the resulting SFF path."""
    print(f"  {player_file.name} -> building SFF ...")
    sff = convert_player_to_sff(
        player_file, WORK_ROOT, OUTPUT_DIR, PARSER_DLL, SPRMAKE2_EXE
    )
    print(f"    wrote {sff} ({sff.stat().st_size} bytes)")


if __name__ == "__main__":
    raise SystemExit(main())
