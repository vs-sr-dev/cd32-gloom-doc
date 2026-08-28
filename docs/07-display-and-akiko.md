# 07 — The display, and why Akiko is not used

This is the disc the platform checklist's open item 5 was waiting for. Seven
CD32 titles had been measured and none of them touched Akiko, the console's
chunky-to-planar converter; the last reading was that the remaining candidate
had to be **a CD32 title with a real-time renderer**, because a video player can
have its frames encoded planar offline and a rasteriser cannot.

Gloom is that title. Its textures are 8-bit chunky, its sprites are 8-bit chunky,
its HUD is 8-bit chunky, its display is seven planar bitplanes, and it does not
touch Akiko.

**The reason is not that it converts chunky to planar some other way. It is that
it never converts anything.**

## The measurement first

```
python tools/scan.py _work/files/Gloom --akiko
```

| Pattern | Whole ISO image | 131 extracted files | 115 decrunched files |
|---|---:|---:|---:|
| `$00B80038` — the C2P port | **0** | **0** | **0** |
| `$00B8003C` | **0** | **0** | **0** |
| `$C0DE0000` — the Akiko id constant | **0** | **0** | **0** |
| `lea $B80000,An` | **0** | — | — |
| `movea.l #$B80000,An` | **0** | — | — |
| bare bytes `00 B8 00 00` | 1 | 1 | 4 |
| bare bytes `00 B8 00 xx` | 9 | 45 | — |
| the strings `akiko` / `AKIKO` | **0** | **0** | **0** |

The single `00 B8 00 00` in the image is inside `/Gloom->HD`, the C-compiled
hard-disk installer. The four in decrunched data are level bytes. And the 45
`00 B8 00 xx` hits in the executable are the false positive the checklist warns
about, in its purest form — eight of them are consecutive entries of one
descending 16-bit table:

```
0124 0114 0104 00f5 00e8 00db 00ce 00c3 00b8 00ae 00a4 009b 0092 008a 0082 007b
                                        ^^^^
```

That is a Paula period table (or a scale table of the same shape). Nothing in it
is an address.

`lowlevel.library` is never opened either, so the CD32-specific surface of this
title is exactly one library — `nonvolatile.library` — and one hand-clocked
joystick port.

## The display, from the copper list

```
python tools/copper.py _work/files/Gloom 0x56e4 0x330
```

The copper list is a **816-byte template at hunk `0x56c4`** that the program
patches and then copies into an 816-byte chip buffer at start-up:

```
99b4  movem.l d2-d7/a2-a6,-(sp)
99b8  lea     $9844.l,a1              ; "graphics.library"
99c2  jsr     -408(a6)                ; OldOpenLibrary
99ce  move.l  $22(a6),$985a.l         ; save gb_ActiView
99d6  suba.l  a1,a1
99d8  jsr     -222(a6)                ; LoadView(NULL)
99dc  move.l  #$320,d0                ; 800 bytes
99e2  moveq   #2,d1                   ; MEMF_CHIP
99e4  jsr     $9dc8.l                 ; -> the hires strip's bitmap
...   (its address and address+$50 are poked into template offsets $42/$46/$4a/$4e)
9a14  move.l  #$330,d0                ; 816 bytes
9a1a  moveq   #2,d1                   ; MEMF_CHIP
9a1c  jsr     $9dc8.l
9a2a  lea     $56c4.l,a0              ; the template
9a30  lea     $59f4.l,a2              ; its end
9a3a  move.l  (a0)+,(a1)+             ; copy it into chip
```

That template contains, in order:

