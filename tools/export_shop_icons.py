#!/usr/bin/env python3
"""Six exact 16x16 native shop icons; shared existing HUD/bonus palette."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/shop-upgrades';OUT=BASE/'generated'


def draw_icon(name):
    p=Image.new('L',(16,16));d=ImageDraw.Draw(p)
    if name.startswith('shot_'):
        count={'shot_ii':2,'shot_iii':3,'shot_iv':4}[name]
        # Clear separate luminous bolts; the same projectile motif on all tiers.
        xs={2:[4,10],3:[2,7,12],4:[1,5,9,13]}[count]
        for i,x in enumerate(xs):
            top=(3 if count==2 else 1 if i==count//2 else 4) if count<4 else (2 if i in (1,2) else 5)
            d.rectangle((x,top+1,x+1,top+6),fill=1)
            d.line((x,top,x,top+5),fill=2)
            d.point((x,top+6),fill=3);d.point((x,top+7),fill=7)
        # Small tier marks, inside the icon but separate from the projectile tips.
        for x in xs:d.point((x,14),fill=7)
    elif name=='bomb':
        d.line((9,5,10,2,12,2),fill=5)
        d.point((12,1),fill=3);d.point((13,2),fill=7);d.point((13,0),fill=2)
        d.rectangle((6,4,10,5),fill=5)
        d.ellipse((2,5,13,15),fill=1);d.ellipse((3,6,12,14),fill=4)
        d.arc((3,6,12,14),180,270,fill=5,width=1)
        d.line((5,7,7,7),fill=2);d.point((4,8),fill=5)
        d.line((5,11,10,11),fill=8)
    elif name=='homing_missile':
        # Diagonal missile plus an explicit target reticle, distinct from the bomb.
        d.polygon([(1,12),(3,14),(10,7),(8,5)],fill=5)
        d.polygon([(3,11),(4,12),(10,6),(9,5)],fill=2)
        d.polygon([(8,5),(11,2),(11,6),(10,7)],fill=8)
        d.polygon([(2,10),(1,7),(6,8)],fill=1)
        d.polygon([(5,13),(8,14),(7,9)],fill=1)
        d.line((1,13,0,15),fill=3);d.point((1,14),fill=7)
        d.ellipse((10,0,15,5),outline=6)
        d.line((12,0,12,2),fill=10);d.line((14,3,15,3),fill=10)
    elif name=='invulnerability':
        # Halo + heraldic shield; no S, green repair marker or opaque box.
        d.arc((0,0,15,15),190,350,fill=2,width=1)
        d.arc((0,0,15,15),10,160,fill=1,width=1)
        d.polygon([(4,3),(11,3),(11,8),(10,10),(7,13),(5,10),(4,8)],fill=5)
        d.polygon([(5,4),(10,4),(10,8),(7,11),(5,8)],fill=1)
        d.line((7,5,7,9),fill=2);d.line((5,7,9,7),fill=2)
        d.point((1,3),fill=7);d.point((13,12),fill=7);d.point((14,11),fill=2)
    else:raise ValueError(name)
    return p


def rgba(p,pal):
    im=Image.new('RGBA',p.size);im.putdata([tuple(pal[i])+(255 if i else 0,) for i in p.getdata()]);return im


def ncm(p):
    a=p.tobytes();return bytes(a[i]|a[i+1]<<4 for i in range(0,len(a),2))


def main():
    cfg=json.loads((BASE/'source/icons.json').read_text());pal=cfg['palette'];OUT.mkdir(parents=True,exist_ok=True)
    raw=bytearray();nc=bytearray();fc=bytearray();rrb=bytearray(64);records=[];indexed=[]
    strip=Image.new('RGBA',(96,16));atlas=Image.new('RGBA',(48,32))
    preview=Image.new('RGBA',(690,310),(18,24,32,255));pd=ImageDraw.Draw(preview)
    for i,item in enumerate(cfg['icons']):
        name=item['id'];p=draw_icon(name);im=rgba(p,pal);im.save(OUT/(name+'.png'))
        strip.paste(im,(i*16,0));atlas.paste(im,(i%3*16,i//3*16))
        records.append(dict(**item,width=16,height=16,indices_offset=len(raw),ncm_offset=len(nc),fcm_offset=len(fc),rrb_base=len(rrb)//64,palette_byte=0xcf))
        raw.extend(p.tobytes());ncmframe=ncm(p.crop((0,0,16,8)))+ncm(p.crop((0,8,16,16)));nc.extend(ncmframe);rrb.extend(ncmframe+bytes(64))
        for y in (0,8):
            for x in (0,8):fc.extend(p.crop((x,y,x+8,y+8)).tobytes())
        indexed.append(dict(id=name,rows=[p.tobytes()[y*16:(y+1)*16].hex() for y in range(16)]))
        x=12+i%3*228;y=12+i//3*150
        pd.text((x,y),item['title'],fill='white')
        enlarged=im.resize((96,96),Image.Resampling.NEAREST);preview.paste(enlarged,(x,y+25),enlarged)
        # Original-size copy to make the intended in-game scale reviewable.
        preview.paste(im,(x+120,y+65),im);pd.text((x+114,y+86),'1x',fill=(160,180,190))
    strip.save(OUT/'shop-icons-strip.png');atlas.save(OUT/'shop-icons-atlas.png');preview.save(OUT/'preview.png')
    for name,data in [('shop.indices.bin',raw),('shop.ncm.bin',nc),('shop.fcm.bin',fc),('shop.rrb.bin',rrb),('palette.rgb',bytes(v for c in pal for v in c)),('palette.palregs.bin',bytes(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in pal))]: (OUT/name).write_bytes(data)
    (OUT/'indexed-source.json').write_text(json.dumps(indexed,indent=2)+'\n')
    lines=['// Local icon frame indices; not automatically imported by the engine.']
    lines += [f'.const SHOP_{r["id"].upper()} = {i}' for i,r in enumerate(records)]
    lines += ['shop_icon_base: .byte '+','.join(str(r['rrb_base']) for r in records),'shop_icon_w: .fill 6, 1','shop_icon_h: .fill 6, 2','shop_icon_pal: .fill 6, $cf']
    (OUT/'shop-icons.inc').write_text('\n'.join(lines)+'\n')
    m=dict(schema=1,icons=records,palette=pal,palette_source=cfg['palette_source'],rrb_glyphs=19,integrated=False,emulator_tested=False,hardware_tested=False,
           provenance='New native pixel icons by Codex; deterministic integer geometry, not resized concept art.')
    m['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    print('Exported 6 distinct 16x16 shop icons, one shared existing HUD/bonus palette.')


if __name__=='__main__':main()
