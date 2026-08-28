# 04 — The boot chain

## Three lines, and no `c/`

`/s/startup-sequence`, 42 bytes:

```
freeanim >nil:
setpatch >nil:
gloom >nil:
```

**There is no `c/`, no `libs/` and no `devs/` directory on this disc.** The two
commands the script runs sit in the root, and Kickstart's `C:` assign finds them
because on a booted CD32 volume the root *is* on the search path. Nine discs in,
that is a fourth shape for the boot directory:

* a whole Workbench `C:` with 59 commands (Prey);
* a small `c/` with SetPatch plus one or two studio tools (Dragonstone, Marvin,
  Speris, Legends, Liberation);
* **no directory at all and no commands** (Microcosm, whose five-byte script
  runs one executable);
* **no directory, but the commands in the root** — this disc.

The order is `freeanim`, then `setpatch`, then the game. Opening
`freeanim.library` first, before anything else, is what the *Amiga CD32
Developer Notes* prescribe: the open tells the console's boot animation to begin
shutting down and returns immediately, and the title is meant to spend the
interval initialising. Here the interval is filled by `SetPatch`, which is a
better use of it than Microcosm's zero-instruction gap and a worse one than
Dragonstone's whole loader.

There is no `NoOpenWB`, no redirection beyond `>nil:` and no reboot command.

## `/s/startup-sequence.bak` — the script this one replaced

31 bytes, sitting on the disc beside the live one:

```
setpatch quiet
run >nil: gloom
```

No `freeanim` — because the machine it was written for had no boot animation to
dismiss — and `run`, which detaches the game from the shell so the shell can
exit. **That is the floppy or hard-disk release's boot script, kept as a backup
file and pressed onto the CD.** It is the cheapest single piece of evidence on
this disc that the CD32 build is the floppy build with a CD32 boot script
dropped on top; see [11-archaeology.md](11-archaeology.md) for the rest.

## `/setpatch` — a fifth version

```
$VER: setpatch 40.3 (10.5.93)
This disk requires Kickstart version 2.0 or greater.
```

10,964 bytes. The known versions across this series are now:

| Version | Date | Disc |
|---|---|---|
| 39.6 | 8.9.92 | Marvin, **Legends** (byte-identical binaries) |
| **40.3** | **10.5.93** | **Gloom** |
| 40.12 | 16.9.93 | Prey CD32, Liberation |
| 40.14 | 7.10.93 | Dragonstone |
| 40.16 | 14.2.94 | Speris (ships, never run) |

Six discs, five versions, no agreement, and the version has nothing to do with
the machine: this is a 3.1-era SetPatch from May 1993 running on a CD32's 3.1
ROM in 1995.

## `/freeanim` — byte-identical to Liberation's

3,492 bytes.

```
SHA-1  449c610071ace58d8c7877aafd114588b8aa7074
```

**That is byte for byte `/c/FreeAnim` on the CD32 release of Liberation: Captive
II** (Byte Engineers / Mindscape, mastered 1994-04-15, where the file is dated
1993-05-19). Two unrelated studios, two publishers, fourteen months apart,
the same 3,492 bytes.

Inside it, exactly what Liberation's disassembly showed:

```
HUNK_DEBUG    HEADDBGV01            SAS/C 6
HUNK_CODE     2,788 bytes, 3 relocations
HUNK_SYMBOL   _main
HUNK_DATA     348 bytes, 6 relocations
strings:      dos.library, freeanim.library, intuition.library,
              "** User Abort Requested **", "*** Break: ", main.c,
              /auto/close/wait
```

`/auto/close/wait` is its `ReadArgs` template, and this is the **fourth**
sighting of that exact string on the format — Prey's `c/freeanim`, `cdgsxl`
1.48's data hunk, Liberation's `c/FreeAnim`, and now this. It is one wrapper
circulating between studios, and this disc is the first place two copies of it
have been shown to be the same bytes rather than the same idea.

The platform checklist's file-hash observation therefore has a third member:
the `.TM` block (seven discs), `SetPatch` 39.6 (Marvin and Legends), and now
`freeanim` (Liberation and Gloom). Commodore-era developer files circulated as
single copies and studios passed them around.

## Libraries: three, and one of them CD32-only

`tools/lvo.py` attributes 56 of the 57 `jsr d16(a6)` sites in the executable:

| Library | Opened by | Calls |
|---|---|---:|
| `exec.library` | `4.w` | 26 |
| `dos.library` | `OldOpenLibrary` (−408) | 12 |
| `graphics.library` | `OldOpenLibrary` (−408) | 5 |
| `nonvolatile.library` | `OldOpenLibrary` (−408) | 4 |
| `ciaa.resource` / `ciab.resource` | `OpenResource` (−498) ×2 | 3 |

All three library opens go through **`OldOpenLibrary` (−408)**, so no version is
requested — the same choice Marvin and Prey make and the opposite of
Liberation's nine `OpenLibrary` calls.

`lowlevel.library` is **never opened and never named**. The CD32 pad is clocked
by hand out of CIA-A and `POTGO` instead (see
[10-input-and-saves.md](10-input-and-saves.md)). `cd.device` is never opened
either — there is no `OpenDevice` call anywhere in the file.

`nonvolatile.library` is opened with no guard flag and no test at the call site:

```
lea     $5cb4.l,a1          ; "nonvolatile.library"
movea.l 4.w,a6
jsr     -408(a6)            ; OldOpenLibrary
move.l  d0,$5cc8.l
```

but **every use of the base tests it for zero first** —
`move.l $5cc8.l,d0 / beq` on the load path, `tst.l` on the save path — so the
game runs with the save system silently absent on a machine that has no such
library. That is Liberation's A1200 hedge done with a null check rather than a
runtime flag, and it is the discriminating evidence the platform checklist asks
for: **this binary expects to run somewhere that is not a CD32.**

## Icons: a second entry point, and one that names Blitz Basic

Four `.info` files, read with their `do_Type`:

| File | Type | `DefaultTool` |
|---|---|---|
| `/Disk.info` | `WBDISK` | `SYS:System/DiskCopy` |
| `/Gloom.info` | **`WBTOOL`** | — (a tool has none) |
| `/Gloom->HD.info` | `WBTOOL` | empty |
| `/s/startup-sequence.info` | `WBPROJECT` | **`blitz2:blitz2`** |

`/Gloom.info` makes the game executable double-clickable on an A1200 or A4000
desktop — a **fifth** form of the second-entry-point pattern the checklist
tracks (Marvin's `IconX` script, Legends' `Disk.info` plus HD installer,
Liberation's `SYS:c/iconx` project icon, Microcosm's total absence, and now a
plain tool icon on the game itself). Four of nine discs now have one.

`/s/startup-sequence.info` is the find. It is a **project** icon whose default
tool is `blitz2:blitz2` — the boot script was last opened, on somebody's
development machine, from **Blitz Basic 2**, and Workbench wrote that into the
icon. The credits screen inside the game says
`UTILITIES CODED IN BLITZ BASIC 2`. Two halves of the disc agree without either
knowing about the other, exactly as Legends' preparer field agreed with its
credits photograph.
