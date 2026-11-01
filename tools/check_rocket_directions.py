"""Verify source identity, palette and independent NCM/FCM/RRB decoding."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/rocket-directions';OUT=BASE/'generated'

def main():
    source=json.loads((BASE/'source/rocket.json').read_text())
    original=next(x for x in json.loads((ROOT/'assets/art/spec-v2/generated/indexed-source.json').read_text()) if x['group']=='rocket' and x['frame']==0)
    assert source['rows']==original['rows']
    pal=json.loads((ROOT/'assets/art/spec-v2/generated/manifest.json').read_text())['palettes']['rocket']
    manifest=json.loads((OUT/'manifest.json').read_text());assert source['palette']==manifest['palette']==pal
    assert len(pal)==16 and pal[0]==[0,0,0]
    records=json.loads((OUT/'indexed-source.json').read_text())
    raw=(OUT/'rocket.indices.bin').read_bytes();nc=(OUT/'rocket.ncm.bin').read_bytes();fc=(OUT/'rocket.fcm.bin').read_bytes();rrb=(OUT/'rocket.rrb.bin').read_bytes()
    assert (len(raw),len(nc),len(fc),len(rrb))==(512,256,512,448)
    assert raw[:256]==bytes.fromhex(''.join(original['rows'])) and raw[:256]!=raw[256:]
    strip=Image.open(OUT/'rocket-views.png').convert('RGBA');assert strip.size==(32,16)
    assert rrb[:64]==bytes(64)
    for n,rec in enumerate(records):
        data=raw[n*256:n*256+256];assert data==bytes.fromhex(''.join(rec['rows'])) and max(data)<=15
        im=Image.open(OUT/(rec['id']+'.png')).convert('RGBA');assert im.size==(16,16)
        assert im.tobytes()==bytes(v for i in data for v in (*pal[i],255 if i else 0))
        assert strip.crop((n*16,0,n*16+16,16)).tobytes()==im.tobytes()
        decoded=bytes(v for b in nc[n*128:n*128+128] for v in (b&15,b>>4));assert decoded==data
        decoded=bytearray(256)
        for t in range(4):
            for y in range(8):
                start=n*256+t*64+y*8;dest=(t//2*8+y)*16+t%2*8
                decoded[dest:dest+8]=fc[start:start+8]
        assert decoded==data
        base=rec['rrb_base'];assert base==1+n*3 and rec['palette_byte']==0xdf
        assert rrb[base*64:(base+2)*64]==nc[n*128:n*128+128]
        assert rrb[(base+2)*64:(base+3)*64]==bytes(64)
    assert (OUT/'palette.rgb').read_bytes()==bytes(v for c in pal for v in c)
    assert (OUT/'palette.palregs.bin').read_bytes()==bytes(c[ch]%16*16+c[ch]//16 for ch in range(3) for c in pal)
    for name,sha in manifest['files'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==sha
    print('PASS: original rocket identity, identical palette, 16x16 binary alpha, static strip and NCM/FCM/RRB round trips.')

if __name__=='__main__':main()
