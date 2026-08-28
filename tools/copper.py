#!/usr/bin/env python3
"""Disassemble an Amiga copper list out of a file at a given offset.

    python tools/copper.py <file> <offset> <length>
"""
import sys, struct

REG = {0x02:'DMACONR',0x08e:'DIWSTRT',0x090:'DIWSTOP',0x092:'DDFSTRT',0x094:'DDFSTOP',
 0x096:'DMACON',0x098:'CLXCON',0x09a:'INTENA',0x09c:'INTREQ',0x09e:'ADKCON',
 0x080:'COP1LCH',0x082:'COP1LCL',0x084:'COP2LCH',0x086:'COP2LCL',0x088:'COPJMP1',0x08a:'COPJMP2',
 0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',0x106:'BPLCON3',0x108:'BPL1MOD',0x10a:'BPL2MOD',
 0x10c:'BPLCON4',0x1fc:'FMODE',0x1fe:'NOP',0x05a:'BLTCON0L',0x1dc:'BEAMCON0',
 0x040:'BLTCON0',0x042:'BLTCON1',0x058:'BLTSIZE'}
for i in range(8):
    REG[0x0e0+4*i] = 'BPL%dPTH' % (i+1); REG[0x0e2+4*i] = 'BPL%dPTL' % (i+1)
for i in range(32):
    REG[0x180+2*i] = 'COLOR%02d' % i
for i in range(8):
    b = 0x120 + 4*i
    REG[b] = 'SPR%dPTH' % i; REG[b+2] = 'SPR%dPTL' % i
for i in range(8):
    b = 0x140 + 8*i
    REG[b]='SPR%dPOS'%i; REG[b+2]='SPR%dCTL'%i; REG[b+4]='SPR%dDATA'%i; REG[b+6]='SPR%dDATB'%i


def main():
    path, off, ln = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    d = open(path, 'rb').read()
    o = off
    while o < off + ln:
        a, b = struct.unpack_from('>HH', d, o)
        if a == 0xFFFF and b == 0xFFFE:
            print("%06x  ffff fffe   END" % o); break
        if a & 1:
            kind = 'WAIT' if not (b & 1) else 'SKIP'
            vp, hp = a >> 8, a & 0xFE
            print("%06x  %04x %04x   %s  VP=%02x HP=%02x  mask=%04x" % (o, a, b, kind, vp, hp, b))
        else:
            r = a & 0x1FE
            print("%06x  %04x %04x   MOVE %-8s <- %04x" % (o, a, b, REG.get(r, '$%03x' % r), b))
        o += 4


if __name__ == '__main__':
    main()
