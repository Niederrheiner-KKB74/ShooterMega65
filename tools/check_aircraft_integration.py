#!/usr/bin/env python3
"""Check integrated assets and execute the assembled hit-axis routine.

Run after tools/build.py. Requires only the normal build dependencies.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
import make_assets as old
import integrate_aircraft as art

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/'build/gen'


def axis_carry(memory, pc, delta, centre, limit, symbols):
    """Small 6502 instruction runner for the actual assembled hit_axis bytes."""
    memory[symbols['tmp']]=delta&255;memory[symbols['tmp']+1]=(delta>>8)&255
    memory[symbols['hit_centre']]=centre;memory[symbols['hit_limit']]=limit
    a=0;c=0;n=0;z=0
    for _ in range(60):
        op=memory[pc];pc+=1
        if op==0x60:return c
        if op==0x38:c=1;continue
        if op in (0x10,0xd0):
            rel=memory[pc];pc+=1
            if (op==0x10 and not n) or (op==0xd0 and not z):pc+=(rel if rel<128 else rel-256)
            continue
        if op in (0xa9,0xe9):v=memory[pc];pc+=1
        elif op in (0xa5,0x85,0xe5):address=memory[pc];pc+=1;v=memory[address]
        elif op in (0xad,0x8d,0xed,0xcd):address=memory[pc]|(memory[pc+1]<<8);pc+=2;v=memory[address]
        else:raise AssertionError(f'Unexpected opcode ${op:02x}')
        if op in (0xa9,0xa5,0xad):a=v
        elif op in (0x85,0x8d):memory[address]=a;continue
        elif op in (0xe9,0xe5,0xed):result=a-v-(1-c);c=int(result>=0);a=result&255
        elif op==0xcd:
            result=a-v;c=int(result>=0);n=(result&128)!=0;z=(result&255)==0;continue
        n=(a&128)!=0;z=a==0
    raise AssertionError('hit_axis did not return')


def main():
    with tempfile.TemporaryDirectory(dir=ROOT/'build') as td:
        baseline=Path(td)
        subprocess.run([sys.executable,str(ROOT/'tools/make_assets.py'),td],check=True,stdout=subprocess.DEVNULL)
        for name in ('map.bin','mapcol.bin','tiles.bin'):
            assert (GEN/name).read_bytes()==(baseline/name).read_bytes(),name
        original=(baseline/'palette.bin').read_bytes();actual=(GEN/'palette.bin').read_bytes()
        for ch in range(3):
            assert actual[ch*256:ch*256+48]==original[ch*256:ch*256+48]
            assert actual[ch*256+112:(ch+1)*256]==original[ch*256+112:(ch+1)*256]
    layout=json.loads((GEN/'aircraft-layout.json').read_text())
    manifest=json.loads((art.ART/'manifest.json').read_text())
    palette=(GEN/'palette.bin').read_bytes()
    for i,kind in enumerate(art.KINDS):
        for n,c in enumerate(manifest['palettes'][kind]):
            for ch in range(3):assert palette[ch*256+(i+3)*16+n]==old.swap(c[ch])
        assert [r['name'] for r in layout['frames'][7+i*3:10+i*3]]==[kind.upper()+str(n) for n in range(3)]
    source=json.loads((art.ART/'indexed-source.json').read_text())
    source={(s['group'],s['frame']):np.frombuffer(bytes.fromhex(''.join(s['rows'])),np.uint8).reshape(s['height'],s['width']) for s in source}
    glyphs=(GEN/'pixies.bin').read_bytes();assert len(glyphs)==86*64 and len(glyphs)<=0x4000
    assert glyphs[:64]==bytes(64)
    for rec in layout['frames']:
        w,h=rec['w']*16,rec['h']*8
        actual=np.zeros((h,w),np.uint8)
        for col in range(rec['w']):
            base=rec['base']+col*(rec['h']+1)
            assert glyphs[(base-1)*64:base*64]==bytes(64)
            assert glyphs[(base+rec['h'])*64:(base+rec['h']+1)*64]==bytes(64)
            for y in range(h):
                for x in range(16):
                    b=glyphs[(base+y//8)*64+(y%8)*8+x//2]
                    actual[y,col*16+x]=(b>>(4*(x%2)))&15
        if rec['pal']==0x2f:
            expected=dict(old.FRAMES)[rec['name']]
        else:
            kind=art.KINDS[(rec['pal']>>4)-3]
            p=np.rot90(source[kind,int(rec['name'][-1])],2)
            expected=np.zeros((h,w),np.uint8);expected[:,(w-p.shape[1])//2:(w-p.shape[1])//2+p.shape[1]]=p
            assert rec['cx']==w//2 and rec['halfw']==p.shape[1]//2
        assert np.array_equal(actual,expected),rec['name']
    sprites=(GEN/'sprite.bin').read_bytes();assert len(sprites)==1536
    for i,frame in enumerate((4,3,5)):
        canvas=np.zeros((24,32),np.uint8);canvas[:,4:28]=source['player',frame]
        for half in range(2):
            block=sprites[i*512+half*256:i*512+(half+1)*256]
            assert block[192:]==bytes(64)
            for y in range(24):
                for x in range(16):assert ((block[y*8+x//2]>>(4 if x%2==0 else 0))&15)==canvas[y,half*16+x]
    assert (GEN/'sprpal.bin').read_bytes()==(art.ART/'player.sprpal.bin').read_bytes()
    prg=(ROOT/'build/SHOOTER.PRG').read_bytes();load=int.from_bytes(prg[:2],'little')
    assert load==0x2001 and load+len(prg)-2<=0xc000
    sym=dict((k,int(v,16)) for k,v in re.findall(r'\.label (\w+)=\$([0-9a-f]+)',(ROOT/'build/main.sym').read_text()))
    memory=bytearray(65536);memory[load:load+len(prg)-2]=prg[2:]
    for centre,limit in ((8,10),(16,14)):
        for delta in range(-512,513):
            assert (axis_carry(memory,sym['hit_axis'],delta,centre,limit,sym)==0)==(abs(delta-centre)<limit),(delta,centre,limit)
    print('PASS: unchanged landscape/tank/shots/explosions; 12 correctly oriented enemy frames; palettes/guards; 3 player sprite pairs; 2050 assembled collision boundary cases; PRG budget.')


if __name__=='__main__':main()
