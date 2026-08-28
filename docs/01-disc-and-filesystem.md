# 01 — The disc and its file system

Reproduce everything here with:

```
python tools/isoread.py "Gloom (1995)(Guildhall Leisure Services)[!].iso" -x _work/files
python tools/sectormap.py "Gloom (1995)(Guildhall Leisure Services)[!].iso"
```

## The primary volume descriptor

The descriptor is written twice, at sectors 16 and 17, byte for byte identical,
with the terminator at 18 — the one habit that crosses mastering tools.

| Field | Value |
|---|---|
| System identifier | `CDTV` — *not* `CD32`, as on every disc in this series |
| Volume identifier | `GLOOM` |
| Volume set identifier | empty |
| Publisher identifier | empty |
| **Data preparer** | `" - ISOCD 1.04 by Pantaray, Inc. USA -"` |
| Application identifier | **empty** |
| Copyright / abstract / bibliographic | empty |
| Volume space size | **772 sectors** (the LSB and MSB copies agree) |
| Logical block size | 2,048 |
| Path table size | 92 bytes |
| M path table | LBA **19** (optional copy: 19) |
| L path table | LBA **20** (optional copy: 20) |
| Root directory | LBA 22, 2,048 bytes, `1995-06-28 18:06:12` |
| Creation date | `1995-06-28 18:06:57.00`, GMT offset **0** |
| Modification / expiry / effective | all NUL |
| File structure version | 1 |

All three of ISOCD 1.04's documented habits are present: the duplicated
descriptor, the optional path-table pointers filled with the mandatory ones, and
NUL padding where ISO 9660 asks for spaces.

**The preparer's name box is empty and only the tool signature is there.** That
is now three discs of nine — Speris (1996), Microcosm (1994) and Gloom (1995) —
so an empty preparer is neither an early nor a late habit; it is what happens
when nobody types anything. It also means this disc offers no name to
cross-check against the credits screen, which on Legends was the cheapest
attribution on the format.

**The application identifier is empty too**, which is a sixth answer to that box
across nine discs: title, genre, medium, title-plus-console, empty, empty.

**Note the M path table at 19 and the L at 20.** Liberation does the same, and
so do the other ISOCD discs here; it is the tool's layout, not a variation.

## The layout

```
LBA   0..15   system area (zero)
LBA  16       primary volume descriptor
LBA  17       primary volume descriptor, duplicate
LBA  18       descriptor terminator
LBA  19       M path table
LBA  20       L path table
LBA  21       the .TM block  (2,048 bytes -- see 02-trademark-block.md)
LBA  22       root directory
LBA  23..739  files and directories
LBA 740..771  32 sectors, all zero, claimed by nothing
--- the declared volume ends at 772 ---
LBA 772..951  180 sectors, all zero: image overrun
```

## 32 unclaimed sectors, on the smallest volume yet

`tools/sectormap.py` builds the map against the **declared** size and reports:

```
declared volume 772 sectors, image 952 sectors, overrun 180
overrun is all zero
unclaimed sectors inside the declared volume: 32 in 1 runs
   LBA 740..771 (32 sectors) all zero
```

The platform checklist has been circling this number for four discs. Marvin,
Prey CD32, Speris, Legends and Microcosm all leave **32**; Liberation alone
leaves 232. The reading that 32 was "a coincidence of small volumes" was killed
by Microcosm's 255,552-sector volume leaving 32.

**Gloom tests it from the other end, and it holds.** 772 sectors is a third of
Speris' volume and 1/331st of Microcosm's, and it still leaves exactly 32. Six
discs from 772 to 255,552 sectors leave 32; Liberation's 232 is the only
outlier and is still unexplained.

## The overrun is 180 sectors

The image is 180 sectors longer than the volume it declares, and the tail is all
zero. The known values are now:

| Disc | Overrun |
|---|---:|
| Marvin, Speris, Legends | 152 |
| Microcosm | 225 |
| **Gloom** | **180** |
| Dragonstone | 106 |
| Liberation | 103 |
| Prey CD32 | 0 |

152 appearing three times still looks like something; the rest is a property of
how a dump was made rather than of the format. Build the sector map against the
declared size and the question does not arise.

## What is on it

131 files, seven directories, 1,315,110 bytes:

| Directory | Files | What |
|---|---:|---|
| `/` | 9 | the executable, `setpatch`, `freeanim`, an HD installer, four icons, `gloomgame` |
| `/maps` | 42 | 21 single-player levels and 21 two-player combat arenas |
| `/misc` | 3 | two fonts and the mission script |
| `/objs` | 20 | chunky sprite banks |
| `/pics` | 12 | six 7-bitplane screens and six palettes |
| `/s` | 3 | the boot script, its backup and its icon |
| `/sfxs` | 26 | 24 PCM effects and two OctaMED modules |
| `/txts` | 20 | texture banks, floors and ceilings |

The complete listing with LBA, size, timestamp, unpacked size and SHA-1 is in
[`notes/file-inventory.md`](../notes/file-inventory.md).

## Occupancy: the smallest game on the format, and the band still holds

| | |
|---|---:|
| Data track, declared | 772 sectors |
| Share of a 333,000-sector CD | **0.232 %** |
| Bytes on disc | 1,315,110 |
| Unpacked | 3,855,390 = **3.86 MB** |

0.232 % is a third of Speris' 0.74 %, which held the record. And yet the *game*,
measured unpacked, is **3.86 MB** — inside the 2.7–13.3 MB band the platform
checklist tracks across eight discs, between Dragonstone (2.7 MB) and Legends
(4.4 MB).

**The band survives a ninth disc, and this one tested it from below.** A 1.3 MB
data track was the first thing that looked able to break it; the 30 % packing
ratio is what saves it, which is exactly why the checklist says to measure the
decompressed size and not the compressed one.

Excluding `setpatch`, `freeanim`, the hard-disk installer and the four icons —
none of which is the game — the figure is 3,813,149 bytes, which does not move
the conclusion.
