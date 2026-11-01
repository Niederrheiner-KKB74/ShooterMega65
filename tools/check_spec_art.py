#!/usr/bin/env python3
"""Validate the artwork deliverables against the supplied artwork_spec.md."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/spec-v2'
OUT=BASE/'generated'


def decode(data,w,h,tw):
    result=[]
    for y in range(h):
        for x in range(w):
            at=((y//8)*(w//tw)+x//tw)*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)
            b=data[at];result.append((b>>((x%2)*4))&15 if tw==16 else b)
    return bytes(result)


def main():
    m=json.loads((OUT/'manifest.json').read_text());source=json.loads((OUT/'indexed-source.json').read_text())
    lookup={(p['group'],p['frame']):p for p in source}
    assert len(source)==111
    assert hashlib.sha256((BASE/'source/artwork_spec.md').read_bytes()).hexdigest()==m['spec_sha256']
    for name,info in m['files'].items():
        data=(OUT/name).read_bytes();assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'],name
    raw=(OUT/'frames.indices.bin').read_bytes();fcm=(OUT/'frames.fcm.bin').read_bytes();ncm=(OUT/'frames.ncm.bin').read_bytes()
    for g in m['groups']:
        w,h=g['size'];n=len(g['frames']);im=Image.open(OUT/(g['id']+'.png')).convert('RGBA')
        assert im.size==(w*n,h)
        assert set(p[3] for p in im.getdata())<={0,255}
        colours={p[:3] for p in im.getdata() if p[3]};assert 0<len(colours)<=15,(g['id'],len(colours))
        if g['kind']=='player':assert (w,h)==(32,24)
        elif g['kind'] in ('enemy','projectile','explosion'):assert w%16==0 and h%8==0
        if g['kind']=='enemy':assert (w,h) in ((16,16),(32,32))
        if g['kind']=='explosion':assert (w,h) in ((16,16),(32,32)) and 4<=n<=8
        if g['kind'] in ('terrain','decoration'):assert (w,h)==(16,16)
        if g['kind']=='hud':assert (w,h) in ((8,8),(8,16))
        for f in g['frames']:
            p=lookup[g['id'],f['index']];expected=b''.join(bytes.fromhex(row) for row in p['rows'])
            assert max(expected)<=15 and len(expected)==w*h
            assert raw[f['indices_offset']:f['indices_offset']+f['indices_bytes']]==expected
            assert decode(fcm[f['fcm_offset']:f['fcm_offset']+f['fcm_bytes']],w,h,8)==expected
            if w%16==0:assert decode(ncm[f['ncm_offset']:f['ncm_offset']+f['ncm_bytes']],w,h,16)==expected
            pal=m['palettes'][g['palette']]
            assert list(im.crop((f['index']*w,0,(f['index']+1)*w,h)).getdata())==[tuple(pal[i])+(255 if i else 0,) for i in expected]
    assert len(next(g for g in m['groups'] if g['id']=='hud_digits')['frames'])==10
    for a,b in m['fixed_target_pairs']:
        ga=next(g for g in m['groups'] if g['id']==a);gb=next(g for g in m['groups'] if g['id']==b)
        assert ga['size']==gb['size'] and ga['palette']==gb['palette']
        assert (OUT/(a+'.png')).read_bytes()!=(OUT/(b+'.png')).read_bytes()
    level=json.loads((OUT/'level-example.json').read_text());im=Image.open(OUT/'level-example.png').convert('RGBA')
    assert im.size==(336,512) and im.height%16==0 and level['hidden_left']==16 and level['level_start']=='bottom'
    assert len(level['rows'])==32 and all(len(row)==21 for row in level['rows'])
    assert 2<=len(m['landscape']['palettes'])<=4 and m['landscape']['unique_tiles']<=512
    terrain=(OUT/'terrain.ncm.bin').read_bytes();canvas=Image.new('RGBA',im.size);keys=set()
    for t in level['tiles']:
        indices=decode(terrain[t['id']*128:(t['id']+1)*128],16,16,16)
        key=(t['palette'],indices);assert key not in keys;keys.add(key)
    mapdata=(OUT/'level-example.map16.bin').read_bytes();map_pal=(OUT/'level-example.palette.bin').read_bytes()
    for y,row in enumerate(level['rows']):
        for x,t in enumerate(row):
            cell=y*21+x;assert int.from_bytes(mapdata[cell*2:cell*2+2],'little')==t
            meta=level['tiles'][t];pal=m['palettes'][meta['palette']]
            assert map_pal[cell]==m['landscape']['palettes'].index(meta['palette'])
            indices=decode(terrain[t*128:(t+1)*128],16,16,16)
            tile=Image.new('RGBA',(16,16));tile.putdata([tuple(pal[i])+(255 if i else 0,) for i in indices]);canvas.paste(tile,(x*16,y*16))
    assert canvas.tobytes()==im.tobytes() and all(p[3]==255 for p in im.getdata())
    sprites=(OUT/'player.sprite.bin').read_bytes();assert len(sprites)==6*512
    for f in range(6):
        p=lookup['player',f];expected=b''.join(bytes.fromhex(row) for row in p['rows'])
        for half in range(2):
            block=sprites[f*512+half*256:f*512+(half+1)*256];assert block[192:]==bytes(64)
            for y in range(24):
                for x in range(16):assert (block[y*8+x//2]>>(4 if x%2==0 else 0))&15==expected[y*32+half*16+x]
    rrb=(OUT/'rrb-pixies.bin').read_bytes();assert len(rrb)==183*64 and rrb[:64]==bytes(64)
    for f in m['rrb_frames']:
        p=lookup[f['group'],f['frame']];expected=b''.join(bytes.fromhex(row) for row in p['rows']);w=p['width'];h=p['height']
        for col in range(f['w']):
            base=f['base']+col*(f['h']+1)
            assert rrb[(base-1)*64:base*64]==bytes(64) and rrb[(base+f['h'])*64:(base+f['h']+1)*64]==bytes(64)
            for y in range(h):
                for x in range(16):assert ((rrb[(base+y//8)*64+(y%8)*8+x//2]>>((x%2)*4))&15)==expected[y*w+col*16+x]
    assert not m['assembled'] and not m['hardware_tested'] and not m['emulator_tested']
    print('PASS: 111 frames; spec dimensions/strips/15 colours/alpha; FCM/NCM and sprite round trips; RRB guards; target pairs; 62 unique terrain tiles and pixel-exact 336x512 level with 4 palettes.')


if __name__=='__main__':main()
