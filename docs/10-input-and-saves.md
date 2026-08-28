# 10 — Input, saves, and a serial two-player link

Hunk offsets throughout; file offset = hunk offset + `0x20`.

## The CD32 pad, clocked by hand

`lowlevel.library` is never opened and never named. Instead the game drives the
controller port directly. There are two copies of the routine, one per port, at
hunk `0x40da` and hunk `0x4172`; the second reads:

```
4172  lea     $bfe001.l,a2         ; CIA-A port A
4178  lea     $dff016.l,a1         ; POTGOR
417e  moveq   #7,d3                ; bit 7 -- this port's clock line
4180  move.w  #$4000,d4            ; the POTGOR data bit for this port
4184  bset    d3,$200(a2)          ; $BFE201: make bit 7 an output
4188  bclr    d3,(a2)              ; $BFE001: drive it low
418a  move.w  #$2000,$dff034.l     ; POTGO: start the shift
4192  moveq   #0,d0
4194  moveq   #6,d1                ; seven bits
4196: tst.b   (a2)   x8            ; the settling delay
41a6  move.w  (a1),d2              ; POTGOR
41a8  bset    d3,(a2)              ; clock high
41aa  bclr    d3,(a2)              ; clock low
41ac  and.w   d4,d2
41ae  bne.s   +
41b0  bset    d1,d0                ; a pressed button reads as 0
41b2: dbra    d1,$4196
41b6  move.w  #$3000,$dff034.l     ; POTGO: release
41be  bclr    d3,$200(a2)          ; $BFE201: bit 7 back to an input
```

That is the CD32 controller protocol written out by hand: pulse the port's clock
line and read the pad's shift register one bit at a time through `POTGOR`.
**`moveq #6,d1` and `dbra` make seven iterations — all seven buttons**
(play/pause, reverse, forward, green, yellow, red, blue), with the two fire
buttons and the directions coming from `JOY0DAT`/`JOY1DAT` and CIA-A as on any
Amiga. The front end offers `PLAYER 1 CD32 PAD 1` and `PLAYER 2 CD32 PAD 2`
beside `JOYSTICK 1`, `JOYSTICK 2` and ` KEYBOARD `.

Doing it this way rather than through `lowlevel.library` means the same code
reads a CD32 pad on a CD32 and a plain joystick on an A1200, with no branch and
no library that might be missing.

## The save system: `nonvolatile.library`, one call per vector

The only CD32-specific library the disc touches. The strings sit together at
hunk `0x5c94`:

```
5c94  "Gloom"                      the application name
5c9a  "Games"                      the item name
5ca0  "gamegamegamegamegame"       20 bytes of data buffer
5cb4  "nonvolatile.library"
```

**Save**, at hunk `0x5cd4`:

```
5cd4  movea.l d0,a6                ; the library base
5cd6  lea     $5c94(pc),a0         ; "Gloom"
5cda  lea     $5c9a(pc),a1         ; "Games"
5cde  lea     $5ca0(pc),a2         ; the buffer
5ce2  moveq   #2,d0                ; <-- length
5ce4  moveq   #-1,d1               ; killRequested
5ce6  jsr     -42(a6)              ; StoreNV
5cea  tst.l   d0
5cec  bne.s   done
5cee  lea     $5c94(pc),a0
5cf2  lea     $5c9a(pc),a1
5cf6  moveq   #-1,d1
5cf8  moveq   #1,d2
5cfa  jsr     -66(a6)              ; SetNVProtection
```

**Load**, at hunk `0x5d00`:

```
5d00  move.l  $5cc8.l,d0           ; the library base
5d06  beq.s   done                 ; absent? then there is no saved game
5d08  movea.l d0,a6
5d0a  lea     $5c94(pc),a0         ; "Gloom"
5d0e  lea     $5c9a(pc),a1         ; "Games"
5d12  moveq   #-1,d1               ; killRequested
5d14  jsr     -30(a6)              ; GetCopyNV
5d18  tst.l   d0
5d1a  beq.s   done
5d1c  movea.l d0,a0
5d1e  lea     $5ca0(pc),a1         ; the 20-byte buffer
5d22  moveq   #4,d1
5d24: move.l  (a0)+,(a1)+          ; five longwords = 20 bytes
      dbra    d1,$5d24
5d2a  movea.l d0,a0
5d2c  jsr     -36(a6)              ; FreeNVData
```

