#!/usr/bin/env python3
"""Reconstruct indexed assets from the supplied reference poster (Pillow required).

No engine files are modified. Run from any directory. Outputs are additive assets.
"""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets/art/reference-board'


def packed_ncm(p):
    assert p.width == 16 and p.height == 8
    a = list(p.getdata())
    return bytes(a[i] | (a[i + 1] << 4) for i in range(0, 128, 2))


def tiled(p, tw):
    # Local tile 0, row-major tile order; transparent padding on right/bottom.
    canvas = Image.new('L', (math.ceil(p.width / tw) * tw, math.ceil(p.height / 8) * 8))
    canvas.paste(p)
    data = bytearray()
    for y in range(0, canvas.height, 8):
        for x in range(0, canvas.width, tw):
            tile = canvas.crop((x, y, x + tw, y + 8))
            data.extend(packed_ncm(tile) if tw == 16 else tile.tobytes())
    return bytes(data)


def rgb_image(indices, palette):
    out = Image.new('RGBA', indices.size)
    out.putdata([tuple(palette[i]) + (0 if i == 0 else 255,) for i in indices.getdata()])
    return out


def family(g):
    if g['kind'] == 'player':
        return 'player'
    if g['kind'] in ('enemy', 'projectile', 'explosion'):
        return 'objects'
    if g['id'] in ('sea', 'coast'):
        return 'water'
    if g['id'] in ('forest', 'cliff'):
        return 'nature'
    return 'structures'


