# 03 — Timestamps: one hour, and seventeen seconds of it

```
python tools/timestamps.py "Gloom (1995)(Guildhall Leisure Services)[!].iso"
```

Full table in [`notes/timestamps.md`](../notes/timestamps.md).

## Every record is real, and they are all the same afternoon

There is no 1978 AmigaDOS epoch here, no 1980 MS-DOS epoch, no clock stuck two
years in the past and no impossible date. **All 138 directory records and the
PVD carry 1995-06-28, between 17:03:41 and 18:06:57, GMT offset 0.** Nine discs
in, this is the first one whose timestamps say nothing except "this is when the
image was assembled" — which is itself worth recording, because the checklist's
advice to sort by timestamp has paid on every previous disc and pays nothing
here.

That also means the disc offers **no development log**. Marvin's file dates
spread over seven months; Prey's separated a re-recorded soundtrack; Gloom's are
one copy operation, so the only thing they date is the mastering session.

## The mastering session, in order

| Time | What |
|---|---|
| 17:03:41 | `/freeanim` |
| 17:04:44 | `/s/startup-sequence.info` |
| 17:17:46 – 17:18:03 | **128 files: everything else except the boot script and the executable** |
| 17:17:58 – 17:18:03 | the seven directory records |
| 17:22:50 | `/s/` and `/s/startup-sequence` |
| **18:06:12** | the root directory record |
| **18:06:22** | `/Gloom`, the game executable |
| **18:06:57** | the PVD — the master |

Three things fall out of it.

**The whole game was copied in seventeen seconds.** 128 files and 1.13 MB
between 17:17:46 and 17:18:03, which at ~66 KB/s is a floppy-speed source or a
slow bus, not the 150–200 KB/s hard disk Microcosm's log implies. The order
inside those seventeen seconds is the alphabetical on-disc order, so it tells
you nothing further.

**`freeanim` and the boot script's icon were copied fourteen minutes before
everything else**, at 17:03:41 and 17:04:44, from somewhere else. They are the
two files on the disc that have nothing to do with Gloom: a Commodore-era
developer wrapper (see [04-boot-chain.md](04-boot-chain.md)) and an icon whose
default tool is `blitz2:blitz2`.

**The executable was written 48 minutes after the data and 35 seconds before the
master.** `/Gloom` at 18:06:22, PVD at 18:06:57. Nothing else moved in between.
Somebody built the game, dropped it into a tree that was already complete, and
cut the image immediately.

The root directory record at 18:06:12 is ten seconds *before* the executable it
indexes; ISOCD writes the directory extents as it lays the volume out, so that
is the tool, not a wrong clock. Compare Legends, where the PVD is stamped two
hours before nine of the files it indexes and the whole set reads 1992 on a 1996
disc.

## Compared with the rest of the format

| Disc | What the timestamps are |
|---|---|
| Dragonstone | AmigaDOS 1978 epoch; the day number is uptime; a 26-minute build log |
| Marvin | seven months of real development; directories on a wrong 1992 clock |
| Prey CD32 | four epochs at once, including 1,213 dates inherited from the CDTV master |
| Speris | all real; four sittings across Dec 1995 and Jan 1996 |
| Legends | all 118 read 1992-03-06 on a 1996 disc — set, and set wrong |
| Liberation | 184 real, 12 on a wrong clock, disproved by the executable's own `$VER:` |
| Microcosm | **inverted**: files real, the PVD itself at the 1978 epoch |
| **Gloom** | **all real, all one hour, and the master 35 s after the last file** |

There is no `$VER:` string anywhere in `/Gloom` to cross-check the build date
against — the checklist's strongest test for a suspicious date has nothing to
work on here, because no date is suspicious.
