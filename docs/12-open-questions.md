# 12 — Open questions

Each with the measurement beside it. An honest question is better than a
plausible answer.

## 1. Where does the renderer write the copper list?

**What is established.** The 3D view's framebuffer is a copper list, four bytes
per pixel, allocated `MEMF_CHIP` and double-buffered; the bitplanes hold a fixed
descending colour-index ramp; each row alternates between colour registers
0–127 and 128–255 through the `BPLCON3` bank field and `BPLCON4`'s `BPLAM`. All
of that comes from the constructor at hunk `0x9cde`–`0x9d90`, the ramp writer at
`0x9b64` and the per-row `WAIT` emitter at `0x9daa`, and the size formula
`4 * (width + (width-1)/32 + 3) * height` matches the copper instruction count
exactly ([07-display-and-akiko.md](07-display-and-akiko.md)).

**What is not.** The inner loop that writes the per-pixel colour values into
that list, once per frame, was not located. Searches for the obvious shapes came
back empty: no `move.w dN,(aM)` followed by `addq.l #4,aM` in the renderer, no
`lea $4(aN),aN`, no scaled-index writes with a `*4` extension word in code (the
seven matches are all inside data), no run of `move.l` to displacements 4, 8, 12,
16, 20. The likely reason is that Capstone cannot follow the renderer linearly —
about 30 % of the 174 KB hunk decodes as data, some of which is plainly
generated or dispatched-into, and every candidate address checked in the
`0x10000`–`0x22000` band turned out to be chunky pixel data.

**What would settle it.** An emulator trace with a write watchpoint on the
allocated copper buffer, which this pipeline does not have. Failing that,
following the `$30(a2)` stride field and the `$24(a2)` buffer pointer out of the
screen descriptor — neither is ever read through `a2`, so the structure is
passed in another register and the reads are not findable by a fixed-offset
grep.

## 1b. How much of a frame does writing the copper list actually take?

Everything in [07-display-and-akiko.md](07-display-and-akiko.md) under "what it
costs" is **static arithmetic, not a measurement**. What is established from the
call graph is that the copper *skeleton* is built once per screen and only the
data words move per frame — 16,200 bytes for the 90 x 90 view, 7,920 for the
66 x 60 one. What is not established is the share of the frame that goes into
writing them, or how badly the CPU is starved by a copper taking ~85 % of the
raster's DMA slots.

**The experiment is cheap and needs no disassembler.** The game exposes
`RESOLUTION` and `WINDOW SIZE` in its own front end and ships two view
geometries whose pixel counts differ by better than 2:1 (8,100 against 3,960).
Comparing frame times at 90 x 90 and 66 x 60 under a cycle-exact emulator
separates the per-pixel cost from the fixed per-frame cost in one measurement.
A debugger watchpoint on the allocated copper buffer plus a raster-line log
would then give the window in which the CPU does the writing, and would settle
open question 1 above at the same time.

The `FMODE = $000F` reading — that the widest AGA fetch mode is there to free
DMA slots for the copper rather than for display width — is an inference from
the same arithmetic and would fall out of the same trace.

## 2. Is the texture record row-major or column-major?

Each wall texture is **4,160 bytes = 65 x 64**, which is certain: the loader
walks the bank with `move.l #$1040,d1` twenty times. Rendered as 64 rows of 65
bytes it produces clean, correctly-oriented textures; rendered as 64 columns of
65 it produces clean textures that are the transpose. Machined panels, dials and
hazard stripes are close enough to symmetric that neither rendering is obviously
wrong.

A column-major layout is what a vertical-strip texture mapper wants, so it is
the better guess — but a guess is what it is. The 65th element of each row (or
column) takes only eight distinct values, all in the range 7–15, across a whole
bank, so it is not picture data; whether it is a wrap-around guard, a per-column
attribute or padding is unresolved.

## 3. What are texel values 251, 253, 254 and 255?

The wall banks use colour indices 0–31 and their palettes have 32 real entries.
Four values above that range occur, rarely and specifically:

| Bank | Value | Occurrences |
|---|---:|---:|
| `txt1_1` | 253 | 106 |
| `txt3_3` | 251 / 254 / 255 | 29 / 28 / 36 |
| `txt1_0` | 255 | 292 |
| `txt4_1` | 255 | 259 |
| `txt3_4` | none | — |

