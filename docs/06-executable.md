# 06 — The executable

```
python tools/hunk.py _work/files/Gloom
python tools/lvo.py _work/files/Gloom --base dos=0x986a --base graphics=0x9856 \
                   --base nonvolatile=0x5cc8 --base ciaa=0x9438 --base ciab=0x0f5e
python tools/scan.py _work/files/Gloom
```

## One hunk, no symbols, no debug

```
HUNK_HEADER  resident=[]  table_size=1  first=0 last=0
  hunk 0: 43532 longwords = 174128 bytes  (any)
HUNK_CODE      hunk 0  174128 bytes at file offset 0x20
HUNK_RELOC32   1277 entries
HUNK_END
```

179,288 bytes on disc, one 174,128-byte hunk requested in **any** memory, 1,277
relocations, **no `HUNK_SYMBOL` and no `HUNK_DEBUG` anywhere**. Step 7 of the
platform checklist says to look for `HUNK_DEBUG` before disassembling anything,
because Microcosm's 77 `HCLN` blocks hand you the architecture of the program
before the first instruction. There is nothing here: this file was assembled
with Devpac 2 (the credits say so) and linked without a symbol table, so every
structural claim in this repository came out of the bytes.

**A single hunk asking for `MEMF_ANY` is itself informative.** The program takes
174 KB of any memory and then allocates every chip-RAM buffer it needs at
runtime through one wrapper (below) — where Marvin claims 1.57 MB of a CD32's
2 MB of chip RAM in its hunk table before it allocates anything.

Throughout this repository, **hunk offset = file offset − 0x20**. Both are
quoted where it matters; `tools/m68kdis.py --hunk 0x20` prints the hunk offset in
the label column, and Capstone's own PC-relative targets are file offsets.

## Where the code is, and where it is not

`tools/m68kdis.py` decodes the hunk linearly and about 40,000 instructions come
out, but the hunk is not all code. Scored by the fraction of plausible
mnemonics per kilobyte:

```
00000  ######+############################+######+###-+.########-.--#+#
10000  #########+#+------+-+-++-----+---+++-+--+++--++--+++------++---+
20000  ----+------######+-###++++++++++++#########
       # code   + mostly code   - mixed   . data
```

* `0x00000`–`0x0f000` — the game: renderer, screen system, script interpreter,
  input, front end, file loader.
* `0x0f000`–`0x22000` — data: chunky graphics (the HUD panel is embedded here as
  8-bit pixels, values `$00`, `$0b`, `$0c`, `$0e`, `$24`, `$25`, `$30`), tables,
  and one run of ByteRun1-looking bytes.
* `0x23000`–`0x24d00` — the OctaMED player.
* `0x24d7c`–`0x25044` — the CrunchMania decoder
  ([05-compression.md](05-compression.md)).
* `0x25046`–`0x25526` — 1,248 bytes of zero: the decoder's tables.
* the last non-zero byte of the hunk is at `0x287ef`; **8,256 bytes of trailing
  zeros** ship after it, and 52,097 of the hunk's 174,128 bytes (29.9 %) are
  zero in total.

Shipping 8 KB of zeros at the end of a code hunk is what happens when a
hand-written assembler program declares its BSS with `ds.b` inside the last
section instead of a separate `HUNK_BSS`. It costs four sectors on the disc.

## What it asks the operating system for

57 `jsr d16(a6)` sites, 56 of them attributable by tracking the last value moved
into `a6`:

| Library | Calls | LVOs |
|---|---:|---|
| `exec.library` | 26 | `SetIntVector` ×10, `OldOpenLibrary` ×3, `FreeMem` ×2, `AllocMem`, `AvailMem`, `AddIntServer`, `RemIntServer`, `Forbid`, `Permit`, `CacheClearU`, `OpenResource`, `GetMsg`, `ReplyMsg`, `WaitPort` |
| `dos.library` | 12 | `Open` ×3, `Close` ×2, `Read` ×2, `Seek` ×3, `Write`, `CurrentDir` |
| `graphics.library` | 5 | `LoadView`, `WaitTOF` ×2, `OwnBlitter`, `DisownBlitter` |
| `nonvolatile.library` | 4 | `GetCopyNV`, `FreeNVData`, `StoreNV`, `SetNVProtection` — one call each |
| `ciaa`/`ciab.resource` | 3 | `AddICRVector` ×2, `RemICRVector` |

Full histogram in [`notes/lvo-gloom.txt`](../notes/lvo-gloom.txt).

Two things this settles immediately.

**`LoadRGB4` (−192) and `LoadRGB32` (−858) are both never called.** That is the
third outcome the platform checklist added after Microcosm: the program is not
using 12-bit colour and it is not using 24-bit colour through the OS, it is
programming the display itself. The answer is in the copper list, and it is
unambiguous — see [07-display-and-akiko.md](07-display-and-akiko.md).

