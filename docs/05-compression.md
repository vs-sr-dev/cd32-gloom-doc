# 05 — Compression: CrunchMania, and the credits name its author

```
python tools/census.py _work/files
python tools/crm.py -a _work/files -o _work/unpacked
```

## The census first

The platform checklist puts the census before the magic scan, because on Legends
a magic scan returned nothing on a disc that was 71 % packed. Here the census
would have found it anyway:

| | |
|---|---:|
| Files at entropy >= 7.0 | **115 of 131** |
| Files whose first longword equals the size or the size minus 4 | 0 |
| Files whose zlib ratio is >= 0.99 | 112 |

Every packed file scores between 6.19 and 7.996; the sixteen that do not are the
executables, the icons, the two boot scripts, `gloomgame` and five of the six
`.pal` files. (The sixth, `pics/blackmagic.pal`, *is* packed — 376 bytes down
from the 512 the others store raw. It is the only palette on the disc that was
worth 136 bytes to the person who built it.)

The magic scan then returns a magic no disc in this series had produced before:

```
CrM2   115 files
```

## `CrM2` is CrunchMania, and the game says so

The credits screen inside `/Gloom` reads, in full:

```
GLOOM
A BLACK MAGIC GAME
PROGRAMMED BY MARK SIBLY
GRAPHICS BY THE BUTLER BROTHERS
MUSIC BY KEV STANNARD
AUDIO BY US
PRODUCED BY US
DESIGNED BY US
GAME CODED IN DEVPAC2
UTILITIES CODED IN BLITZ BASIC 2
RENDERED IN DPAINT3 AND DPAINT4
DECRUNCHING CODE BY THOMAS SCHWARZ
```

`CrM!` and `CrM2` are the magic numbers of **CrunchMania**, by Thomas Schwarz.
The last line of the credits is not a thank-you, it is an attribution of the 690
bytes of decoder that sit at hunk offset `0x24d7c` of the executable — and it is
the first time on this format that a disc has named the cruncher it uses. Four
crunchers were previously known here (RNC ProPack on Dragonstone, the Imploder
on Speris, Bytekiller on Legends, and Liberation's twelve-byte `RNC` container
that is not RNC ProPack); this is the fifth, and the only one whose author is
credited on screen.

## The container

Fourteen bytes, big-endian:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | `'CrM2'` (or `'CrM!'`) |
| 4 | 2 | leeway — extra bytes needed to decrunch in place |
| 6 | 4 | unpacked length |
| 10 | 4 | packed length |
| 14 | — | the stream, read **backwards** from its last byte |

`14 + packed == filesize` holds on **all 115 files**, which is what confirms the
header length before any decoding. The checklist's warning applies in reverse
here: a magic you do not recognise is still a header you must measure, and the
14 comes from the file set, not from a format description.

It also comes from the game. The file loader at hunk `0x9504` opens the file,
seeks to the end and back to get the length, and then reads exactly **14 bytes**
into a scratch buffer before comparing the first longword with `'CrM2'` and
`'CrM!'`:

```
09504  clr.l   $94f8.l
0950e  move.l  d1,d5
09510  movea.l $986a.l,a6          ; dos.library
09516  move.l  a0,d1               ; the filename
09518  move.l  #$3ed,d2            ; MODE_OLDFILE
0951e  jsr     -30(a6)             ; Open
09522  move.l  d0,d7
09528  move.l  d7,d1
0952a  moveq   #0,d2
0952c  moveq   #1,d3
0952e  jsr     -66(a6)             ; Seek(file, 0, OFFSET_END)
...    (Seek back to the beginning, keeping the length in d4)
0953e  move.l  d7,d1
09540  move.l  #$94ea,d2           ; the scratch buffer
09546  moveq   #14,d3              ; <- the header length
09548  jsr     -42(a6)             ; Read
...
09562  move.l  $94ea.l,d0
09566  cmpi.l  #$43724d32,d0       ; 'CrM2'
0956e  cmpi.l  #$43724d21,d0       ; 'CrM!'
```

The leeway word is 0 on 98 of the 115 files and 2, 4, 8, 12, 14 or 20 on the
rest — always small, always even, and always on files the game decrunches into
a buffer it also reads from. Nothing on the disc verifies it, and this document
does not claim to know what the decruncher does with it beyond reading it and
discarding it (`tst.w (a0)+`).

