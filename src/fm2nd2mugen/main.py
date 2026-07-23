"""Entrypoint: convert every `.player` in the input volume into a MUGEN character.

Paths follow the volume contract (/input, /output, /mugen) and can be overridden
with environment variables for local runs. This milestone builds the SFF + AIR; the
rest of the character folder is assembled by later stages.
"""

import os
import sys
from pathlib import Path

from fm2nd2mugen.character_pipeline import convert_player_to_character
from fm2nd2mugen.fm2nd.player_discovery import find_player_files

INPUT_DIR = Path(os.environ.get("FM2ND_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("FM2ND_OUTPUT_DIR", "/output"))
WORK_ROOT = Path(os.environ.get("FM2ND_WORK_DIR", "/tmp/fm2nd-build"))
PARSER_DLL = Path(
    os.environ.get("FM2ND_PARSER_DLL", "/opt/fm2ndparser/Fm2ndParser.dll")
)
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
    """Convert a single `.player`, reporting the resulting SFF + AIR paths."""
    print(f"  {player_file.name} -> building SFF + AIR ...")
    artifacts = convert_player_to_character(
        player_file, WORK_ROOT, OUTPUT_DIR, PARSER_DLL, SPRMAKE2_EXE
    )
    print(f"    wrote {artifacts.sff_path} and {artifacts.air_path}")


if __name__ == "__main__":
    raise SystemExit(main())
