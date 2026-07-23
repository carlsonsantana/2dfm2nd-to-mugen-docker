"""Tests for the character-JSON reader (fm2nd2mugen.skill_reader)."""

import json
from pathlib import Path

import pytest

from fm2nd2mugen.skill_reader import ImageFrame, SkillAnimation, load_skills


def _write_json(tmp_path: Path, document: object) -> Path:
    path = tmp_path / "char.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _i_block(i: int, x: int, y: int, wait: int, turn_x: bool, turn_y: bool) -> dict:
    return {
        "index": 1,
        "type": "I",
        "i": i,
        "x": x,
        "y": y,
        "wait": wait,
        "turnX": turn_x,
        "turnY": turn_y,
        "ignoreDirection": False,
    }


def test_keeps_only_i_blocks_in_document_order(tmp_path: Path) -> None:
    document = {
        "skills": [
            {
                "index": 12,
                "name": "Standing",
                "blocks": [
                    {"index": 0, "type": "Settings"},
                    _i_block(3, -2, 5, 10, True, False),
                    {"index": 2, "type": "M"},
                    _i_block(4, 0, 0, 0, False, True),
                ],
            }
        ]
    }

    skills = load_skills(_write_json(tmp_path, document))

    assert skills == [
        SkillAnimation(
            index=12,
            name="Standing",
            frames=[
                ImageFrame(3, -2, 5, 10, True, False),
                ImageFrame(4, 0, 0, 0, False, True),
            ],
        )
    ]


def test_frameless_skill_has_empty_frames(tmp_path: Path) -> None:
    document = {
        "skills": [
            {
                "index": 40,
                "name": "Dash cancel",
                "blocks": [{"index": 0, "type": "Settings"}, {"index": 1, "type": "C"}],
            }
        ]
    }

    (skill,) = load_skills(_write_json(tmp_path, document))

    assert skill.frames == []
    assert skill.name == "Dash cancel"


def test_preserves_all_skills(tmp_path: Path) -> None:
    document = {
        "skills": [
            {"index": 0, "name": "A", "blocks": [_i_block(1, 0, 0, 1, False, False)]},
            {"index": 1, "name": "B", "blocks": []},
        ]
    }

    skills = load_skills(_write_json(tmp_path, document))

    assert [s.index for s in skills] == [0, 1]


def test_rejects_non_list_skills(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="'skills' must be a list"):
        load_skills(_write_json(tmp_path, {"skills": {}}))


def test_rejects_i_block_missing_field(tmp_path: Path) -> None:
    bad = {"index": 1, "type": "I", "i": 3, "x": 0, "y": 0, "turnX": False}
    document = {"skills": [{"index": 0, "name": "X", "blocks": [bad]}]}

    with pytest.raises(ValueError, match="'wait' must be an int"):
        load_skills(_write_json(tmp_path, document))


def test_rejects_non_object_top_level(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="top-level object"):
        load_skills(_write_json(tmp_path, [1, 2, 3]))
