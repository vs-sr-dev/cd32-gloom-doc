#!/usr/bin/env python3
"""Static scans over a 68k binary: library-call LVOs, custom-chip registers,
Akiko references, io_Command immediates.

    python tools/scan.py <file> [--lvo] [--regs] [--akiko] [--iocmd] [--all]
"""
import sys, struct, collections

def be16(d, o): return struct.unpack_from('>H', d, o)[0]
def be32(d, o): return struct.unpack_from('>I', d, o)[0]
def s16(v): return v - 0x10000 if v & 0x8000 else v

REG = {
    0x000:'BLTDDAT',0x002:'DMACONR',0x004:'VPOSR',0x006:'VHPOSR',0x008:'DSKDATR',
    0x00A:'JOY0DAT',0x00C:'JOY1DAT',0x00E:'CLXDAT',0x010:'ADKCONR',0x012:'POT0DAT',
    0x014:'POT1DAT',0x016:'POTGOR',0x018:'SERDATR',0x01A:'DSKBYTR',0x01C:'INTENAR',
    0x01E:'INTREQR',0x020:'DSKPTH',0x022:'DSKPTL',0x024:'DSKLEN',0x02A:'VPOSW',
    0x02C:'VHPOSW',0x02E:'COPCON',0x030:'SERDAT',0x032:'SERPER',0x034:'POTGO',
    0x036:'JOYTEST',0x03A:'STREQU',0x03C:'STRVBL',0x03E:'STRHOR',0x040:'BLTCON0',
    0x042:'BLTCON1',0x044:'BLTAFWM',0x046:'BLTALWM',0x048:'BLTCPTH',0x04A:'BLTCPTL',
    0x04C:'BLTBPTH',0x04E:'BLTBPTL',0x050:'BLTAPTH',0x052:'BLTAPTL',0x054:'BLTDPTH',
    0x056:'BLTDPTL',0x058:'BLTSIZE',0x05A:'BLTCON0L',0x05C:'BLTSIZV',0x05E:'BLTSIZH',
    0x060:'BLTCMOD',0x062:'BLTBMOD',0x064:'BLTAMOD',0x066:'BLTDMOD',0x070:'BLTCDAT',
    0x072:'BLTBDAT',0x074:'BLTADAT',0x07C:'DENISEID',0x07E:'DSKSYNC',0x080:'COP1LCH',
    0x082:'COP1LCL',0x084:'COP2LCH',0x086:'COP2LCL',0x088:'COPJMP1',0x08A:'COPJMP2',
    0x08E:'DIWSTRT',0x090:'DIWSTOP',0x092:'DDFSTRT',0x094:'DDFSTOP',0x096:'DMACON',
    0x098:'CLXCON',0x09A:'INTENA',0x09C:'INTREQ',0x09E:'ADKCON',
    0x0A0:'AUD0LCH',0x0A2:'AUD0LCL',0x0A4:'AUD0LEN',0x0A6:'AUD0PER',0x0A8:'AUD0VOL',0x0AA:'AUD0DAT',
    0x0B0:'AUD1LCH',0x0B2:'AUD1LCL',0x0B4:'AUD1LEN',0x0B6:'AUD1PER',0x0B8:'AUD1VOL',0x0BA:'AUD1DAT',
    0x0C0:'AUD2LCH',0x0C2:'AUD2LCL',0x0C4:'AUD2LEN',0x0C6:'AUD2PER',0x0C8:'AUD2VOL',0x0CA:'AUD2DAT',
    0x0D0:'AUD3LCH',0x0D2:'AUD3LCL',0x0D4:'AUD3LEN',0x0D6:'AUD3PER',0x0D8:'AUD3VOL',0x0DA:'AUD3DAT',
    0x0E0:'BPL1PTH',0x0E2:'BPL1PTL',0x0E4:'BPL2PTH',0x0E6:'BPL2PTL',0x0E8:'BPL3PTH',0x0EA:'BPL3PTL',
    0x0EC:'BPL4PTH',0x0EE:'BPL4PTL',0x0F0:'BPL5PTH',0x0F2:'BPL5PTL',0x0F4:'BPL6PTH',0x0F6:'BPL6PTL',
    0x0F8:'BPL7PTH',0x0FA:'BPL7PTL',0x0FC:'BPL8PTH',0x0FE:'BPL8PTL',
    0x100:'BPLCON0',0x102:'BPLCON1',0x104:'BPLCON2',0x106:'BPLCON3',0x108:'BPL1MOD',0x10A:'BPL2MOD',
    0x10C:'BPLCON4',0x110:'BPL1DAT',0x112:'BPL2DAT',0x114:'BPL3DAT',0x116:'BPL4DAT',
    0x118:'BPL5DAT',0x11A:'BPL6DAT',0x11C:'BPL7DAT',0x11E:'BPL8DAT',
    0x180:'COLOR00',0x1FC:'FMODE',0x1FE:'NOP',
}
for i in range(32):
    REG.setdefault(0x180 + 2*i, 'COLOR%02d' % i)