They index nothing in the bank's palette. Transparency, animation, a light
source, a switch or a door are all plausible; the disc does not say which.

## 4. Was there a second zone?

Measured: the campaigns are `1`, `3` and `4` in the map and texture names and
`tile_1`, `tile_2`, `tile_3` in the script; the two-player arenas are `com1`,
`com2`, `com3` with no gap; no `map2_*` or `txt2_*` file exists and no string in
any executable names one; the mission script has three campaigns and the front
end offers three (`play spacehulk series`, `play gothic tomb series`,
`play hell series`).

So the gap is in exactly the two families tied to campaigns and in neither of
the others. That is suggestive and it is not proof: a numbering that skips 2 is
equally consistent with a rename that was never applied. The checklist's
usual tell — a loader table with an `0xFFFF` row where an entry used to be, or a
presence flag the loader honours — is not present, because the texture-bank
loader tolerates an *empty name* in its list and simply stores zero
([08-graphics-formats.md](08-graphics-formats.md)), which is a mechanism that
leaves no trace of what is missing.

The floppy release would settle it in one `diff`.

## 5. Does the retail pressing have audio tracks?

The dump available here is a single data track with no cue sheet. The executable
never calls `OpenDevice`, never names `cd.device` and issues no `CD_PLAY*`
command, so **nothing on this disc would play a Red Book track if one existed**
([09-audio.md](09-audio.md)). Whether the pressing carries one anyway — as
Microcosm carries 203 seconds that nothing plays — cannot be answered from a
data-track-only image.

## 6. Does `StoreNV` really write two bytes?

The save path is `moveq #2,d0` into `StoreNV`; the load path copies five
longwords out of what `GetCopyNV` returns
([10-input-and-saves.md](10-input-and-saves.md)). Under Commodore's published
register conventions that is a two-byte store and a twenty-byte read. Both
numbers are unambiguous in the bytes; the conventions are taken from the
documentation and not verified against a disassembly of the ROM library. If they
are right, this is a live out-of-bounds read in a shipped retail game, and it
would be worth checking on Microcosm's ten-byte `MCOSM`/`core` record and
Liberation's four-vector usage whether either does the same.

## 7. What is the CrunchMania leeway word?

Offset 4 of the container is a word that is 0 on 98 of the 115 files and 2, 4,
8, 12, 14 or 20 on the other seventeen. The decoder reads it and discards it
(`tst.w (a0)+`). The seventeen non-zero ones are the largest sprite banks, the
larger sound effects and one module, which fits the usual meaning — the extra
headroom a stream needs to decrunch in place without the write pointer
overtaking the read pointer — but nothing on the disc uses the value, so nothing
on the disc confirms it.

## 8. Where does `blackmagic.pal` get its extra 136 bytes?

Five of the six `pics/*.pal` files ship raw at 512 bytes; `blackmagic.pal` is
packed to 376. Every other palette on the disc was left alone. It is one file
and 136 bytes, and it is the only asymmetry in the whole packing pass.

## 9. Is `CHAT MODE ENABLED` reachable?

The string, the hires text line, the character mapper, the keyboard table and
the modem dialler are all present and all consistent with a working feature. No
attempt was made here to determine whether the front end can reach it, or whether
it is only reachable when a remote link is up.

## 10. Which of the six screen descriptors the game actually offers

Six descriptors exist at hunk `0x5550`: one 320 x 248 at 1x1, one 90 x 90 at
2x2, and four 66 x 60 at 2x2 in two top/bottom pairs whose `y` differs by one
pixel. The front end has `RESOLUTION`, `WINDOW SIZE` and `FULL SCREEN WINDOW`
options and a two-player split screen, which accounts for the shapes, but which
menu item selects which descriptor — and why two of the split-screen pairs
differ by a single raster line — was not traced.

## 11. Is the 32-sector run a mastering constant or a coincidence?

Six discs from 772 to 255,552 sectors leave exactly 32 unclaimed zero sectors at
the end of the volume; Liberation, cut with the same ISOCD 1.04, leaves 232.
Gloom removes the last plausible confound (that 32 might scale with something)
by being 300 times smaller than Microcosm and still leaving 32. **What makes
Liberation different is still unexplained**, and it is the only question in this
list that a tenth disc is likely to answer for free.
