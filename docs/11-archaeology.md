# 11 — Archaeology

The platform checklist's ninth open item asks whether a CD32 disc exists that
*was* cleaned up before it was pressed. This one was not, and what it kept is
unusually coherent: nearly all of it points the same way, at a floppy-and-hard-disk
release that the CD32 build is a light dressing on top of.

## The credits screen, in full

At hunk `0x0a9dd`:

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

Four of those lines are tool attributions, and **three of them are confirmed by
the disc itself**, from three different directions:

* `DECRUNCHING CODE BY THOMAS SCHWARZ` — every packed file on the disc carries
  the `CrM2` magic of Thomas Schwarz's **CrunchMania**
  ([05-compression.md](05-compression.md)).
* `UTILITIES CODED IN BLITZ BASIC 2` — `/s/startup-sequence.info` is a Workbench
  **project** icon whose `DefaultTool` is `blitz2:blitz2`
  ([04-boot-chain.md](04-boot-chain.md)).
* `RENDERED IN DPAINT3 AND DPAINT4` — four of the six `pics/*.pal` files begin
  with the Deluxe Paint default 16-colour palette, untouched
  ([08-graphics-formats.md](08-graphics-formats.md)).

`GAME CODED IN DEVPAC2` is consistent with what the executable is: a single
174 KB hunk with no `HUNK_SYMBOL`, no `HUNK_DEBUG`, 1,277 relocations and
hand-written interrupt code throughout.

The data preparer field is empty, so unlike Legends there is no mastering-tool
name to cross-check against the credits. This is the attribution the disc gives
instead, and it is richer.

## The floppy release is still on the disc, four times over

**`/Gloom->HD`, 26,200 bytes** — an AmigaDOS executable, one 23,852-byte hunk
with 574 relocations, SAS/C-compiled (`mathffp.library`, `subchk`), opening
`dos`, `intuition`, `graphics`, `exec` and `console.device`, with an IFF reader
(`BMHD`, `BODY`, `CMAP`, `CRNG`) for its own dialog artwork. Its strings:

```
Gloom Harddrive Installer
&Select destination directory for Gloom
Work:Games
Can't open selected directory!
&Please select a directory, not a file!
Installing Gloom to
gloomprog:
gloomdata:
Installation complete!
Finished
Please insert disk
Copying
INSTALL   ABORT
```

`Please insert disk ` is a floppy prompt in an installer that assigns
`gloomprog:` and `gloomdata:` — **the two-disk floppy release's volume names**,
which is exactly the "read the loader's paths for evidence of the earlier
release" step, paying out on a program the CD32 can never usefully run. Legends
carries its A1200 installer the same way; this is the second disc of nine to do
it.

**Two floppy prompts compiled into the CD32 game executable:**

```
hunk 0x06ef7   please insert gloom data disk
hunk 0x094c1   please write enable the gloom data disk!
```

The second is the one that gives it away: a CD is never write-enabled and the
CD32 has no disk to swap. Those are the floppy build's disk-swap and save-disk
messages, still linked in, in a program whose save system is
`nonvolatile.library`.

**`/s/startup-sequence.bak`**, 31 bytes, is the boot script the CD32 one
replaced:

```
setpatch quiet
run >nil: gloom
```

**`/gloomgame`**, 32 bytes, contents `gamegamegamegamegamegamegamegame`, is
named by no string in any executable on the disc. The CD32 build keeps the same
filler in a 20-byte NVRAM buffer instead
([10-input-and-saves.md](10-input-and-saves.md)). It is the floppy release's
save file, pressed onto a read-only medium.

Put together: **the CD32 build is the floppy/hard-disk build.** It opens no
`lowlevel.library`, reads the pad by hand so the same code works with a
joystick, null-checks `nonvolatile.library` at every use so it degrades on a
machine that has none, ships a Workbench tool icon on the game executable, and
carries the other SKU's installer, boot script, save file and disk prompts. The
platform checklist's discriminating test for "did not use Akiko" versus "could
not use Akiko" comes out on the *could not* side — except that on this disc it
turns out not to matter, because there was nothing to convert
([07-display-and-akiko.md](07-display-and-akiko.md)).

