# 08 — Graphics formats

All sizes below are after CrunchMania; regenerate the tree with
`python tools/crm.py -a _work/files -o _work/unpacked`, then
`python tools/assets.py _work/unpacked`. The full inventory is in
[`notes/asset-inventory.md`](../notes/asset-inventory.md).

Everything the game draws is **8-bit chunky**. The only planar data on the disc
is the six `pics/` screens, which are the front end.

## `pics/` — 7-bitplane screens, ByteRun1 inside CrunchMania

Twelve files: six images and six palettes.

```
offset 0   UWORD  width in pixels
offset 2   UWORD  height in rows
offset 4   UWORD  bitplanes
offset 6   UWORD  0
offset 8   ULONG  bitmap size = width/8 * height * planes
offset 12  IFF ByteRun1 (PackBits) stream
```

The bitmap is interleaved planar: `planes` consecutive rows of `width/8` bytes
per display line, which is what the copper's `BPL1MOD = 6 * 40` requires.

| File | Bytes | w | h | Planes | Declared bitmap | ByteRun1 gives |
|---|---:|---:|---:|---:|---:|---|
| `blackmagic` | 15,365 | 320 | 240 | 7 | 67,200 | exact |
| `combat` | 62,475 | 320 | 232 | 7 | 64,960 | exact |
| `gothic` | 59,932 | 320 | 240 | 7 | 67,200 | exact |
| `hell` | 59,592 | 320 | 240 | 7 | 67,200 | exact |
| `spacehulk` | 62,286 | 320 | 240 | 7 | 67,200 | exact |
| `theend` | 54,621 | 320 | 256 | 7 | 71,680 | exact |

All six unpack to their declared size to the byte, which is the check that the
layout is right. **The disc therefore compresses these twice**: an IFF run-length
encoder inside a Huffman-plus-LZ cruncher. On `blackmagic` — the publisher's
logo, mostly black — the run-length layer alone takes 67,200 bytes to 15,353,
because a blank 40-byte plane row encodes as the two bytes `d9 00`.

`tools/pic.py` decodes and renders one:

```
python tools/pic.py _work/unpacked/pics/spacehulk _work/files/pics/spacehulk.pal -o out.png
```

### `pics/*.pal` — 128 entries of an AGA `LOCT` pair

512 bytes, and **not** 256 twelve-bit colours. Each entry is two big-endian
words: the first carries the high nibble of each gun, the second the low, which
is exactly how AGA's `BPLCON3.LOCT` pair is written and exactly how the copper
builder at hunk `0x9c3c` reads them (see
[07-display-and-akiko.md](07-display-and-akiko.md)).

```
gothic     entry 2 = 0fff 0fff  ->  R=ff G=ff B=ff
spacehulk  entry 1 = 0110 000c  ->  R=10 G=10 B=0c
```

Read as 256 single words the picture renders as noise. Read as pairs it renders.
The first 32 entries of `gothic`, `hell`, `combat` and `theend` are the Deluxe
Paint default 16-colour palette with every nibble doubled — a tell that the
artwork came out of DPaint and never had its top end touched, which the credits
(`RENDERED IN DPAINT3 AND DPAINT4`) agree with.

## `txts/` — chunky texture banks

Fourteen wall banks and six floor/ceiling tiles.

**Wall banks** (`txt1_0`..`txt1_4`, `txt3_1`..`txt3_4`, `txt4_1`..`txt4_3`):

```
offset 0    ULONG  offset of the palette
offset 4    N x 4160 bytes: one texture each
            4160 = 65 x 64  -- 64 rows of 65 bytes, or 64 columns of 65
palette     UWORD x N: 12-bit $0RGB, 0xFFFF = an unused slot
```

4,160 is the size the loader itself uses: the texture-bank loader at hunk
`0x9f24` reads eight names out of a list, loads each, and walks the result with
`move.l #$1040,d1` (4,160) twenty times (`moveq #$13,d0`).

| File | Bytes | Textures | Palette words | Used | `0xFFFF` |
|---|---:|---:|---:|---:|---:|
| `txt1_0` | 33,348 | 8 | 32 | 30 | 2 |
| `txt1_1` | 83,716 | 20 | **256** | **32** | **224** |
| `txt1_2` | 83,716 | 20 | 256 | 32 | 224 |
| `txt1_3` | 83,332 | 20 | 256 | 32 | 224 |
| `txt1_4` | 83,268 | 20 | 256 | 32 | 224 |
| `txt3_1` | 83,716 | 20 | 256 | 32 | 224 |
| `txt3_2` | 83,716 | 20 | 256 | 32 | 224 |
| `txt3_3` | 75,396 | 18 | 256 | 32 | 224 |
| `txt3_4` | 17,156 | 4 | 256 | 22 | 234 |
| `txt4_1` | 83,716 | 20 | 256 | 32 | 224 |
| `txt4_2` | 83,268 | 20 | 256 | 32 | 224 |
| `txt4_3` | 83,268 | 20 | 256 | 32 | 224 |