```
FMODE    <- 000f          AGA: 4x bitplane fetch and 4x sprite fetch
DMACON   <- 0120
DIWSTRT  <- 1e81
DIWSTOP  <- 23c1
$1e4     <- 2000          DIWHIGH  (ECS/AGA only)
DDFSTRT  <- 0038
DDFSTOP  <- 00c0
BPLCON1  <- 0000
BPLCON0  <- a200          HIRES, BPU=2
BPL1MOD  <- 0050          80 = 1 x 80 bytes  -> 2 planes interleaved, 640 px
BPL2MOD  <- 0050
BPLCON3  <- 0000
BPLCON4  <- 0000
COLOR01  <- 0fff   COLOR02 <- 0f0f   COLOR03 <- 0ff0
BPL1PTH/PTL, BPL2PTH/PTL   <- patched with the 800-byte buffer
WAIT VP=1a
   ... all 32 sprite registers written to 0 ...
WAIT VP=24
DMACON   <- 0100
DDFSTOP  <- 00a0
BPLCON0  <- 7200          lores, BPU=7          <- SEVEN BITPLANES
BPL1MOD  <- 00f0          240 = 6 x 40 bytes    <- 7 planes interleaved, 320 px
BPL2MOD  <- 00f0
BPLCON3  <- 0200          bank 0, LOCT=1  -> COLOR00..COLOR23
BPLCON3  <- 8200          bank 4, LOCT=1  -> COLOR00..COLOR23
BPLCON3  <- 0000          bank 0, LOCT=0  -> COLOR00..COLOR23
BPLCON3  <- 8000          bank 4, LOCT=0  -> COLOR00..COLOR23
BPL1PTH .. BPL7PTL        <- seven bitplane pointers
DIWSTRT  <- 2c81   DIWSTOP <- f4c1
WAIT VP=00
DMACON   <- 8100
COP2LCH/COP2LCL/COPJMP2   <- patched: jump to the other frame's copper list
   ... the whole block again ...
DMACON   <- 0100
FFFF FFFE
```

Four things in there decide the AGA question without a single palette file
being opened:

* **`BPLCON0 = $7200` sets `BPU = 7`.** Seven bitplanes. OCS and ECS stop at six.
* **`FMODE = $000F`.** The register does not exist below AGA, and this is its
  widest setting.
* **`BPLCON3` is written with `LOCT`** (bit 9) set on half the colour passes,
  which is the AGA eight-bits-per-gun write and nothing else.
* **`BPLCON4` and `DIWHIGH` are written**, neither of which exists on OCS.

`BPL1MOD = $00F0 = 240 = 6 x 40` is the interleaved-bitmap signature the
checklist gives: `(planes - 1) * bytes_per_row` with 40 bytes per row = 320
pixels. The bitplane pointers confirm it — they are poked by a loop that steps
**40 bytes per plane, seven times**, at hunk `0x98ee`:

```
98e6  movea.l $0(a0),a1        ; the screen's copper block
98ea  movea.l (a1),a1
98ec  move.l  $20(a0),d0       ; the planar bitmap
98f0  moveq   #6,d1            ; seven planes
98ee: move.w  d0,$6(a1)        ; BPLnPTL value word
      swap    d0
      move.w  d0,$2(a1)        ; BPLnPTH value word
      swap    d0
      addi.l  #$28,d0          ; +40 bytes: the next plane
      addq.w  #8,a1            ; the next pair of copper MOVEs
      dbra    d1
```

The list is **double buffered**: it ends by writing `COP2LCH`/`COP2LCL` and
`COPJMP2`, and the two halves are patched at start-up to point at each other.

The top of the screen — raster lines `$1a` to `$24` — is a separate **2-plane,
640-pixel hires strip** with three colours (white, magenta, yellow) and an
800-byte bitmap. That is the two-player chat line; see
[10-input-and-saves.md](10-input-and-saves.md).

## 128 colours at 24 bits, built into a copper list at run time

For an ordinary planar screen the constructor at hunk `0x9c3c` allocates
**`$430` = 1,072 bytes** of chip RAM and fills it with a copper list that loads
the whole palette (hunk `0x9c52`–`0x9cbc`):