for i in range(8):
    b = 0x120 + 4*i
    REG[b] = 'SPR%dPTH' % i; REG[b+2] = 'SPR%dPTL' % i
for i in range(8):
    b = 0x140 + 8*i
    REG[b]='SPR%dPOS'%i; REG[b+2]='SPR%dCTL'%i; REG[b+4]='SPR%dDATA'%i; REG[b+6]='SPR%dDATB'%i

def regs(d):
    """Histogram absolute custom-chip register references: any longword 00DFF0xx / 00DFFxxx."""
    h = collections.Counter()
    for i in range(0, len(d) - 4):
        if d[i] == 0x00 and d[i+1] == 0xDF and d[i+2] in (0xF0, 0xF1):
            off = ((d[i+2] & 0x0F) << 8) | d[i+3]
            h[off] += 1
    return h

def lvos(d):
    """Histogram jsr/jmp d16(a6) -- 4EAE xxxx / 4EEE xxxx."""
    h = collections.Counter()
    sites = collections.defaultdict(list)
    for i in range(0, len(d) - 4, 2):
        w = be16(d, i)
        if w in (0x4EAE, 0x4EEE):
            off = s16(be16(d, i + 2))
            h[off] += 1
            sites[off].append(i)
    return h, sites

def akiko(d):
    out = {}
    out['bytes 00 B8 00 00'] = [i for i in range(len(d)-4) if d[i:i+4] == b'\x00\xb8\x00\x00']
    out['bytes 00 B8 00 38 (C2P port)'] = [i for i in range(len(d)-4) if d[i:i+4] == b'\x00\xb8\x00\x38']
    out['bytes 00 B8 00 3C'] = [i for i in range(len(d)-4) if d[i:i+4] == b'\x00\xb8\x00\x3c']
    out['C0DE0000 id constant'] = [i for i in range(len(d)-4) if d[i:i+4] == b'\xc0\xde\x00\x00']
    out['any 00 B8 00 xx'] = [i for i in range(len(d)-3) if d[i]==0 and d[i+1]==0xB8 and d[i+2]==0]
    return out

def iocmd(d):
    """move.w #n,$1c(An)  ==  3?7c 00nn 001c"""
    h = collections.Counter()
    for i in range(0, len(d) - 6, 2):
        w = be16(d, i)
        if (w & 0xF1FF) == 0x317C and be16(d, i+2) < 0x100 and be16(d, i+4) == 0x001C:
            h[be16(d, i+2)] += 1
    return h

if __name__ == '__main__':
    path = sys.argv[1]
    opts = set(sys.argv[2:]) or {'--all'}
    if '--all' in opts: opts = {'--lvo','--regs','--akiko','--iocmd'}
    d = open(path, 'rb').read()
    if '--lvo' in opts:
        h, _ = lvos(d)
        print("=== jsr/jmp d16(a6): %d call sites, %d distinct offsets" % (sum(h.values()), len(h)))
        for off, n in sorted(h.items()):
            print("  %5d  x%d" % (off, n))
    if '--regs' in opts:
        h = regs(d)
        print("=== absolute custom-chip references: %d, %d distinct" % (sum(h.values()), len(h)))
        for off, n in sorted(h.items()):
            print("  $DFF%03X  %-10s x%d" % (off, REG.get(off, '?'), n))
    if '--akiko' in opts:
        print("=== Akiko")
        for k, v in akiko(d).items():
            print("  %-30s %d  %s" % (k, len(v), [hex(x) for x in v[:20]]))
    if '--iocmd' in opts:
        h = iocmd(d)
        print("=== io_Command immediates (3?7c 00nn 001c): %d" % sum(h.values()))
        for c, n in sorted(h.items()):
            print("  %3d  x%d" % (c, n))
