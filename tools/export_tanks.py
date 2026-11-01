#!/usr/bin/env python3
"""Native 16x16 tank art with directional track animation; no image sampling."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/ground-vehicles'
OUT=BASE/'generated'
DIRECTIONS=('north','east','south','west')


def frame(direction,phase):
    # Geometry/material masks are rotated BEFORE world-space lighting.
    body=Image.new('L',(16,16));d=ImageDraw.Draw(body)
    d.polygon([(4,3),(6,2),(10,2),(11,4),(11,12),(10,14),(5,14),(4,12)],fill=10)
    d.rectangle((5,11,10,13),fill=9)
    d.rectangle((6,4,10,9),fill=11)
    d.point((5,4),fill=6);d.point((10,4),fill=6)
    d.rectangle((7,0,8,5),fill=4)
    d.rectangle((6,6,9,9),fill=10);d.point((7,7),fill=9)
    d.line((6,12,9,12),fill=2);d.point((10,10),fill=7)
    tracks=Image.new('L',(16,16));t=ImageDraw.Draw(tracks)
    t.rectangle((2,3,4,13),fill=2);t.rectangle((11,3,13,13),fill=2)
    for y in range(3,14):
        # Both belt surfaces move toward the tail, opposite the travel direction.
        for x in (2,3,4,11,12,13):
            tracks.putpixel((x,y),[2,3,5,3][(y-phase)%4])
    rotate={'north':None,'east':Image.Transpose.ROTATE_270,'south':Image.Transpose.ROTATE_180,'west':Image.Transpose.ROTATE_90}[direction]
    if rotate is not None:body=body.transpose(rotate);tracks=tracks.transpose(rotate)
    original=body.copy();px=original.load()
    for y in range(16):
        for x in range(16):
            v=px[x,y]
            if v not in (9,10,11,4):continue
            top=y==0 or not px[x,y-1];left=x==0 or not px[x-1,y]
            bottom=y==15 or not px[x,y+1];right=x==15 or not px[x+1,y]
            if v in (9,10,11):body.putpixel((x,y),11 if top or left else 9 if bottom or right else v)
            elif v==4:body.putpixel((x,y),6 if top or left else 2 if bottom or right else 4)
    # Overlay body so tracks remain partly hidden under the chassis edges.
    result=tracks.copy();result.paste(body,mask=body.point(lambda v:255 if v else 0))
    visible=tracks.point(lambda v:255 if v else 0)
    visible.paste(0,(0,0,16,16),body.point(lambda v:255 if v else 0))
    return result,visible


def ncm(p):
    a=p.tobytes();assert p.size==(16,8)
    return bytes(a[i]|a[i+1]<<4 for i in range(0,128,2))


def rgba(p,palette):
    im=Image.new('RGBA',p.size);im.putdata([tuple(palette[i])+(255 if i else 0,) for i in p.getdata()]);return im


def main():
    cfg=json.loads((BASE/'source/tank.json').read_text());pal=cfg['palette']
    OUT.mkdir(parents=True,exist_ok=True)
    raw=bytearray();ncmbytes=bytearray();fcm=bytearray();rrb=bytearray(64);records=[];indexed=[]
    sheet=Image.new('RGBA',(64,64));preview=Image.new('RGBA',(600,4*152),(18,24,32,255))
    for di,direction in enumerate(DIRECTIONS):
        strip=Image.new('RGBA',(64,16));mask=None
        for phase in range(4):
            p,mask=frame(direction,phase);im=rgba(p,pal);strip.paste(im,(phase*16,0));sheet.paste(im,(phase*16,di*16))
            rec=dict(direction=direction,phase=phase,indices_offset=len(raw),ncm_offset=len(ncmbytes),fcm_offset=len(fcm),rrb_base=len(rrb)//64,w=1,h=2,palette_byte=0x4f)
            raw.extend(p.tobytes());ncmbytes.extend(ncm(p.crop((0,0,16,8)))+ncm(p.crop((0,8,16,16))))
            for y in (0,8):
                for x in (0,8):fcm.extend(p.crop((x,y,x+8,y+8)).tobytes())
            rrb.extend(ncm(p.crop((0,0,16,8)))+ncm(p.crop((0,8,16,16)))+bytes(64))
            records.append(rec);indexed.append(dict(direction=direction,phase=phase,rows=[p.tobytes()[y*16:(y+1)*16].hex() for y in range(16)]))
        strip.save(OUT/('tank_'+direction+'.png'));mask.save(OUT/('track_mask_'+direction+'.png'))
        enlarged=strip.resize((512,128),Image.Resampling.NEAREST)
        ImageDraw.Draw(preview).text((10,di*152+2),direction+'  16x16 / 4 frames',fill='white');preview.paste(enlarged,(10,di*152+20),enlarged)
        # Native animated previews, four discrete frames, no interpolation.
        animation=[rgba(frame(direction,i)[0],pal).resize((128,128),Image.Resampling.NEAREST) for i in range(4)]
        animation[0].save(OUT/('tank_'+direction+'.webp'),save_all=True,append_images=animation[1:],duration=cfg['preview_frame_ms'],loop=0,lossless=True,background=(0,0,0,0))
    sheet.save(OUT/'tank_atlas.png');preview.save(OUT/'preview.png')
    for name,data in [('tank.indices.bin',raw),('tank.ncm.bin',ncmbytes),('tank.fcm.bin',fcm),('tank.rrb.bin',rrb)]: (OUT/name).write_bytes(data)
    (OUT/'palette.rgb').write_bytes(bytes(v for c in pal for v in c))
    (OUT/'palette.palregs.bin').write_bytes(bytes(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in pal))
    (OUT/'indexed-source.json').write_text(json.dumps(indexed,indent=2)+'\n')
    inc=['// Optional import tables; not automatically included by Stage 2.']
    for i,r in enumerate(records):inc.append(f'.const TANK_{r["direction"].upper()}_{r["phase"]}={i}')
    inc+=['tank_frame_base: .byte '+','.join(str(r['rrb_base']) for r in records),'tank_frame_w: .fill 16, 1','tank_frame_h: .fill 16, 2','tank_frame_pal: .fill 16, $4f']
    (OUT/'tank-frames.inc').write_text('\n'.join(inc)+'\n')
    manifest=dict(schema=1,frame_size=[16,16],frames=records,palette=pal,shared_palette='stage2 fixed_targets, text bank 4 ($4f); no extra bank',
                  provenance='New code-native pixel art by Codex; not extracted from the reference board.',source_sha256=hashlib.sha256((BASE/'source/tank.json').read_bytes()).hexdigest(),
                  source_stage2_commit=cfg['stage2_commit'],frame_ms=cfg['preview_frame_ms'],animation='0,1,2,3, repeat; freeze phase on stop; barrel follows travel direction',
                  rrb_glyphs=len(rrb)//64,hardware_tested=False,emulator_tested=False,integrated=False)
    manifest['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported 16 tank frames, shared Stage-2 bank-4 palette, 49 guarded RRB glyphs.')


if __name__=='__main__':main()