```
9c72  movea.l $3a(a2),a1        ; the screen's palette: 128 x {high word, low word}
9c76  moveq   #0,d0             ; BPLCON3 value, bank 0, LOCT clear
9c78  moveq   #3,d3             ; four banks
9c7a: move.w  #$106,(a0)+       ; BPLCON3
      move.w  d0,(a0)+
      move.w  #$180,d1          ; COLOR00
      moveq   #$1f,d2           ; 32 registers
9c86: move.w  d1,(a0)+          ; COLORnn
      move.w  (a1),(a0)+        ;   <- the HIGH word of the pair
      addq.w  #4,a1
      addq.w  #2,d1
      dbra    d2
9c92  lea     -$7e(a1),a1       ; step back 126: now pointing at the LOW words
9c96  move.w  #$106,(a0)+       ; BPLCON3
      bset    #9,d0             ;   with LOCT set
      move.w  d0,(a0)+
      bclr    #9,d0
      ... the same 32 registers, reading the LOW word of each pair ...
9cb6  subq.w  #2,a1
9cb8  addi.w  #$2000,d0         ; the next BPLCON3 bank
9cbc  dbra    d3
9cc0  move.l  #$fffffffe,(a0)+
9cc6  move.l  #$00840000,(a0)+  ; COP2LCH
      move.l  #$00860000,(a0)+  ; COP2LCL
      move.l  #$008a0000,(a0)+  ; COPJMP2
```

**Four `BPLCON3` banks x 32 colour registers x two `LOCT` passes = 128 colours at
eight bits per gun**, and the arithmetic closes exactly: 8 x (1 + 32) + 4 = 268
longwords = **1,072 bytes**, the size that was allocated.

The `lea -$7e(a1)` is the whole trick in one instruction. After 32 entries `a1`
has advanced 128 bytes; stepping back 126 leaves it two bytes further on than it
started, which is the **low** word of the first pair. So the six `.pal` files on
the disc are not 256 colours — they are **128 entries of two big-endian words,
the AGA `LOCT` pair**, and reading them any other way produces noise. Rendered
with the pair, `pics/spacehulk` is a group of space marines.

Applying the checklist's `needs_more_than_4_bits` test to the reconstructed
8-bit values: `pics/spacehulk` uses genuinely non-reducible values throughout,
while `gothic`, `hell`, `combat` and `theend` have their first 32 entries filled
with the Deluxe Paint default 16-colour palette written twice (`0fff 0fff`,
`068b 068b`, `0555 0555`, …), which reduces. **This disc uses AGA's colour depth
and it uses AGA's plane count.** It is the fourth of nine to use both.

## And now the 3D view, which has no bitplanes at all

The game keeps six **screen descriptors**, 62 bytes each, at hunk `0x5550`:

| # | at | copper A | copper B | x | y | width | height | xscale | yscale | on screen |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | `0x5550` | `$503e` | `$5046` | 0 | 42 | **320** | 248 | 1 | 1 | 320 x 248 |
| 1 | `0x558e` | `$503e` | `$5046` | 70 | 76 | **90** | 90 | 2 | 2 | 180 x 180 |
| 2 | `0x55cc` | `$503e` | `$5042` | 94 | 42 | **66** | 60 | 2 | 2 | 132 x 120 |
| 3 | `0x560a` | `$5042` | `$5046` | 94 | 166 | 66 | 60 | 2 | 2 | 132 x 120 |
| 4 | `0x5648` | `$503e` | `$5042` | 94 | 42 | 66 | 60 | 2 | 2 | 132 x 120 |
| 5 | `0x5686` | `$5042` | `$5046` | 94 | 165 | 66 | 60 | 2 | 2 | 132 x 120 |

Records 2/3 and 4/5 are the top and bottom halves of a split screen, one pixel
apart in `y` — the two-player mode the front end calls `TWO PLAYER GAME`.
Records 0 and 1 are the single-player full-screen and windowed views, which is
what the front end's `RESOLUTION`, `WINDOW SIZE` and `FULL SCREEN WINDOW`
options select. The field layout is confirmed by the constructor at hunk
`0x9a9c`, which computes `width * xscale` into `+$14` and `height * yscale` into
`+$16`.

A screen whose `+$36` field is non-zero gets the planar bitmap and the
128-colour palette copper above. **A screen whose `+$36` is zero gets something
else**, and this is the finding:

