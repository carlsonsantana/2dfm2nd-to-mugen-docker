"""Tests for the `.air` writer (fm2nd2mugen.air_writer)."""

from pathlib import Path

import pytest

from fm2nd2mugen.air_writer import build_actions, render_air, write_air
from fm2nd2mugen.air_writer import _ticks
from fm2nd2mugen.skill_reader import ImageFrame, SkillAnimation

# 0000-numbered sprites mapped 1:1; enough for the simple cases.
IDENTITY_MAP = {i: (0, i) for i in range(10)}


@pytest.mark.parametrize(
    "wait, expected",
    [(0, 0), (1, 1), (2, 1), (3, 2), (4, 2), (5, 3), (8, 5), (10, 6), (100, 60)],
)
def test_wait_rounds_independently_per_frame(wait: int, expected: int) -> None:
    # wait * 10ms / 16.667ms == wait * 0.6, rounded; wait 0 -> 0.
    assert _ticks(wait) == expected


@pytest.mark.parametrize(
    "turn_x, turn_y, expected_suffix",
    [(False, False, "0, 0, 0, 0, 1"), (True, False, "1"), (False, True, "1")],
)
def test_flip_param_appended_only_when_set(
    turn_x: bool, turn_y: bool, expected_suffix: str
) -> None:
    skill = SkillAnimation(0, "S", [ImageFrame(0, 0, 0, 1, turn_x, turn_y)])

    (frame,) = build_actions([skill], IDENTITY_MAP)[0].frames

    assert frame.flip == ("H" if turn_x else "") + ("V" if turn_y else "")


def test_render_matches_golden_with_non_identity_map() -> None:
    skills = [
        SkillAnimation(
            0,
            "Walk",
            [
                ImageFrame(1, 0, 0, 10, False, False),
                ImageFrame(2, 3, -4, 5, True, True),
            ],
        ),
        SkillAnimation(7, "Logic", []),
    ]
    # group 2 and renumbered images prove the writer reads placement from the map.
    sprite_map = {1: (2, 11), 2: (2, 12)}

    text = render_air(build_actions(skills, sprite_map))

    assert text == (
        "; MUGEN .air generated from a 2D Fighter Maker 2nd .player\n"
        "\n"
        '; Skill "Walk" (index 0)\n'
        "[Begin Action 0]\n"
        "Clsn2Default: 1\n"
        " Clsn2[0] = 1, 1, 1, 1\n"
        "2, 11, 0, 0, 6\n"
        "2, 12, 3, -4, 3, HV\n"
        "\n"
        '; Skill "Logic" (index 7): no frames, skipped\n'
    )


def test_group_and_image_come_from_map_not_hardcoded() -> None:
    skill = SkillAnimation(3, "S", [ImageFrame(5, 0, 0, 1, False, False)])

    (frame,) = build_actions([skill], {5: (4, 99)})[0].frames

    assert (frame.group, frame.image) == (4, 99)


def test_missing_image_index_is_fatal() -> None:
    skill = SkillAnimation(9, "Bad", [ImageFrame(99, 0, 0, 1, False, False)])

    with pytest.raises(ValueError, match="no sprite in the SFF map"):
        build_actions([skill], IDENTITY_MAP)


def test_write_air_creates_utf8_file_with_flattened_name(tmp_path: Path) -> None:
    # non-ASCII name + embedded newline: UTF-8 round-trips, comment stays one line.
    skill = SkillAnimation(0, "立ち\nガード", [ImageFrame(0, 0, 0, 1, False, False)])
    actions = build_actions([skill], IDENTITY_MAP)
    air_path = tmp_path / "out" / "char.air"

    write_air(actions, air_path)

    text = air_path.read_text(encoding="utf-8")
    assert text == render_air(actions)
    assert '; Skill "立ち ガード" (index 0)' in text  # newline flattened to a space
