# 02 — The `.TM` block

```
python tools/tmsector.py "Gloom (1995)(Guildhall Leisure Services)[!].iso"
```

## Follow the pointer

The primary volume descriptor's application-use area, from offset 883:

```
offset 883:  00
offset 884:  46 53 00 00        "FS"
offset 888:  54 4D 00 14        "TM", 0x0014 = 20      <- the constant
offset 892:  00 00 08 00        0x0800 = 2048          <- the block's length
offset 896:  00 00 00 15        0x15   = 21            <- the block's LBA
```

That is the ISOCD shape exactly: an `'FS'` record, then the `'TM'` tag, then the
fixed constant 20, then the length and the LBA. The block lands at sector 21
because the volume starts at 19 and the path tables take 19 and 20 — a
consequence of the layout, not a rule. Read the tag and follow the pointer;
do not assume the sector.

## Seven discs, the same 2,048 bytes

```
whole block   SHA-1 c5ffcef2a5e33d2df606185823cd95d1c174d65f   2,048 bytes
banner        SHA-1 8d84115154d70360b3469acc99cdad3db0ed2c92   bytes 0x000..0x44C
object file   SHA-1 690aae24a96b69659066e691d0b07db301260572   bytes 0x44C..0x7B8
```

All three match Dragonstone, Marvin, Prey CD32, Legends, Liberation and
Microcosm. **This is the seventh byte-identical copy.**

The first ~1,100 bytes are the Commodore ASCII-art banner:

```
*************************************************
*                                               *
* Copyright (c) 1993 - Commodore Electronics Ltd.*
*              All rights reserved.             *
*                                               *
*       CCCC    TM                              *
...
```

and from offset `0x44C` there are 876 bytes of unlinked AmigaDOS object file: a
compilation unit named `exec`, with `HUNK_EXT`, `HUNK_SYMBOL` and Commodore's
own assembler macro names (`REMHEAD.033`, `ENABLE.031/032/034`) intact. That
accident happened once, at Commodore, when the `CD32.TM` distribution file was
assembled; every disc since has copied the file.

The score across the format is now **seven discs with the Commodore banner and
one (Speris) carrying `cdtv.device` instead**. The mismatch took four discs to
find and four discs have matched since, which is the shape of the finding: the
block is whatever `.TM` file the person cutting the master handed the tool.

**Gloom ships no `.TM` file in its root**, like Speris and Microcosm and unlike
both Prey masters, which carry theirs as an ordinary file as well as embedding
it. Nothing on the disc reads the sector.
