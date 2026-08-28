# 00 — Overview

**Gloom**, Black Magic Software / Guildhall Leisure Services, 1995, Amiga CD32.

One `MODE1/2048` data track of **772 declared sectors — 1.58 MB**, which is the
smallest volume this pipeline has seen by a factor of three. 131 files in seven
directories. 115 of the 131 are packed with a cruncher no disc here had met
before. There is no `c/`, no `libs/`, no `devs/`; the boot script is three lines
and every command it names sits in the root.

## The disc in one table

| | |
|---|---|
| Image | 1,949,696 bytes = 952 sectors |
| Declared volume | **772 sectors** = 1,581,056 bytes; 180 zero sectors of overrun |
| Tracks supplied | one data track only; no cue sheet, no audio track in this dump |
| PVD system identifier | `CDTV` — as on every disc here |
| PVD volume identifier | `GLOOM` |
| PVD application / publisher / volume-set id | **all empty** |
| Data preparer | ` - ISOCD 1.04 by Pantaray, Inc. USA -` — **empty name**, tool signature only |
| Master cut | **1995-06-28 18:06:57**, GMT offset 0 |
| Files / directories | **131 / 7** |
| Bytes on disc | 1,315,110 |
| Compression | **CrunchMania `CrM2`**, 115 of 131 files, 1,090,916 -> 3,631,196 bytes (**30.0 %**) |
| Whole game, unpacked | **3,855,390 bytes = 3.86 MB** |
| Share of a 333,000-sector CD | **0.232 %** |
| Unclaimed sectors in the volume | **32, all zero**, LBA 740–771 |
| `.TM` block | sector 21, 2,048 bytes, **the seventh byte-identical copy** of the Commodore banner |
| Boot script | three lines: `freeanim`, `setpatch`, `gloom` |
| `c/`, `libs/`, `devs/` | **none** — `freeanim` and `setpatch` sit in the root |
| Game executable | one hunk, 174,128 bytes, `MEMF_ANY`, 1,277 relocations, no symbols, no debug hunks |
| Libraries opened | 3: `dos`, `graphics`, `nonvolatile` (+ `ciaa`/`ciab.resource`) |
| `lowlevel.library` | **never opened** — the CD32 pad is clocked by hand |
| `cd.device` | **never opened**; no `OpenDevice` anywhere |
| Display | **7 bitplanes**, interleaved, 320 px, double-buffered, 128 colours at **24 bits** loaded from the copper |
| AGA | **required** — `FMODE = $000F`, `BPLCON0` with `BPU = 7`, `BPLCON3` `LOCT`, `BPLCON4` `BPLAM`, `DIWHIGH` |
| Akiko | **zero references** — and the 3D view has no chunky-to-planar step to give it |
| Music | **two OctaMED `MMD1` modules** |
| Effects | 24 raw 8-bit PCM files with a four-byte `{Paula period, length}` header |
| Save system | CD32 `nonvolatile.library`, app `Gloom`, item `Games` |
| Cut / leftover | an A1200 hard-disk installer, two floppy-disk prompts in the shipped binary, a demo build's refusal, ten debug colour flashes, 224 empty palette slots, and a whole missing zone number |

## What is interesting about this disc

**It is the disc the Akiko question was waiting for, and it answers it by not
needing the answer.** Gloom is a real-time texture-mapped renderer whose
textures, sprites and HUD are all 8-bit chunky, on a console whose headline
feature converts chunky to planar. It does not touch Akiko — and, unlike the
seven discs before it, that is not because the conversion is done elsewhere.
**There is no conversion.** The 3D view is displayed as a copper list with one
`MOVE` per pixel, over bitplanes that hold a fixed colour-index ramp. See
[07-display-and-akiko.md](07-display-and-akiko.md).

**It is the fifth cruncher on the format, and the game names its author in its
own credits screen.** `CrM2` is CrunchMania; the credits read
`DECRUNCHING CODE BY THOMAS SCHWARZ`, who wrote it. See
[05-compression.md](05-compression.md).

**It is the smallest CD32 volume seen here, and it still leaves 32 sectors.**
772 sectors against Speris' 2,303 and Microcosm's 255,552 — and all three leave
exactly 32 unclaimed sectors of zeros at the end. See
[01-disc-and-filesystem.md](01-disc-and-filesystem.md).

**Its `freeanim` is byte-identical to Liberation's.** Same 3,492 bytes, same
SHA-1, two unrelated studios, two publishers, fourteen months apart. See
[04-boot-chain.md](04-boot-chain.md).

**The whole master was assembled in one hour and the game data copied in
seventeen seconds.** See [03-timestamps.md](03-timestamps.md).
