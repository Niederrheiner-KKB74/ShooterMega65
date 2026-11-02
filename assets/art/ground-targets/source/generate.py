"""Native ground targets, exact existing palettes/edges, no game or level edits."""
import hashlib
import json
import math
from pathlib import Path
import random
from PIL import Image,ImageDraw

BASE=Path(__file__).resolve().parents[1];OUT=BASE/'generated'
GROUPS=('hangar','depot','checkpoint','bunker','radar','fuel','crates')
DIRS=('n','ne','e','se','s','sw','w','nw')
EXTENSION=[[16,18,22],[72,58,47],[225,65,24],[255,234,161]]
# Each heading is explicitly laid out, not a flipped/rotated sprite.
LIGHT={
 'n': ([(5,4),(7,2),(10,4),(11,9),(4,9)],(8,1)),
 'ne': ([(6,4),(11,2),(13,5),(9,11),(4,9)],(14,1)),
 'e': ([(6,4),(11,5),(13,8),(10,11),(5,11)],(14,8)),
 'se': ([(4,6),(10,4),(13,10),(10,13),(5,10)],(14,14)),
 's': ([(4,5),(11,5),(10,11),(8,13),(5,11)],(8,14)),
 'sw': ([(3,5),(10,4),(11,9),(5,13),(2,10)],(1,14)),
 'w': ([(4,5),(10,4),(11,10),(5,11),(2,8)],(1,8)),
 'nw': ([(2,5),(5,2),(11,5),(9,11),(4,10)],(1,1))}
HEAVY={
 'n': [((13,13),(13,1)),((19,13),(19,1))],
 'ne': [((17,10),(25,2)),((21,14),(29,6))],
 'e': [((19,13),(30,13)),((19,19),(30,19))],
 'se': [((21,17),(29,25)),((17,21),(25,29))],
 's': [((19,19),(19,30)),((13,19),(13,30))],
 'sw': [((14,21),(6,29)),((10,17),(2,25))],
 'w': [((13,19),(1,19)),((13,13),(1,13))],
 'nw': [((10,14),(2,6)),((14,10),(6,2))]}

def rows(p):
    b=p.tobytes();return [''.join(format(v,'x') for v in b[y*p.width:(y+1)*p.width]) for y in range(p.height)]

def image(strings):return Image.frombytes('L',(len(strings[0]),len(strings)),bytes(int(v,16) for row in strings for v in row))

def rgb(p,pal,alpha=False):
    result=Image.new('RGBA' if alpha else 'RGB',p.size)
    result.putdata([tuple(pal[v])+((255 if v else 0,) if alpha else ()) for v in p.tobytes()]);return result

def restore_rim(p,original,rim=2):
    for y in range(p.height):
        for x in range(p.width):
            if min(x,y,p.width-1-x,p.height-1-y)<rim:p.putpixel((x,y),original.getpixel((x,y)))

def fragment(d,x,y,w,h,body,light,shadow):
    d.polygon([(x,y+1),(x+w-1,y),(x+w,y+h-1),(x+1,y+h)],fill=shadow)
    d.polygon([(x,y+1),(x+w-1,y),(x+w-1,y+h-2),(x+1,y+h-1)],fill=body)
    d.line((x,y+1,x+w-1,y),fill=light)

