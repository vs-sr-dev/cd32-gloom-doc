#!/usr/bin/env python3
"""Minimal AmigaDOS hunk-file reader: header, code/data/bss, reloc, symbol, debug."""
import sys, struct

HUNK = {
    0x3E7: 'HUNK_UNIT', 0x3E8: 'HUNK_NAME', 0x3E9: 'HUNK_CODE', 0x3EA: 'HUNK_DATA',
    0x3EB: 'HUNK_BSS', 0x3EC: 'HUNK_RELOC32', 0x3ED: 'HUNK_RELOC16', 0x3EE: 'HUNK_RELOC8',
    0x3EF: 'HUNK_EXT', 0x3F0: 'HUNK_SYMBOL', 0x3F1: 'HUNK_DEBUG', 0x3F2: 'HUNK_END',
    0x3F3: 'HUNK_HEADER', 0x3F5: 'HUNK_OVERLAY', 0x3F6: 'HUNK_BREAK',
    0x3F7: 'HUNK_DREL32', 0x3F8: 'HUNK_DREL16', 0x3F9: 'HUNK_DREL8',
    0x3FA: 'HUNK_LIB', 0x3FB: 'HUNK_INDEX',
}
MEM = {0: 'any', 1: 'chip', 2: 'fast'}

def be32(d, o): return struct.unpack_from('>I', d, o)[0]

def parse(path, verbose=True):
    d = open(path, 'rb').read()
    o = 0
    if be32(d, 0) != 0x3F3:
        raise SystemExit("%s: not a hunk file (first longword %08x)" % (path, be32(d, 0)))
    o = 4
    # resident library names
    names = []
    while True:
        n = be32(d, o); o += 4
        if n == 0: break
        names.append(d[o:o + n * 4].rstrip(b'\0').decode('latin1')); o += n * 4
    table_size = be32(d, o); first = be32(d, o + 4); last = be32(d, o + 8); o += 12
    sizes = []
    for i in range(last - first + 1):
        v = be32(d, o); o += 4
        sizes.append((v & 0x3FFFFFFF, MEM.get(v >> 30, '?%d' % (v >> 30))))
    if verbose:
        print("HUNK_HEADER  resident=%r  table_size=%d  first=%d last=%d" % (names, table_size, first, last))
        for i, (sz, m) in enumerate(sizes):
            print("  hunk %d: %d longwords = %d bytes  (%s)" % (i, sz, sz * 4, m))
    hunks = []
    cur = None
    hidx = -1
    while o < len(d):
        t = be32(d, o); o += 4
        tid = t & 0x3FFFFFFF
        name = HUNK.get(tid, 'UNKNOWN_%X' % tid)
        if tid in (0x3E9, 0x3EA):  # CODE, DATA
            n = be32(d, o); o += 4
            hidx += 1
            cur = dict(index=hidx, kind=name, off=o, size=n * 4, relocs=[], symbols=[], debug=[])
            hunks.append(cur)
            if verbose: print("%-14s hunk %d  %d bytes at file offset 0x%x" % (name, hidx, n * 4, o))
            o += n * 4
        elif tid == 0x3EB:  # BSS
            n = be32(d, o); o += 4
            hidx += 1
            cur = dict(index=hidx, kind=name, off=None, size=n * 4, relocs=[], symbols=[], debug=[])
            hunks.append(cur)
            if verbose: print("%-14s hunk %d  %d bytes (no file image)" % (name, hidx, n * 4))
        elif tid == 0x3EC:  # RELOC32
            total = 0
            while True:
                cnt = be32(d, o); o += 4
                if cnt == 0: break
                hno = be32(d, o); o += 4
                offs = [be32(d, o + 4 * i) for i in range(cnt)]
                o += 4 * cnt
                total += cnt
                if cur is not None: cur['relocs'].append((hno, offs))
            if verbose: print("%-14s %d entries" % (name, total))
        elif tid == 0x3F0:  # SYMBOL
            syms = []
            while True:
                n = be32(d, o); o += 4
                if n == 0: break
                s = d[o:o + n * 4].rstrip(b'\0').decode('latin1'); o += n * 4
                v = be32(d, o); o += 4
                syms.append((s, v))
            if cur is not None: cur['symbols'] = syms
            if verbose:
                print("%-14s %d symbols" % (name, len(syms)))
                for s, v in syms: print("      %-32s 0x%x" % (s, v))
        elif tid == 0x3F1:  # DEBUG
            n = be32(d, o); o += 4
            blob = d[o:o + n * 4]
            if cur is not None: cur['debug'].append((o, blob))
            if verbose: print("%-14s %d bytes at 0x%x  tag=%r" % (name, n * 4, o, blob[:12]))
            o += n * 4
        elif tid == 0x3F2:  # END
            if verbose: print("%-14s" % name)
        elif tid in (0x3ED, 0x3EE, 0x3F7, 0x3F8, 0x3F9):
            total = 0
            while True:
                cnt = be32(d, o); o += 4
                if cnt == 0: break
                o += 4
                o += (2 if tid in (0x3EE, 0x3F9) else 2) * cnt if tid in (0x3ED, 0x3EE, 0x3F8, 0x3F9) else 4 * cnt
                total += cnt
            o = (o + 3) & ~3
            if verbose: print("%-14s %d entries" % (name, total))
        else:
            if verbose: print("%-14s (0x%x) at 0x%x -- stopping" % (name, tid, o - 4))
            break
    return d, hunks, sizes

if __name__ == '__main__':
    parse(sys.argv[1])
