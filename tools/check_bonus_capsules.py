#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/bonus-capsules';OUT=BASE/'generated'


def decode(data,w,h,tw):
    values=[]
    for y in range(h):
        for x in range(w):
            at=((y//8)*(w//tw)+x//tw)*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)
            b=data[at];values.append((b>>((x%2)*4))&15 if tw==16 else b)
    return bytes(values)


def main():
    m=json.loads((OUT/'manifest.json').read_text());cfg=json.loads((BASE/'source/capsules.json').read_text())
    assert len(m['designs'])==4 and m['palette']==cfg['palette'] and m['integrated']
    for name,info in m['files'].items():
        data=(OUT/name).read_bytes();assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256']
    source={s['id']:s for s in json.loads((OUT/'indexed-source.json').read_text())}
    raw=(OUT/'capsules.indices.bin').read_bytes();nc=(OUT/'capsules.ncm.bin').read_bytes();fc=(OUT/'capsules.fcm.bin').read_bytes();rrb=(OUT/'capsules.rrb.bin').read_bytes();used=set();sizes=[]
    for desc in m['designs']:
        w,h=desc['size'];assert w%16==0 and h%8==0
        p=b''.join(bytes.fromhex(r) for r in source[desc['id']]['rows']);assert max(p)<=15
        im=Image.open(OUT/(desc['id']+'.png')).convert('RGBA');assert im.size==(w,h)
        assert list(im.getdata())==[tuple(m['palette'][i])+(255 if i else 0,) for i in p]
        assert set(v[3] for v in im.getdata())=={0,255};used.update(v[:3] for v in im.getdata() if v[3])
        assert raw[desc['indices_offset']:desc['indices_offset']+w*h]==p
        for data,key,tw in [(nc,'ncm_offset',16),(fc,'fcm_offset',8)]:assert decode(data[desc[key]:desc[key]+w*h//(2 if tw==16 else 1)],w,h,tw)==p
        for col in range(w//16):
            base=desc['rrb_base']+col*(h//8+1)
            assert rrb[(base-1)*64:base*64]==bytes(64) and rrb[(base+h//8)*64:(base+h//8+1)*64]==bytes(64)
            decoded=decode(rrb[base*64:(base+h//8)*64],16,h,16)
            assert decoded==b''.join(p[y*w+col*16:y*w+(col+1)*16] for y in range(h))
        if desc['design']=='gold_coin':
            glyph=cfg['glyphs']['$'];gx,gy=desc['glyph_origin'];scale=desc['glyph_scale']
            for yy,row in enumerate(glyph):
                for xx,v in enumerate(row):
                    if v=='1':
                        for sy in range(scale):
                            for sx in range(scale):assert p[(gy+yy*scale+sy)*w+gx+xx*scale+sx]==3,desc['id']
            assert 4 not in p, 'coins must have no dark rectangular label panel'
            x0,y0,x1,y1=desc['body_box'];assert x1-x0==y1-y0
            alpha=im.getchannel('A').crop((x0,y0,x1+1,y1+1))
            assert alpha.tobytes()==alpha.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
            assert alpha.tobytes()==alpha.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
            assert alpha.getpixel((0,0))==0
        else:
            assert desc['design']=='medieval_shield' and desc['label'] is None
            assert desc['glyph_origin']==[None,None]
            assert sum(1 for x in range(w) if p[15*w+x])==1, 'shield needs pointed lower tip'
            assert p[6*w+7]==2 and p[10*w+7]==2, 'heraldic cross missing'
        if desc['label']=='$':sizes.append((w,h,(desc['body_box'][2]-desc['body_box'][0]+1)*(desc['body_box'][3]-desc['body_box'][1]+1)))
        assert desc['palette_byte']==0xcf
    assert len(used)<=15 and len({s[:2] for s in sizes})==3 and sizes[0][2]<sizes[1][2]<sizes[2][2]
    assert [round(s[2]**.5) for s in sizes]==[10,14,18], 'coin diameters must form balanced 10/14/18 progression'
    print(f'PASS: pointed medieval shield without S; 3 circular coins with embossed dollar glyphs; {len(used)} shared colours; exact FCM/NCM/RRB and guards.')


if __name__=='__main__':main()