def ruined(original,name):
    p=original.copy();d=ImageDraw.Draw(p);fixed=name=='bunker'
    dark,ash=(12,13) if fixed else (15,11)
    # Scorch stays inside the old 32x32 footprint. No animated smoke/flames.
    d.ellipse((3,5,28,28),fill=ash);d.ellipse((5,7,27,27),fill=dark)
    rng=random.Random(6500+GROUPS.index(name))
    for _ in range(25):
        x=rng.randrange(4,26);y=rng.randrange(7,27)
        fragment(d,x,y,rng.randrange(2,5),rng.randrange(2,4),3 if fixed else 7,5 if fixed else 8,dark)
    if name=='hangar':
        d.line((4,4,27,4),fill=8,width=2);d.line((4,5,4,23),fill=13,width=2)
        # Fallen corrugated roof sheets, snapped trusses and a low front wall.
        d.polygon([(6,9),(18,13),(13,22),(4,17)],fill=6)
        for dy in (0,3,6):d.line((6,10+dy,15,14+dy),fill=12)
        d.polygon([(20,7),(26,10),(24,20),(18,17)],fill=7)
        for yy in (10,13,16):d.line((21,yy,25,yy+1),fill=13)
        d.line((8,25,23,8),fill=11,width=3);d.line((8,24,22,8),fill=8)
        d.line((5,27,13,27),fill=8,width=2);d.line((19,27,26,27),fill=7,width=2)
    elif name=='depot':
        d.line((4,4,27,4),fill=13,width=2);d.line((4,5,4,16),fill=8)
        d.polygon([(7,7),(19,9),(14,18),(5,15)],fill=6)
        d.line((7,8,18,10),fill=8);d.line((6,11,15,13),fill=12)
        d.polygon([(20,15),(27,19),(24,26),(16,23)],fill=14)
        d.line((20,17,24,20),fill=10);d.point((22,18),fill=13)
        for x,y in ((8,22),(15,25),(24,9)):fragment(d,x,y,4,3,12,13,11)
        d.rectangle((12,26,18,28),fill=11)
    elif name=='checkpoint':
        # Keep the NS approach intact at the border; toppled striped barrier.
        d.ellipse((10,8,23,25),fill=11);d.ellipse((12,10,21,23),fill=15)
        for x in (3,25):
            d.rectangle((x,13,x+3,20),fill=11);fragment(d,x,16,3,4,7,8,15)
        d.line((5,10,26,23),fill=11,width=4);d.line((5,9,26,22),fill=8,width=2)
        for x,y in ((7,11),(12,14),(17,17),(22,20)):d.line((x,y-1,x+1,y+1),fill=10,width=2)
        d.line((12,25,18,28),fill=6,width=2);d.point((13,25),fill=13)
    elif name=='bunker':
        d.polygon([(4,7),(25,6),(28,11),(25,18),(20,15),(10,18),(5,14)],fill=4)
        d.line((4,7,24,6),fill=6,width=2);d.line((4,8,4,14),fill=5)
        d.polygon([(8,11),(18,9),(24,13),(21,21),(11,24),(6,18)],fill=12)
        d.line((9,12,13,15,10,18),fill=13,width=2)
        for x,y in ((5,22),(12,24),(23,20),(19,10),(8,16)):
            fragment(d,x,y,5,4,3,6,13)
        d.line((6,27,11,27),fill=5,width=2);d.line((23,25,26,25),fill=4,width=2)
    elif name=='radar':
        d.rectangle((13,17,18,25),fill=6);d.line((14,17,14,22),fill=13)
        d.arc((4,12,26,28),0,205,fill=13,width=2)
        d.arc((6,14,24,26),10,145,fill=7,width=2)
        d.line((5,15,23,26),fill=8);d.line((8,24,23,16),fill=6,width=2)
        d.line((15,19,22,13),fill=13);d.line((12,19,7,13),fill=8)
        d.rectangle((21,6,23,12),fill=11);d.point((22,6),fill=10)
    elif name=='fuel':
        for x,y in ((4,13),(18,17)):
            d.rectangle((x,y,x+9,26),fill=11)
            d.ellipse((x,y-3,x+10,y+3),fill=6,outline=8)
            d.ellipse((x+2,y-1,x+8,y+2),fill=15)
            d.line((x,y+3,x,23),fill=12)
            d.line((x+1,23,x+8,24),fill=14)
        d.line((8,8,15,12),fill=8,width=2);d.line((24,7,27,13),fill=13)
        d.polygon([(11,23),(16,20),(19,24),(16,27)],fill=6);d.line((11,23,16,20),fill=13)
    elif name=='crates':
        for x,y,w,h in ((4,5,10,4),(17,8,9,3),(6,19,11,3),(17,23,10,3)):
            d.polygon([(x,y),(x+w,y+2),(x+w-1,y+h+2),(x,y+h)],fill=14)
            d.line((x,y,x+w,y+2),fill=9)
            d.line((x+2,y+1,x+w-2,y+3),fill=11)
        d.line((8,10,23,24),fill=6,width=2);d.line((8,10,21,22),fill=10)
        for x,y in ((7,7),(20,11),(10,20),(24,25)):d.point((x,y),fill=13)
    restore_rim(p,original)
    assert min(p.tobytes())>0
    return p