## The decoder, transcribed from the loader

Not from a format description. The dispatcher is at hunk `0x24d7c`:

```
24d7c  movem.l d0-d7/a0-a6,-(sp)
24d80  move.l  (a0)+,d0
24d82  lea     $24daa(pc),a5        ; the CrM! decoder
24d86  cmp.l   #$43724d21,d0        ; 'CrM!'
24d8c  beq.s   +12
24d8e  lea     $24eb8(pc),a5        ; the CrM2 decoder
24d92  cmp.l   #$43724d32,d0        ; 'CrM2'
24d98  bne.s   +10                  ; not ours: return
24d9a  tst.w   (a0)+                ; the leeway word, read and dropped
24d9c  move.l  (a0)+,d1             ; unpacked length
24d9e  move.l  (a0)+,d2             ; packed length
24da0  movea.l a0,a2                ; the stream
24da2  jsr     (a5)
24da4  movem.l (sp)+,d0-d7/a0-a6
24da8  rts
```

`CrM2`, at hunk `0x24eb8`, is a Huffman-plus-LZ stream decoded backwards:

* `a1` walks **down** from the end of the output, `a2` walks **down** from the
  end of the packed data. `d6` is a 32-bit bit buffer refilled a word at a time
  from `-(a2)`; `d7` counts the bits left before a refill.
* The last word of the stream is the number of valid bits in the first buffer
  load, which is what makes the whole thing self-aligning.
* Each block begins with two alphabets read out of the stream: a **9-bit**
  literal/length alphabet and a **4-bit** offset-width alphabet, each stored as
  a count of code lengths, then one count per length, then the symbol values.
  `BUILD` (hunk `0x2500e`) turns the counts into the canonical-Huffman
  `limit[16]` / `base[16]` pair the decode loop at hunk `0x24f6a` uses.
* A 16-bit count gives the number of symbols in the block.
* A symbol with **bit 8 set** is a literal: its low byte is written to `-(a1)`.
* A symbol without bit 8 is a match length; the offset-width alphabet then gives
  a bit count `k`, `k` bits are read, bit `k` is set on the result, and
  `length + 3` bytes are copied down from `a1 + offset + 1`. `k = 0` is the
  special short case (`d1 = 1`, `bset #16`).
* One bit after the block says whether another block follows.

The dispatcher and both decoders occupy hunk `0x24d7c`–`0x25044`, **712 bytes**,
and their scratch tables live immediately after them in a **1,248-byte run of
zeros** at hunk `0x25046`, shipped on the disc as part of the code hunk: the
decoder addresses them as `lea $25046(pc),a6` and indexes `$1e(a6)` through
`$4de(a6)`.

Transcribed register for register into [`tools/crm.py`](../tools/crm.py) it
decrunched **115 of 115 files on the first run**, with the output pointer landing
exactly on zero every time — the same in-place self-check the Imploder gives, and
the reason a wrong implementation fails loudly instead of quietly.

## What it bought

| | |
|---|---:|
| Packed bytes on disc | 1,090,916 |
| Unpacked | 3,631,196 |
| Ratio | **30.04 %** |

The best ratio on the disc is `txts/roof1` at **2.4 %** (394 bytes for a
16,448-byte texture that is nearly all one colour); the worst is
`sfxs/trollhit.bin` at 95.7 %, which is raw 8-bit speech and barely compressible.
The full log is in [`notes/decrunch-log.txt`](../notes/decrunch-log.txt).

## The `CrM!` decoder ships and nothing uses it

The dispatcher tests both magics and the executable carries both decoders —
`CrM!` at hunk `0x24daa`, `CrM2` at `0x24eb8`, 712 bytes between them. **No file
on the disc is `CrM!`.** `CrM!` is CrunchMania's earlier, non-Huffman method; the
loader supports it because the linked-in decruncher supports it, and the packer
was set to method 2. It is a small, cheap example of the checklist's general
finding: what a CD32 disc ships and what it runs are different sets.

## The rule about floppy origin holds

The platform checklist's strongest compression finding is that packing tracks
the *floppy* origin of a title, not the disc — **[4 of 4]** on the positive side
and **[4 of 4]** on the negative. Gloom has a floppy and hard-disk SKU whose
installer is still on the CD (see
[11-archaeology.md](11-archaeology.md)), and it is packed. **[5 of 5].**
