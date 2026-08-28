# 09 — Audio

## There is no Red Book track, and nothing could play one

The dump supplied for this pipeline is a single `MODE1/2048` data track with no
cue sheet and no audio track. That is a property of the dump, not necessarily of
the pressing — but the executable settles the question anyway:

* **`OpenDevice` (exec −444) is never called.** `tools/lvo.py` attributes 56 of
  the 57 library calls in the file and none of them opens a device.
* `cd.device` does not appear as a string anywhere on the disc.
* Histogramming the `io_Command` immediates (`3?7c 00nn 001c`, the shape the
  platform checklist gives) over the whole executable finds **one** hit, value
  2, and with no device open it is a coincidence in data.

So no `CD_PLAYTRACK` (38), no `CD_PLAYMSF` (39), no `CD_TOCLSN` (35), no
`CD_ATTENUATE` (45). Whatever is on the other tracks of a retail pressing, this
program would not touch it. All the music and all the effects are Paula.

That makes Gloom the fourth disc in this series with no Red Book music that the
game uses — after Prey (both releases), Speris and Microcosm — and the third
where the soundtrack is a tracker format.

## `sfxs/med1` and `sfxs/med2` — OctaMED

Two modules, magic `MMD1`:

| File | Bytes on disc | Unpacked | Declared module length |
|---|---:|---:|---:|
| `med1` | 96,420 | 147,392 | 147,392 |
| `med2` | 57,270 | 72,974 | 72,974 |

The `MMD1` header's own length field agrees with the decrunched file size to the
byte on both, which is a free check that the CrunchMania transcription is right.

`MMD1` is **OctaMED**, not ProTracker — the disc scans clean for `M.K.`,
`M!K!`, `FLT4` and the `NCHN` family, so the checklist's ProTracker sweep finds
nothing and the checklist's advice to ignore the extension applies twice over
(neither file has one).

The instrument names survive, and they are the composer's working names:

```
med1:  STRING1MAJ  CRESCENDO1  TINABEAT1  TENSE  beepo  FLUTEBULLY
       tom1  tom2  snare1  snare2  flutebullyhigh  string+harpsichord
med2:  STRING1MAJ  CRESCENDO1  BELL1  NATURALBEAT2  tom2  snare1  snare2
```

`STRING1MAJ`, `CRESCENDO1`, `tom2`, `snare1` and `snare2` are in both, so the two
tunes share a sample kit. The credits read `MUSIC BY KEV STANNARD`. No postal
address, no group signature, no `deadbeef` sentinel — unlike Marvin's twelve
in-house modules.

There is no `FORM`+`8SVX` anywhere on the disc, packed or unpacked. The
checklist's cheapest tool fingerprint — the `ANNO` chunk of an embedded IFF
sample — has nothing to find here.

## `sfxs/*.bin` — 24 raw effects with a four-byte header

```
offset 0  UWORD  Paula period
offset 2  UWORD  length in words
offset 4  BYTE[] signed 8-bit PCM
```

`4 + 2 * length == filesize` on **all 24 files**, which is what identifies the
header without disassembling the player. The period is the sample rate, in the
form Paula wants it, stored per effect — so unlike Prey, where the rate had to
be pulled out of `AUDxPER` immediates in the code, this disc keeps it in the
data.

`PAL rate = 3,546,895 / period`:

| Rate | Period | Files |
|---:|---:|---|
| 11,050 Hz | 321 | `die`, `footstep`, `grunt`, `grunt3`, `grunt4`, `robot`, `splat`, `token` |
| 9,935 Hz | 357 | `shoot2` |
| 9,359 Hz | 379 | `dragon` |
| 9,118 Hz | 389 | `trollhit` |
| 8,867 Hz | 400 | `shoot` |
| 8,630 Hz | 411 | `grunt2` |
| 8,588 Hz | 413 | `trollmad` |
| 8,287 Hz | 428 | `robodie` |
| 7,711 Hz | 460 | `shoot5` |
| 7,436 Hz | 477 | `lizhit` |
| 6,982 Hz | 508 | `teleport` |
| 6,593 Hz | 538 | `shoot3` |
| 6,379 Hz | 556 | `lizard` |
| 5,941 Hz | 597 | `ghoul` |
| 4,212 Hz | 842 | `door` |
| 4,077 Hz | 870 | `shoot4` |

**Period 321 is the studio default** — eight of the 24 use it, exactly, and they
are the human and mechanical noises. Everything else was pitched by ear: the
door is at a quarter of the rate to make it deep, `shoot4` lower still. This is
the same per-clip choice Liberation makes with its `VHDR` rates, done a
different way; there is no single "the disc's sample rate" to quote.

Twelve of the 24 files are a whole number of 4,096-word blocks (`8196`, `16388`
bytes) and the rest are not, so the lengths are the recordings, not a buffer.

Four Paula channel base registers are written absolutely — `AUD0LCH` three
times, `AUD1LCH`, `AUD2LCH` and `AUD3LCH` once each — and the CIA-B timer is
used for the music interrupt (`ciab.resource`, `AddICRVector`), which is the
ordinary OctaMED arrangement.
