"""Refine the Iron City enemies and export exact-scale comparisons."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'assets/art/level4/source'))
import generate_mechs as base

D=ImageDraw.Draw
PIPES={
 'north':((6,13),(9,13)), 'northeast':((3,11),(5,12)),
 'east':((2,6),(2,9)), 'southeast':((3,3),(5,2)),
 'south':((6,2),(9,2)), 'southwest':((11,3),(13,5)),
 'west':((13,6),(13,9)), 'northwest':((10,13),(12,11)),
}
FORWARD=dict(zip(base.DIR8,((0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1))))


def armor(im,body,light,dark):
    """A one-pixel bevel, lit in screen coordinates."""
    source=im.copy()
    for y in range(1,im.height-1):
        for x in range(1,im.width-1):
            if source.getpixel((x,y))!=body:
                continue
            if source.getpixel((x,y-1)) in (0,1) or source.getpixel((x-1,y)) in (0,1):
                im.putpixel((x,y),light)
            elif source.getpixel((x,y+1)) in (0,1) or source.getpixel((x+1,y)) in (0,1):
                im.putpixel((x,y),dark)


def jet(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    shape,nose,glass,tail,edge=base.JET[pose]
    d.polygon(shape,fill=3)
    armor(im,3,5,2)
    d.line(edge,fill=6)
    d.line((nose,tail),fill=4,width=3)
    dx,dy=FORWARD[pose]
    for side in (-1,1):
        x=glass[0]-dx+side*dy*2
        y=glass[1]-dy-side*dx*2
        if im.getpixel((x,y)):
            d.point((x,y),fill=2)
            if im.getpixel((x-dx,y-dy)):d.point((x-dx,y-dy),fill=5)
    d.line((glass,(glass[0]-dx,glass[1]-dy)),fill=8,width=2)
    d.point(glass,fill=10)
    d.point((glass[0]-dx,glass[1]-dy),fill=9)
    d.point(nose,fill=6)
    d.point(edge[0],fill=12)
    # Two independently outlined exhaust outlets.
    for x,y in PIPES[pose]:
        d.point((x+dx,y+dy),fill=6)
        d.point((x,y),fill=11)
    im=base.outline(im);d=D(im)
    for i,(x,y) in enumerate(PIPES[pose]):
        d.point((x,y),fill=(12,14,13)[phase])
        if phase==1 and 1<=x-dx<=14 and 1<=y-dy<=14:d.point((x-dx,y-dy),fill=15)
        if phase==2 and i==0:d.point((x,y),fill=15)
    return im


def heli(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    cabin,boom,tail,rails,glass,hub=base.HELI[pose]
    dx,dy=FORWARD[pose]
    d.line(rails,fill=3,width=2)
    for x,y in rails:
        a=(max(1,min(14,x+dx)),max(1,min(14,y+dy)))
        b=(max(1,min(14,x-2*dx)),max(1,min(14,y-2*dy)))
        d.line((a,b),fill=2,width=2)
        d.line((a,(x,y)),fill=6)
        d.point(a,fill=13)
    d.polygon(boom,fill=3)
    d.line(tail,fill=5)
    d.point(tail[0],fill=7);d.point(tail[1],fill=13)
    d.polygon(cabin,fill=4)
    armor(im,4,6,3)
    gx=(glass[0][0]+glass[1][0])//2
    gy=(glass[0][1]+glass[1][1])//2
    for offset in (0,-2):
        x,y=gx+offset*dx,gy+offset*dy
        d.line(((x,y),(x+dy,y-dx)),fill=8,width=2)
        d.point((x,y),fill=10)
    d.point((hub[0]-1,hub[1]+1),fill=14)
    im=base.outline(im);d=D(im)
    cx,cy=hub
    rx,ry=((6,-1),(5,4),(1,6))[phase]
    d.line((cx-rx,cy-ry,cx+rx,cy+ry),fill=7)
    d.point(hub,fill=6)
    return im


HUBS={
 'straight':((3,3),(12,3),(3,12),(12,12)),
 'left':((4,4),(12,2),(4,11),(12,13)),
 'right':((3,2),(11,4),(3,13),(11,11)),
}


def drone(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    cx=7 if pose!='right' else 8
    for x,y in HUBS[pose]:
        d.line((cx,8,x,y),fill=1,width=3)
        d.line((cx,8,x,y),fill=5)
    d.polygon([(cx,4),(cx+3,6),(cx+3,10),(cx,12),(cx-3,10),(cx-3,6)],
              fill=4,outline=1)
    d.polygon([(cx,5),(cx+2,6),(cx+2,8),(cx-2,9),(cx-2,6)],fill=6)
    d.line((cx-2,6,cx,5,cx+2,6),fill=7)
    d.point((cx-2,9),fill=13);d.point((cx+2,9),fill=12)
    d.line((cx-1,10,cx+1,10),fill=8)
    d.point((cx,10),fill=10)
    for x,y in HUBS[pose]:
        # Open pixels between blades make the disks read as translucent.
        d.ellipse((x-2,y-2,x+2,y+2),outline=5)
        d.point((x-1,y-1),fill=7)
        d.point((x+1,y+1),fill=3)
        dx,dy=((2,0),(1,2),(1,-2))[phase]
        d.line((x-dx,y-dy,x+dx,y+dy),fill=6)
        d.point((x,y),fill=13)
    return im


def mech(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    lead=((2,-1),(1,0),(-1,2),(0,1))[phase]
    dx,dy=FORWARD[pose]
    for x,offset in zip((5,10),lead):
        footx=x+dx*offset
        footy=11+dy*offset
        d.line((x,8,footx,footy),fill=1,width=4)
        d.line((x,8,footx,footy),fill=3,width=2)
        d.point((footx-1,footy-1),fill=6)
        d.rectangle((footx-2,footy,footx+1,footy+2),fill=2,outline=1)
        d.line((footx-1,footy,footx,footy),fill=5)
        d.point((footx,footy+1),fill=14)
    # Separate shoulder plates and angular torso.
    for x in (2,10):
        d.polygon([(x+1,4),(x+3,4),(x+4,6),(x+3,9),(x+1,9),(x,7),(x,5)],
                  fill=3,outline=1)
        d.line((x+1,5,x+2,5),fill=6)
        d.line((x+1,7,x+2,7),fill=14)
    d.polygon([(5,3),(10,3),(11,5),(10,10),(8,11),(5,10),(4,7)],fill=4,outline=1)
    d.line((5,7,5,4,9,4),fill=6)
    d.line((6,9,9,9),fill=2)
    face={'north':((6,4),(9,4)),'east':((9,5),(9,7)),
          'south':((6,7),(9,7)),'west':((5,5),(5,7))}[pose]
    d.line(face,fill=8,width=2)
    d.point(face[0],fill=10)
    gx,gy={'north':(12,6),'east':(10,7),'south':(12,6),'west':(5,7)}[pose]
    tx,ty=gx+dx*4,gy+dy*4
    d.line((gx,gy,tx,ty),fill=1,width=3)
    d.line((gx,gy,tx,ty),fill=4)
    d.point((tx,ty),fill=7)
    return im


def walker(phase,wreck=False):
    im=base.walker(phase,wreck);d=D(im)
    if wreck:
        for x,y in ((10,7),(12,5),(14,3)):
            d.ellipse((x-2,y-1,x+2,y+1),fill=3)
            d.point((x-1,y-1),fill=5)
        d.line((10,12,12,9,13,13),fill=14)
        d.point((24,19),fill=15)
        return im
    for i,(x,y,fx,fy) in enumerate(((8,12,3,5),(23,12,28,5),(9,20,4,27),(22,20,27,27))):
        fy+=2 if (i+phase)%2 else -1
        jx,jy=(x+fx)//2,(y+fy)//2
        d.ellipse((jx-2,jy-2,jx+2,jy+2),fill=2,outline=1)
        d.arc((jx-2,jy-2,jx+2,jy+2),145,310,fill=6)
        d.point((jx,jy),fill=9)
        d.line((fx-1,fy-1,fx+1,fy-1),fill=6)
        d.point((fx,fy+1),fill=14)
    for x in (9,22):
        d.line((x,13,x,18),fill=2)
        d.line((x+1,13,x+1,16),fill=5)
    for x in (11,19):
        d.rectangle((x,19,x+2,21),fill=2)
        d.point((x,19),fill=14)
    d.line((14,21,17,21),fill=10)
    d.arc((10,8,21,19),140,315,fill=7)
    return im


def decode(frame,palette):
    rows=frame['rows']
    im=Image.frombytes('L',(len(rows[0])//2,len(rows)),bytes.fromhex(''.join(rows)))
    return base.rgba(im,palette)


def comparison(path,group,poses,phases,new,reference):
    # Same source pixels and same 4x scaling for both sides.
    cellw,cellh=144,154
    board=Image.new('RGB',((phases+1)*cellw,len(poses)*cellh+24),(25,31,38))
    d=D(board)
    d.text((5,4),'Level 1',fill='white')
    d.text((cellw+5,4),'Level 4  /  4x',fill='white')
    for row,pose in enumerate(poses):
        for col in range(phases+1):
            y=row*cellh+24;x=col*cellw
            ground=(75,76,68) if row%2 else (34,41,49)
            d.rectangle((x+1,y,x+cellw-2,y+cellh-1),fill=ground)
            if col==0:
                label,art=reference(pose)
            else:
                label=f'{pose} / {col-1}'
                art=new.get((group,pose,col-1))
            d.text((x+4,y+3),label,fill='white')
            if art is not None:
                scale=art.resize((art.width*4,art.height*4),Image.Resampling.NEAREST)
                board.paste(scale,(x+(cellw-scale.width)//2,y+20),scale)
    board.save(path)


def main():
    out=base.ENEMY
    out.mkdir(parents=True,exist_ok=True)
    palettes={k:base.pal(v) for k,v in base.COLORS.items()}
    ref=ROOT/'assets/art/enemy-views/generated'
    ref_pal=json.loads((ref/'palettes.json').read_text())
    ref_art={(f['group'],f['pose']):decode(f,[tuple(p) for p in ref_pal[f['palette']]])
             for f in json.loads((ref/'indexed-source.json').read_text()) if f['phase']==0}
    tanks=ROOT/'assets/art/ground-vehicles/generated'
    data=(tanks/'palette.rgb').read_bytes()
    tank_pal=[tuple(data[i:i+3]) for i in range(0,48,3)]
    tank_art={f['direction']:decode(f,tank_pal)
              for f in json.loads((tanks/'indexed-source.json').read_text()) if f['phase']==0}
    sprites={}
    records=[]
    for group,poses,phases,palette,draw,ref_group in (
        ('jet',base.DIR8,3,'air',jet,'fighter'),
        ('attack_heli',base.DIR8,3,'heli',heli,'helicopter'),
        ('drone',tuple(HUBS),3,'drone',drone,'bomber'),
        ('mech',base.DIR4,4,'mechs',mech,'tank'),
        ('walker',('south','destroyed'),2,'mechs',None,'tank'),
    ):
        samples=[]
        for pose in poses:
            for phase in range(1 if pose=='destroyed' else phases):
                im=walker(phase,pose=='destroyed') if group=='walker' else draw(pose,phase)
                records.append(dict(group=group,pose=pose,phase=phase,width=im.width,
                                    height=im.height,palette=palette,rows=base.encode(im)))
                art=base.rgba(im,palettes[palette])
                sprites[group,pose,phase]=art
                samples.append((f'{pose} / {phase}',art))
        base.sheet(out/f'{group}-preview.png',samples,3 if group=='walker' else phases,dual=True)
        def reference(pose):
            if ref_group=='tank':
                return 'Panzer',tank_art['south' if pose=='destroyed' else pose]
            return f'{ref_group} / {pose}',ref_art[ref_group,pose]
        comparison(out/f'{group}-vergleich.png',group,poses,phases,sprites,reference)
    base.save(out/'palettes.json',palettes)
    base.save(out/'placement.json',{'walker':{'guns':[[8,6]]}})
    base.save(out/'indexed-source.json',records)


if __name__=='__main__':
    main()
