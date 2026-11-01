"""Native indexed enemy views: eight headings and real foreshortened bank poses."""
import hashlib
import json
import math
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/enemy-views';OUT=BASE/'generated'
DIRS=('north','northeast','east','southeast','south','southwest','west','northwest')

def rotate(a,clockwise):
    if clockwise%90==0:return np.ascontiguousarray(np.rot90(a,-clockwise//90))
    h,w=a.shape;cx=(w-1)/2;cy=(h-1)/2;c=math.cos(math.radians(clockwise));s=math.sin(math.radians(clockwise))
    out=np.zeros_like(a)
    for y in range(h):
        for x in range(w):
            sx=round(cx+(x-cx)*c+(y-cy)*s);sy=round(cy-(x-cx)*s+(y-cy)*c)
            if 0<=sx<w and 0<=sy<h:out[y,x]=a[sy,sx]
    return out

def bank(a,side):
    # Down-facing plane: asymmetric wing foreshortening plus a small nose yaw.
    # This is not just rotating or mirroring a top-down picture.
    sign=-1 if side=='left' else 1;out=np.zeros_like(a);cy=cx=15.5;yaw=sign*.12;roll=sign*.16
    for y in range(32):
        for x in range(32):
            xx=x-cx;yy=y-cy;v=xx-yaw*yy
            scale=.72 if v*sign>0 else .92
            dx=v/(scale-yaw*roll);dy=yy-roll*dx
            sx=round(cx+dx);sy=round(cy+dy)
            if 0<=sx<32 and 0<=sy<32:out[y,x]=a[sy,sx]
    return out

def rgba(a,pal):
    h,w=a.shape;p=Image.new('RGBA',(w,h));p.putdata([tuple(pal[int(v)])+(255 if v else 0,) for v in a.flat]);return p

def checker(size):
    p=Image.new('RGB',size);p.putdata([(42,95,77) if (x//4+y//4)%2 else (130,63,110) for y in range(size[1]) for x in range(size[0])]);return p

def enclosed(a):
    h,w=a.shape;seen=np.zeros_like(a,dtype=bool);q=deque()
    for y in range(h):
        for x in range(w):
            if (x in (0,w-1) or y in (0,h-1)) and a[y,x]==0:seen[y,x]=True;q.append((x,y))
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and not seen[yy,xx] and a[yy,xx]==0:seen[yy,xx]=True;q.append((xx,yy))
    return (a==0)&~seen

def ncm(a):
    out=bytearray();h,w=a.shape
    for y in range(0,h,8):
        for x in range(0,w,16):
            b=a[y:y+8,x:x+16].tobytes();out.extend(b[i]|b[i+1]<<4 for i in range(0,128,2))
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    spec=ROOT/'assets/art/spec-v2/generated';m=json.loads((spec/'manifest.json').read_text())
    original=json.loads((BASE/'source/before.json').read_text())
    src={(r['group'],r['frame']):np.frombuffer(bytes.fromhex(''.join(r['rows'])),np.uint8).reshape(r['height'],r['width']) for r in json.loads((spec/'indexed-source.json').read_text())}
    before={(r['group'],r['frame']):np.frombuffer(bytes.fromhex(''.join(r['rows'])),np.uint8).reshape(r['height'],r['width']) for r in original['frames']}
    raw=bytearray();nc=bytearray();fc=bytearray();rrb=bytearray(64);records=[];entries=[];lines=[]
    for group in ('fighter','helicopter','bomber','armoured_plane'):
        poses=DIRS if group in ('fighter','helicopter') else ('straight','left','right')
        size=src[group,0].shape[0];strip=Image.new('RGBA',(len(poses)*3*size,size))
        overview=Image.new('RGB',(len(poses)*(size*5+8),size*5+30),(18,24,32));od=ImageDraw.Draw(overview)
        for i,pose in enumerate(poses):
            anim=[]
            effect=np.array(Image.open(spec/('animation-mask-'+group+'.png')).convert('L'))
            arrays=[src[group,p].copy() for p in range(3)]
            if size==16:
                effect=rotate(effect,(i*45-180)%360);arrays=[rotate(a,(i*45-180)%360) for a in arrays]
            elif pose!='straight':
                effect=bank(effect,pose);arrays=[bank(a,pose) for a in arrays]
            # Raster transforms can enclose a new one-pixel gap. Repair only
            # static body gaps common to all phases, never rotor/exhaust gaps.
            repaired=np.zeros_like(effect,dtype=bool)
            if group!='helicopter':
                repaired=np.logical_or.reduce([enclosed(a) for a in arrays]) & (effect==0) & np.logical_and.reduce([a==0 for a in arrays])
                for a in arrays:a[repaired]={'fighter':10,'bomber':11,'armoured_plane':8}[group]
            for phase in range(3):
                a=arrays[phase]
                im=rgba(a,m['palettes'][group]);strip.paste(im,((i*3+phase)*size,0));anim.append(im.resize((size*5,size*5),Image.Resampling.NEAREST))
                record=dict(group=group,pose=pose,phase=phase,width=size,height=size,palette=group,indices_offset=len(raw),ncm_offset=len(nc),fcm_offset=len(fc),rrb_base=len(rrb)//64,
                            palette_byte=({'fighter':5,'bomber':6,'helicopter':7,'armoured_plane':8}[group]<<4)|15,
                            rows=[a[y].tobytes().hex() for y in range(size)])
                if phase==0:
                    record['effect_mask_rows']=[bytes(int(v!=0) for v in row).hex() for row in effect]
                    record['derived_body_repairs']=[[int(x),int(y)] for y,x in np.argwhere(repaired)]
                records.append(record);raw.extend(a.tobytes());nc.extend(ncm(a))
                for y in range(0,size,8):
                    for x in range(0,size,8):fc.extend(a[y:y+8,x:x+8].tobytes())
                for x in range(0,size,16):
                    for y in range(0,size,8):rrb.extend(ncm(a[y:y+8,x:x+16]))
                    rrb.extend(bytes(64))
            od.text((i*(size*5+8)+4,5),pose,fill='white');bg=checker((size*5,size*5))
            bg.paste(anim[0],(0,0),anim[0]);overview.paste(bg,(i*(size*5+8)+4,25))
            anim[0].save(OUT/f'{group}-{pose}.webp',save_all=True,append_images=anim[1:],duration=100,loop=0,lossless=True)
        strip.save(OUT/(group+'.png'));overview.save(OUT/(group+'-preview.png'));lines.append(overview)
        entries.append(dict(group=group,size=[size,size],poses=list(poses),phases=3,strip_order='pose-major, then phase 0/1/2'))
    width=max(p.width for p in lines);preview=Image.new('RGB',(width,sum(p.height+28 for p in lines)),(18,24,32));d=ImageDraw.Draw(preview);y=0
    for group,line in zip(('fighter','helicopter','bomber','armoured_plane'),lines):
        d.text((5,y+5),group,fill='white');preview.paste(line,(0,y+23));y+=line.height+28
    preview.save(OUT/'preview.png')
    # Before/after on two contrasting backgrounds plus explicit changed-pixel mask.
    audit=Image.new('RGB',(930,4*205),(18,24,32));ad=ImageDraw.Draw(audit);audit_stats={}
    for i,group in enumerate(('fighter','helicopter','bomber','armoured_plane')):
        a=src[group,0];b=before[group,0];size=a.shape[0];scale=5;changed=(a!=b)
        assert not np.any(changed & (b!=0)),group
        audit_stats[group]=dict(repaired_pixels_per_phase=int(changed.sum()),opaque_before=int((b!=0).sum()),opaque_after=int((a!=0).sum()))
        ad.text((4,i*205+4),group,fill='white')
        for j,(label,data,bgcolor) in enumerate([('Vorher / gruen',b,(35,140,85)),('Nachher / gruen',a,(35,140,85)),('Nachher / magenta',a,(235,25,180))]):
            x=6+j*230;ad.text((x,i*205+20),label,fill='white');p=Image.new('RGB',(size*scale,size*scale),bgcolor)
            im=rgba(data,m['palettes'][group]).resize(p.size,Image.Resampling.NEAREST);p.paste(im,(0,0),im);audit.paste(p,(x,i*205+38))
        mask=Image.new('RGB',(size,size));mask.putdata([(255,220,40) if v else (30,35,40) for v in changed.flat]);audit.paste(mask.resize((size*scale,size*scale),Image.Resampling.NEAREST),(700,i*205+38));ad.text((700,i*205+20),'Gefuellte Pixel',fill='white')
    audit.save(OUT/'opacity-audit.png')
    (OUT/'opacity-audit.json').write_text(json.dumps(audit_stats,indent=2)+'\n')
    (OUT/'indexed-source.json').write_text(json.dumps(records,indent=2)+'\n')
    for name,data in [('views.indices.bin',raw),('views.ncm.bin',nc),('views.fcm.bin',fc),('views.rrb.bin',rrb)]: (OUT/name).write_bytes(data)
    pal={g:m['palettes'][g] for g in ('fighter','helicopter','bomber','armoured_plane')}
    (OUT/'palettes.json').write_text(json.dumps(pal,indent=2)+'\n')
    inc=['// Standalone local bases and source palette indices; remap and relocate on runtime import.']
    inc += [f'.const EV_{r["group"].upper()}_{r["pose"].upper()}_{r["phase"]} = {i}' for i,r in enumerate(records)]
    for label,values in [('base_lo',[r['rrb_base']&255 for r in records]),('base_hi',[r['rrb_base']>>8 for r in records]),
                         ('w',[r['width']//16 for r in records]),('h',[r['height']//8 for r in records]),('pal',[r['palette_byte'] for r in records])]:
        inc.append('enemy_view_'+label+': .byte '+','.join(str(v) for v in values))
    (OUT/'views.inc').write_text('\n'.join(inc)+'\n')
    manifest=dict(schema=1,groups=entries,frames=len(records),rrb_glyphs=len(rrb)//64,source_palette_indices=True,runtime_integrated=False,hardware_tested=False,
       provenance='Original indexed aircraft retained; explicit opaque-hull repairs. New 45-degree views use nearest-neighbour index sampling; banks use asymmetric wing foreshortening, roll and nose yaw. Existing exhaust/rotor phases retained.')
    manifest['files']={f.name:dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Exported {len(records)} views/phases, {len(rrb)//64} local guarded glyphs; audit {audit_stats}')

if __name__=='__main__':main()
