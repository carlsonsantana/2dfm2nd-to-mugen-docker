# MUGEN tool: `sprmake2`

Reference for `sprmake2`, the official MUGEN 1.0 tool this project drives (under
Wine) to **build an SFF** from PNG source images. Source of truth: the tool's own
`--help` output and `mugen/docs/sprmake2.html` (SpriteMaker ver 2.00beta, Elecbyte
2009). Its reverse — extracting PNGs from an SFF for the round-trip test — is
[`sff2png`](sff2png-usage.md).

`sprmake2.exe` is a **32-bit x86 Windows binary** (ships with `Microsoft.VC90.CRT`
/ `Elecbyte.MUGEN.libs`, `processorArchitecture="x86"`), so Wine must be able to
run 32-bit PE code. It is mounted at runtime under `/mugen` and never
redistributed in the image.

## SFF background

- Sprites live in `.sff` files ("SFFs"), which may also embed palettes.
- MUGEN 1.0 uses **SFF v2**. `sprmake2` builds SFF v2 from **PNG** source images.
- MUGEN 1.0 can load both SFF v1 and v2; we only produce v2.

## `sprmake2` — build an SFF

### CLI

```
Usage: sprmake2 [options] [-o <out_file>] <in_file>
Options: c - automatically crop images and adjust axes
         f - link duplicate files
         o - override output filename
         p - link duplicate successive palettes
         q - quiet mode (except warnings & errors)
         Q - very quiet mode (no errors)
         v - verbose mode (reports linked/cropped/etc sprites and palettes)
         V - very verbose mode (reports everything)
         txt2def - convert in_file (sff1 .txt) to out_file (sff2 .def)

e.g. sprmake2 -c -f -n file.def
```

`<in_file>` is the **definition file** (a `.def`) describing how to assemble the
source PNGs into an SFF. Example:

```
sprmake2.exe -o chars\kfm\kfm.sff work\kfm\kfm-sff.def
```

The output filename can be given either via `-o` or the `filename =` key in the
def's `[Output]` section.

### Definition file format

INI-style, parsed top to bottom. Sections: `[Output]`, `[Option]`, `[Pal]`,
`[Sprite]`. `[Option]` blocks may appear any number of times and change the state
applied to the `[Sprite]`/`[Pal]` lines that follow. `;` starts a comment.

**`[Output]`**
- `filename = <path>` — SFF file to create (required unless `-o` is used).

**`[Option]`** (all optional; defaults shown)
- `input.dir =` — directory to read source files from. Defaults to the def's own
  directory.
- `sprite.compress.5 = none|lz5|rle5` — compression for 32-color sprites.
- `sprite.compress.8 = none|rle8` — compression for 256-color sprites (lossless).
- `sprite.compress.24 = none` — (rle16/rle24 not available).
- `sprite.decompressonload = 0|1`.
- `sprite.detectduplicates = 0|1`.
- `sprite.autocrop = 0|1` — **0 = do not crop** (default), 1 = auto-crop before
  adding. We use **0** to preserve exact dimensions/pixel positions.
- `pal.detectduplicates = 0|1`.
- `pal.discardduplicates = 0|1`.
- `pal.reverseact = 0|1`, `pal.reversepng = 0|1` — reverse color order on load.
- `sprite.usepal = -1 | group,item` — palette applied to following sprites.
  `-1` = "autopal": add and use each sprite's **own** embedded palette. A
  `group,item` value makes sprites share an already-added palette (their own
  palette data is discarded).
- `sprite.removecolors = -1 | start,end` — remove a color range; `-1` disables.

**`[Pal]`** — palette entries. Accepts `.act`, `.pcx`, `.png` (palette extracted).
Format: `group,itemno, fname, startcol,endcol`. Character palettes are `1,1`–`1,6`.

**`[Sprite]`** — sprite entries. Accepts **8-bit `.png`**.
Format: `group,itemno, fname, axisx, axisy` with an optional inline
`? usepal = <value>` override.
- `axisx, axisy` = the sprite's axis, measured from the **upper-left corner** of
  the bitmap (the point that maps to the sprite's on-screen draw position).

Annotated excerpt from `kfm-sff.def`:

```
[Output]
filename = chars/kfm/kfm.sff

[Option]
sprite.compress.8 = rle8
sprite.autocrop = 1
pal.detectduplicates = 1
pal.discardduplicates = 1

[Pal]
1,1, kfm.act, 0,255
1,2, kfm2.act, 0,255

[Option]
sprite.usepal = -1   ;autopal: use each sprite's own palette

[Sprite]
9000, 1, f-faceb.png, 0, 0 ? usepal = -1

[Option]
sprite.usepal = 1,1  ;these sprites share palette (1,1)

[Sprite]
9000, 0, f-face.png,  0,  0
   0, 0, stand00.png, 18,105
   0, 1, stand01.png, 18,104
```

### How this project uses it

Per `CLAUDE.md` conventions, for the SFF-building task:

- Each FM2nd image index `N` → `[Sprite]` line `0, N, <N>.png, 0, 0` (group 0,
  image = flat index, axis `0,0`; frame offsets are handled later in `.air`).
- `sprite.autocrop = 0` — faithful, no cropping.
- `sprite.usepal = -1` — each PNG carries its own palette (the `img/` exports all
  share global palette 0; `pal.detectduplicates`/`discardduplicates` collapse the
  copies). Embedded-palette sprites (`paletteType == 1`) also just carry their own
  palette, so no special-casing is needed.
- `sprite.compress.8 = none` (or `rle8`; both are lossless for pixels).

## Verifying the result

The reverse tool [`sff2png`](sff2png-usage.md) explodes an SFF back into PNGs; the
round-trip test uses it to confirm `sprmake2` preserved every sprite's pixels.