```
9cde  move.w  $c(a2),d0           ; width
9ce2  move.w  d0,d1
9ce4  subq.w  #1,d0
9ce6  lsr.w   #5,d0               ; (width-1) / 32
9ce8  addq.w  #3,d0
9cea  add.w   d1,d0               ; d0 = width + (width-1)/32 + 3
9cec  move.w  d0,d1
9cee  lsl.w   #2,d1
9cf0  move.w  d1,$30(a2)          ; bytes per row
9cf4  mulu.w  $e(a2),d0           ; x height
9cf8  addq.w  #4,d0
9cfa  lsl.l   #2,d0               ; x 4 -> bytes
9cfe  move.l  d0,$1c(a2)
9d02  lsl.l   #1,d0               ; x 2 -> double buffered
9d04  jsr     $9dc8.l             ; MEMF_CHIP
```

**Four bytes per pixel**, plus one extra longword per 32 pixels and three more
per row. Those are not pixels. They are **copper instructions**, and the routine
immediately after emits them:

```
9d14  move.w  $a(a2),d6           ; the first raster line
9d1e  move.w  #$111,d3            ; the initial value  (RGB 1,1,1)
9d22  move.w  #$8000,d4           ; the BPLCON4 / bank alternator
9d26: moveq   #$7f,d0             ; colour register 127, counting down
9d28  move.w  $c(a2),d1
9d2c  subq.w  #1,d1               ; width - 1 pixels
9d2e:   move.w  d0,d2
        addq.w  #1,d2
        andi.w  #$1f,d2
        bne.s   noswitch          ; every 32 registers ...
        move.w  d0,d2
        subi.w  #$1f,d2
        andi.w  #$ffe0,d2
        lsl.w   #8,d2             ; ... the BPLCON3 bank number ...
        or.w    d4,d2             ; ... ORed with the alternator
        move.w  #$106,(a0)+       ; BPLCON3
        move.w  d2,(a0)+
noswitch:
        move.w  d0,d2
        andi.w  #$1f,d2
        add.w   d2,d2
        addi.w  #$180,d2
        move.w  d2,(a0)+          ; COLORnn        <- one MOVE per pixel
        move.w  d3,(a0)+          ;   its value    <- the pixel
        addi.w  #$111,d3
        subq.w  #1,d0
        dbra    d1
9d66  bsr.w   $9daa               ; emit a WAIT for the next raster line
9d6a  move.w  #$10c,(a0)+         ; BPLCON4
9d6e  move.w  d4,(a0)+            ;   BPLAM = $80 or $00
9d70  bchg    #15,d4              ;   ... alternating every row
9d74  dbra    d7                  ; the next row
```

and the per-row `WAIT` at hunk `0x9daa`:

```
9daa  subq.w  #1,d6
9dac  move.b  d6,(a0)+            ; VP  = this raster line
9dae  move.b  #$e1,(a0)+          ; HP  = $e0, and bit 0 set: a WAIT
9db2  move.w  #$fffe,(a0)+
9db6  addq.w  #1,d6
9db8  add.w   $12(a2),d6          ; += yscale
```

## What that means

**The 3D view's framebuffer is a copper list.** For every rendered pixel there
is one copper `MOVE` to a colour register; for every rendered row there is a
`WAIT` at that raster line and a `BPLCON4` write. The bitplanes underneath hold
a **fixed descending ramp of colour indices** — 127, 126, 125, … each repeated
`xscale` times — written once at screen creation, bit by bit, by the only
chunky-to-planar loop in the program (hunk `0x9b64`):

