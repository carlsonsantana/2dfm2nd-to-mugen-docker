# FM2nd → MUGEN `.air` mapping

How this project turns 2D Fighter Maker 2nd (FM2nd) skills into a MUGEN 1.0
animation (`.air`) file. The neutral MUGEN format is described in
[`docs/mugen/air-format.md`](mugen/air-format.md); the FM2nd JSON fields referenced
here are defined in `fm2ndparser/docs/json-spec.md`. This document is the source of
truth for the conversion **conventions and their current limits**.

Scope: this is the **assets + animation** milestone. Gameplay logic is out of
scope — see [Deferred](#deferred) for everything intentionally left out.

## Inputs

- The character JSON produced by `fm2ndparser -x` (an internal artifact — the user
  only ever supplies a `.player`). Read by `skill_reader`.
- The `sprite_map` returned by the SFF build: `fm2nd_image_index → (group, image)`.
  The `.air` writer looks every sprite up through this map and **never hardcodes a
  group number**, so a future change to sprite numbering flows through unchanged.

> **Requires "normal" parser output.** `skill.index`, `I.i`, `I.x`, `I.y`,
> `I.wait`, `turnX`, and `turnY` are all `normal-only` fields — `fm2ndparser
> --clean-up` zeroes them. The pipeline must run the parser **without**
> `--clean-up`, or every action collapses to frame 0 at offset 0.

## Actions

- Each FM2nd **skill** with **at least one `I` block** becomes one
  `[Begin Action N]`, where `N = skill.index`, verbatim. Indices are unique in the
  file, so no renumbering or de-duplication is done. Collisions with MUGEN's
  reserved action numbers are **not** handled in this milestone.
- Each populated action is preceded by a name header comment for readability:

  ```
  ; Skill "Standing" (index 12)
  [Begin Action 12]
  ```

- A skill with **no `I` blocks** (pure logic) produces **no action** — only a
  comment recording that it was skipped, so nothing is silently lost:

  ```
  ; Skill "Dash cancel" (index 40): no frames, skipped
  ```

## Frames

Each `I` block, in document order, becomes one animation element. Non-`I` blocks
(`Settings`, `M`, `C`, `R`, `FA`, `FD`, …) are ignored for framing.

| MUGEN field       | FM2nd source | Notes |
|-------------------|--------------|-------|
| `group`, `image`  | `I.i`        | Looked up in `sprite_map`. A missing index is **fatal** (raises) — never a dangling reference. |
| `xoffset`         | `I.x`        | **Provisional straight pass-through** (see below). |
| `yoffset`         | `I.y`        | Provisional straight pass-through. Both systems use Y-down. |
| `time`            | `I.wait`     | Converted, see [Timing](#timing). |
| `flip`            | `turnX` / `turnY` | `turnX → H`, `turnY → V`, both → `HV`, neither → omitted. |

### Timing

One FM2nd `wait` unit is 10 ms; one MUGEN tick is 1000/60 ≈ 16.667 ms. So:

```
time = round(I.wait * 0.6)
```

- Rounded **independently per frame** (no cumulative error carry). Simpler; a
  fraction of a tick of drift per frame is accepted for this milestone.
- `wait == 0 → time == 0` (kept as a zero-tick frame, not inflated to 1).
- The rounder never emits `-1` — that value is reserved for loop/hold semantics,
  which FM2nd does not express (see below).

### Offsets are provisional

FM2nd exports **no per-sprite axis**, so the `.sff` axis stays at `(0, 0)` and
`I.x`/`I.y` carry all positioning. They are currently passed through **unchanged**.
This is very likely to render the character uniformly shifted, because FM2nd's
origin convention differs from MUGEN's feet/center axis. The intended fix is a
**single** character-wide origin constant added to every frame once validated
against a real MUGEN render — deliberately not guessed at now.

## Collision boxes

Real hit/hurt boxes are **not** converted yet. Every action instead gets one
placeholder default hurt box and no attack boxes:

```
Clsn2Default: 1
 Clsn2[0] = 1, 1, 1, 1
```

- **`Clsn2` only, never `Clsn1`.** A `Clsn1` would mark the frame as actively
  attacking; stamping it on every frame (idle included) would be wrong.
- `1, 1, 1, 1` is a deliberate zero-area **placeholder** — valid syntax, obvious
  "replace me". It is not a functional hurt box.

## Looping

Frames are emitted as the raw FM2nd sequence with **MUGEN's default loop** — no
`-1`, no `LoopStart`. FM2nd has no hold-last-frame concept, and loop/transition
flow lives in the deferred logic blocks, so no loop semantics are invented here.

## Output

`<name>.air`, written in **UTF-8**, placed beside `<name>.sff` in the character's
`/output/<name>/` folder.

## Deferred

Intentionally out of scope for this milestone:

- Real `FA` → `Clsn1` and `FD` → `Clsn2` box conversion (placeholder box for now).
- The origin-constant offset correction (`I.x`/`I.y` pass through raw).
- `I.ignoreDirection` (facing behaviour), driven by state logic.
- Loop/hold/transition semantics, which live in the logic blocks.
- All non-`I` logic blocks (`M`, `C`, `R`, `COM`, gauges, AI, sound triggers).
- MUGEN reserved-action-number handling.