## Ten debug colour flashes, and the game's entire error handling

Ten sites in the executable do this:

```
move.w  d0,-(sp)
move.w  #$ffff,d0
move.w  #$0000,$dff106      ; BPLCON3: bank 0, LOCT off
move.w  #<colour>,$dff180   ; COLOR00
dbra    d0,-               ; 65,536 times
move.w  (sp)+,d0
```

| Hunk | Colour | |
|---|---|---|
| `0x0115c` | `$0f0f` | magenta |
| `0x06b4c` | `$0f00` | red |
| `0x06b68` | `$0fff` | white |
| `0x07880` | `$0f80` | orange |
| `0x0838e` | `$0f08` | pink |
| `0x083aa` | `$080f` | violet |
| `0x08712` | `$0f0f` | magenta |
| `0x09de2` | `$0f00` | red |
| `0x09e72` | `$0ff0` | yellow |
| `0x0a092` | `$000f` | blue |

They are the only ten writes to `BPLCON3` and the only ten to `COLOR00` in the
whole file. What they do is paint the screen background a colour and spin.

The one at `0x09de2` is the memory allocator's failure path:

```
9dda  jsr     -198(a6)            ; AllocMem
9dde  tst.l   d0
9de0  bne.s   ok
9de2  ... red flash, 65,536 iterations ...
9dfe  movea.l d0,a0               ; d0 is still zero
9e00  move.l  $504a.l,(a0)        ; and it writes through it
```

**Out of memory in the shipped retail game means: flash the screen red for about
a tenth of a second, then write to address zero.** Microcosm's equivalent is 195
copies of `internal hardware error`; Gloom's is ten colours and no text at all.

## A demo build's refusal, in the retail binary

At hunk `0x07425`, in a string table whose entries are prefixed with a one-byte
index:

```
01 "sorry...not available in demo"
```

Liberation ships `[Sorry, this is only a 1 disk demo.]` as a dialogue record in
its retail executable. **That is now two discs of nine carrying a demo build's
refusal into the retail product**, from unrelated studios two years apart. It is
worth promoting from an oddity to a thing to check for.

## `CHAT MODE ENABLED`

At hunk `0x067d6`, beside the modem dialler and the hires text line
([10-input-and-saves.md](10-input-and-saves.md)). Whether it is reachable from
the shipped front end is not settled here; the string is written in the
imperative-report style of a development message rather than in the lower-case
style of every other message the player sees (`health bonus!`,
`weapon boosted to full!`, `got the thermo glasses!`).

## `WankFuckShit`

Twelve bytes at hunk `0x23f33`, immediately after the string `ciax.resource` at
`0x23f24`, inside the OctaMED player. `ciax.resource` is itself a template — the
program patches the `x` to `a` or `b` before each of its two `OpenResource`
calls. The obscenity is NUL-terminated, referenced by nothing this document
could find, and sits in the middle of the player's data area. It is on a pressed
retail disc.

## 224 empty palette slots per texture bank

Nine of the twelve wall-texture banks declare a 256-entry palette, fill 32 of it
and leave the remaining 224 entries as `FFFF`. That is 448 bytes a bank and
5.4 KB across the disc of a sentinel meaning "no colour here"
([08-graphics-formats.md](08-graphics-formats.md)). Legends' `EMPTY PAL` slots
are the same phenomenon with a name on it.

## The number 2 is missing

The mission script names three campaigns, the front end offers three, and the
files are numbered `1`, `3` and `4`:

| | Textures | Maps |
|---|---|---|
| Spacehulk | `txt1_0` … `txt1_4` | `map1_1` … `map1_7` |
| Gothic tomb | `txt3_1` … `txt3_4` | `map3_1` … `map3_7` |
| Hell | `txt4_1` … `txt4_3` | `map4_1` … `map4_7` |

