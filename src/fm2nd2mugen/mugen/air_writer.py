"""Turn typed FM2nd skills into a MUGEN 1.0 `.air` (animation) file.

Mirrors `sprite_def_writer`'s build -> render -> write split. The mapping rules and
their current limits live in docs/air-mapping.md; the target format in
docs/mugen/air-format.md. Sprite placement is read from the `sprite_map` so the
group number is never hardcoded here.
"""

from dataclasses import dataclass
from pathlib import Path

from fm2nd2mugen.fm2nd.skill_reader import ImageFrame, SkillAnimation

# FM2nd waits in 10 ms units; MUGEN runs at 60 ticks/s (~16.667 ms/tick).
_FM2ND_WAIT_MS = 10.0
_MUGEN_TICK_MS = 1000 / 60

# Placeholder hurt box for every action until real FD boxes are converted; a
# deliberate zero-area "replace me" (see docs/air-mapping.md). No Clsn1 (attack).
_CLSN_COUNT = 1
_CLSN_BOX = "1, 1, 1, 1"

_HEADER = "; MUGEN .air generated from a 2D Fighter Maker 2nd .player"


@dataclass(frozen=True)
class AirFrame:
    """One resolved animation element (a rendered frame line)."""

    group: int
    image: int
    xoffset: int
    yoffset: int
    time: int
    flip: str  # "", "H", "V", or "HV"


@dataclass(frozen=True)
class AirAction:
    """One `[Begin Action]`. Empty `frames` marks a frameless (skipped) skill."""

    number: int
    name: str
    frames: list[AirFrame]


def build_actions(
    skills: list[SkillAnimation],
    sprite_map: dict[int, tuple[int, int]],
) -> list[AirAction]:
    """Resolve each skill's frames against `sprite_map` into renderable actions.

    Example:
        >>> build_actions(load_skills(json), {3: (0, 3)})
        [AirAction(number=12, name='Standing', frames=[AirFrame(...)])]
    """
    return [_action_from(skill, sprite_map) for skill in skills]


def render_air(actions: list[AirAction]) -> str:
    """Render the full `.air` text (header + one block per action)."""
    body = "\n\n".join(_render_action(action) for action in actions)
    return f"{_HEADER}\n\n{body}\n" if body else f"{_HEADER}\n"


def write_air(actions: list[AirAction], air_path: Path) -> None:
    """Render and write the `.air` to `air_path` in UTF-8.

    Example:
        >>> write_air(actions, Path("/output/ryu/ryu.air"))
    """
    air_path.parent.mkdir(parents=True, exist_ok=True)
    air_path.write_text(render_air(actions), encoding="utf-8")


def _action_from(
    skill: SkillAnimation, sprite_map: dict[int, tuple[int, int]]
) -> AirAction:
    """Map one skill to an `AirAction`, resolving every frame's sprite."""
    frames = [_frame_from(frame, sprite_map, skill) for frame in skill.frames]
    return AirAction(skill.index, skill.name, frames)


def _frame_from(
    frame: ImageFrame,
    sprite_map: dict[int, tuple[int, int]],
    skill: SkillAnimation,
) -> AirFrame:
    """Resolve one `I` block to an `AirFrame`; missing sprite is fatal."""
    placement = sprite_map.get(frame.image_index)
    if placement is None:
        raise ValueError(
            f"skill {skill.index} ({skill.name!r}) references image index "
            f"{frame.image_index}, which has no sprite in the SFF map"
        )
    group, image = placement
    return AirFrame(
        group=group,
        image=image,
        xoffset=frame.x,
        yoffset=frame.y,
        time=_ticks(frame.wait),
        flip=_flip(frame.turn_x, frame.turn_y),
    )


def _ticks(wait: int) -> int:
    """FM2nd wait (10 ms units) -> MUGEN ticks, independent per-frame rounding.

    `wait 0 -> 0`; never returns `-1` (reserved for loop/hold, which FM2nd lacks).
    """
    return round(wait * _FM2ND_WAIT_MS / _MUGEN_TICK_MS)


def _flip(turn_x: bool, turn_y: bool) -> str:
    """FM2nd turnX/turnY -> MUGEN flip param (`H`, `V`, `HV`, or empty)."""
    return ("H" if turn_x else "") + ("V" if turn_y else "")


def _render_action(action: AirAction) -> str:
    """Render one action: a comment for frameless skills, else the full block."""
    label = f'Skill "{_comment_safe(action.name)}" (index {action.number})'
    if not action.frames:
        return f"; {label}: no frames, skipped"
    lines = [
        f"; {label}",
        f"[Begin Action {action.number}]",
        f"Clsn2Default: {_CLSN_COUNT}",
        f" Clsn2[0] = {_CLSN_BOX}",
    ]
    lines += [_render_frame(frame) for frame in action.frames]
    return "\n".join(lines)


def _render_frame(frame: AirFrame) -> str:
    """Render one animation element line, appending the flip only when set."""
    line = (
        f"{frame.group}, {frame.image}, {frame.xoffset}, {frame.yoffset}, {frame.time}"
    )
    return f"{line}, {frame.flip}" if frame.flip else line


def _comment_safe(name: str) -> str:
    """Flatten a skill name to a single line so it can't break its comment."""
    return name.replace("\r", " ").replace("\n", " ")
