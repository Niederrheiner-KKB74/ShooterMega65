#!/usr/bin/env python3
"""Export spec-sized pixel sources, PNG strips and candidate NCM/FCM data.

This is an additive art delivery. It does not change the running prototype.
"""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, __version__

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/spec-v2'
OUT=BASE/'generated'
BOARD=ROOT/'assets/art/reference-board/source/reference-board.png'


def ncm(p):
    a=p.tobytes()
    assert p.size==(16,8)
    return bytes(a[i]|(a[i+1]<<4) for i in range(0,128,2))


def tiles(p,mode):
    tw=16 if mode=='ncm' else 8
    assert p.width%tw==0 and p.height%8==0
    return b''.join(ncm(p.crop((x,y,x+tw,y+8))) if mode=='ncm' else p.crop((x,y,x+tw,y+8)).tobytes()
                    for y in range(0,p.height,8) for x in range(0,p.width,tw))


def rgba(p,pal):
    im=Image.new('RGBA',p.size)
    im.putdata([tuple(pal[v])+(255 if v else 0,) for v in p.getdata()])
    return im


def draw_targets():
    # Code-native pixel designs. Upper/left bevels are light; bottom/right dark.
    results={}
    for name,size in [('bunker',32),('flak',16)]:
        p=Image.new('L',(size,size));d=ImageDraw.Draw(p)
        if name=='bunker':
            d.rectangle((3,7,28,27),fill=3);d.rectangle((3,7,28,9),fill=6);d.rectangle((3,8,5,26),fill=5)
            d.rectangle((26,10,28,27),fill=2);d.rectangle((6,11,25,25),fill=4)
            d.rectangle((8,15,23,20),fill=1);d.line((8,14,23,14),fill=6)
            d.rectangle((11,24,20,29),fill=2);d.line((7,23,24,23),fill=5)
        else:
            d.rectangle((2,4,13,13),fill=3);d.line((2,4,12,4),fill=6);d.line((2,4,2,12),fill=5)
            d.ellipse((4,5,12,12),fill=4);d.line((6,7,6,1),fill=6,width=2)
            d.line((9,7,9,1),fill=5,width=2);d.rectangle((6,8,9,10),fill=2)
        results[name]=p
        rubble=Image.new('L',(size,size));d=ImageDraw.Draw(rubble)
        for y in range(3,size-2):
            for x in range(2,size-2):
                if ((x-size/2)/(size/2))**2+((y-size*.61)/(size*.3))**2<1 and (x*13+y*7)%9<6:
                    d.point((x,y),fill=[2,3,4,5][(x+2*y)%4])
        for x,y in [(size//3,size//2),(size//2,size*2//3)]:
            d.point((x,y),fill=8);d.point((x+1,y+1),fill=7)
        results[name+'_destroyed']=rubble
    return results


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((BASE/'source/crops.json').read_text())
    board=Image.open(BOARD).convert('RGB');assert board.size==(1536,1024)
    groups=[];families={}
    for g in cfg['groups']:
        if g['id']=='explosion_24':continue
        name='explosion_32' if g['id']=='explosion_32' else g['id']
        crops=[]
        for box in g['boxes']:
            im=board.crop(box).convert('RGBA')
            if not g.get('opaque'):
                im.putdata([p[:3]+(0 if max(p[:3])<=24 else 255,) for p in im.getdata()])
                im=im.crop(im.getbbox())
            crops.append(im)
        mw=max(p.width for p in crops);mh=max(p.height for p in crops)
        frames=[]
        for im in crops:
            w,h=g['size']
            if g.get('opaque'):frame=im.resize((w,h),Image.Resampling.NEAREST)
            else:
                # Source sampling is nearest-neighbour; no blended edge colours.
                fw,fh=g.get('content_size',[w,h]);s=min(fw/mw,fh/mh)
                small=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.NEAREST)
                frame=Image.new('RGBA',(w,h));frame.paste(small,((w-small.width)//2,(h-small.height)//2))
            if g['kind']=='enemy':frame=frame.transpose(Image.Transpose.ROTATE_180)
            if g['kind'] in ('player','enemy'):
                # Re-establish upper-left edge light after orientation changes.
                # Discrete bevel steps, then palette reduction; no blurred pixels.
                original=frame.copy();px=original.load();lit=frame.load()
                for y in range(h):
                    for x in range(w):
                        if not px[x,y][3]:continue
                        top=y==0 or not px[x,y-1][3];left=x==0 or not px[x-1,y][3]
                        bottom=y==h-1 or not px[x,y+1][3];right=x==w-1 or not px[x+1,y][3]
                        gain=1.16 if top or left else .82 if bottom or right else 1
                        lit[x,y]=tuple(min(255,round(v*gain)) for v in px[x,y][:3])+(255,)
            frames.append(frame)
        family=g.get('palette',name)
        for im in frames:families.setdefault(family,[]).extend(p[:3] for p in im.getdata() if p[3])
        groups.append(dict(id=name,kind=g['kind'],size=g['size'],frames=frames,palette=family,opaque=g.get('opaque',False),provenance='reference-board-derived; nearest sampling, inferred black mask, quantized; not original-grid recovery'))
    palettes={}
    for family,pixels in families.items():
        im=Image.new('RGB',(len(pixels),1));im.putdata(pixels)
        pal=im.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).getpalette()
        pal=(pal+[0]*45)[:45]
        palettes[family]=[[0,0,0]]+[pal[i:i+3] for i in range(0,45,3)]
    def index(im,pal):
        p=Image.new('L',im.size);cache={};data=[]
        for r,g,b,a in im.getdata():
            if not a:data.append(0);continue
            key=(r,g,b)
            if key not in cache:cache[key]=min(range(1,16),key=lambda i:sum((key[k]-pal[i][k])**2 for k in range(3)))
            data.append(cache[key])
        p.putdata(data);return p
    for g in groups:g['frames']=[index(p,palettes[g['palette']]) for p in g['frames']]
    palettes['fixed_targets']=[[0,0,0],[18,25,32],[39,45,47],[69,77,76],[103,112,106],[153,164,145],[213,219,181],[173,67,32],[245,157,51],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
    palettes['fixed_targets'][9:12]=[[36,62,28],[58,85,37],[90,116,54]]
    for name,p in draw_targets().items():groups.append(dict(id=name,kind='fixed_target',size=list(p.size),palette='fixed_targets',frames=[p],provenance='new code-native pixel design by Codex; upper-left bevel lighting; not extracted from poster'))
    hud=json.loads((BASE/'source/hud.json').read_text())
    palettes['hud']=hud['palette']
    for name,patterns in [('hud_digits',hud['digits']),('hud_icons',hud['icons'])]:
        frames=[]
        for pattern in patterns:
            p=Image.new('L',(8,8));p.putdata([int(v,16) for row in pattern for v in row]);frames.append(p)
        groups.append(dict(id=name,kind='hud',size=[8,8],palette='hud',frames=frames,provenance='new manually specified pixel patterns by Codex'))
    manifest=dict(schema=2,spec_sha256=hashlib.sha256((BASE/'source/artwork_spec.md').read_bytes()).hexdigest(),
                  board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),pillow=__version__,assembled=False,emulator_tested=False,hardware_tested=False,palettes=palettes,groups=[])
    raw=bytearray();fcm=bytearray();ncmdata=bytearray();rrb=bytearray(64);rrb_frames=[];player=bytearray();indexed=[]
    previews=[];terrain=[]
    for g in groups:
        pal=palettes[g['palette']];w,h=g['size'];strip=Image.new('RGBA',(w*len(g['frames']),h))
        entry={k:v for k,v in g.items() if k!='frames'};entry['frames']=[]
        for i,p in enumerate(g['frames']):
            strip.paste(rgba(p,pal),(i*w,0))
            f=dict(index=i,indices_offset=len(raw),indices_bytes=w*h,fcm_offset=len(fcm),fcm_bytes=len(tiles(p,'fcm')))
            raw.extend(p.tobytes());fcm.extend(tiles(p,'fcm'))
            if w%16==0:
                f.update(ncm_offset=len(ncmdata),ncm_bytes=len(tiles(p,'ncm')));ncmdata.extend(tiles(p,'ncm'))
            if g['kind'] in ('enemy','projectile','explosion'):
                base=len(rrb)//64
                for x in range(0,w,16):
                    for y in range(0,h,8):rrb.extend(ncm(p.crop((x,y,x+16,y+8))))
                    rrb.extend(bytes(64))
                rrb_frames.append(dict(group=g['id'],frame=i,base=base,w=w//16,h=h//8,palette=g['palette']))
            if g['kind']=='player':
                f['sprite_offset']=len(player)
                for x in (0,16):
                    a=p.crop((x,0,x+16,24)).tobytes()
                    player.extend(bytes((a[j]<<4)|a[j+1] for j in range(0,len(a),2))+bytes(64))
            indexed.append(dict(group=g['id'],frame=i,width=w,height=h,palette=g['palette'],rows=[p.tobytes()[y*w:(y+1)*w].hex() for y in range(h)]))
            entry['frames'].append(f)
            if g['kind'] in ('terrain','decoration'):terrain.append((g['id'],i,p,g['palette']))
        strip.save(OUT/(g['id']+'.png'));manifest['groups'].append(entry)
        # Contact sheet displays nearest-neighbour enlargements, labels outside assets.
        scale=4 if g['kind'] not in ('hud',) else 6
        row=Image.new('RGBA',(900,max(64,h*scale+24)),(18,24,32,255));d=ImageDraw.Draw(row);d.text((8,4),f"{g['id']}  {w}x{h}",fill='white')
        enlarged=strip.resize((strip.width*scale,h*scale),Image.Resampling.NEAREST)
        row.paste(enlarged,(8,22),enlarged);previews.append(row)
    (OUT/'frames.indices.bin').write_bytes(raw);(OUT/'frames.fcm.bin').write_bytes(fcm);(OUT/'frames.ncm.bin').write_bytes(ncmdata)
    (OUT/'rrb-pixies.bin').write_bytes(rrb);(OUT/'player.sprite.bin').write_bytes(player)
    manifest['rrb_frames']=rrb_frames
    manifest['runtime_budget']={'all_rrb_glyphs':len(rrb)//64,'stage1_limit':256,'all_frames_fit_stage1':len(rrb)<=16384,'automatic_integration':False}
    (OUT/'indexed-source.json').write_text(json.dumps(indexed,indent=2)+'\n')
    rgbdata=bytearray();regs=bytearray();manifest['palette_offsets']={}
    for name,pal in palettes.items():
        manifest['palette_offsets'][name]=len(rgbdata);rgbdata.extend(v for c in pal for v in c)
        regs.extend(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in pal)
    (OUT/'palettes.rgb').write_bytes(rgbdata);(OUT/'palettes.palregs.bin').write_bytes(regs)
    # Compose fixed targets onto opaque ground in their fourth terrain palette.
    for g in groups:
        if g['kind']!='fixed_target':continue
        p=g['frames'][0];ground=Image.new('L',p.size)
        ground.putdata([9+int((x*7+y*11)%13==0)+int((x+y*3)%23==0) for y in range(p.height) for x in range(p.width)])
        ground.paste(p,mask=p.point(lambda v:255 if v else 0))
        for y in range(0,p.height,16):
            for x in range(0,p.width,16):terrain.append((g['id'],(y//16)*(p.width//16)+x//16,ground.crop((x,y,x+16,y+16)),g['palette']))
    # A deduplicated tile sheet and a top-to-bottom map using four palettes.
    unique=[];lookup={};tile_meta=[]
    for name,i,p,palname in terrain:
        key=(palname,p.tobytes())
        if key not in lookup:
            lookup[key]=len(unique);unique.append((p,palname));tile_meta.append(dict(id=lookup[key],palette=palname,group=name,frame=i))
    sheet=Image.new('RGBA',(16*13,16*math.ceil(len(unique)/13)))
    for i,(p,palname) in enumerate(unique):sheet.paste(rgba(p,palettes[palname]),((i%13)*16,(i//13)*16))
    sheet.save(OUT/'terrain-sheet.png')
    assert len(unique)<=512
    ids={(name,i):lookup[pn,p.tobytes()] for name,i,p,pn in terrain}
    level=Image.new('RGBA',(336,512));rows=[]
    for y in range(32):
        row=[]
        for x in range(21):
            # Hidden left column is filled deliberately, never relied on for visible targets.
            name='sea' if x<6 else 'coast' if x==6 else 'forest'
            i=(x*3+y)%6
            if x in (14,15):name='road';i=2 if x==14 else 3
            if 11<=x<=13 and 9<=y<=11:name='base';i=(x+y)%6
            if 10<=x<12 and 15<=y<17:name='bunker';i=(y-15)*2+x-10
            if 17<=x<19 and 25<=y<27:name='bunker_destroyed';i=(y-25)*2+x-17
            if (x,y)==(8,20):name='flak';i=0
            if (x,y)==(18,19):name='flak_destroyed';i=0
            tile=ids[name,i];row.append(tile);p,pn=unique[tile]
            level.paste(rgba(p,palettes[pn]),(x*16,y*16))
        rows.append(row)
    level.save(OUT/'level-example.png')
    (OUT/'level-example.json').write_text(json.dumps(dict(width=336,height=512,tile_size=16,hidden_left=16,level_start='bottom',row_order='top-to-bottom',tiles=tile_meta,rows=rows),indent=2)+'\n')
    (OUT/'level-example.map16.bin').write_bytes(b''.join(t.to_bytes(2,'little') for row in rows for t in row))
    # Palette IDs are local to this level bundle; no fixed runtime bank assignment.
    terrainpals=['water','nature','structures','fixed_targets'];tilebytes=bytearray();map_pal=bytearray()
    for p,pn in unique:tilebytes.extend(tiles(p,'ncm'))
    for row in rows:map_pal.extend(terrainpals.index(unique[t][1]) for t in row)
    (OUT/'terrain.ncm.bin').write_bytes(tilebytes);(OUT/'level-example.palette.bin').write_bytes(map_pal)
    manifest['landscape']={'unique_tiles':len(unique),'palettes':terrainpals,'tile_size':16,'map_width':336,'map_height':512,'current_stage1_direct_import':False}
    manifest['fixed_target_pairs']=[['bunker','bunker_destroyed'],['flak','flak_destroyed']]
    preview=Image.new('RGBA',(900,sum(p.height for p in previews)),(18,24,32,255));y=0
    for p in previews:preview.paste(p,(0,y));y+=p.height
    preview.save(OUT/'preview-all.png');preview.crop((0,0,900,sum(p.height for p in previews[:5]))).save(OUT/'preview-aircraft.png')
    preview.crop((0,preview.height-sum(p.height for p in previews[-6:]),900,preview.height)).save(OUT/'preview-additions.png')
    manifest['files']={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f"Exported {len(indexed)} frames, {len(unique)} terrain tiles, 4 landscape palettes, {len(rrb)//64} guarded RRB glyphs")


if __name__=='__main__':main()
