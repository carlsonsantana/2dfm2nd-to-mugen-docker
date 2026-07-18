# CLAUDE.md

Guidance for working in this repository.

## Purpose

This project is a **containerized converter that turns 2D Fighter Maker 2nd
(FM2nd) characters into MUGEN 1.0 characters**. It processes **every FM2nd
`.player` file found in the `/input` volume**, producing one complete MUGEN 1.0
character folder (`.def`/`.cns`/`.cmd`/`.air`/`.sff`/`.snd`/`.act`) per input.

The heavy lifting is split by data type:

- **Binary artifacts** (SFF sprites, SND sounds) are built with **MUGEN's own
  official tools**, run under **Wine** because they are Windows executables.
- **Text and JSON artifacts** (`.air`, `.act`, `.def`/`.cns`/`.cmd`) are
  generated with **Python** scripts.

## Architecture

Everything runs inside a **single combined Docker image** (extends the existing
`Dockerfile`): it builds the `fm2ndparser` submodule in a .NET build stage, then
a runtime stage layers the .NET runtime + Python + Wine so one entrypoint can run
the whole pipeline.

The entrypoint discovers every `.player` in `/input` and runs the pipeline below
on each one:

```
each .player in /input
  (1) fm2ndparser   [.NET, in-image]   → JSON + indexed BMP (img/, 1/–7/) + WAV
  (2) Python        transform JSON      → .air, .act, .def/.cns/.cmd skeleton
  (3) Wine + MUGEN tools (/mugen)       → build .sff from sprites, .snd from sounds
  (4) assemble MUGEN character folder   → /output/<name>/
```

### Volume contract

| Mount     | Role |
|-----------|------|
| `/input`  | Holds the FM2nd `.player` files to convert; every `.player` found here is processed. |
| `/output` | The generated MUGEN character folder is written to `/output/<name>/`. |
| `/mugen`  | A full MUGEN 1.0 install **including its official tools** (e.g. `sprmake2`). The tools are invoked from here via Wine. |

The MUGEN engine and its official tools are **never redistributed in the image** —
they are mounted at runtime under `/mugen`. If they are absent, the binary-build
steps cannot run.

## Core principles

- **Target engine: MUGEN 1.0** — SFF v2 sprites and 1.0 syntax for all text files.
- **Prefer MUGEN's official tools (via Wine) for binary files** (SFF, SND); use
  **Python for JSON/text**. Do not reimplement SFF/SND writers in Python.
- **One `.player` → one MUGEN character**, batched over every `.player` in
  `/input`. Stages, demos, and `.kgt` cascade conversion are out of scope for now.
