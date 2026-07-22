# MUGEN format: `.air`

Reference for the MUGEN 1.0 **Animation (`.air`)** format this project generates.
Source of truth: Elecbyte's `mugen/docs/air.html` (MUGEN 1.0). This document
describes the format only — how FM2nd characters are mapped onto it is a project
concern, kept separately in [`docs/air-mapping.md`](../air-mapping.md).

## What an `.air` file is

- An `.air` file is a list of **actions**. Each action is an ordered sequence of
  **animation elements** (frames) plus optional **collision boxes**.
- Each action has a number. Other files reference actions by that number (e.g. a
  state in the `.cns` plays `anim = 200`), so the numbering is the contract.
- MUGEN runs animation timing in **ticks**; the engine runs at **60 ticks per
  second** (one tick ≈ 16.667 ms).

## Action header

An action begins with a header naming its number `N`:

```
[Begin Action N]
```

Everything until the next `[Begin Action ...]` belongs to action `N`.

## Animation elements (frames)

Each non-blank, non-`Clsn` line inside an action is one frame:

```
group, image, xoffset, yoffset, time [, flip [, blend]]
```

| Field     | Meaning |
|-----------|---------|
| `group`   | Sprite group number in the `.sff`. |
| `image`   | Sprite image number within that group. |
| `xoffset` | Horizontal shift of the sprite's axis, in pixels (positive = right). |
| `yoffset` | Vertical shift of the sprite's axis, in pixels (**positive = down**). |
| `time`    | Ticks to display this frame. `-1` = display until the action ends (see below). |
| `flip`    | Optional: `H` (horizontal), `V` (vertical), or `HV`. Omit for none. |
| `blend`   | Optional transparency, e.g. `A`, `S`, `AS256D256`. Omit for opaque. |

The offsets are applied relative to the sprite's **axis**, which is defined per
sprite in the `.sff` (not in the `.air`).

### Timing and looping

- A frame with `time ≥ 0` shows for that many ticks. `time = 0` is valid — a
  zero-tick frame.
- A frame with `time = -1` is shown until the action ends; it is only meaningful
  on the **last** frame and freezes the action there instead of looping.
- By **default an action loops** back to its first frame after the last one.
- A `LoopStart` line placed among the elements moves the loop point: after the
  last frame the action restarts from the element following `LoopStart` rather
  than from the top.

```
[Begin Action 0]
0, 0, 0, 0, 8
0, 1, 0, 0, 8
LoopStart
0, 2, 0, 0, 8
0, 3, 0, 0, 8
```

## Collision boxes (`Clsn`)

Two box types, each a list of axis-relative rectangles `x1, y1, x2, y2`:

- **`Clsn1`** — *attack* boxes. A frame carrying a `Clsn1` is actively hitting.
- **`Clsn2`** — *hurt* boxes. Where the character can be hit.

Boxes are declared **immediately before** the frame they apply to. The count is
given first, then each indexed box:

```
Clsn2: 1
 Clsn2[0] = -10, -60, 10, 0
0, 0, 0, 0, 8
```

### Default boxes

A `Clsn1Default` / `Clsn2Default` block declared at the top of an action applies
to **every** frame that does not carry its own boxes — convenient for a single
constant box across the whole action:

```
[Begin Action 0]
Clsn2Default: 1
 Clsn2[0] = -10, -60, 10, 0
0, 0, 0, 0, 8
0, 1, 0, 0, 8
```

## Comments

A semicolon `;` begins a comment that runs to the end of the line. Blank lines are
ignored.

```
; standing animation
[Begin Action 0]
0, 0, 0, 0, -1   ; single held frame
```
