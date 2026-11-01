"""Create genuine effects-only animation from one canonical drawing per type."""
import json
import math
from PIL import Image, ImageDraw

WARM=[[245,94,23],[255,178,48],[255,241,173]]
SETTINGS={
 'player':dict(rect=[13,19,19,24],ports=[[15,19]],direction=1),
 'fighter':dict(rect=[5,0,11,3],ports=[[6,2],[9,2]],direction=-1),
 'bomber':dict(rect=[12,0,21,6],ports=[[14,5],[18,5]],direction=-1),
 'armoured_plane':dict(rect=[12,0,21,5],ports=[[14,4],[18,4]],direction=-1),
}


def load_pixels(record):
    return Image.frombytes('L',(record['width'],record['height']),b''.join(bytes.fromhex(r) for r in record['rows']))


def remap(p,old,new):
    lut=[0]+[min(range(1,13),key=lambda i:sum((old[v][c]-new[i][c])**2 for c in range(3))) for v in range(1,16)]
    return p.point(lut+[0]*240)


def make(source):
    result={};metadata={}
    for name,record in source['groups'].items():
        w,h=record['width'],record['height']
        if name=='helicopter':
            pal=record['palette'];body=Image.new('L',(w,h));d=ImageDraw.Draw(body)
            # Reconstruct a clean, fixed fuselage; old blades are not baked into it.
            d.rectangle((7,1,8,6),fill=7);d.rectangle((6,2,9,2),fill=2)
            d.ellipse((5,5,10,13),fill=11);d.ellipse((6,5,9,12),fill=7)
            d.rectangle((6,9,9,11),fill=4);d.point((6,9),fill=2)
            d.line((6,7,9,7),fill=5);d.point((7,12),fill=9)
            rotor=[];mask=Image.new('L',(w,h))
            for angle in (0,60,120):
                layer=Image.new('L',(w,h));draw=ImageDraw.Draw(layer)
                a=math.radians(angle);dx=round(6.5*math.cos(a));dy=round(6.5*math.sin(a))
                draw.line((8-dx,7-dy,8+dx,7+dy),fill=7,width=1)
                draw.point((8-dx,7-dy),fill=2);draw.point((8+dx,7+dy),fill=4)
                rotor.append(layer)
                mask=Image.frombytes('L',(w,h),bytes(255 if a or b else 0 for a,b in zip(mask.tobytes(),layer.tobytes())))
            frames=[]
            for layer in rotor:
                p=body.copy();p.paste(layer,mask=layer.point(lambda v:255 if v else 0))
                ImageDraw.Draw(p).rectangle((7,6,8,7),fill=6);p.putpixel((7,6),2)
                frames.append(p)
            kind='rotor';notes='New clean fixed fuselage reconstructed from the prior reference; only two-blade rotor geometry varies.'
        else:
            pal=record['palette'][:13]+WARM
            body=remap(load_pixels(record),record['palette'],pal)
            conf=SETTINGS[name];x0,y0,x1,y1=conf['rect'];ImageDraw.Draw(body).rectangle((x0,y0,x1-1,y1-1),fill=0)
            mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rectangle((x0,y0,x1-1,y1-1),fill=255)
            frames=[]
            for phase in range(3):
                p=body.copy()
                for x,y in conf['ports']:
                    length=2+phase
                    for step in range(length):
                        yy=y+step*conf['direction']
                        for xx in (x,x+1):
                            if 0<=yy<h and mask.getpixel((xx,yy)):
                                p.putpixel((xx,yy),15 if step==0 else 14 if step<length-1 else 13)
                    # Alternating one-pixel tip keeps the flame cycle asymmetric.
                    yy=y+(length-1)*conf['direction']
                    if 0<=yy<h and mask.getpixel((x+phase%2,yy)):p.putpixel((x+phase%2,yy),14)
                frames.append(p)
            if name=='player':
                left,right=record['banking']
                frames += [remap(load_pixels(left),record['palette'],pal),frames[0].copy(),remap(load_pixels(right),record['palette'],pal)]
            kind='exhaust';notes='One canonical body, palette reduced to 12 body colours + 3 dedicated flame colours; indices 3/5 are separate banking poses.'
        result[name]=dict(frames=frames,palette=pal,mask=mask)
        metadata[name]=dict(kind=kind,loop=[0,1,2],frame_ms=100,mask_file='animation-mask-'+name+'.png',notes=notes,
                            steady_frame=4 if name=='player' else 0,banking_frames=[3,5] if name=='player' else [])
    return result,metadata


def apply(groups,palettes,base):
    source=json.loads((base/'source/aircraft-animation.json').read_text())
    fixed,metadata=make(source)
    for g in groups:
        if g['id'] in fixed:
            g['frames']=fixed[g['id']]['frames'];palettes[g['palette']]=fixed[g['id']]['palette']
            g['provenance']='Canonical aircraft body with newly constructed effects-only animation; see source/aircraft-animation.json and tools/aircraft_animation.py.'
    return fixed,metadata
