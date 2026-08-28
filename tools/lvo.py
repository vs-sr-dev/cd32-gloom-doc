#!/usr/bin/env python3
"""Attribute every `jsr d16(a6)` in a single-hunk 68k program to a library.

Walks the code linearly with Capstone, remembers the last value moved into a6
(absolute long, PC-relative, or `movea.l 4.w,a6` for exec), and names the LVO
from that library's vector table.

    python tools/lvo.py <file> [--hunk 0x20] [--base name=addr ...]
"""
import sys, collections
from capstone import Cs, CS_ARCH_M68K, CS_MODE_M68K_020, CS_MODE_BIG_ENDIAN

EXEC = {-30:'Supervisor',-72:'InitCode',-78:'InitStruct',-84:'MakeLibrary',-96:'FindResident',
 -102:'InitResident',-108:'Alert',-114:'Debug',-120:'Disable',-126:'Enable',-132:'Forbid',
 -138:'Permit',-144:'SetSR',-150:'SuperState',-156:'UserState',-162:'SetIntVector',
 -168:'AddIntServer',-174:'RemIntServer',-180:'Cause',-186:'Allocate',-192:'Deallocate',
 -198:'AllocMem',-204:'AllocAbs',-210:'FreeMem',-216:'AvailMem',-222:'AllocEntry',
 -228:'FreeEntry',-246:'AddTail',-252:'Remove',-270:'Enqueue',-276:'FindName',-282:'AddTask',
 -288:'RemTask',-294:'FindTask',-300:'SetTaskPri',-306:'SetSignal',-318:'Wait',-324:'Signal',
 -330:'AllocSignal',-336:'FreeSignal',-354:'AddPort',-360:'RemPort',-366:'PutMsg',-372:'GetMsg',
 -378:'ReplyMsg',-384:'WaitPort',-390:'FindPort',-396:'AddLibrary',-402:'RemLibrary',
 -408:'OldOpenLibrary',-414:'CloseLibrary',-420:'SetFunction',-432:'AddDevice',-438:'RemDevice',
 -444:'OpenDevice',-450:'CloseDevice',-456:'DoIO',-462:'SendIO',-468:'CheckIO',-474:'WaitIO',
 -480:'AbortIO',-486:'AddResource',-492:'RemResource',-498:'OpenResource',-552:'OpenLibrary',
 -636:'CacheClearU',-648:'CachePreDMA',-654:'CachePostDMA'}

DOS = {-30:'Open',-36:'Close',-42:'Read',-48:'Write',-54:'Input',-60:'Output',-66:'Seek',
 -72:'DeleteFile',-78:'Rename',-84:'Lock',-90:'UnLock',-96:'DupLock',-102:'Examine',
 -108:'ExNext',-114:'Info',-120:'CreateDir',-126:'CurrentDir',-132:'IoErr',-138:'CreateProc',
 -144:'Exit',-150:'LoadSeg',-156:'UnLoadSeg',-174:'SetComment',-180:'SetProtection',
 -186:'DateStamp',-192:'Delay',-198:'WaitForChar',-210:'ParentDir',-216:'IsInteractive',
 -222:'Execute',-798:'PutStr',-948:'FPuts'}

GFX = {-30:'BltBitMap',-36:'BltTemplate',-42:'ClearEOL',-48:'ClearScreen',-54:'TextLength',
 -60:'Text',-66:'SetFont',-72:'OpenFont',-78:'CloseFont',-120:'InitGels',-192:'LoadRGB4',
 -198:'InitMasks',-216:'InitBitMap',-222:'LoadView',-228:'InitView',-234:'InitVPort',
 -240:'MrgCop',-246:'MakeVPort',-252:'FreeVPortCopLists',-258:'FreeCopList',-270:'WaitTOF',
 -276:'QBlit',-282:'InitTmpRas',-288:'GetSprite',-300:'MoveSprite',-306:'LockLayerRom',
 -456:'OwnBlitter',-462:'DisownBlitter',-552:'GetColorMap',-558:'FreeColorMap',
 -564:'GetRGB4',-588:'WaitBlit',-828:'SetChipRev',-834:'SetABPenDrMd',-858:'LoadRGB32'}

NV  = {-30:'GetCopyNV',-36:'FreeNVData',-42:'StoreNV',-48:'DeleteNV',-54:'GetNVInfo',
 -60:'GetNVList',-66:'SetNVProtection'}

CIA = {-6:'AddICRVector',-12:'RemICRVector',-18:'AbleICR',-24:'SetICR'}

TABLES = {'exec': EXEC, 'dos': DOS, 'graphics': GFX, 'nonvolatile': NV, 'ciaa': CIA, 'ciab': CIA}


def main():
    path = sys.argv[1]
    hunk = 0x20
    if '--hunk' in sys.argv:
        hunk = int(sys.argv[sys.argv.index('--hunk') + 1], 0)
    bases = {}
    for a in sys.argv:
        if a.startswith('--base'):
            pass
    for i, a in enumerate(sys.argv):
        if a == '--base':
            name, addr = sys.argv[i + 1].split('=')
            bases[int(addr, 0)] = name
    d = open(path, 'rb').read()
    md = Cs(CS_ARCH_M68K, CS_MODE_M68K_020 | CS_MODE_BIG_ENDIAN)
    md.detail = False
    cur = None
    d0lib = [None]
    counts = collections.defaultdict(collections.Counter)
    sites = collections.defaultdict(list)
    pos = hunk
    end = len(d)
    while pos < end:
        got = False
        for ins in md.disasm(d[pos:end], pos):
            got = True
            pos = ins.address + ins.size
            m, ops = ins.mnemonic, ins.op_str
            if m.startswith('move') and ops.endswith(', d0'):
                src = ops.split(',')[0].strip()
                lastd0 = None
                if src.startswith('$'):
                    t = src[1:].rstrip('.lw')
                    try: lastd0 = bases.get(int(t, 16))
                    except ValueError: pass
                d0lib[0] = lastd0
            if m.startswith('movea') and ops.endswith(', a6'):
                src = ops.split(',')[0].strip()
                if src in ('$4', '$4.w', '$4.l'):     # movea.l 4.w,a6
                    cur = 'exec'
                elif src == 'd0':
                    cur = d0lib[0] or 'unknown(d0)'
                elif src.startswith('$'):
                    t = src[1:].rstrip('.lw')
                    try: v = int(t, 16)
                    except ValueError: v = None
                    cur = bases.get(v, 'unknown@%s' % src)
                else:
                    cur = 'unknown(%s)' % src
            elif m.startswith('lea') and ops.endswith(', a6'):
                cur = 'lea(%s)' % ops.split(',')[0].strip()
            elif m in ('jsr', 'jmp') and '(a6)' in ops:
                off = ops.split('(')[0]
                try:
                    v = int(off.replace('$', '').replace('-', '-0x') if off.startswith('-')
                            else '0x' + off.replace('$', ''), 16)
                except ValueError:
                    v = None
                if off.startswith('-$'): v = -int(off[2:], 16)
                elif off.startswith('$'): v = int(off[1:], 16)
                name = TABLES.get(cur, {}).get(v, '?')
                counts[cur][(v, name)] += 1
                sites[cur].append((ins.address - hunk, v, name))
        if not got:
            pos += 2
    total = 0
    for lib in sorted(counts):
        n = sum(counts[lib].values()); total += n
        print("=== %s : %d calls" % (lib, n))
        for (v, name), c in sorted(counts[lib].items()):
            print("    %5d  %-16s x%d" % (v, name, c))
    print("\ntotal %d attributed call sites" % total)


if __name__ == '__main__':
    main()
