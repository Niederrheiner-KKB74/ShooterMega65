"""Check repaired hulls, all poses/phases, binary layouts and actual runtime alpha."""
import hashlib
import json
import math
import re
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/enemy-views';OUT=BASE/'generated';SPEC=ROOT/'assets/art/spec-v2/generated'

def pixels(r):return bytes.fromhex(''.join(r['rows']))

def decode(data,w,h,tw):
    out=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            at=((y//8)*(w//tw)+x//tw)*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)
            out[y*w+x]=(data[at]>>((x%2)*4))&15 if tw==16 else data[at]
    return bytes(out)

def holes(data,w,h):
    seen=set();q=deque()
    for y in range(h):
        for x in range(w):
            if (x in (0,w-1) or y in (0,h-1)) and not data[y*w+x]:seen.add((x,y));q.append((x,y))
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and not data[yy*w+xx] and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
    return [y*w+x for y in range(h) for x in range(w) if not data[y*w+x] and (x,y) not in seen]

def runtime_alpha(canonical):
    gen=ROOT/'build/gen';const=(gen/'assets.inc').read_text();tables=(gen/'frames.inc').read_text();runs=(gen/'pixruns.inc').read_text()
    def table(name):return [int(v) for v in re.search(r'^'+name+r': .byte (.+)$',tables,re.M)[1].split(',')]
    def runline(name):return re.search(r'^'+name+r': .byte (.+)$',runs,re.M)[1]
    sources=[int(v) for v in re.findall(r'pixie_data\+(\d+)',runline('pixrun_src_lo'))]
    dests=[int(v) for v in re.findall(r'\+(\d+)\)',runline('pixrun_dst_lo'))]
    lengths=[int(v.lstrip('<')) for v in runline('pixrun_len_lo').split(',')]
    stored=(gen/'pixies.bin').read_bytes();full=bytearray(512*64)
    assert len(sources)==len(dests)==len(lengths)
    for s,d,n in zip(sources,dests,lengths):full[d:d+n]=stored[s:s+n]
    lo,hi,ws,hs=map(table,('frame_base','frame_base_hi','frame_w','frame_h'))
    pals=table('frame_pal');bankbytes=(gen/'palette.bin').read_bytes()
    sourcepal=json.loads((SPEC/'manifest.json').read_text())['palettes']
    for group,prefix in [('fighter','FIGHTER'),('helicopter','HELI'),('bomber','BOMBER'),('armoured_plane','ARMOURED')]:
        for phase in range(3):
            index=int(re.search(r'FR_'+prefix+str(phase)+r'=(\d+)',const)[1]);base=lo[index]+hi[index]*256;w=ws[index]*16;h=hs[index]*8
            decoded=bytearray(w*h)
            for c in range(ws[index]):
                start=(base+c*(hs[index]+1))*64
                part=decode(full[start:start+hs[index]*64],16,h,16)
                for y in range(h):decoded[y*w+c*16:y*w+c*16+16]=part[y*16:y*16+16]
            ref=canonical[group,phase];assert [v!=0 for v in decoded]==[v!=0 for v in ref]
            # Check actual remapped RGB too; 0 is the only transparent index.
            bank=pals[index]>>4
            for got,want in zip(decoded,ref):
                if not want:continue
                actual=[]
                for ch in range(3):
                    b=bankbytes[ch*256+bank*16+got];actual.append((b%16)*16+b//16)
                assert actual==sourcepal[group][want]

def main():
    before=json.loads((BASE/'source/before.json').read_text());old={(r['group'],r['frame']):r for r in before['frames']}
    canonical={(r['group'],r['frame']):pixels(r) for r in json.loads((SPEC/'indexed-source.json').read_text())}
    fixes=json.loads((ROOT/'assets/art/spec-v2/source/enemy-opacity.json').read_text())['groups']
    for key,r in old.items():
        a=pixels(r);b=canonical[key];expected=fixes.get(key[0],{}).get('repairs',[])
        positions={y*r['width']+x:index for x,y,index in expected}
        assert {i for i,(x,y) in enumerate(zip(a,b)) if x!=y}==set(positions)
        assert all(a[i]==0 and b[i]==v for i,v in positions.items())
    pal=json.loads((OUT/'palettes.json').read_text());assert pal==before['palettes']
    tanks=json.loads((ROOT/'assets/art/ground-vehicles/generated/indexed-source.json').read_text())
    assert len(tanks)==16
    assert all(not holes(pixels(t),16,16) for t in tanks),'transparent enclosed tank hole'
    recs=json.loads((OUT/'indexed-source.json').read_text());assert len(recs)==66
    frames={(r['group'],r['pose'],r['phase']):r for r in recs}
    raw=(OUT/'views.indices.bin').read_bytes();nc=(OUT/'views.ncm.bin').read_bytes();fc=(OUT/'views.fcm.bin').read_bytes();rrb=(OUT/'views.rrb.bin').read_bytes();assert len(rrb)==325*64
    groups={g['group']:g for g in json.loads((OUT/'manifest.json').read_text())['groups']}
    for group,g in groups.items():
        assert len(g['poses'])==(8 if group in ('fighter','helicopter') else 3)
        strip=Image.open(OUT/(group+'.png')).convert('RGBA');size=g['size'][0];assert strip.size==(len(g['poses'])*3*size,size)
        assert len({pixels(frames[group,p,0]) for p in g['poses']})==len(g['poses'])
        for pi,pose in enumerate(g['poses']):
            base=pixels(frames[group,pose,0]);mask=bytes.fromhex(''.join(frames[group,pose,0]['effect_mask_rows']))
            assert Image.open(OUT/f'{group}-{pose}.webp').n_frames==3
            assert len({pixels(frames[group,pose,n]) for n in range(3)})==3
            for phase in range(3):
                r=frames[group,pose,phase];a=pixels(r);assert max(a)<=15 and len(a)==size*size
                assert all(mask[i] for i,(v,w) in enumerate(zip(a,base)) if v!=w),'body animated'
                if group!='helicopter':assert all(mask[i] for i in holes(a,size,size)),(group,pose,phase,'transparent body hole')
                im=strip.crop(((pi*3+phase)*size,0,(pi*3+phase+1)*size,size))
                assert im.tobytes()==bytes(v for i in a for v in (*pal[group][i],255 if i else 0))
                assert raw[r['indices_offset']:r['indices_offset']+len(a)]==a
                assert decode(nc[r['ncm_offset']:r['ncm_offset']+len(a)//2],size,size,16)==a
                assert decode(fc[r['fcm_offset']:r['fcm_offset']+len(a)],size,size,8)==a
                for c in range(size//16):
                    start=(r['rrb_base']+c*(size//8+1))*64;part=decode(rrb[start:start+size//8*64],16,size,16)
                    assert part==b''.join(a[y*size+c*16:y*size+c*16+16] for y in range(size))
                    assert rrb[start+size//8*64:start+(size//8+1)*64]==bytes(64)
            if pose in ('south','straight'):assert base==canonical[group,0]
    runtime_alpha(canonical)
    m=json.loads((OUT/'manifest.json').read_text())
    for name,info in m['files'].items():
        b=(OUT/name).read_bytes();assert len(b)==info['bytes'] and hashlib.sha256(b).hexdigest()==info['sha256']
    print('PASS: explicit zero-only repairs; unchanged palettes; 66 poses/phases; static bodies/effects masks; no enclosed body holes; PNG/NCM/FCM/RRB; runtime compressed glyph alpha and RGB match corrected source.')

if __name__=='__main__':main()