**There is no `txt2_*` and no `map2_*` anywhere on the disc**, and no string in
any executable names one. Meanwhile the two-player arenas are numbered
contiguously, `com1_*`, `com2_*`, `com3_*`, twenty-one files with no gap. And
the script addresses the three campaigns by a *different* index again —
`tile_1`, `tile_2`, `tile_3` — so the gap is in the asset naming only.

That is as far as the disc goes. It does not prove a cut second zone; a
numbering that skips 2 can as easily be a renumbering that was never done. What
it does show is that the two families with a gap are the ones tied to the
campaigns and the family without a gap is not. Recorded in
[12-open-questions.md](12-open-questions.md) with the measurement beside it.

## Small things

* **The mission script ships as plain text**, uncompiled, at `misc/script`, in a
  CrunchMania container: 140 command lines drawn from ten of a vocabulary of
  fourteen
  (`pict draw text wait play done dark show hide loop rest tile cont_ game`),
  dispatched by a chain of `cmp.l #'pict',d0 / beq` at hunk `0x7800`. It opens
  with a comment:

  ```
  ;
  ;script for gloom game
  ;
  ```

  and it contains all 22 of the game's mission briefings in lower case, jokes
  included: `beware the wheel of death!`, `don't let those teleports confuse
  you!`, `ummmm...shoot...shoot...run...shoot...`, `chunky chunder chunks...from
  hell of course!`, `stop dragon your feet!`. On a format where the text is
  usually a compiled string table, an editable script with the author's comment
  markers still in it is worth reading to the end.

* **The `CrM!` decoder ships and nothing uses it.** Both CrunchMania methods are
  linked in; every file on the disc is method 2.

* **8,256 bytes of zeros at the end of the code hunk**, plus a 1,248-byte zero
  run at hunk `0x25046` for the decruncher's tables. 52,097 of the hunk's
  174,128 bytes — 29.9 % — are zero. A `HUNK_BSS` would have cost nothing on
  the disc; four sectors were spent instead.

* **`freeanim` and the boot script's icon are fourteen minutes older than every
  other file** ([03-timestamps.md](03-timestamps.md)), and `freeanim` is
  byte-identical to the one on the CD32 release of Liberation.

* **The `.TM` sector nothing reads** still carries 876 bytes of Commodore's own
  `exec` build output, for the seventh time ([02-trademark-block.md](02-trademark-block.md)).

## The publisher control: Guildhall twice

Legends (Krisalis Software / Guildhall, 1996) and Gloom (Black Magic Software /
Guildhall, 1995) are the two discs in this series with the same publisher, a
year apart. If mastering practice were a publisher-level habit they should look
alike. They do not:

| | Legends (1996) | Gloom (1995) |
|---|---|---|
| Preparer | `Richard Teather (Programmer) - …` | **empty name** |
| Application id | `Legends` | **empty** |
| Cue `CATALOG` | `5012323060062` | no cue supplied |
| Timestamps | all `1992-03-06` — impossible | all real, one hour |
| Audio tracks | **28**, 88.6 % of the disc | none in this dump, and no `cd.device` |
| Cruncher | Bytekiller, no magic number | **CrunchMania `CrM2`** |
| `SetPatch` | 39.6 (8.9.92) | **40.3 (10.5.93)** |
| `c/` directory | yes | **none** |
| Save system | password | `nonvolatile.library` |
| Display | 8 planes front end, 4–5 planes levels | **7 planes throughout** |
| `Disk.info` SHA-1 | `cf7194c0cc95` | `234e5e5b0322` |

**Nothing carries across.** The two discs share one habit and it is not the
publisher's: both ship the other SKU's hard-disk installer, which is a studio
decision about what was in the build directory.

Where a shared file *does* turn up, it crosses publishers instead: Gloom's
`freeanim` is Liberation's (Mindscape), and Legends' `SetPatch` is Marvin's
(21st Century). **On this format the unit of shared practice is the developer's
tool shelf, not the label on the box.** Prey CDTV against Prey CD32 remains the
only control that has ever corrected a claim here; a publisher-level control
does not.