def main():
    cfg = json.loads((BASE / 'source/crops.json').read_text())
    source_path = BASE / 'source' / cfg['source']
    source = Image.open(source_path).convert('RGB')
    assert list(source.size) == cfg['source_size']
    gen = BASE / 'generated'
    gen.mkdir(parents=True, exist_ok=True)
    groups, palette_pixels = [], {}
    for g in cfg['groups']:
        crops = []
        for box in g['boxes']:
            assert 0 <= box[0] < box[2] <= source.width and 0 <= box[1] < box[3] <= source.height
            crop = source.crop(box).convert('RGBA')
            if not g.get('opaque', False):
                # Poster black is an inferred mask, not an original alpha channel.
                crop.putdata([tuple(p[:3]) + (0 if max(p[:3]) <= cfg['black_threshold'] else 255,) for p in crop.getdata()])
                bbox = crop.getbbox()
                assert bbox, g['id']
                crop = crop.crop(bbox)
            crops.append(crop)
        # Same scale within each group, bottom aligned: no per-frame auto-zoom.
        maxw = max(c.width for c in crops)
        maxh = max(c.height for c in crops)
        frames, engine_frames = [], []
        for crop in crops:
            for size, dest in [(tuple(g['size']), frames), ((16,16), engine_frames)] if g['kind'] in ('terrain','decoration') else [(tuple(g['size']), frames)]:
                if g.get('opaque', False):
                    image = crop.resize(size, Image.Resampling.BOX)
                else:
                    factor = min(size[0] / maxw, size[1] / maxh)
                    resized = crop.resize((max(1,round(crop.width*factor)),max(1,round(crop.height*factor))),Image.Resampling.BOX)
                    image = Image.new('RGBA', size)
                    image.paste(resized, ((size[0]-resized.width)//2,size[1]-resized.height))
                dest.append(image)
                visible=[p[:3] for p in image.getdata() if p[3] >= cfg['alpha_cutoff']]
                palette_pixels.setdefault(family(g), []).extend(visible)
                if g['kind'] in ('enemy','projectile','explosion'):
                    palette_pixels.setdefault(g['id'], []).extend(visible)
        groups.append((g,frames,engine_frames))
    palettes = {}
    for name, pixels in palette_pixels.items():
        sample=Image.new('RGB',(len(pixels),1));sample.putdata(pixels)
        quant=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
        flat=quant.getpalette()
        palettes[name]=[[0,0,0]]+[flat[i:i+3] for i in range(0,45,3)]
    def index_image(im, pal, opaque=False):
        indices=Image.new('L',im.size)
        # Exact nearest RGB, restricted to 1..15: index zero remains transparent.
        cache={}
        values=[]
        for p in im.getdata():
            if not opaque and p[3] < cfg['alpha_cutoff']:
                values.append(0);continue
            rgb=p[:3]
            if rgb not in cache:
                cache[rgb]=min(range(1,16),key=lambda i:sum((rgb[c]-pal[i][c])**2 for c in range(3)))
            values.append(cache[rgb])
        indices.putdata(values)
        return indices
    manifest=dict(schema=1,source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                  provenance='Derived from user-supplied PNG by crop, black-mask inference, BOX reduction and 15-colour quantization. NOT original-grid recovery.',
                  prototype_commit='e4fe5111babb5985333a8b337275ac665d08c536',pillow=pillow_version,
                  assembled=False,emulator_tested=False,hardware_tested=False,palettes=palettes,groups=[])
    bank={'objects':2,'water':1,'nature':3,'structures':4}
    raw=bytearray();fcm=bytearray();ncm=bytearray();pixies=bytearray(64);terrain=bytearray();player=bytearray()
    pix_info=[];tile_info=[];source_data=[];preview_rows=[]
    for g,frames,engine_frames in groups:
        palname=g['id'] if g['kind'] in ('enemy','projectile','explosion') else family(g)
        pal=palettes[palname]
        indexed=[index_image(im,pal,g.get('opaque',False)) for im in frames]
        entry=dict(id=g['id'],kind=g['kind'],palette=palname,source_boxes=g['boxes'],size=g['size'],frames=[],labels=g.get('labels',[]),note=g.get('note',''))
        # Preserve orientation from poster (aircraft noses up); runtime enemies rotate 180°.
        strip=Image.new('RGBA',(g['size'][0]*len(indexed),g['size'][1]))
        row=Image.new('RGBA',(760,max(130,g['size'][1]*4+22)),(20,24,32,255))
        ImageDraw.Draw(row).text((5,3),g['id']+' (source orientation)',fill='white')
        rrb_images=[]
        for i,p in enumerate(indexed):
            rgba=rgb_image(p,pal);strip.paste(rgba,(i*p.width,0))
            row.paste(rgba.resize((p.width*4,p.height*4),Image.Resampling.NEAREST),(8+i*max(36,p.width*4+8),24),rgba.resize((p.width*4,p.height*4),Image.Resampling.NEAREST))
            fi=dict(frame=i,indices_offset=len(raw),indices_bytes=p.width*p.height,
                    fcm_offset=len(fcm),fcm_bytes=len(tiled(p,8)),ncm_offset=len(ncm),ncm_bytes=len(tiled(p,16)))
            raw.extend(p.tobytes());fcm.extend(tiled(p,8));ncm.extend(tiled(p,16));entry['frames'].append(fi)
            source_data.append(dict(group=g['id'],frame=i,width=p.width,height=p.height,palette=palname,rows=[p.tobytes()[y*p.width:(y+1)*p.width].hex() for y in range(p.height)]))
            if g['kind']=='player':
                canvas=Image.new('L',(32,24));canvas.paste(p,(4,0))
                start=len(player)
                for half in range(2):
                    a=list(canvas.crop((half*16,0,half*16+16,24)).getdata())
                    player.extend(bytes((a[j]<<4)|a[j+1] for j in range(0,len(a),2))+bytes(64))
                fi['player_sprite_offset']=start;fi['player_sprite_bytes']=512
            elif g['kind'] in ('enemy','projectile','explosion'):
                # Stage-1 currently hardcodes a single palette $2f for ALL objects.
                p=index_image(frames[i],palettes['objects'])
                w=math.ceil(p.width/16)*16;h=math.ceil(p.height/8)*8
                canvas=Image.new('L',(w,h));canvas.paste(p,((w-p.width)//2,0))
                if g['kind']=='enemy':
                    # Rotate content inside its original visible frame, then centre-pad.
                    canvas=Image.new('L',(w,h));canvas.paste(p.transpose(Image.Transpose.ROTATE_180),((w-p.width)//2,0))
                base=len(pixies)//64
                for x in range(0,w,16):
                    for y in range(0,h,8):pixies.extend(packed_ncm(canvas.crop((x,y,x+16,y+8))))
                    pixies.extend(bytes(64))
                rec=dict(name=g['id'].upper()+'_'+str(i),group=g['id'],frame=i,base=base,w=w//16,h=h//8,palette_byte=0x2f,
                         visible_x=(w-p.width)//2,visible_width=p.width,visible_height=p.height,rotated_180=g['kind']=='enemy')
                pix_info.append(rec);fi['rrb']=rec
                rrb_images.append(rgb_image(canvas,palettes['objects']))
        strip.save(gen/(g['id']+'.png'))
        if rrb_images:
            rstrip=Image.new('RGBA',(rrb_images[0].width*len(rrb_images),rrb_images[0].height))
            for i,im in enumerate(rrb_images):rstrip.paste(im,(i*im.width,0))
            rstrip.save(gen/(g['id']+'-rrb.png'))
        preview_rows.append(row)
        if engine_frames:
            estrip=Image.new('RGBA',(16*len(engine_frames),16))
            for i,im in enumerate(engine_frames):
                p=index_image(im,pal,g.get('opaque',False));estrip.paste(rgb_image(p,pal),(i*16,0))
                base=len(terrain)//64;terrain.extend(tiled(p,16))
                tile_info.append(dict(group=g['id'],frame=i,glyph_top=base,glyph_bottom=base+1,palette_byte=(bank[family(g)]<<4)|15))
            estrip.save(gen/(g['id']+'-engine16.png'))
        manifest['groups'].append(entry)
    assert len(pixies)//64 <= 256, '8-bit frame_base and 16KB pixie region exceeded'
    assert len(terrain)//64 <= 256, 'Stage-1 map glyph offsets are one byte'
    manifest['rrb_frames']=pix_info;manifest['terrain_tiles']=tile_info
    manifest['totals']={'frames':len(source_data),'rrb_glyphs':len(pixies)//64,'terrain_glyphs':len(terrain)//64}
    for name,data in [('frames.indices.bin',raw),('frames.fcm.bin',fcm),('frames.ncm.bin',ncm),('rrb-pixies.bin',pixies),('terrain16.ncm.bin',terrain),('player-all.sprite.bin',player),('player-normal.sprite.bin',player[4*512:5*512])]:
        (gen/name).write_bytes(data)
    # Engine planar register data: R plane, G plane, B plane; swapped nibbles.
    swap=lambda v:((v&15)<<4)|(v>>4)
    sprpal=palettes['player']*2
    (gen/'player.sprpal.bin').write_bytes(bytes(swap(c[ch]) for ch in range(3) for c in sprpal))
    rgbdata=bytearray();regdata=bytearray();manifest['palette_offsets']={}
    for name,pal in palettes.items():
        manifest['palette_offsets'][name]=len(rgbdata)
        rgbdata.extend(bytes(v for c in pal for v in c))
        regdata.extend(bytes(swap(c[ch]) for ch in range(3) for c in pal))
    (gen/'palettes.rgb').write_bytes(rgbdata)
    (gen/'palettes.palregs.bin').write_bytes(regdata)
    lines=['// Candidate frame table, not automatically included by the engine.']
    for i,rec in enumerate(pix_info):lines.append(f'.const ART_{rec["name"]} = {i}')
    for label,key in [('art_frame_base','base'),('art_frame_w','w'),('art_frame_h','h')]:lines.append(label+': .byte '+','.join(str(r[key]) for r in pix_info))
    (gen/'rrb-frames.inc').write_text('\n'.join(lines)+'\n')
    (gen/'indexed-source.json').write_text(json.dumps(source_data,indent=2)+'\n')
    manifest['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(gen.iterdir()) if p.is_file() and p.name != 'manifest.json' and not p.name.startswith('preview')}
    (gen/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    preview=Image.new('RGBA',(760,sum(r.height for r in preview_rows)),(20,24,32,255));y=0
    for r in preview_rows:preview.paste(r,(0,y));y+=r.height
    preview.save(gen/'preview.png')
    preview.crop((0,0,760,sum(r.height for r in preview_rows[:5]))).save(gen/'preview-aircraft.png')
    print(json.dumps(manifest['totals']))


if __name__=='__main__':main()
