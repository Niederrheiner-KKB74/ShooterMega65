"""Verify new art and independently decode the shop's exported NCM glyphs."""
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from PIL import Image
import make_shop
import import_art

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/shop'
OUT=ROOT/'build/shop-refresh'

def main():
    manifest=json.loads((BASE/'generated/manifest.json').read_text())
    assert manifest['palette']==[list(c) for c in import_art.HUD_PAL]
    assert hashlib.sha256((BASE/'source/player-reference.png').read_bytes()).hexdigest()==manifest['source_sha256']
    for icon in json.loads((BASE/'generated/indexed-source.json').read_text()):
        data=bytes.fromhex(''.join(icon['rows']));assert len(data)==256
        assert set(data)<={0,1,2,3,4,5,6,7,8,10}
        im=Image.open(BASE/'generated'/(icon['id']+'.png')).convert('RGBA')
        assert im.size==(16,16)
        assert im.tobytes()==bytes(v for i in data for v in (*manifest['palette'][i],255 if i else 0))
        mapped=np.array([make_shop.ICON_HUD_MAP[i] for i in data],np.uint8).reshape(16,16)
        assert np.array_equal(make_shop.icon(icon['id']),mapped)
        assert set(mapped.flatten())<={2,5,8,9,10,11,12,13,14,15}
    make_shop.main(OUT)
    data=(OUT/'SHOP').read_bytes();count=int.from_bytes(data[2:4],'little')
    assert data[:2]==b'SH' and count<=255 and len(data)==4+count*64
    tables=(OUT/'shop_data.inc').read_text()
    for name,(image,_) in [('panel',make_shop.panel_image()),('msg',make_shop.message_image()),('dlg',make_shop.dialog_image())]:
        values=re.search(r'^shop_'+name+r'_glyph: .byte (.+)$',tables,re.M).group(1)
        tiles=[int(x) for x in values.split(',')];decoded=np.zeros_like(image)
        cols=image.shape[1]//16
        for n,t in enumerate(tiles):
            assert t<count
            glyph=data[4+t*64:4+(t+1)*64]
            pixels=np.array([v for b in glyph for v in (b&15,b>>4)],np.uint8).reshape(8,16)
            y=n//cols*8;x=n%cols*16;decoded[y:y+8,x:x+16]=pixels
        assert np.array_equal(decoded,image) and not (decoded==0).any()
    print(f'PASS: Extra-Life/Exit PNG, allowed HUD/shop indices, real importer, three SHOP token maps decoded; {count}/255 glyphs.')

if __name__=='__main__':main()