def ruined_hall(original,name):
    p=original.copy();d=ImageDraw.Draw(p)
    # Preserve each module's complete two-pixel rim, including original wall joints.
    brick='brick' in name;index=sum(map(ord,name))%4
    outlines=[[(3,3),(11,2),(13,5),(13,12),(10,13),(2,12),(2,6)],
              [(2,4),(8,2),(13,3),(12,10),(9,13),(3,13)],
              [(3,2),(12,3),(13,8),(11,13),(3,12),(2,7)],
              [(2,3),(10,2),(13,6),(12,13),(5,13),(2,9)]]
    d.polygon(outlines[index],fill=15)
    d.polygon([(4,4),(10,3),(12,7),(10,11),(5,12),(3,8)],fill=11)
    beams=[(2,4,12,10),(4,2,11,13),(2,10,12,4),(3,12,9,2)]
    x0,y0,x1,y1=beams[index];d.line((x0,y0,x1,y1),fill=6,width=2)
    d.line((x0,y0-1,x1,y1-1),fill=14 if brick else 8)
    bits=[((3,8),(8,4),(9,11)),((4,5),(10,9),(3,11)),((3,4),(8,9),(10,5)),((5,3),(3,9),(9,10))][index]
    for x,y in bits:fragment(d,x,y,3,2,14 if brick else 7,8 if brick else 13,15)
    if name.endswith('1_1'):
        d.rectangle((5,5,9,7),fill=15);d.line((4,8,10,10),fill=12)
    restore_rim(p,original)
    return p

def base_gun(size):
    p=Image.new('L',(size,size));d=ImageDraw.Draw(p)
    if size==16:
        d.polygon([(4,2),(11,2),(14,5),(14,11),(11,14),(4,14),(1,11),(1,5)],fill=1)
        d.polygon([(4,3),(11,3),(13,5),(13,10),(10,12),(4,12),(2,10),(2,5)],fill=9)
        d.line((4,3,11,3,13,5),fill=11);d.line((4,3,2,5,2,10),fill=5)
        d.line((4,13,11,13,13,11),fill=2)
        for x,y in ((3,4),(12,4),(3,11),(12,11)):d.point((x,y),fill=6)
        d.ellipse((4,4,11,11),fill=2,outline=4)
    else:
        d.polygon([(7,4),(24,4),(28,8),(28,24),(24,28),(7,28),(3,24),(3,8)],fill=1)
        d.polygon([(7,5),(23,5),(26,8),(26,23),(23,26),(7,26),(5,23),(5,8)],fill=9)
        d.line((7,5,23,5,26,8),fill=11,width=2);d.line((7,5,5,8,5,23),fill=5)
        d.line((7,27,24,27,27,24),fill=2)
        for x,y in ((7,8),(24,8),(7,23),(24,23)):
            d.rectangle((x-1,y-1,x+1,y+1),fill=1);d.point((x-1,y-1),fill=6)
        for y in (11,14,17,20):d.line((6,y,9,y),fill=2);d.point((6,y),fill=5)
        d.ellipse((9,9,23,23),fill=2,outline=4)
    return p

def upper_bevel(p):
    a=p.copy();d=ImageDraw.Draw(p)
    for y in range(p.height):
        for x in range(p.width):
            if a.getpixel((x,y))!=3:continue
            top=y==0 or a.getpixel((x,y-1))==0
            left=x==0 or a.getpixel((x-1,y))==0
            bottom=y==p.height-1 or a.getpixel((x,y+1))==0
            right=x==p.width-1 or a.getpixel((x+1,y))==0
            if top or left:d.point((x,y),fill=5)
            elif bottom or right:d.point((x,y),fill=2)