All four of `nonvolatile.library`'s vectors, one call each — the same shape
Liberation shows. Three things are worth recording exactly as measured.

**The base is null-checked at every use.** The library is opened with
`OldOpenLibrary` and no error branch (see
[04-boot-chain.md](04-boot-chain.md)), but the load path starts
`move.l $5cc8.l,d0 / beq` and the save path is only reached with the base
already in `a6`. The game runs with its save system silently absent, which is
what a binary that also ships on floppy has to do.

**The store declares two bytes and the load copies twenty.** `StoreNV`'s length
parameter is `D0` and it is `moveq #2,d0`; `GetCopyNV` returns a copy of what
was stored and the loader then reads five longwords out of it. If the documented
register conventions hold, the game writes a two-byte NVRAM item and reads
eighteen bytes past the end of the allocation it gets back. This document does
not assert that as a bug — the parameter registers come from Commodore's
published API, not from a disassembly of the library — but the `moveq #2` and
the `dbra` count are what the bytes say, and they do not agree with each other.
It is listed in [12-open-questions.md](12-open-questions.md).

**The buffer's initial contents shipped.** Twenty bytes reading
`gamegamegamegamegame` sit in the executable's data. On a machine with no saved
game and no `nonvolatile.library`, that string *is* the save state the game
starts from. It is the same filler as `/gloomgame`, a 32-byte file in the root
containing `gamegamegamegamegamegamegamegame` and **named by nothing in the
executable** — see [11-archaeology.md](11-archaeology.md).

Across the nine discs the save systems are now: a password (Dragonstone,
Legends), a password plus `nonvolatile` (Marvin), `nonvolatile` plus floppy
save-disk code (Speris), none at all (both Preys), `nonvolatile` alone and
unguarded (Microcosm), four mechanisms at once (Liberation), and
**`nonvolatile` alone with the base null-checked at every use** (Gloom).

## A serial two-player link, with a modem dialler

The front end's menu strings are all in the clear:

```
ONE PLAYER GAME          TWO PLAYER GAME          TWO PLAYER COMBAT
PLAYER 1 CD32 PAD 1      PLAYER 2 CD32 PAD 2
REMOTE LINK OPTIONS      UNLINK FROM REMOTE PLAYER
RESOLUTION               WINDOW SIZE              FULL SCREEN WINDOW
FLOOR                    CEILING
VIOLENCE MODEL: MEATY    MEATY   MESSY
ABOUT GLOOM              EXIT GLOOM               CONTINUE        QUIT GAME
```

and behind `REMOTE LINK OPTIONS`:

```
NULL LINK      NULL MODEM      DIAL UP      ANSWER
BAUD RATE: 2400
DIAL:
ATDT
ATTEMPTING TO CONNECT...ESC TO ABORT
CONNECT
waiting for other player
player selects options / other player selects options
```

`ATDT` is the Hayes tone-dial command. `SERDAT` and `SERPER` are each written
once, absolutely. So the CD32 release carries a **two-player mode over a null
modem cable or an actual modem at 2400 baud**, on a console whose serial port
most owners never used, and it carries a dialler for it.

The chat that goes with it is the hires strip at the top of the display
(see [07-display-and-akiko.md](07-display-and-akiko.md)): 640 pixels, two
bitplanes, three colours, an 800-byte chip bitmap, a scrolling text routine at
hunk `0x687e` that shifts the whole line left byte by byte, its own 40-glyph
character mapper at hunk `0x68c6` (`A`–`Z` to 9–34, `.` `!` `?` `,` to 36–39,
`0`–`9` to 0–9), and a keyboard table at hunk `0x9229`:

```
QWERTYUIOP
 ASDFGHJKL
1ZXCVBNM
```

The string `CHAT MODE ENABLED` is at hunk `0x67d6`.

The combat mode's own result strings are there too — `player one wins combat
game!`, `player two wins combat game!`, and, for the case where there is no
second player, `player wins combat game!` and `player loses combat game!`.
