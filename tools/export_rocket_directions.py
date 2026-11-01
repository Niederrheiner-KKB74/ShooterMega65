"""Two static 16x16 views of the existing game projectile, same indexed palette."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/rocket-directions'
OUT=BASE/'generated'

def turn_right_45(src):
    # Inverse sampling in image coordinates (y grows downward): clockwise 45°.
    # Work on indices directly: no interpolation, resizing or palette reduction.
    dst=bytearray(256);k=math.sqrt(.5);centre=7.5
    for y in range(16):
        for x in range(16):
            sx=round(centre+(x-centre)*k+(y-centre)*k)
            sy=round(centre-(x-centre)*k+(y-centre)*k)
            if 0<=sx<16 and 0<=sy<16:dst[y*16+x]=src[sy*16+sx]
    return bytes(dst)

def main():
    cfg=json.loads((BASE/'source/rocket.json').read_text())
    pal=cfg['palette'];src=bytes.fromhex(''.join(cfg['rows']))
    frames=[src,turn_right_45(src)];OUT.mkdir(parents=True,exist_ok=True)
    strip=Image.new('RGBA',(32,16));preview=Image.new('RGB',(460,200),(18,24,32));d=ImageDraw.Draw(preview)
    nc=bytearray();fc=bytearray();rrb=bytearray(64);records=[]
    for n,data in enumerate(frames):
        name=('rocket_up','rocket_right45')[n]
        im=Image.new('RGBA',(16,16));im.putdata([tuple(pal[v])+(255 if v else 0,) for v in data]);im.save(OUT/(name+'.png'))
        strip.paste(im,(n*16,0));x=12+n*228
        d.text((x,8),('Original: nach oben','45 Grad nach rechts')[n],fill='white')
        large=im.resize((128,128),Image.Resampling.NEAREST);preview.paste(large,(x,35),large);preview.paste(im,(x+155,100),im);d.text((x+153,122),'1x',fill='white')
        frame=bytes(data[i]|data[i+1]<<4 for i in range(0,256,2));nc.extend(frame);rrb.extend(frame+bytes(64))
        for ty in (0,8):
            for tx in (0,8):
                for y in range(8):fc.extend(data[(ty+y)*16+tx:(ty+y)*16+tx+8])
        records.append(dict(id=name,width=16,height=16,angle_clockwise=n*45,rows=[data[y*16:y*16+16].hex() for y in range(16)],rrb_base=1+n*3,palette_byte=0xdf))
    strip.save(OUT/'rocket-views.png');preview.save(OUT/'preview.png')
    for name,data in [('rocket.indices.bin',b''.join(frames)),('rocket.ncm.bin',nc),('rocket.fcm.bin',fc),('rocket.rrb.bin',rrb),
                      ('palette.rgb',bytes(v for c in pal for v in c)),('palette.palregs.bin',bytes((c[ch]&15)<<4|c[ch]>>4 for ch in range(3) for c in pal))]:
        (OUT/name).write_bytes(data)
    (OUT/'indexed-source.json').write_text(json.dumps(records,indent=2)+'\n')
    (OUT/'rocket-views.inc').write_text('// Static views, NOT animation frames. Local bases. Source palette indices!\n// Runtime import must remap colours using merge_bank(), then relocate glyph bases.\nrocket_view_base: .byte 1,4\nrocket_view_w: .byte 1,1\nrocket_view_h: .byte 2,2\nrocket_view_pal: .byte $df,$df\n')
    m=dict(palette=pal,source=cfg['source'],source_pixel_sha256=hashlib.sha256(src).hexdigest(),
           transform='clockwise 45 degrees about (7.5,7.5), inverse nearest-neighbour index sampling, transparent outside 16x16',
           static_views=True,integrated=False,hardware_tested=False)
    m['files']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print('Original + clockwise 45-degree rocket view: 16x16, exact existing rocket palette; exported NCM/FCM/RRB.')

if __name__=='__main__':main()