```
9b6c  movea.l $20(a2),a0          ; the planar bitmap
9b70  move.w  $8(a2),d0           ; x
9b76  lsr.w   #3,d0               ; -> byte index
9b78  not.w   d1
9b7a  andi.w  #7,d1               ; -> bit number, MSB first
9b7e  moveq   #$7f,d7             ; colour index 127
9b80  move.w  $c(a2),d6           ; width
9b86: move.w  $10(a2),d5
      subq.w  #1,d5               ; xscale - 1
9b8c: move.w  d7,d4
      moveq   #6,d3               ; seven planes
9b90:   bclr  d1,(a0,d0.w)
        lsr.w #1,d4
        bcc.s +
        bset  d1,(a0,d0.w)
+       lea   $28(a0),a0          ; +40: the next plane
        dbra  d3
      lea     -$118(a0),a0        ; -280: back to plane 0
      subq.w  #1,d1
      bpl.s   +
      moveq   #7,d1
      addq.w  #1,d0
+     dbra    d5
      subq.w  #1,d7               ; the next colour index
      dbra    d6
```

Seven `bset`/`bclr` per pixel with a 40-byte stride is an absurdly slow
chunky-to-planar routine — and it runs **once per screen**, over one row, on a
constant. It is not in the frame path.

The alternation is what makes it work. `d4` toggles between `$8000` and `$0000`
each row, and it is used twice: ORed into the `BPLCON3` bank (so odd rows
address colour banks 4–7 instead of 0–3, i.e. registers 128–255 instead of
0–127) and written to `BPLCON4`, whose `BPLAM` field XORs the bitplane index
before the colour lookup (so on those rows index `n` becomes `n | $80`). **Each
row displays out of one half of the 256-register palette while the copper is
filling the other half for the row below it.** Seven bitplanes give 128 distinct
indices; AGA's 256 colour registers give two banks of them; the copper does the
rest.

## What it costs

### The skeleton is static; only the data words move

The obvious objection to the whole arrangement is that the CPU must now
regenerate a 34 KB copper program every frame on a 14 MHz 68EC020 sharing the
bus with the chipset. **It does not**, and the call graph says so: the builder at
hunk `0x9cde`–`0x9d90` has no direct callers at all. It is reached only by the
`beq.w` fall-through from the screen constructor at `0x9c3c`, which is called
from `0x8ccc`, `0x828a` and `0x82b2` — screen open, not any frame path. The
per-row `WAIT` emitter at `0x9daa` is likewise called from exactly two places,
`0x9d66` and `0x9d78`, both inside the builder.

So the register numbers, the `BPLCON3` bank switches, the `WAIT`s and the
`BPLCON4` writes are laid down **once per screen**. What a frame has to change is
**the data word of each `COLOR` move — two bytes out of every four**:

| View | List | Rewritten per frame | | At 50 Hz |
|---|---:|---:|---:|---:|
| 90 x 90, scale 2 | 34,216 B (x2 = 68,432) | 8,100 px x 2 B = **16,200 B** | 47 % | 791 KB/s |
| 66 x 60, scale 2 | 17,056 B (x2 = 34,112) | 3,960 px x 2 B = **7,920 B** | 46 % | 387 KB/s |

The 68,432 figure is *both* buffers; one is written per frame, and not half of
that one.

The row allocation `4 * (width + (width-1)/32 + 3)` closes exactly, with no
slack: for width 90 that is 95 longwords = **90 `COLOR` moves + 3 `BPLCON3` bank
switches + 1 `WAIT` + 1 `BPLCON4`**, and for width 66 it is 71 = 66 + 3 + 1 + 1.
Three banks because the register index counts down from 127 and crosses a
32-register boundary twice.

### And it is not an extra pass — it is the only pass

There is no chunky buffer anywhere in the pipeline, so the rasteriser's store
*is* the copper-list write. For the same 8,100 pixels a conventional route would
cost, in chip-RAM traffic alone:

```
chunky write   8,100 B
chunky read    8,100 B      (the C2P has to read it back)
planar write   7,087 B      (8,100 px x 7 planes / 8)
               -------
               23,287 B     plus the conversion itself
```

against **16,200 B written once, no read-back and no conversion**. The copper
route is cheaper in bandwidth and free in ALU work; what it costs is two bytes
per pixel where a planar bitmap costs seven-eighths of one, which is exactly why
the view is a window and not the screen.

### The binding constraint is copper DMA, and it explains the geometry

