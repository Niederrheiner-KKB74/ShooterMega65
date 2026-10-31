#!/usr/bin/env python3
"""Decode exported graphics independently, including prototype guards and sprite order."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'assets/art/reference-board/generated'


def decode_tile(data, width, height, tw):
    cols=(width+tw-1)//tw
    result=[]
    for y in range(((height+7)//8)*8):
        row=[]
        for x in range(cols*tw):
            tile=(y//8)*cols+x//tw
            b=data[tile*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)]
            row.append((b>>((x%2)*4))&15 if tw==16 else b)
        result.append(row)
    return result


def main():
    m=json.loads((DIR/'manifest.json').read_text())
    source=json.loads((DIR/'indexed-source.json').read_text())
    assert len(source)==94
    assert not m['hardware_tested'] and not m['emulator_tested'] and not m['assembled']
    assert hashlib.sha256((DIR.parent/'source/reference-board.png').read_bytes()).hexdigest()==m['source_sha256']
    for name,info in m['files'].items():
        data=(DIR/name).read_bytes()
        assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'],name
    raw=(DIR/'frames.indices.bin').read_bytes()
    fcm=(DIR/'frames.fcm.bin').read_bytes();ncm=(DIR/'frames.ncm.bin').read_bytes()
    lookup={(s['group'],s['frame']):s for s in source}
    for g in m['groups']:
        w,h=g['size'];strip=Image.open(DIR/(g['id']+'.png')).convert('RGBA')
        assert strip.size==(w*len(g['frames']),h)
        for f in g['frames']:
            s=lookup[(g['id'],f['frame'])];expected=b''.join(bytes.fromhex(r) for r in s['rows'])
            assert len(expected)==w*h and max(expected)<=15 and any(expected)
            assert raw[f['indices_offset']:f['indices_offset']+f['indices_bytes']]==expected
            for data,mode,tw in [(fcm,'fcm',8),(ncm,'ncm',16)]:
                decoded=decode_tile(data[f[mode+'_offset']:f[mode+'_offset']+f[mode+'_bytes']],w,h,tw)
                for y,row in enumerate(decoded):
                    for x,v in enumerate(row):assert v==(expected[y*w+x] if y<h and x<w else 0)
            image=strip.crop((f['frame']*w,0,(f['frame']+1)*w,h))
            pal=m['palettes'][g['palette']]
            assert list(image.getdata())==[tuple(pal[v])+(0 if v==0 else 255,) for v in expected]
    glyphs=(DIR/'rrb-pixies.bin').read_bytes()
    assert len(glyphs)==159*64 and glyphs[:64]==bytes(64)
    assert len(glyphs)<=0x4000
    for rec in m['rrb_frames']:
        strip=Image.open(DIR/(rec['group']+'-rrb.png')).convert('RGBA')
        w,h=rec['w']*16,rec['h']*8
        expected=list(strip.crop((rec['frame']*w,0,(rec['frame']+1)*w,h)).getdata())
        pal=m['palettes']['objects']
        for c in range(rec['w']):
            base=rec['base']+c*(rec['h']+1)
            assert glyphs[(base-1)*64:base*64]==bytes(64)
            assert glyphs[(base+rec['h'])*64:(base+rec['h']+1)*64]==bytes(64)
            # Simulate the renderer's preceding-row fetch for all fine Y offsets.
            for k in range(8):
                for y in range(h+8):
                    sy=y-k;pixelrow=[]
                    for x in range(16):
                        addr=(base+sy//8)*64+(sy%8)*8+x//2
                        v=(glyphs[addr]>>((x%2)*4))&15
                        rgba=tuple(pal[v])+(0 if v==0 else 255,)
                        want=expected[sy*w+c*16+x] if 0<=sy<h else (0,0,0,0)
                        assert rgba==want,(rec['name'],k,y,x)
    sprites=(DIR/'player-all.sprite.bin').read_bytes()
    pal=m['palettes']['player']
    assert len(sprites)==6*512
    for i in range(6):
        s=lookup[('player',i)];p=b''.join(bytes.fromhex(r) for r in s['rows'])
        for half in range(2):
            block=sprites[i*512+half*256:i*512+(half+1)*256]
            assert block[192:]==bytes(64)
            for y in range(24):
                for x in range(16):
                    v=(block[y*8+x//2]>>(4 if x%2==0 else 0))&15
                    sx=half*16+x-4
                    assert v==(p[y*24+sx] if 0<=sx<24 else 0)
    assert (DIR/'player-normal.sprite.bin').read_bytes()==sprites[2048:2560]
    assert len((DIR/'player.sprpal.bin').read_bytes())==96
    assert len((DIR/'terrain16.ncm.bin').read_bytes())==104*64
    land=(DIR/'terrain16.ncm.bin').read_bytes()
    for tile in m['terrain_tiles']:
        w=16;i=tile['frame'];group=next(g for g in m['groups'] if g['id']==tile['group'])
        strip=Image.open(DIR/(tile['group']+'-engine16.png')).convert('RGBA')
        decoded=decode_tile(land[tile['glyph_top']*64:(tile['glyph_bottom']+1)*64],16,16,16)
        pal=m['palettes'][group['palette']]
        rgba=[tuple(pal[v])+(0 if v==0 else 255,) for row in decoded for v in row]
        assert rgba==list(strip.crop((i*16,0,(i+1)*16,16)).getdata())
    regs=(DIR/'palettes.palregs.bin').read_bytes()
    for name,offset in m['palette_offsets'].items():
        pal=m['palettes'][name]
        assert regs[offset:offset+48]==bytes(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in pal)
    print('PASS: 94 indexed frames, FCM/NCM round trips and padding, 36 guarded RRB frames at all 8 Y offsets, 6 player sprite pairs, hashes and region budgets.')


if __name__=='__main__':main()