**Nine of the twelve banks declare a 256-entry palette and fill 32 of it.** The
other 224 slots are `FFFF FFFF FFFF …` all the way to the end of the file. That
is 448 bytes per bank, 5.4 KB across the disc, of a sentinel that means "empty" —
the same shape as Legends' `EMPTY PAL` slots, in a format that spells it in hex.
`txt3_4` fills only 22 of its 256, and the texels in it never exceed 31.

Texel values run 0–31 with a handful of exceptions: `txt1_1` uses `253` in 106
places, `txt3_3` uses `251`, `254` and `255`, `txt1_0` and `txt4_1` use `255`.
Those are out of range for the 32-entry palette and are markers of some kind;
what they mark is not settled here (see
[12-open-questions.md](12-open-questions.md)).

**Floors and ceilings** (`floor1`..`floor3`, `roof1`..`roof3`) are all exactly
16,448 bytes with no header at all:

```
16,384 bytes  chunky, 128 x 128
UWORD         31   (the colour count minus one)
UWORD x 31    12-bit $0RGB
```

Texel values in them never exceed 28, and `roof1` — a flat ceiling — packs from
16,448 bytes to **394**, the best ratio on the disc.

## `objs/` — chunky sprite banks

Twenty files, and the header is unusually informative:

```
offset 0   UWORD  log2(number of rotations)      3 -> 8, 0 -> 1
offset 2   UWORD  number of animation states
offset 4   UWORD  maximum frame width
offset 6   UWORD  maximum frame height
offset 8   ULONG  bytes of frame data
offset 12  ULONG x (2^rot * states)  offsets to the frames
frames:
   UWORD  x anchor      UWORD  y anchor
   UWORD  width         UWORD  height
   BYTE[width*height]   chunky, 0 = transparent
```

`2^rotations * states` equals the number of offsets in the table on all twenty
files, which is what confirms the first two fields:

| File | Rotations | States | Frames | Max w x h |
|---|---:|---:|---:|---|
| `player` | 8 | 5 | 40 | 33 x 63 |
| `marine` | 8 | 5 | 40 | 34 x 64 |
| `baldy` | 8 | 6 | 48 | 38 x 64 |
| `demon` | 8 | 6 | 48 | 40 x 67 |
| `lizard` | 8 | 6 | 48 | 44 x 65 |
| `phantom` | 8 | 6 | 48 | 46 x 71 |
| `troll` | 8 | 6 | 48 | 65 x 69 |
| `terra` | 8 | 5 | 40 | 71 x 64 |
| `ghoul` | 8 | 3 | 24 | 55 x 85 |
| `deathhead` | 8 | 3 | 24 | 55 x 55 |
| `dragon` | 8 | 4 | 32 | **155 x 91** |
| `tokens` | **1** | 6 | 6 | 25 x 25 |
| `baldy2` … `troll2` | **1** | 11–15 | 11–15 | up to 72 x 56 |

The `*2` files are the death animations: one viewpoint, eleven to fifteen frames,
no rotations — a corpse does not need eight angles. `tokens` is the pickups.
`dragon` is the largest asset on the disc at 340,456 bytes unpacked, 26 % of
everything.

## `maps/` — 42 levels

21 single-player (`map1_1`..`map1_7`, `map3_1`..`map3_7`, `map4_1`..`map4_7`) and
21 two-player arenas (`com1_1`..`com3_7`).

```
offset 0    ULONG x 29   section offsets  (the first is 116 = 29 * 4)
section 0   8,192 bytes  = 64 x 64 UWORDs -- the level grid
sections 1.. variable-length lists; an empty one is four bytes
```

**Every level file on the disc has exactly 29 sections and most of them are
empty.** `map1_1` fills ten and leaves nineteen at four bytes each; across the
42 maps the count of non-empty sections runs from 5 (`com1_1` and thirteen other
arenas) to 29 (`map3_6` alone). Sections 0, 1, 2, 4 and 5 are non-empty in all
42; sections 27 and 28 are used by one and two maps respectively. So the table
is a fixed-width index over a variable-length object list, not a set of unused
slots — a distinction worth making before calling anything a leftover.

Section 0, the grid, has 70 distinct values on `map1_1`, with `0xFFFF` among
them.

The level names come from `misc/script`, which addresses them as `play_map1_1`
and so on; the loader prefixes `maps/`. The combat arenas are built from a
template string `com1_1` at hunk `0x7e28` with the two digits patched in place.

## `misc/` — fonts and the script

`bigfont.bin` (10,820 bytes) and `smallfont.bin` (18,264) are offset tables
followed by fixed-size glyphs (260 and 204 bytes each). The character mapper is
in the executable at hunk `0x68c6` and maps `A`–`Z` to 9–34, `.` `!` `?` `,` to
36–39 and `0`–`9` to 0–9 — 40 glyphs, no lower case, and space handled
separately as a cursor advance.

`misc/script` is plain ASCII and is quoted in full in
[11-archaeology.md](11-archaeology.md).