A copper `MOVE` occupies two DMA slots and a `WAIT` three; a PAL line offers on
the order of 113 slots to non-display DMA. Per row block:

| View | MOVEs | Slots | Available over `yscale` lines | |
|---|---:|---:|---:|---:|
| 90 x 90, scale 2 | 94 | 191 | 226 | **85 %** |
| 66 x 60, scale 2 | 70 | 143 | 226 | 63 % |

Three things follow, and all three match what shipped.

* **`yscale = 2` is not a picture-quality choice, it is what makes the copper
  fit.** At 1:1 a row block would have ~113 slots for 191 slots of work. Every
  3D-view descriptor on the disc is `2 x 2`; the only `1 x 1` descriptor is
  record 0, the ordinary planar screen the menus use.
* **The width ceiling is DMA, not palette.** Seven bitplanes give 128 indices,
  so 128 looks like the limit — but subtract the fixed six slots per row block
  (`WAIT` plus three moves) from 226 and there are 217 left, which is
  **108 `COLOR` moves**, before bitplane DMA takes anything. The widest view on
  the disc is 90.
* **`FMODE = $000F` starts to look like a bandwidth decision rather than a width
  one.** A 320-pixel lores display does not need the widest AGA fetch mode for
  width; it does need bitplane DMA out of the copper's way. *This one is an
  inference* — working out the exact AGA fetch-mode slot allocation is not done
  here — but it is testable and it points the same way as the other two.

CPU side, as a ballpark only: 8,100 word stores against ~283,740 CPU clocks per
frame at 14.19 MHz and 50 Hz is **11–23 %** of the frame's budget for the stores
alone, before any rasterisation arithmetic — and worse in practice, because the
copper is taking most of the chip-RAM slots the CPU would otherwise use.

**None of this is a measurement.** No cycle-accurate trace was run; see
[12-open-questions.md](12-open-questions.md) for the experiment that would settle
it, which does not require a disassembler.

## So the answer to the Akiko question

Gloom renders in chunky. Its textures are 65 x 64 chunky bytes, its sprites are
chunky bytes with 0 as transparent, its HUD is chunky bytes compiled into the
executable, and its shading is done by picking a 12-bit `$0RGB` value out of one
of sixteen pre-shaded copies of the level palette — a sixteen-pointer table at
hunk `0x4ef8`, filled at hunk `0x9680`–`0x96de` by a routine that pulls each
4-bit gun out of a `$0RGB` word, subtracts the shade level 1..15, clamps at zero
and reassembles. The value that ends up in the framebuffer is therefore **not a
colour index at all — it is the colour**, ready to be a copper `MOVE`'s data
word.

There is nothing for a chunky-to-planar converter to convert. Akiko's port would
take chunky bytes and give back bitplane longwords, and this program has no use
for bitplane longwords in its frame path: its frame path produces copper
instructions. Feeding the renderer's output through Akiko would mean first
inventing a planar display for it.

That is a different negative from the seven before it:

* **Marvin, Speris, Legends, Prey** — planar assets, planar display, nothing to
  convert.
* **Liberation** — a first-person 3D engine whose renderer is a Blitter program
  drawing pre-rendered planar wall sprites, and whose two CD32 libraries sit
  behind one runtime flag because the same binary runs on an A1200.
* **Microcosm** — a CD32-exclusive with no A1200 path at all, whose video is
  stored planar because the conversion was done offline on a workstation.
* **Gloom** — a real-time chunky renderer, on a disc that also has an A1200 SKU,
  which sidesteps the conversion entirely by making the copper the framebuffer.

Nine discs, nine negatives, and the shape of the answer has changed again. The
checklist's prediction after Microcosm was that a CD32-exclusive real-time
renderer would settle it. Gloom is a real-time renderer and is *not*
CD32-exclusive — its hard-disk installer is on the disc — so it does not settle
the prediction. What it does settle is narrower and more useful: **"is there a
chunky buffer?" is not the right question. The right question is "is there a
planar destination?"** A title can rasterise in chunky and still never need
Akiko, if it never puts the result in bitplanes.