**Ten `SetIntVector` calls, plus `AddIntServer` and two CIA ICR vectors.** The
program takes the interrupt system apart completely. `Forbid` and `Permit`
bracket the takeover; `CacheClearU` runs once, which on a 68020 means the
program writes code or copper lists it is about to execute.

`OpenResource` is called twice on a name held as **`ciax.resource`** with the
`x` patched to `a` or `b` in place before each call — a template, in a program
that opens both CIAs.

## How it reaches the hardware

`tools/scan.py --regs` counts 146 absolute custom-chip references across 37
distinct registers, and **zero `lea $DFF000,An`**. This is the Prey pattern: a
program that writes every register absolutely, and that a test counting `lea`
loads would score as never touching the hardware.

| Register | Writes | What it says |
|---|---:|---|
| `INTENA` | 21 | interrupt masking around everything |
| `DMACON` / `DMACONR` | 11 / 13 | bitplane, blitter and audio DMA |
| `INTREQ` | 11 | the hand-written interrupt handlers |
| `BPLCON3` | 10 | **all ten are `$0000`** — see below |
| `COLOR00` | 10 | the same ten sites |
| `BLTCON0`, `BLTSIZE`, `BLTxPT`, `BLTxMOD` | 4–5 each | one blit shape only |
| `AUD0LCH`–`AUD3LCH` | 3/1/1/1 | four Paula channels |
| `POTGO` / `POTGOR` | 4 / 2 | **the CD32 pad, clocked by hand** |
| `JOY0DAT` / `JOY1DAT` | 2 / 2 | two joystick ports |
| `SERDAT` / `SERPER` | 1 / 1 | the serial two-player link |
| `COP1LCH`, `COPJMP1` | 2, 3 | installing the copper list |

Every one of the ten `BPLCON3` writes is `$0000` and every one is immediately
followed by a `COLOR00` write and a delay loop:

```
115c  3f 00                      move.w  d0,-(sp)
115e  30 3c ff ff                move.w  #$ffff,d0
1162  33 fc 00 00 00 df f1 06    move.w  #$0000,$dff106      ; BPLCON3: bank 0, LOCT off
116a  33 fc 0f 0f 00 df f1 80    move.w  #$0f0f,$dff180      ; COLOR00 = magenta
1172  51 c8 ff ee                dbra    d0,$1162
1176  30 1f                      move.w  (sp)+,d0
```

That is a **debug colour flash**: paint the screen background one colour and
spin 65,536 times. There are ten of them and each uses a different colour. They
are documented in [11-archaeology.md](11-archaeology.md), where one of them
turns out to be the game's entire out-of-memory handling.

There are no `io_Command` immediates of the shape `3?7c 00nn 001c` worth the
name — the histogram finds one, `2`, and since **no `OpenDevice` call exists
anywhere in the file** it is a coincidence in data. Nothing on this disc talks
to `cd.device`, so nothing would play a Red Book track if one were present.

## The memory map, through one wrapper

Every allocation goes through a wrapper at hunk `0x9dc8`, called fifteen times:

```
9dc8  movem.l d2-d7/a2-a6,-(sp)
9dcc  moveq   #$10,d3            ; 16 bytes of link header per block
9dd0  add.l   d3,d0
9dd6  movea.l 4.w,a6
9dda  jsr     -198(a6)           ; AllocMem(size+16, flags)
9dde  tst.l   d0
9de0  bne.s   ok
9de2  ... debug colour flash, red ...
9dfe  movea.l d0,a0              ; d0 is zero here
9e00  move.l  $504a.l,(a0)       ; and it writes through it
```

The blocks are chained through a head pointer at hunk `0x504a` so the whole
allocation can be released in one pass at exit (`FreeMem` twice, from a walker
at `0x9e46`). The requests, in order, are 8 bytes chip, `$100`, `$100`, `$8000`,
`$1400`, `$1000`, `$4000` bytes public, the display bitmaps and copper lists
(see [07](07-display-and-akiko.md)), and `$118 * lines` for a saved screen
strip.

`$118` is 280 = **7 × 40**, the interleaved row pitch of a 7-bitplane 320-pixel
display, and it appears eleven times in the front 64 KB of code. It is the
single most load-bearing constant in the program.

## 68020

The code is 68020-only in at least two ways: 32-bit branch displacements
(`6f ff 00 00 00 f2` — `ble.l`), and full extension-word addressing with scaled
index registers. A 68000 would not run it. That is consistent with a title whose
other SKU is an A1200 game and inconsistent with an A500 port.
