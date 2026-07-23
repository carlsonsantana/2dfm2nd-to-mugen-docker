"""Read the fm2ndparser character JSON into the typed slice the `.air` writer needs.

This is the only module that touches the raw JSON; everything downstream works on
the typed `SkillAnimation` / `ImageFrame` objects. Only `I` (image) blocks are kept
— see docs/air-mapping.md — and the schema is fm2ndparser/docs/json-spec.md.

The `I`/`skill.index` fields are `normal-only`: this reader assumes the parser ran
WITHOUT `--clean-up`, which would zero them.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_IMAGE_BLOCK_TYPE = "I"


@dataclass(frozen=True)
class ImageFrame:
    """One FM2nd `I` block — a single animation frame (fields per json-spec.md)."""

    image_index: int  # I.i, looked up in the sprite_map for its SFF (group, image)
    x: int  # I.x -> AIR xoffset
    y: int  # I.y -> AIR yoffset
    wait: int  # I.wait (10 ms units) -> AIR time
    turn_x: bool  # -> H flip
    turn_y: bool  # -> V flip


@dataclass(frozen=True)
class SkillAnimation:
    """One FM2nd skill reduced to its ordered animation frames.

    `frames` is empty for a pure-logic skill (no `I` blocks); the AIR writer emits a
    comment for it instead of a `[Begin Action]`.
    """

    index: int  # skill.index -> MUGEN action number
    name: str
    frames: list[ImageFrame]


def load_skills(character_json: Path) -> list[SkillAnimation]:
    """Load every skill from `character_json` as a typed `SkillAnimation`.

    Example:
        >>> load_skills(Path("work/ryu/ryu.json"))
        [SkillAnimation(index=0, name='Standing', frames=[ImageFrame(...)]), ...]
    """
    document = json.loads(character_json.read_text(encoding="utf-8"))
    top = _as_mapping(document, character_json, "top-level object")
    skills = _read_list(top, "skills", character_json)
    return [
        _skill_from(_as_mapping(raw, character_json, "skill"), character_json)
        for raw in skills
    ]


def _skill_from(raw: Mapping[str, object], source: Path) -> SkillAnimation:
    """Build a `SkillAnimation`, keeping only `I` blocks in document order."""
    frames = [
        _frame_from(_as_mapping(block, source, "block"), source)
        for block in _read_list(raw, "blocks", source)
        if _block_type(block) == _IMAGE_BLOCK_TYPE
    ]
    return SkillAnimation(
        index=_read_int(raw, "index", source),
        name=_read_str(raw, "name", source),
        frames=frames,
    )


def _frame_from(raw: Mapping[str, object], source: Path) -> ImageFrame:
    """Build one `ImageFrame` from an `I` block mapping."""
    return ImageFrame(
        image_index=_read_int(raw, "i", source),
        x=_read_int(raw, "x", source),
        y=_read_int(raw, "y", source),
        wait=_read_int(raw, "wait", source),
        turn_x=_read_bool(raw, "turnX", source),
        turn_y=_read_bool(raw, "turnY", source),
    )


def _block_type(block: object) -> str | None:
    """Return a block's `type` string, or None if it isn't a typed object."""
    if isinstance(block, Mapping):
        kind = block.get("type")
        return kind if isinstance(kind, str) else None
    return None


def _as_mapping(value: object, source: Path, what: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source!s}: expected {what} to be an object, got {value!r}")
    return value


def _read_list(raw: Mapping[str, object], key: str, source: Path) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{source!s}: field {key!r} must be a list, got {value!r}")
    return value


def _read_int(raw: Mapping[str, object], key: str, source: Path) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{source!s}: field {key!r} must be an int, got {value!r}")
    return value


def _read_str(raw: Mapping[str, object], key: str, source: Path) -> str:
    value = raw.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{source!s}: field {key!r} must be a string, got {value!r}")
    return value


def _read_bool(raw: Mapping[str, object], key: str, source: Path) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{source!s}: field {key!r} must be a bool, got {value!r}")
    return value
