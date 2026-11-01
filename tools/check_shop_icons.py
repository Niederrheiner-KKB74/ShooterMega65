"""Independently decode exports and verify native pixel/palette constraints."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/shop-upgrades'
OUT=BASE/'generated'
cfg=json.loads((BASE/'source/icons.json').read_text())
m=json.loads((OUT/'manifest.json').read_text())
ids=['shot_ii','shot_iii','shot_iv','bomb','homing_missile','invulnerability']
assert [x['id'] for x in m['icons']]==ids
pal=cfg['palette']; colors=set()
raw=(OUT/'shop.indices.bin').read_bytes()
nc=(OUT/'shop.ncm.bin').read_bytes()
fc=(OUT/'shop.fcm.bin').read_bytes()
rrb=(OUT/'shop.rrb.bin').read_bytes()
assert (len(raw),len(nc),len(fc),len(rrb))==(1536,768,1536,1216)
assert rrb[:64]==bytes(64)
indexed=json.loads((OUT/'indexed-source.json').read_text())
strip=Image.open(OUT/'shop-icons-strip.png').convert('RGBA')
atlas=Image.open(OUT/'shop-icons-atlas.png').convert('RGBA')
assert strip.size==(96,16) and atlas.size==(48,32)
for i,name in enumerate(ids):
    im=Image.open(OUT/(name+'.png')).convert('RGBA');assert im.size==(16,16)
    data=raw[i*256:(i+1)*256]
    assert max(data)<12
    expected=[tuple(pal[v])+(255 if v else 0,) for v in data]
    assert list(im.getdata())==expected
    colors.update(c for c in expected if c[3])
    assert strip.crop((i*16,0,(i+1)*16,16)).tobytes()==im.tobytes()
    x=i%3*16;y=i//3*16
    assert atlas.crop((x,y,x+16,y+16)).tobytes()==im.tobytes()
    assert bytes.fromhex(''.join(indexed[i]['rows']))==data
    decoded=bytes(v for b in nc[i*128:(i+1)*128] for v in (b&15,b>>4))
    assert decoded==data
    decoded=bytearray(256)
    for tile in range(4):
        tx=tile%2*8;ty=tile//2*8
        for row in range(8):
            start=i*256+tile*64+row*8
            decoded[(ty+row)*16+tx:(ty+row)*16+tx+8]=fc[start:start+8]
    assert decoded==data
    base=m['icons'][i]['rrb_base'];assert base==1+i*3
    assert rrb[base*64:(base+2)*64]==nc[i*128:(i+1)*128]
    assert rrb[(base+2)*64:(base+3)*64]==bytes(64)
    assert m['icons'][i]['palette_byte']==0xcf
    if i<3:assert sum(v!=0 for v in data[224:240])==i+2
assert len(colors)<=15 and len({raw[i*256:(i+1)*256] for i in range(6)})==6
assert (OUT/'palette.rgb').read_bytes()==bytes(v for c in pal for v in c)
assert (OUT/'palette.palregs.bin').read_bytes()==bytes((c[ch]%16)*16+c[ch]//16 for ch in range(3) for c in pal)
for name,record in m['files'].items():
    b=(OUT/name).read_bytes();assert len(b)==record['bytes']
    assert hashlib.sha256(b).hexdigest()==record['sha256']
print(f'PASS: six 16x16 icons, {len(colors)} opaque palette colors, PNG atlases, NCM/FCM/RRB round trips and checksums.')