def barrel(p,start,end,width):
    d=ImageDraw.Draw(p);x0,y0=start;x1,y1=end;dx=x1-x0;dy=y1-y0
    # World-space NW highlights; heading profiles are never mirrored images.
    ox,oy=(-1,0) if dx==0 else (0,-1) if dy==0 or dx*dy>0 else (-1,-1)
    d.line((x0,y0,x1,y1),fill=1,width=3)
    d.line((x0,y0,x1,y1),fill=5)
    # Narrow steel tube with a lit NW side, separate breech and muzzle collar.
    d.line((x0+ox,y0+oy,x1+ox,y1+oy),fill=6)
    for t,col in ((.18,4),(.38,2),(.78,4)):
        mx,my=round(x0+dx*t),round(y0+dy*t)
        if abs(dx)>abs(dy):d.line((mx,my-1,mx,my+1),fill=col)
        else:d.line((mx-1,my,mx+1,my),fill=col)
        d.point((mx+ox,my+oy),fill=5)
    d.point(end,fill=1) # visible dark muzzle, never a transparent hole

def gun(size):
    base=base_gun(size);frames={};muzzles={};masks={}
    for direction in DIRS:
        top=Image.new('L',(size,size));d=ImageDraw.Draw(top)
        if size==16:
            poly,tip=LIGHT[direction];d.polygon(poly,fill=3);upper_bevel(top)
            d.rectangle((6,6,10,10),fill=2)
            d.rectangle((6,6,9,9),fill=3);d.line((6,6,9,6),fill=5)
            d.point((6,7),fill=6);d.point((9,9),fill=1)
            d.line((6,9,7,9),fill=7) # tank-family red identification mark
            d.point((9,7),fill=10)
            # Draw the barrel last so the turret never hides its whole breech.
            barrel(top,(8,8),tip,3)
        else:
            # Explicit double-barrel endpoints per heading; fixed turntable centre.
            dx,dy={'n':(0,-1),'ne':(1,-1),'e':(1,0),'se':(1,1),'s':(0,1),'sw':(-1,1),'w':(-1,0),'nw':(-1,-1)}[direction]
            d.polygon([(12,9),(19,9),(24,14),(23,20),(18,24),(11,22),(8,16)],fill=3)
            upper_bevel(top)
            d.rectangle((11,11,20,19),fill=10);d.line((11,11,20,11),fill=6)
            tip=HEAVY[direction][0][1]
            d.ellipse((12,12,19,19),fill=4,outline=5)
            d.rectangle((13,13,17,17),fill=3);d.line((13,13,17,13),fill=6)
            d.line((14,17,17,17),fill=7)
            d.rectangle((14,14,16,15),fill=1);d.point((14,14),fill=5)
            for x,y in ((10,14),(21,15),(12,20),(19,21)):
                d.point((x,y),fill=6);d.point((x,y+1),fill=2)
            d.line((10,17,10,19),fill=1);d.line((21,17,21,19),fill=1)
            for start,end in HEAVY[direction]:
                sx,sy=start;ex,ey=end
                # Armoured recoil sleeve stops before the long, narrow tube.
                bx,by=round(sx+(ex-sx)*.25),round(sy+(ey-sy)*.25)
                d.line((sx,sy,bx,by),fill=1,width=5)
                d.line((sx-1,sy-1,bx-1,by-1),fill=4,width=3)
                barrel(top,start,end,3)
        p=base.copy();mask=top.point(lambda v:255 if v else 0);p.paste(top,mask=mask)
        frames[direction]=rows(p);muzzles[direction]=list(tip)
        masks[direction]=rows(top.point(lambda v:1 if v else 0))
    for phase in range(2):
        p=Image.new('L',(16,16));d=ImageDraw.Draw(p)
        if phase==0:
            d.polygon([(8,0),(10,5),(14,3),(11,8),(15,11),(10,10),(8,15),(6,10),(2,12),(5,7),(2,3),(6,5)],fill=8)
            d.polygon([(8,3),(10,8),(8,12),(6,8)],fill=15);d.rectangle((7,6,8,9),fill=6)
        else:
            d.polygon([(7,1),(10,6),(13,5),(10,10),(12,13),(8,11),(5,15),(5,10),(1,8),(5,6),(3,3)],fill=14)
            d.polygon([(7,4),(10,7),(8,11),(5,8)],fill=8);d.rectangle((6,6,8,9),fill=15)
        frames['flash'+str(phase)]=rows(p)
    p=base.copy();d=ImageDraw.Draw(p)
    if size==16:
        d.ellipse((4,4,11,12),fill=12,outline=2)
        d.line((6,7,10,10,12,8),fill=3,width=3);d.line((6,6,10,9,12,8),fill=5)
        d.point((7,9),fill=7);d.point((8,8),fill=14);d.point((6,10),fill=13)
    else:
        d.polygon([(11,10),(20,9),(23,15),(19,23),(10,21),(7,16)],fill=12)
        d.line((12,14,8,8,5,10),fill=2,width=5);d.line((12,13,8,8,5,9),fill=5)
        d.line((19,17,24,23,27,21),fill=2,width=4);d.line((19,16,24,22,27,21),fill=4)
        for x,y in ((12,18),(18,12),(19,20)):fragment(d,x,y,3,3,3,5,13)
        d.point((16,16),fill=14);d.point((15,18),fill=7)
    frames['wreck']=rows(p)
    tips={direction:[list(end) for _,end in HEAVY[direction]] if size==32 else [list(LIGHT[direction][1])] for direction in DIRS}
    return dict(size=[size,size],palette='fixed_targets',frames=frames,muzzle=muzzles),dict(base=rows(base),upper_masks=masks,barrel_tips=tips,lighting='fixed world top-left; eight authored heading profiles, no image rotation/mirroring')

