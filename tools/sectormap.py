#!/usr/bin/env python3
"""Build a sector map of the volume from the directory tree and list what
nothing claims. Built against the *declared* volume size, not the image size.

    python tools/sectormap.py <image.iso>
"""
import sys, struct, hashlib
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isoread import SECTOR, parse, walk, u32be


def main():
    data = open(sys.argv[1], 'rb').read()
    pvd = data[16 * SECTOR:17 * SECTOR]
    declared = u32be(pvd, 84)
    image = len(data) // SECTOR
    root = parse(pvd[156:190])
    entries = []
    walk(data, root['lba'], root['size'], '', entries)
    owner = [None] * declared
    def claim(lba, size, name):
        for s in range(lba, lba + max(1, (size + SECTOR - 1) // SECTOR)):
            if s < declared:
                owner[s] = name
    for s in range(0, 16): owner[s] = 'system area'
    owner[16] = 'PVD'; owner[17] = 'PVD (duplicate)'; owner[18] = 'terminator'
    # path tables
    ptl = struct.unpack_from('<I', pvd, 140)[0]
    ptm = struct.unpack_from('>I', pvd, 148)[0]
    ptsize = struct.unpack_from('>I', pvd, 136)[0]
    claim(ptl, ptsize, 'L path table')
    claim(ptm, ptsize, 'M path table')
    # trademark block, via the 'TM' tag in the application-use area
    au = pvd[883:1395]
    i = au.find(b'TM')
    if i >= 0:
        tmlen = struct.unpack_from('>I', au, i + 4)[0]
        tmlba = struct.unpack_from('>I', au, i + 8)[0]
        claim(tmlba, tmlen, '.TM block')
    claim(root['lba'], root['size'], 'root directory')
    for e in entries:
        claim(e['lba'], e['size'], e['path'] + ('/' if e['dir'] else ''))
    print("declared volume %d sectors, image %d sectors, overrun %d" %
          (declared, image, image - declared))
    if image > declared:
        tail = data[declared * SECTOR:]
        print("overrun is %s" % ("all zero" if not tail.strip(b'\0') else "NOT all zero"))
    runs = []
    s = 0
    while s < declared:
        if owner[s] is None:
            e = s
            while e < declared and owner[e] is None: e += 1
            runs.append((s, e - 1))
            s = e
        else:
            s += 1
    total = sum(b - a + 1 for a, b in runs)
    print("unclaimed sectors inside the declared volume: %d in %d runs" % (total, len(runs)))
    for a, b in runs:
        blob = data[a * SECTOR:(b + 1) * SECTOR]
        print("   LBA %d..%d (%d sectors) %s" %
              (a, b, b - a + 1, "all zero" if not blob.strip(b'\0') else "NOT zero"))


if __name__ == '__main__':
    main()
