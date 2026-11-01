#!/usr/bin/env python3
"""Medieval shield and three gold coin sizes, sharing the HUD/bonus palette."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/bonus-capsules';OUT=BASE/'generated'


def rgba(p,pal):
    im=Image.new('RGBA',p.size);im.putdata([tuple(pal[i])+(255 if i else 0,) for i in p.getdata()]);return im


def ncm(p):
    a=p.tobytes();return bytes(a[i]|a[i+1]<<4 for i in range(0,len(a),2))


def main():
    cfg=json.loads((BASE/'source/capsules.json').read_text());pal=cfg['palette'];OUT.mkdir(parents=True,exist_ok=True)
    raw=bytearray();nc=bytearray();fc=bytearray();rrb=bytearray(64);records=[];source=[]
    preview=Image.new('RGBA',(720,300),(18,24,32,255));pd=ImageDraw.Draw(preview)
    for i,desc in enumerate(cfg['designs']):
        w,h=desc['size'];box=desc['body_box'];x0,y0,x1,y1=box
        p=Image.new('L',(w,h));d=ImageDraw.Draw(p)
        gx=gy=None
        if desc['design']=='medieval_shield':
            d.polygon([(2,1),(13,1),(13,7),(12,10),(10,12),(7,15),(4,12),(2,8)],fill=5)
            d.line([(2,7),(2,1),(12,1)],fill=2)
            d.polygon([(4,3),(11,3),(11,7),(10,10),(7,12),(5,10),(4,7)],fill=1)
            d.polygon([(8,3),(11,3),(11,7),(10,10),(8,12)],fill=6)
            d.line((7,3,7,12),fill=2,width=2);d.line((4,6,11,6),fill=2,width=2)
            d.point((4,3),fill=10)
        else:
            d.ellipse(box,fill=1)
            d.ellipse((x0+1,y0+1,x1-1,y1-1),fill=3)
            d.ellipse((x0+2,y0+2,x1-2,y1-2),fill=7)
            d.arc((x0+1,y0+1,x1-1,y1-1),180,270,fill=2,width=1)
            glyph=cfg['glyphs']['$'];scale=desc['glyph_scale'];gw=len(glyph[0])*scale;gh=len(glyph)*scale
            gx=(w-gw)//2;gy=(h-gh)//2
            # Embossed dollar on the gold face: no dark rectangular label panel.
            for yy,row in enumerate(glyph):
                for xx,v in enumerate(row):
                    if v=='1':d.rectangle((gx+xx*scale,gy+yy*scale,gx+(xx+1)*scale-1,gy+(yy+1)*scale-1),fill=3)
        rgba(p,pal).save(OUT/(desc['id']+'.png'))
        rec=dict(**desc,indices_offset=len(raw),ncm_offset=len(nc),fcm_offset=len(fc),rrb_base=len(rrb)//64,palette_byte=0xcf,glyph_origin=[gx,gy])
        raw.extend(p.tobytes())
        for y in range(0,h,8):
            for x in range(0,w,16):nc.extend(ncm(p.crop((x,y,x+16,y+8))))
            for x in range(0,w,8):fc.extend(p.crop((x,y,x+8,y+8)).tobytes())
        for x in range(0,w,16):
            for y in range(0,h,8):rrb.extend(ncm(p.crop((x,y,x+16,y+8))))
            rrb.extend(bytes(64))
        source.append(dict(id=desc['id'],width=w,height=h,rows=[p.tobytes()[y*w:(y+1)*w].hex() for y in range(h)]));records.append(rec)
        im=rgba(p,pal).resize((w*6,h*6),Image.Resampling.NEAREST);xx=12+i*158
        pd.text((xx,14),desc['id'],fill='white');pd.text((xx,31),f'{w}x{h}',fill='white');preview.paste(im,(xx,65),im)
    preview.save(OUT/'preview.png')
    for name,data in [('capsules.indices.bin',raw),('capsules.ncm.bin',nc),('capsules.fcm.bin',fc),('capsules.rrb.bin',rrb),('palette.rgb',bytes(v for c in pal for v in c)),('palette.palregs.bin',bytes(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in pal))]: (OUT/name).write_bytes(data)
    (OUT/'indexed-source.json').write_text(json.dumps(source,indent=2)+'\n')
    m=dict(schema=1,designs=records,palette=pal,shared_palette='Stage 2 HUD/bonus bank 12, $cf; exact RGB match',
           provenance='Revised native pixel designs: heraldic medieval shield without S, circular gold coins in three diameters with embossed dollar signs.',integrated=False,hardware_tested=False,emulator_tested=False,rrb_glyphs=len(rrb)//64)
    m['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('Exported medieval shield and 3 gold coin sizes, using unchanged HUD/bonus bank 12.')


if __name__=='__main__':main()
