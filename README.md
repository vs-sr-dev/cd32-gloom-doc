# cd32-gloom-doc

Reverse-engineering notes on **Gloom** (Black Magic Software / Guildhall Leisure
Services, 1995) for the **Amiga CD32** — a real-time texture-mapped first-person
shooter that renders in 8-bit chunky pixels on a console whose headline feature
is a chunky-to-planar converter, and **never touches it**, because its 3D view is
displayed as a copper list with one `MOVE` per pixel and there is no planar
destination to convert to.

This repository documents a 772-sector data track: **the smallest CD32 volume in
this series by a factor of three**, 131 files of which 115 are packed with a
cruncher no previous disc here used, a three-line boot script, no `c/` and no
`libs/`, and a game that unpacks to 3.86 MB — still inside the 2.7–13.3 MB band
that eight earlier discs have not broken.

**Documentation only.** No game asset, no extracted art, no audio, no executable
code is committed here. The tools in [`tools/`](tools/) reproduce every figure,
table and image in these pages from your own legally obtained copy.

## What is documented

| Doc | Contents |
|---|---|
| [00-overview.md](docs/00-overview.md) | The disc in one table, and what is actually on it |
| [01-disc-and-filesystem.md](docs/01-disc-and-filesystem.md) | A 772-sector volume that still leaves exactly 32 sectors unclaimed |
| [02-trademark-block.md](docs/02-trademark-block.md) | The seventh byte-identical copy of Commodore's `.TM` block |
| [03-timestamps.md](docs/03-timestamps.md) | A whole master in one hour, and the game data in seventeen seconds |
| [04-boot-chain.md](docs/04-boot-chain.md) | Three lines, no `c/`, and a `freeanim` byte-identical to Liberation's |
| [05-compression.md](docs/05-compression.md) | CrunchMania — the fifth cruncher on the format, and the credits name its author |
| [06-executable.md](docs/06-executable.md) | One hunk, no symbols, 56 library calls, and 8 KB of shipped zeros |
| [07-display-and-akiko.md](docs/07-display-and-akiko.md) | **AKIKO measured to zero, and a framebuffer that is a copper list** |
| [08-graphics-formats.md](docs/08-graphics-formats.md) | ByteRun1 inside CrunchMania, 65x64 chunky textures, and `LOCT`-pair palettes |
| [09-audio.md](docs/09-audio.md) | Two OctaMED modules, 24 effects that carry their own Paula period, no `cd.device` |
| [10-input-and-saves.md](docs/10-input-and-saves.md) | Seven pad buttons clocked by hand, and a 2400-baud modem dialler |
| [11-archaeology.md](docs/11-archaeology.md) | The archaeology, and Guildhall twice |
| [12-open-questions.md](docs/12-open-questions.md) | Eleven things unresolved, with the measurement beside each |
| [notes/file-inventory.md](notes/file-inventory.md) | All 131 files with LBA, size, timestamp, unpacked size and SHA-1 |
| [cd32-platformnotes-doc](https://github.com/vs-sr-dev/cd32-platformnotes-doc) | **Platform checklist** — what to look for on *any* CD32 or CDTV disc. Shared by every Amiga CD pipeline; this repo does not keep a copy |

Raw tool output — the ISO listing, the entropy census, the sector map, the
timestamp log, the decrunch log, the LVO histogram, the register histogram, the
copper list, the asset inventory and the string dump — is in [`notes/`](notes/).

## Highlights

**Akiko is measured to zero, and this time the reason is new.** No `$00B80038`,
no `$00B80000` pointer load, no `$C0DE0000`, in the raw image, in all 131
extracted files and in all 115 decrunched ones. The 45 bare `00 B8 00 xx` byte
hits in the executable include eight consecutive entries of a descending 16-bit
table (`… 00c3 00b8 00ae 00a4 …`), which is the false positive the platform
checklist warns about, in its purest form.

**And it does not need Akiko, because it has no planar destination.** The 3D
view's framebuffer *is* a copper list. The constructor allocates
`4 * (width + (width-1)/32 + 3) * height` bytes twice over in chip RAM — one
copper instruction per pixel — and the emitter writes, per rendered row, a
`WAIT` at that raster line, one `MOVE` to a colour register per pixel, a
`BPLCON3` bank switch every 32 registers and a `BPLCON4` write. The bitplanes
underneath hold a fixed descending ramp of colour indices, 127, 126, 125 …,
written once at screen creation by the only chunky-to-planar loop in the program
(seven `bset`/`bclr` per pixel at a 40-byte stride, over one row, over a
constant). `BPLCON4`'s `BPLAM` field toggles between `$80` and `$00` every row
and the `BPLCON3` bank is ORed with the same flag, so each row displays out of
one half of AGA's 256 colour registers while the copper fills the other half for
the row below it. There is no chunky pixel to convert, because the value the
renderer produces is not an index — it is the colour, picked out of one of
sixteen pre-shaded copies of the level palette, ready to be a copper `MOVE`'s
data word.

That gives a sharper form of the platform checklist's question. It is not "is
there a chunky buffer?" — Gloom has nothing else. **It is "is there a planar
destination?"**

**AGA is required, four times over.** `FMODE = $000F`, `BPLCON0` with `BPU = 7`
(a value that does not exist on OCS or ECS), `BPLCON3` written with `LOCT`, and
`BPLCON4` and `DIWHIGH` written at all. `LoadRGB4` and `LoadRGB32` are both
never called: the 128-colour, 24-bit palette is built into a 1,072-byte copper
list at run time as four `BPLCON3` banks x 32 registers x two `LOCT` passes, and
the arithmetic closes exactly on the size that was allocated.

**The fifth cruncher on the format, and the game credits its author.** 115 of
131 files carry `CrM2` — CrunchMania, by Thomas Schwarz — and the credits screen
reads `DECRUNCHING CODE BY THOMAS SCHWARZ`. The container is fourteen bytes
(`14 + packed == filesize` on all 115), which the game's own loader confirms by
reading exactly fourteen before testing the magic. Transcribed register for
register out of the executable, `tools/crm.py` decrunched **115 of 115 files on
the first run**, with the backwards output pointer landing on zero every time.
1,090,916 bytes become 3,631,196: **30.0 %**.

**`/freeanim` is byte-identical to Liberation's `/c/FreeAnim`.** SHA-1
`449c610071ace58d8c7877aafd114588b8aa7074`, 3,492 bytes, SAS/C 6, `ReadArgs`
template `/auto/close/wait` — two unrelated studios, two publishers, fourteen
months apart, the same bytes. The format's shared-file list now has three
members: the `.TM` block (seven discs), `SetPatch` 39.6 (two), and this.

**The credits screen names four tools and the disc confirms three of them.**
CrunchMania from the packed files; **Blitz Basic 2** from
`/s/startup-sequence.info`, a Workbench project icon whose `DefaultTool` is
`blitz2:blitz2`, written by whoever last opened the boot script on a development
machine; and Deluxe Paint from four palettes that still begin with its default
16 colours.

**The floppy release is still on the disc, four times over.** A 26 KB
`Gloom->HD` hard-disk installer that says `Please insert disk ` and assigns
`gloomprog:` and `gloomdata:`; `please insert gloom data disk` and
`please write enable the gloom data disk!` compiled into the CD32 executable;
`/s/startup-sequence.bak`, the boot script this one replaced; and `/gloomgame`,
32 bytes reading `gamegamegamegamegamegamegamegame`, named by nothing.

**Out of memory means a red flash and a write to address zero.** Ten sites in
the executable set `COLOR00` to a distinctive colour and spin 65,536 times; one
of them is `AllocMem`'s failure path, after which the code carries on with a
null pointer. They are the only ten writes to `COLOR00` in the file, and they
are the entire error-reporting surface of the shipped game.

**The band held, from below.** The data track is 0.232 % of a CD — a third of
the previous record — and the game unpacks to 3.86 MB, which lands between
Dragonstone's 2.7 MB and Legends' 4.4 MB. Nine discs, four years, eight studios,
and the number bounded by 2 MB of chip RAM rather than by the medium has not
moved.

## Reproducing

```
pip install capstone pillow

python tools/isoread.py "Gloom (1995)(Guildhall Leisure Services)[!].iso" -x _work/files
python tools/sectormap.py "Gloom (1995)(Guildhall Leisure Services)[!].iso"
python tools/tmsector.py  "Gloom (1995)(Guildhall Leisure Services)[!].iso"
python tools/timestamps.py "Gloom (1995)(Guildhall Leisure Services)[!].iso"

python tools/census.py _work/files
python tools/crm.py -a _work/files -o _work/unpacked
python tools/assets.py _work/unpacked

python tools/hunk.py    _work/files/Gloom
python tools/scan.py    _work/files/Gloom
python tools/lvo.py     _work/files/Gloom --base dos=0x986a --base graphics=0x9856 \
                        --base nonvolatile=0x5cc8 --base ciaa=0x9438 --base ciab=0x0f5e
python tools/copper.py  _work/files/Gloom 0x56e4 0x330
python tools/m68kdis.py _work/files/Gloom 0x24d9c 0x2c8 --hunk 0x20
python tools/pic.py     _work/unpacked/pics/spacehulk _work/files/pics/spacehulk.pal -o out.png
```

`_work/` is git-ignored. Nothing extracted from the disc is committed.

## A note on the disassembly

The Capstone M68K backend prints wrong-but-plausible immediates and
displacements on this code. `tools/m68kdis.py` therefore prints the raw bytes
beside every instruction, and **every constant, displacement and absolute
address quoted in these pages was re-read from those bytes.** Two conventions
that matter when checking the listings: the hunk starts at file offset `0x20`,
so *hunk offset = file offset − 0x20*; and Capstone's own PC-relative targets
are printed as file offsets while `--hunk 0x20` puts hunk offsets in the label
column.

## Related

* [cd32-platformnotes-doc](https://github.com/vs-sr-dev/cd32-platformnotes-doc) — the shared CD32/CDTV checklist
* [cd32-microcosm-doc](https://github.com/vs-sr-dev/cd32-microcosm-doc) — Psygnosis, 1994, the previous Akiko candidate
* [cd32-liberation-doc](https://github.com/vs-sr-dev/cd32-liberation-doc) — Mindscape, 1994, whose `freeanim` is this disc's
* [cd32-legends-doc](https://github.com/vs-sr-dev/cd32-legends-doc) — Guildhall, 1996, the publisher control
* [cd32-thesperislegacy-doc](https://github.com/vs-sr-dev/cd32-thesperislegacy-doc), [cd32-dragonstone-doc](https://github.com/vs-sr-dev/cd32-dragonstone-doc), [cd32-marvinsmarvellousadventure-doc](https://github.com/vs-sr-dev/cd32-marvinsmarvellousadventure-doc), [cd32-prey-doc](https://github.com/vs-sr-dev/cd32-prey-doc)
