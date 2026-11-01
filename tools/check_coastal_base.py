#!/usr/bin/env python3
"""Independently decode the compiled level and check terrain/spawn budgets."""
import json
import struct
from collections import deque
from pathlib import Path
from PIL import Image
import build_level

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/coastal-base/generated';BUILD=ROOT/'build/coastal-base'


def main():
    lv=json.loads((ROOT/'levels/coastal_base.json').read_text());rows=build_level.expand_map(lv['map'])
    assert len(rows)==375 and all(len(r)==21 for r in rows)
    assert len(set(tuple(r) for r in rows))<=256
    gfx=(BUILD/'LCGFX').read_bytes();dat=(BUILD/'LCDAT').read_bytes()
    assert len(gfx)<=16384 and len(dat)<=16384 and gfx[:2]==b'SG' and dat[:2]==b'SL'
    assert struct.unpack_from('<H',gfx,2)[0]==208 and len(gfx)==4+192+104*128
    header=struct.unpack_from('<2sBBHHHHHHHHB',dat)
    _,version,nmeta,nrows,om,od,orr,oe,of,op,speed,ndict=header
    assert version==1 and nrows==375 and speed==128 and ndict<=256
    manifest=json.loads((BASE/'manifest.json').read_text());metadata=json.loads((BASE/'level-example.json').read_text())['tiles']
    assert len(manifest['palettes'])==4 and len(metadata)==104
    original=json.loads((ROOT/'assets/art/spec-v2/generated/manifest.json').read_text())
    assert manifest['palettes']['fixed_targets']==original['palettes']['fixed_targets'], 'shared tank palette changed'
    reverse={1:'water',2:'nature',3:'structures',4:'fixed_targets'}
    # Decode the packed SG palette, not the source RGB array.
    pals={}
    for bank in range(1,5):
        chunk=gfx[4+(bank-1)*48:4+bank*48]
        pals[bank]=[tuple(build_level.swap(chunk[ch*16+i]) for ch in range(3)) for i in range(16)]
        assert [list(c) for c in pals[bank]]==manifest['palettes'][reverse[bank]]
    image=Image.new('RGBA',(336,6000));terrain=gfx[196:];tile_pixels=[]
    for t in range(104):
        values=[]
        for y in range(16):
            for x in range(16):
                b=terrain[t*128+(y//8)*64+(y%8)*8+x//2];values.append((b>>((x%2)*4))&15)
        assert min(values)>0 and max(values)<=15;tile_pixels.append(values)
    for r in range(nrows):
        di=dat[orr+r];row=dat[od+di*21:od+(di+1)*21]
        for c,mi in enumerate(row):
            top,bot,colour=dat[om+mi*3:om+mi*3+3];t=top//2
            assert top%2==0 and bot==top+1 and t==rows[r][c] and colour&15==15
            p=Image.new('RGBA',(16,16));p.putdata([pals[colour>>4][v]+(255,) for v in tile_pixels[t]])
            image.paste(p,(c*16,(374-r)*16))
    clean=Image.open(BASE/'level-clean.png').convert('RGBA');assert image.tobytes()==clean.tobytes()
    # Every tank's full 16px footprint must be on land at its trigger row.
    for e in lv['events']:
        if e['type']=='ground':
            assert e['dir'] in ('east','south','west')
            for c in {(e['x']+16)//16,(e['x']+31)//16}:
                tile=metadata[rows[e['row']][c]]
                assert tile['palette']!='water',e
    assert sum(e['type']=='ground' for e in lv['events'])==8  # even if all survive, <10 slots
    waves=[e for e in lv['events'] if e['type']=='formation']
    assert len(waves)==24 and min(b['row']-a['row'] for a,b in zip(waves,waves[1:]))>=14
    assert all(lv['formations'][e['formation']]['count']<=5 for e in waves)
    # Conservative air-slot occupancy: actual compiled dy/wait bytecode, delayed
    # members, y>=256 removal. Horizontal exits and player kills only reduce it.
    def lifetime(path,start_y):
        code=build_level.compile_path('check',path);pc=0;y=start_y*4;t=0;vy=0
        while t<4096:
            op=code[pc];pc+=1
            if op<128:
                duration=op;vy=code[pc+1];vy=vy if vy<128 else vy-256;pc+=2
            elif op==0x85:duration=code[pc];pc+=1;vy=0
            elif op==0x84:continue
            elif op==0x80:
                assert vy>0,'path does not leave the screen';duration=4096-t
            else:raise AssertionError('unsupported test path instruction')
            for _ in range(duration):
                y+=vy;t+=1
                if y>=256*4:return t
        raise AssertionError('air enemy never exits')
    changes=[]
    for event in waves:
        f=lv['formations'][event['formation']];life=lifetime(lv['paths'][f['path']],f.get('y',-32))
        for member in range(f['count']):
            start=max(0,32*event['row']-400)+member*f['delay']
            changes.extend([(start,1),(start+life,-1)])
    active=peak=0
    for _,delta in sorted(changes):active+=delta;peak=max(peak,active)
    assert peak<=20
    assert not any(e['type'] in ('boss','speed') for e in lv['events'])
    assert lv['events'][-1]==dict(row=375,type='end')
    # Road/bridge/checkpoint component must connect forest entry, detour and base.
    road=set()
    for r,row in enumerate(rows):
        for c,t in enumerate(row):
            if metadata[t]['name'].startswith(('road','bridge','checkpoint')):
                for y in range(16):
                    for x in range(16):
                        if tile_pixels[t][y*16+x] in (7,8,9,10):road.add((c*16+x,r*16+15-y))
    start=(13*16+15,162*16+8);assert start in road
    seen={start};q=deque([start])
    while q:
        x,y=q.popleft()
        for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if p in road and p not in seen:seen.add(p);q.append(p)
    for target in ((13*16+15,372*16+8),(17*16+15,246*16+8),(7*16+8,338*16+15)):
        assert target in seen,('disconnected road',target)
    print(f'PASS: SG/SL decoded pixel-exactly; {ndict}/256 rows; 4 palettes; files {len(gfx)}/{len(dat)} bytes; road/bridge connected; 8 tanks on land; 24 formations, peak {peak}/20 air slots.')


if __name__=='__main__':main()
