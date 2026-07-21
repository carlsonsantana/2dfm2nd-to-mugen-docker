# MUGEN tool: `sff2png`

Reference for `sff2png`, the official MUGEN tool this project drives (under Wine)
to **explode an SFF back into PNGs** — the reverse of [`sprmake2`](sprmake2-usage.md)
and the basis of the round-trip test. Source of truth: the tool's own `-h` output
and observed behavior running it against `chars/kfm/kfm.sff` (there is **no
Elecbyte HTML doc** for this tool).

`sff2png.exe` is a **32-bit x86 Windows binary** (ships with `Microsoft.VC90.CRT`,
`processorArchitecture="x86"`), so Wine must be able to run 32-bit PE code. It is
mounted at runtime under `/mugen` and never redistributed in the image.

## What it does

`sff2png` (**SFF2PNG v0.2, 2010-07-12**, Elecbyte 2010) reads an SFF (v1 or v2) and
writes every sprite back out as a PNG, plus a `sprmake2`-compatible `.def` that
could rebuild the same SFF. The round-trip test uses it to explode our generated
`.sff` back into PNGs and compare them pixel-for-pixel against the source images.

## CLI

```
Usage: sff2png [options] <infilename[.sff]> <outfilestr>

Note: <outfilestr> should not have an extension.
Warning: SFF2PNG will overwrite files without confirmation.

Options:
 -h -?  Prints this help message
 -f[n]  Forces all files to have the palette of the nth frame (n defaults to 0)
```

- `<infilename[.sff]>` — the SFF to read (the `.sff` extension is optional).
- `<outfilestr>` — a **path prefix**, not a filename: no extension. Every output
  path is built by appending to this string, so `out/spr` yields `out/spr000.png`,
  `out/spr001.png`, …, `out/spr-sff.def`. The directory must already exist.

## Expected input

- An SFF file. SFF **v2** (what this project produces) and v1 are both accepted.
- Nothing else — palettes are read from inside the SFF.

## Expected output

Given `sff2png in.sff out/spr`:

1. **One PNG per sprite**, named `out/spr<NNN>.png` where `<NNN>` is a **zero-padded
   3-digit counter in SFF storage order** (`%s%03i.png`): `spr000.png`,
   `spr001.png`, … This counter is **not** the sprite's group/image number — for
   `kfm` the first file `spr000.png` is sprite `(9000, 1)`.
2. A companion **`out/spr-sff.def`** — a complete `sprmake2` def (with
   `[Output]`/`[Option]`/`[Pal]`/`[Sprite]` sections) mapping each PNG back to its
   sprite. The `[Sprite]` lines use the `sprmake2` sprite format:

   ```
   [Sprite]
   9000, 1, /abs/path/spr000.png,   0,  0     ; group, image, fname, axisx, axisy
   9000, 0, /abs/path/spr001.png,   0,  0
      0, 0, /abs/path/spr002.png,  18,105
   ```

   i.e. **`group, image, fname, axisx, axisy`** — the same 5-field layout
   `sprmake2` consumes (**not** `startcol,endcol`; that is the `[Pal]` format). The
   `fname` is written as the full `<outfilestr>` path; take its basename to find
   the PNG sitting next to the def.

Because the PNGs are numbered sequentially (SFF storage order), **always parse the
`[Sprite]` section of `-sff.def` to recover each PNG's `(group, image)`** rather
than assuming `spr000.png` is image 0.

## Palette / transparency behavior (important for the round-trip test)

- Output PNGs are **8-bit indexed** (Pillow mode `P`). Without `-f`, each PNG keeps
  its own sprite palette; `-f[n]` forces every PNG onto frame *n*'s palette.
- `sff2png` writes **no `tRNS` chunk** — it does not mark any index transparent.
  MUGEN's convention is that **palette index 0 is the transparent color**, but the
  PNG stores index 0 as an ordinary (usually opaque) color. So a transparent pixel
  comes out as *"index 0, opaque"*, whereas an image exported by other tools (e.g.
  the FM2nd reference PNGs) may mark the same pixel transparent via `tRNS`.
- Consequently, comparing an `sff2png` PNG against a reference PNG by naive RGBA is
  wrong: the same transparent region can be `(0,0,0,255)` in one and `(0,0,0,0)` in
  the other. The comparison must **normalize transparency first** — treat index 0
  (and any `tRNS`-transparent index) as "transparent", then require: both
  transparent, or same RGB. This is the "transparent color may differ" case.

## How this project uses it

The round-trip test (Task 7) runs:

```
sff2png /output/<name>/<name>.sff <work>/rt/spr
```

then parses `<work>/rt/spr-sff.def`'s `[Sprite]` section to map each `spr<NNN>.png`
to its `(0, image)`, and compares that PNG against the source image of the same
index with a transparency-normalized, pixel-exact check (same width, same height,
same color at every pixel; file size/compression ignored).