def checker(size):
    im=Image.new('RGB',size);im.putdata([(27,37,45) if (x//4+y//4)%2 else (42,57,58) for y in range(size[1]) for x in range(size[0])]);return im

def gun_previews(name,gdef,pal,construction):
    order=list(DIRS)+['flash0','flash1','wreck'];size=gdef['size'][0]
    ims=[rgb(image(gdef['frames'][f]),pal,True) for f in order]
    strip=Image.new('RGBA',(sum(im.width for im in ims),size));x=0
    for im in ims:strip.paste(im,(x,(size-im.height)//2));x+=im.width
    strip.save(OUT/(name+'-1x.png'));strip.resize((strip.width*4,strip.height*4),Image.Resampling.NEAREST).save(OUT/(name+'-4x.png'))
    cell=size*4+8;canvas=Image.new('RGB',(cell*11,size*5+68),(18,24,32));d=ImageDraw.Draw(canvas)
    for i,(f,im) in enumerate(zip(order,ims)):
        xx=i*cell+4;d.text((xx,4),f,fill='white')
        bg=checker((size,size));bg.paste(im,((size-im.width)//2,(size-im.height)//2),im);canvas.paste(bg,(xx,20))
        canvas.paste(bg.resize((size*4,size*4),Image.Resampling.NEAREST),(xx,size+40))
    canvas.save(OUT/(name+'.png'))
    rgb(image(construction['base']),pal,True).save(OUT/(name+'-base.png'))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reference=json.loads((BASE/'source/intact-reference.json').read_text())
    pals=reference['palettes'];ft=[list(c) for c in pals['fixed_targets']];ft[12:]=EXTENSION
    byname={t['name']:t for t in reference['tiles']};destroyed=[];group_images=[];hall_images=[]
    for name in GROUPS:
        original=Image.new('L',(32,32));palette=byname[name+'_0_0']['palette']
        for ty in range(2):
            for tx in range(2):original.paste(image(byname[f'{name}_{tx}_{ty}']['pixels']),(tx*16,ty*16))
        broken=ruined(original,name)
        for ty in range(2):
            for tx in range(2):
                destroyed.append(dict(name=f'{name}_destroyed_{tx}_{ty}',of=f'{name}_{tx}_{ty}',palette=palette,pixels=rows(broken.crop((tx*16,ty*16,tx*16+16,ty*16+16)))))
        group_images.append((name,original,broken,ft if palette=='fixed_targets' else pals[palette]))
    for tile in reference['tiles']:
        name=tile['name']
        if not name.startswith('complex_'):continue
        original=image(tile['pixels']);broken=ruined_hall(original,name)
        destroyed.append(dict(name=name+'_destroyed',of=name,palette=tile['palette'],pixels=rows(broken)))
        hall_images.append((name,original,broken,pals[tile['palette']]))
    light,layers16=gun(16);heavy,layers32=gun(32)
    result=dict(schema=1,palettes=dict(fixed_targets=ft),destroyed_tiles=destroyed,ground_gun=light,heavy_gun=heavy)
    (OUT/'ground-targets.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'construction.json').write_text(json.dumps(dict(ground_gun=layers16,heavy_gun=layers32),indent=2)+'\n',encoding='utf-8',newline='\n')
    preview=Image.new('RGB',(728,382),(18,24,32));d=ImageDraw.Draw(preview)
    d.text((8,5),'A: intakt / zerstoert - jeweils 32x32, 1 Bildpixel = 1 Spielpixel',fill='white')
    for i,(name,a,b,pal) in enumerate(group_images):
        x=8+i*103;d.text((x,24),name,fill='white');preview.paste(rgb(a,pal),(x,42));preview.paste(rgb(b,pal),(x+36,42))
    d.text((8,94),'D: modulare Hallen - identische 2-Pixel-Raender, innen zerstoert',fill='white')
    for i,(name,a,b,pal) in enumerate(hall_images):
        x=8+(i%5)*144;y=116+(i//5)*58
        short=name.replace('complex_','');d.text((x,y),short,fill=(195,210,210))
        preview.paste(rgb(a,pal),(x,y+16));preview.paste(rgb(b,pal),(x+22,y+16))
    d.text((8,354),'Links jeweils Original. Nur neue Daten; bestehende Assets und Level bleiben unveraendert.',fill=(160,185,185))
    preview.save(OUT/'destroyed-sheet.png');preview.resize((preview.width*4,preview.height*4),Image.Resampling.NEAREST).save(OUT/'destroyed-sheet-4x.png')
    compact=Image.new('RGB',(824,278),(18,24,32));cd=ImageDraw.Draw(compact)
    cd.text((8,4),'Gebaeude: intakt links / zerstoert rechts (3x)',fill='white')
    for i,(name,a,b,pal) in enumerate(group_images):
        x=8+(i%4)*204;y=23+(i//4)*126;cd.text((x,y),name,fill='white')
        compact.paste(rgb(a,pal).resize((96,96),Image.Resampling.NEAREST),(x,y+16))
        compact.paste(rgb(b,pal).resize((96,96),Image.Resampling.NEAREST),(x+100,y+16))
    compact.save(OUT/'ruins-preview.png')
    gun_previews('ground-gun',light,ft,layers16);gun_previews('heavy-gun',heavy,ft,layers32)
    # Sample valid hall layouts with mixed intact/destroyed modules.
    hallpreview=Image.new('RGB',(600,330),(18,24,32));hd=ImageDraw.Draw(hallpreview)
    broken_by={r['of']:r for r in destroyed}
    for si,style in enumerate(('steel','brick')):
        for state in range(3):
            canvas=Image.new('RGB',(80,64));w=5;h=4
            for ty in range(h):
                for tx in range(w):
                    cx=0 if tx==0 else 2 if tx==w-1 else 1;cy=0 if ty==0 else 2 if ty==h-1 else 1
                    name=f'complex_{style}_{cx}_{cy}'
                    if cx==cy==1 and (tx+ty)%2:name=f'complex_{style}_plain'
                    dead=state==2 or state==1 and (tx+ty)%3!=0
                    p=image((broken_by[name] if dead else byname[name])['pixels']);canvas.paste(rgb(p,pals['structures']),(tx*16,ty*16))
            x=8+state*198;y=8+si*156
            hd.text((x,y),style+' / '+('intakt','gemischt','zerstoert')[state],fill='white');hallpreview.paste(canvas.resize((160,128),Image.Resampling.NEAREST),(x,y+18))
    hallpreview.save(OUT/'hall-seams-preview.png')
    status=dict(schema=1,source_commit=reference['source_commit'],parts=['A','B','C','D'],new_tiles=len(destroyed),
                palette_extension={str(12+i):c for i,c in enumerate(EXTENSION)},integrated=False,hardware_tested=False,
                provenance='New deterministic native pixel rubble and explicitly drawn heading profiles; exact original palette indices and copied border pixels. No AI image reduction.')
    status['files']={f.name:dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in sorted(OUT.iterdir()) if f.is_file() and f.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Generated A+B+C+D: 48 opaque destruction tiles, light 16x16 and heavy 32x32 guns, 8 directions + 2 flashes + wreck each.')

if __name__=='__main__':main()