- **Milestone: assets + animation first.** Faithfully convert sprites, sounds,
  animations (`.air` with Clsn1/Clsn2), and palettes (`.act`), plus a **minimal
  playable skeleton** `.def`/`.cns`/`.cmd`. Full gameplay logic is deferred (see
  [Status](#status--future-work)).

## The `fm2ndparser` submodule

`fm2ndparser/` is a git submodule (a .NET tool). Initialize it before building:

```bash
git submodule update --init
```

It reads FM2nd binary files and, with `-x`, exports embedded resources:

- **JSON** describing the character (skills = ordered blocks, commands, settings,
  palettes, resource metadata).
- **Indexed 8-bit BMP** sprites under `img/` (global palette 0) plus palette-swap
  folders `1/`–`7/` (global palettes 1–7).
- **Sounds** (`.wav`/`.mid`/`.cda`) under `snd/`.

**Rely on the submodule's own documentation as the source of truth** for the input
formats — do not guess field names or layouts:

- `fm2ndparser/README.md`
- `fm2ndparser/docs/cli-usage.md` — invocation, flags, output location.
- `fm2ndparser/docs/output-formats.md` — resource folder layout, indexed-BMP and
  palette handling, sound export.
- `fm2ndparser/docs/json-spec.md` — full field-by-field JSON schema, every block
  type, and enums.

## Conversion conventions

These conventions define how FM2nd concepts map onto MUGEN. Follow them unless the
submodule docs contradict an assumption here.

### Sprites (SFF)

- Every FM2nd image → SFF **group 0**, image number = the FM2nd flat index (1:1).
  FM2nd images are a shared pool referenced by skills, so a flat shared numbering
  is both simplest and faithful.
- Sprite pixel data comes from the `img/` BMPs (global palette 0) exported by
  `fm2ndparser -x`.

### Palettes (ACT)

- Global palette 0 → the SFF's default palette (`pal1`).
- Global palettes 1–7 → MUGEN `.act` files, referenced as `pal2`–`pal8` in the
  `.def`.
- Sprites with an **embedded** palette (`paletteType == 1`) keep their own
  per-sprite palette (allowed by SFF v2); they do not participate in the swaps.

### Animations (AIR)

- Each FM2nd **skill** → one `[Begin Action N]`, where `N = skill.index`.
- Each `I` block → one animation frame:
  - sprite `(0, i)` (group 0, image `I.i`),
  - offset from `I.x` / `I.y` (apply FM2nd→MUGEN coordinate conversion),
  - `time = I.wait`,
  - H-flip from `I.turnX`, V-flip from `I.turnY`.
- `FA` blocks → `Clsn1` (attack) boxes; `FD` blocks → `Clsn2` (hurt) boxes,
  attached to the frame they accompany.
- Non-`I` logic blocks (movement `M`, cancels `C`, commands `COM`, reactions `R`,
  gauges, AI, …) are **ignored in `.air`** for this milestone.

### Sounds (SND)

- Flat WAV index → `.snd` group 0, index = the FM2nd sound index.
- `S`-block sound triggers are wired up later, with the deferred gameplay logic.

## Build & run

Build the combined image and initialize the submodule first:

```bash
git submodule update --init
docker build -t fm2nd2mugen .
```

Run the conversion — mount a directory of `.player` files as `/input`, an output
directory, and the MUGEN install. Every `.player` in `/input` is converted:

```bash
docker run --rm \
  -v /path/to/players:/input:ro \
  -v /path/to/output:/output \
  -v /path/to/mugen:/mugen:ro \
  fm2nd2mugen
```

Under the hood, stage (1) invokes the parser roughly as:

```bash
dotnet /opt/fm2ndparser/Fm2ndParser.dll <file> -x
```

which writes `<basename>.json` and the `<basename>/` resource folder relative to
the current working directory (see `fm2ndparser/docs/cli-usage.md`).

## Status / future work

- **Current focus:** assets + animation + a minimal playable skeleton.
- **Deferred:** full gameplay-logic translation — FM2nd movement (`M`), cancels
  (`C`), command states (`COM`), reactions (`R`), gauges, and CPU/AI into MUGEN
  statedefs/CNS. Many FM2nd constructs have no clean MUGEN equivalent; expand
  coverage incrementally.
- The **Python code structure and dependencies are not yet designed** — decide
  them when that code is written; keep the "MUGEN tools for binary, Python for
  text" split.

## Code style

- Functions: 4-20 lines. Split if longer.
- Files: under 500 lines. Split by responsibility.
- One thing per function, one responsibility per module (SRP).
- Names: specific and unique. Avoid `data`, `handler`, `Manager`.
  Prefer names that return <5 grep hits in the codebase.
- Types: explicit. No `any`, no `Dict`, no untyped functions.
- No code duplication. Extract shared logic into a function/module.
- Early returns over nested ifs. Max 2 levels of indentation.
- Exception messages must include the offending value and expected shape.

## Comments

- Keep your own comments. Don't strip them on refactor — they carry
  intent and provenance.
- Write WHY, not WHAT. Skip `// increment counter` above `i += 1`.
- Docstrings on public functions: intent + one usage example.
- Reference issue numbers / commit SHAs when a line exists because
  of a specific bug or upstream constraint.

## Dependencies

- Inject dependencies through constructor/parameter, not global/import.
- Wrap third-party libs behind a thin interface owned by this project.
- Use requirements.txt to list all dependencies.
- Use `virtualenv` to install dependencies locally, but don't use it in the container.

## Structure

- Follow the python convention.
- Prefer small focused modules over god files.
- Predictable paths: controller/model/view, src/lib/test, etc.

## Formatting

- Use the language default formatter (`black`). Don't discuss style beyond that.
