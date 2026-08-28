#!/usr/bin/env python3
"""Sort every directory record by timestamp and print the mastering log."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from isoread import SECTOR, parse, walk, u32be

data = open(sys.argv[1], 'rb').read()
pvd = data[16 * SECTOR:17 * SECTOR]
root = parse(pvd[156:190])
entries = []
walk(data, root['lba'], root['size'], '', entries)
entries.append(dict(ts=root['ts'], path='/ (root directory record)', dir=True, size=root['size']))
print("PVD creation date: %s" % pvd[813:830].decode('latin1'))
print()
print("| timestamp | bytes | path |")
print("|---|---:|---|")
for e in sorted(entries, key=lambda x: (x['ts'], x['path'])):
    print("| %s | %d | `%s%s` |" % (e['ts'], e['size'], e['path'], '/' if e['dir'] else ''))
