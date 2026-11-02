"""Additional independent checks: rims of all modules, fixed bases and exact previews."""
import hashlib
import json
from pathlib import Path
from PIL import Image

BASE=Path(__file__).resolve().parents[1];OUT=BASE/'generated'

def unpack(strings):return [[int(v,16) for v in row] for row in strings]

def main():
    art=json.loads((OUT/'ground-targets.json').read_text())
    ref=json.loads((BASE/'source/intact-reference.json').read_text());original={t['name']:t for t in ref['tiles']}
    pals=ref['palettes'];new=art['palettes']['fixed_targets']
    assert new[:12]==pals['fixed_targets'][:12], 'protected tank palette changed'
    assert new[12:]==[[16,18,22],[72,58,47],[225,65,24],[255,234,161]]
    assert len(art['destroyed_tiles'])==48
    halls=[]
    for t in art['destroyed_tiles']:
        a=unpack(t['pixels']);old=unpack(original[t['of']]['pixels'])
        assert len(a)==16 and all(len(row)==16 and min(row)>0 and max(row)<=15 for row in a)
        assert t['palette']==original[t['of']]['palette'], 'palette switch could alter borders'
        if t['of'].startswith('complex_'):
            halls.append(t['of'])
            for y in range(16):
                for x in range(16):
                    if min(x,y,15-x,15-y)<2:assert a[y][x]==old[y][x],('hall edge mismatch',t['name'],x,y)
        else:
            # Two-pixel rim of whole 32x32 group, not each internal tile seam.
            tx=int(t['of'][-3]);ty=int(t['of'][-1])
            for y in range(16):
                for x in range(16):
                    xx=tx*16+x;yy=ty*16+y
                    if min(xx,yy,31-xx,31-yy)<2:assert a[y][x]==old[y][x],('group edge mismatch',t['name'],x,y)
    assert len(halls)==20
    construction=json.loads((OUT/'construction.json').read_text())
    for key in ('ground_gun','heavy_gun'):
        g=art[key];size=g['size'][0];layers=construction[key];base=unpack(layers['base'])
        assert len(g['frames'])==11 and set(g['muzzle'])=={'n','ne','e','se','s','sw','w','nw'}
        for direction,mask in layers['upper_masks'].items():
            a=unpack(g['frames'][direction]);m=unpack(mask)
            assert all(a[y][x]==base[y][x] for y in range(size) for x in range(size) if not m[y][x]),'stationary base moved'
            assert layers['barrel_tips'][direction][0]==g['muzzle'][direction]
            for x,y in layers['barrel_tips'][direction]:assert a[y][x]>0,('muzzle not visible',key,direction,x,y)
        # Native horizontal strip reconstructs the source pixel colours/alpha exactly.
        name='ground-gun' if size==16 else 'heavy-gun';strip=Image.open(OUT/(name+'-1x.png')).convert('RGBA');x0=0
        for direction in list(g['muzzle'])+['flash0','flash1','wreck']:
            a=unpack(g['frames'][direction]);h=len(a);w=len(a[0]);crop=strip.crop((x0,(size-h)//2,x0+w,(size-h)//2+h))
            assert crop.tobytes()==bytes(v for row in a for i in row for v in (*new[i],255 if i else 0));x0+=w
        scaled=Image.open(OUT/(name+'-4x.png')).convert('RGBA')
        assert scaled.size==(strip.width*4,strip.height*4)
        assert scaled.tobytes()==strip.resize(scaled.size,Image.Resampling.NEAREST).tobytes()
    sheet=Image.open(OUT/'destroyed-sheet.png');scaled=Image.open(OUT/'destroyed-sheet-4x.png')
    assert scaled.tobytes()==sheet.resize(scaled.size,Image.Resampling.NEAREST).tobytes()
    m=json.loads((OUT/'manifest.json').read_text())
    for name,info in m['files'].items():
        b=(OUT/name).read_bytes();assert len(b)==info['bytes'] and hashlib.sha256(b).hexdigest()==info['sha256']
    print('PASS: 48 opaque tiles; exact 32x32 group rims and all 20 hall-module rims; protected palette 0-11; both stationary bases; all primary/secondary muzzle tips; native previews, exact 4x scaling and checksums.')

if __name__=='__main__':main()
