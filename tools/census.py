#!/usr/bin/env python3
"""Per-file census: size, Shannon entropy, zlib ratio, first longword vs size,
last non-zero byte, and a magic-number scan. Section 5 of the platform notes
says the census comes *before* the magic scan; this does both, in that order.

    python tools/census.py _work/files
"""
import sys, os, math, zlib, hashlib, struct, collections

MAGICS = [b'RNC\x01', b'RNC\x02', b'IMP!', b'ATN!', b'PP20', b'PP11', b'XPKF',
          b'CrM!', b'CrM2', b'LZX', b'SQSH', b'\x00\x00\x03\xf3', b'FORM', b'DMS!',
          b'MMD0', b'MMD1', b'MMD2', b'MMD3', b'S404', b'S403', b'TPWM', b'RJP\x01']

def entropy(b):
    if not b: return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum((v / n) * math.log2(v / n) for v in c.values())

def lastnz(b):
    i = len(b) - 1
    while i >= 0 and b[i] == 0: i -= 1
    return i + 1

def walk(root):
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for f in sorted(fn):
            yield os.path.join(dp, f)

def main():
    root = sys.argv[1]
    print("%-28s %8s %6s %6s %10s %10s %8s  %s" %
          ("file", "size", "ent", "zlib", "first LW", "vs size", "lastnz", "magic"))
    rows = []
    hashes = collections.defaultdict(list)
    for p in walk(root):
        b = open(p, 'rb').read()
        rel = os.path.relpath(p, root).replace(chr(92), '/')
        e = entropy(b)
        z = len(zlib.compress(b, 9)) / len(b) if b else 0
        lw = struct.unpack_from('>I', b, 0)[0] if len(b) >= 4 else 0
        rel_note = ''
        if lw == len(b): rel_note = '== filesize'
        elif lw == len(b) - 4: rel_note = '== size-4'
        elif lw == len(b) + 4: rel_note = '== size+4'
        mg = ''
        for m in MAGICS:
            if b.startswith(m):
                mg = m.decode('latin1', 'replace'); break
        hashes[hashlib.sha1(b).hexdigest()].append(rel)
        rows.append((rel, len(b), e, z, lw, rel_note, lastnz(b), mg))
        print("%-28s %8d %6.3f %6.3f %10d %10s %8d  %s" %
              (rel, len(b), e, z, lw, rel_note, lastnz(b), mg))
    print()
    hi = [r for r in rows if r[2] >= 7.0]
    print("files at entropy >= 7.0: %d of %d" % (len(hi), len(rows)))
    for r in hi: print("   %-28s %6.3f" % (r[0], r[2]))
    print()
    print("first longword == filesize or filesize-4: %d" %
          len([r for r in rows if r[5]]))
    print()
    dups = {k: v for k, v in hashes.items() if len(v) > 1}
    print("duplicate SHA-1 groups: %d" % len(dups))
    for k, v in dups.items(): print("   %s  %s" % (k[:12], v))

    # whole-image magic sweep is done separately in scan_magic()
if __name__ == '__main__':
    main()
