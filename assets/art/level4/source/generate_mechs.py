"""Native indexed sprites and final boss for Operation Iron City."""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parents[4]
ENEMY=ROOT/'assets/art/enemies-level4/generated'
BOSS=ROOT/'assets/art/boss-level4/generated'
DIR8=('north','northeast','east','southeast','south','southwest','west','northwest')
DIR4=DIR8[::2]
D=ImageDraw.Draw
COLORS={
 'air':'000000 171d2b 303849 4d5664 78808a a4aaa9 d2d2bf e8e5cd 315269 5f9fae a9dfdc 8b3335 ce4c3c f18149 f9bd66 fce7a0',
 'heli':'000000 222722 343d2b 4f5c3c 6c7950 96915d c6b481 ead8a9 263e42 426d71 89b9aa 6e4637 b45c3e e7a34e f3cd7a fce7aa',
 'drone':'000000 212834 344957 586974 82949a abbbba d9ddd0 f1ecd9 225168 398a9d 8bd9db 813d38 c65c39 f08a46 f6bb61 ffe2a4',
 'mechs':'000000 182330 2b4151 3c5c73 527889 80a0a8 b0c1bd e4e2cb 20506c 3b879a 86d2d4 743d33 bc533c ef8249 f4bd59 ffe6a3',
}
BOSS_COLORS='000000 181e2a 2e3744 455360 657782 91a3a5 c0c8b9 e5e0c4 28546b 4c9bac 9de1db 713936 b7493c e97642 f6b854 fff0b6'


def pal(text):
    return [tuple(bytes.fromhex(value)) for value in text.split()]


def rgba(im,palette):
    out=Image.new('RGBA',im.size)
    out.putdata([palette[v]+(255 if v else 0,) for v in im.tobytes()])
    return out


def encode(im):
    return [''.join(f'{im.getpixel((x,y)):02x}' for x in range(im.width))
            for y in range(im.height)]


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='ascii',newline='\n')


def outline(im):
    mask=im.point(lambda value:255 if value else 0)
    result=Image.new('L',im.size)
    result.paste(1,mask=mask.filter(ImageFilter.MaxFilter(3)))
    result.paste(im,mask=mask)
    return result


# Every heading is laid out in screen coordinates: silhouette, nose, canopy,
# tailpipe, leading edge. The only phase-dependent pixels are exhaust lights.
JET={
 'north': ([(7,1),(9,4),(10,7),(13,11),(13,12),(9,11),(9,13),(6,13),(6,11),(2,12),(2,11),(5,7),(6,4)],(7,2),(7,5),(7,13),[(3,11),(6,7),(7,3)]),
 'northeast': ([(13,2),(12,5),(11,8),(13,12),(12,13),(8,10),(5,13),(3,12),(2,10),(5,7),(2,5),(3,4),(8,5)],(12,3),(10,5),(3,12),[(3,5),(8,6),(12,3)]),
 'east': ([(14,7),(11,9),(8,10),(4,13),(3,13),(4,9),(2,9),(2,6),(4,6),(3,2),(4,2),(8,5),(11,6)],(13,7),(10,7),(2,7),[(4,3),(8,6),(12,7)]),
 'southeast': ([(13,13),(10,12),(7,11),(3,13),(2,12),(5,8),(2,5),(3,3),(5,2),(8,5),(10,2),(11,3),(10,8)],(12,12),(10,10),(3,3),[(10,3),(9,8),(12,12)]),
 'south': ([(8,14),(6,11),(5,8),(2,4),(2,3),(6,4),(6,2),(9,2),(9,4),(13,3),(13,4),(10,8),(9,11)],(8,13),(8,10),(8,2),[(3,4),(6,8),(8,12)]),
 'southwest': ([(2,13),(3,10),(4,7),(2,3),(3,2),(7,5),(10,2),(12,3),(13,5),(10,8),(13,10),(12,11),(7,10)],(3,12),(5,10),(12,3),[(3,3),(6,7),(3,12)]),
 'west': ([(1,8),(4,6),(7,5),(11,2),(12,2),(11,6),(13,6),(13,9),(11,9),(12,13),(11,13),(7,10),(4,9)],(2,8),(5,8),(13,8),[(11,3),(7,6),(3,8)]),
 'northwest': ([(2,2),(5,3),(8,4),(12,2),(13,3),(10,7),(13,10),(12,12),(10,13),(7,10),(5,13),(4,12),(5,7)],(3,3),(5,5),(12,12),[(3,3),(6,7),(5,12)]),
}

# Cabin silhouette, tail boom, tail cap, rocket rails, glass, hub.
HELI={
 'north': ([(6,2),(9,2),(10,4),(10,8),(8,9),(6,9),(5,7),(5,4)],[(7,8),(8,8),(8,13),(7,13)],((6,13),(9,13)),((3,6),(12,6)),((6,3),(9,5)),(7,6)),
 'northeast': ([(10,2),(12,3),(13,5),(12,7),(9,9),(6,8),(6,6),(8,3)],[(7,7),(9,8),(4,13),(3,12)],((2,11),(5,13)),((5,4),(12,10)),((9,4),(12,5)),(9,6)),
 'east': ([(13,6),(13,9),(11,10),(7,10),(6,9),(6,6),(8,5),(11,5)],[(7,7),(7,8),(2,8),(2,7)],((2,6),(2,9)),((9,3),(9,12)),((10,6),(12,9)),(9,7)),
 'southeast': ([(13,10),(12,12),(10,13),(8,12),(6,9),(7,6),(9,6),(12,8)],[(8,7),(7,9),(2,4),(3,3)],((2,5),(4,2)),((6,12),(12,6)),((10,9),(11,12)),(9,9)),
 'south': ([(6,13),(9,13),(10,11),(10,7),(9,6),(6,6),(5,8),(5,11)],[(7,7),(8,7),(8,2),(7,2)],((6,2),(9,2)),((3,9),(12,9)),((6,10),(9,12)),(8,9)),
 'southwest': ([(5,13),(3,12),(2,10),(3,8),(6,6),(9,7),(9,9),(7,12)],[(8,8),(6,7),(11,2),(12,3)],((10,2),(13,4)),((4,5),(10,12)),((3,9),(6,11)),(6,9)),
 'west': ([(2,6),(2,9),(4,10),(8,10),(9,9),(9,6),(7,5),(4,5)],[(8,7),(8,8),(13,8),(13,7)],((13,6),(13,9)),((6,3),(6,12)),((3,6),(5,9)),(6,8)),
 'northwest': ([(2,5),(3,3),(5,2),(7,3),(9,6),(8,9),(6,9),(3,7)],[(7,8),(8,6),(13,11),(12,12)],((11,13),(13,10)),((4,9),(10,4)),((3,4),(6,6)),(6,6)),
}


def jet(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    shape,nose,glass,tail,edge=JET[pose]
    d.polygon(shape,fill=3)
    d.line(edge,fill=5)
    d.line((nose,tail),fill=4,width=2)
    d.line((nose,glass),fill=6)
    d.point(glass,fill=9)
    d.point(nose,fill=10)
    d.point(edge[0],fill=12)
    im=outline(im)
    d=D(im)
    d.point(tail,fill=(12,13,15)[phase])
    return im


def heli(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    cabin,boom,tail,rails,glass,hub=HELI[pose]
    d.line(rails,fill=3,width=2)
    for x,y in rails:
        d.point((x,y),fill=13)
        d.point((x+1,y),fill=6)
    d.polygon(boom,fill=3);d.line(tail,fill=13)
    d.polygon(cabin,fill=4)
    d.line(cabin[:2],fill=6)
    d.rectangle(glass,fill=9)
    d.point(glass[0],fill=10)
    im=outline(im);d=D(im)
    cx,cy=hub
    dx,dy=((6,-1),(5,4),(1,6))[phase]
    d.line((cx-dx,cy-dy,cx+dx,cy+dy),fill=7)
    d.point(hub,fill=6)
    return im


DRONE_HUBS={
 'straight':((3,3),(12,3),(3,12),(12,12)),
 'left':((2,5),(11,2),(5,13),(13,10)),
 'right':((4,2),(13,5),(2,10),(10,13)),
}


def drone(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    center=(7 if pose!='right' else 8,8)
    for x,y in DRONE_HUBS[pose]:
        d.line((center,(x,y)),fill=3,width=2)
        d.line((center,(x-1,y)),fill=5)
        d.ellipse((x-2,y-2,x+2,y+2),fill=2,outline=1)
    x,y=center
    d.polygon([(x,y-4),(x+3,y-2),(x+3,y+2),(x,y+4),(x-3,y+2),(x-3,y-2)],fill=6,outline=1)
    d.line((x-2,y-1,x,y-3,x+2,y-1),fill=7)
    d.point((x-2,y+1),fill=12);d.point((x+2,y+1),fill=13)
    d.line((x-1,y+2,x+1,y+2),fill=9);d.point((x,y+2),fill=10)
    for x,y in DRONE_HUBS[pose]:
        dx,dy=((2,0),(1,2),(1,-2))[phase]
        d.line((x-dx,y-dy,x+dx,y+dy),fill=6)
        d.point((x,y),fill=13)
    return im


def small_mech(pose,phase):
    im=Image.new('L',(16,16));d=D(im)
    # Feet alternate the lead; phase 1 and 3 pass at different heights.
    stride=((2,-1),(0,0),(-1,2),(0,1))[phase]
    if pose in ('north','south'):
        for x,offset in zip((4,9),stride):
            y=(10+offset) if pose=='south' else (11-offset)
            d.rectangle((x,y,x+3,y+3),fill=2,outline=1)
            d.line((x+1,y+1,x+1,y+2),fill=5)
            d.line((x,y+3,x+3,y+3),fill=4)
        d.polygon([(4,4),(6,2),(10,2),(12,4),(12,9),(10,11),(5,11),(3,8)],fill=3,outline=1)
        d.line((4,5,6,3,9,3),fill=6)
        d.rectangle((6,5,9,7),fill=8)
        if pose=='south':d.line((6,6,9,6),fill=10)
        else:d.line((6,6,9,6),fill=12)
        d.line((3,7,3,9),fill=14)
        d.line((12,6,13,10 if pose=='south' else 3),fill=2,width=3)
        d.point((13,9 if pose=='south' else 4),fill=6)
    else:
        toward=1 if pose=='east' else -1
        for x,offset in zip((5,9),stride):
            xx=x+toward*offset
            d.rectangle((xx,10,xx+2,14-(offset==0)),fill=2,outline=1)
            d.point((xx+1,12),fill=5)
        shell=([(4,4),(7,2),(10,3),(11,5),(11,9),(8,11),(4,9)] if pose=='east'
               else [(3,5),(5,3),(8,2),(11,4),(11,9),(7,11),(4,9)])
        d.polygon(shell,fill=3,outline=1)
        d.line(shell[:3],fill=6)
        front=10 if pose=='east' else 4
        d.line((front,5,front,6),fill=10)
        d.line((7,8,7+toward*6,8),fill=2,width=3)
        d.line((8,7,7+toward*6,7),fill=5)
        d.point((7+toward*5,8),fill=14)
    return im


def walker(phase,wreck=False):
    im=Image.new('L',(32,32));d=D(im)
    if wreck:
        d.polygon([(7,9),(20,6),(26,12),(26,22),(20,26),(9,24),(5,18)],fill=1)
        d.polygon([(9,10),(19,8),(24,14),(23,21),(18,24),(10,22)],fill=3)
        d.line((8,12,4,6,1,8),fill=2,width=4)
        d.line((22,19,27,26,30,24),fill=2,width=4)
        d.line((6,18,4,25,1,27),fill=4,width=2)
        d.line((12,10,18,16,14,23),fill=1,width=2)
        for x,y in ((12,14),(19,18),(24,22)):
            d.polygon([(x-2,y+3),(x,y-4),(x+2,y+3)],fill=12)
            d.point((x,y+1),fill=14)
        return im
    for i,(x,y,endx,endy) in enumerate(((8,12,3,5),(23,12,28,5),(9,20,4,27),(22,20,27,27))):
        endy+=2 if (i+phase)%2 else -1
        d.line((x,y,endx,endy),fill=1,width=6)
        d.line((x,y,endx,endy),fill=3,width=3)
        d.line((x-1,y-1,endx-1,endy-1),fill=5)
        d.rectangle((endx-2,endy-2,endx+2,endy+2),fill=2,outline=1)
        d.point((endx-1,endy-1),fill=6)
    d.polygon([(9,7),(22,7),(25,12),(25,20),(20,24),(11,24),(6,20),(6,12)],fill=2,outline=1)
    d.polygon([(9,9),(21,9),(23,13),(22,20),(19,22),(12,22),(8,19),(8,13)],fill=3)
    d.line((8,17,8,13,10,9,20,9),fill=6)
    d.ellipse((10,8,21,19),fill=2,outline=5)
    d.ellipse((13,11,18,16),fill=4)
    d.line((12,20,19,20),fill=10)
    for x in (9,21):d.point((x,19),fill=14)
    return im


def sheet(path,samples,columns,scale=4,dual=False):
    w=max(110,max(i.width for _,i in samples)*scale+8)
    h=max(i.height for _,i in samples)*scale+24
    halves=2 if dual else 1
    board=Image.new('RGB',(w*columns*halves,math.ceil(len(samples)/columns)*h+18),(25,31,38))
    d=D(board)
    for half in range(halves):
        ground=(32,39,47) if half==0 else (114,115,105)
        if dual:d.text((half*columns*w+4,3),'Dunkler Grund' if half==0 else 'Heller Grund',fill='white')
        for i,(label,im) in enumerate(samples):
            x=(half*columns+i%columns)*w;y=i//columns*h+18
            d.rectangle((x,y,x+w-1,y+h-1),fill=ground)
            d.text((x+4,y+2),label,fill='white' if half==0 else (20,26,30))
            art=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            board.paste(art,(x+(w-art.width)//2,y+18),art)
    board.save(path)


def enemies():
    ENEMY.mkdir(parents=True,exist_ok=True)
    palettes={k:pal(v) for k,v in COLORS.items()}
    records=[]
    for group,poses,phases,palette in (
        ('jet',DIR8,3,'air'),('attack_heli',DIR8,3,'heli'),
        ('drone',tuple(DRONE_HUBS),3,'drone'),('mech',DIR4,4,'mechs'),
        ('walker',('south','destroyed'),2,'mechs'),
    ):
        samples=[]
        for pose in poses:
            for phase in range(1 if pose=='destroyed' else phases):
                if group=='jet':im=jet(pose,phase)
                elif group=='attack_heli':im=heli(pose,phase)
                elif group=='drone':im=drone(pose,phase)
                elif group=='mech':im=small_mech(pose,phase)
                else:im=walker(phase,pose=='destroyed')
                records.append(dict(group=group,pose=pose,phase=phase,width=im.width,
                                    height=im.height,palette=palette,rows=encode(im)))
                samples.append((f'{pose} / {phase}',rgba(im,palettes[palette])))
        sheet(ENEMY/f'{group}-preview.png',samples,3 if group=='walker' else phases,dual=True)
    save(ENEMY/'palettes.json',palettes)
    save(ENEMY/'placement.json',{'walker':{'guns':[[8,6]]}})
    save(ENEMY/'indexed-source.json',records)


MOUNTS=((10,10),(86,10),(5,37),(91,37))


def torso():
    im=Image.new('L',(112,64));d=D(im)
    # Separate shoulder blocks, hands and hip line make the biped readable.
    for x in (3,83):
        d.polygon([(x+3,8),(x+22,6),(x+27,12),(x+27,29),(x+20,34),
                   (x+5,32),(x,23),(x,13)],fill=1)
        d.polygon([(x+4,10),(x+21,8),(x+25,13),(x+24,27),(x+19,31),
                   (x+6,29),(x+2,22),(x+2,14)],fill=3)
        d.line((x+2,18,x+4,11,x+21,8),fill=6,width=2)
        d.line((x+7,29,x+21,29,x+24,25),fill=2,width=2)
    for x in (2,90):
        d.polygon([(x+6,25),(x+18,27),(x+21,36),(x+19,52),(x+13,58),
                   (x+4,55),(x,46),(x+1,34)],fill=1)
        d.polygon([(x+6,28),(x+17,30),(x+19,36),(x+16,50),(x+12,55),
                   (x+5,53),(x+2,45),(x+3,35)],fill=3)
        d.line((x+3,44,x+3,36,x+6,28,x+15,30),fill=5)
        d.rectangle((x+5,33,x+15,38),fill=2,outline=4)
        d.line((x+6,34,x+12,34),fill=7)
        for dx in (5,9,13):d.line((x+dx,51,x+dx+1,53),fill=14)
    d.polygon([(36,4),(76,4),(85,12),(91,24),(86,43),(79,52),
               (76,62),(37,62),(32,51),(24,43),(21,24),(28,12)],fill=1)
    d.polygon([(37,6),(75,6),(83,14),(88,24),(83,41),(77,49),
               (73,59),(39,59),(35,48),(27,41),(24,24),(30,14)],fill=4)
    d.polygon([(34,13),(48,9),(65,9),(78,14),(84,25),(79,39),
               (72,47),(40,47),(33,39),(29,25)],fill=3)
    d.line((24,25,30,14,37,6,75,6,82,13),fill=6,width=2)
    d.line((25,28,28,40,36,49,39,58),fill=5)
    d.line((40,59,73,59,78,49,84,41,87,26),fill=2,width=2)
    # Cockpit canopy and drone latch high on the back.
    d.rectangle((47,6,64,12),fill=2,outline=5)
    d.line((49,7,61,7),fill=7)
    d.polygon([(45,13),(66,13),(71,17),(69,23),(43,23),(40,18)],fill=2)
    d.polygon([(45,15),(65,15),(68,18),(65,21),(45,21),(42,18)],fill=8)
    d.line((45,16,65,16),fill=10)
    d.line((49,18,62,18),fill=9)
    # Split chest shutters, with triangular armor and colored vent lights.
    d.polygon([(41,24),(70,24),(76,30),(74,45),(68,51),(44,51),(37,45),(36,30)],fill=1)
    d.polygon([(42,26),(69,26),(73,31),(71,43),(67,48),(45,48),(40,43),(39,31)],fill=4)
    d.line((40,42,40,31,43,26,69,26),fill=6)
    d.line((55,27,55,47),fill=2,width=2)
    for x in (44,61):
        for y in (32,35,38):d.line((x,y,x+6,y),fill=2)
        d.line((x,41,x+5,41),fill=9)
    for x in (28,77):
        d.polygon([(x,24),(x+6,20),(x+6,29),(x+1,35)],fill=5)
        d.line((x+1,26,x+4,23),fill=14)
    for x in (38,63):
        d.rectangle((x,51,x+11,59),fill=2,outline=1)
        d.line((x+1,52,x+9,52),fill=6)
        d.line((x+3,55,x+8,55),fill=12)
    for x,y in ((27,19),(81,19),(37,51),(73,51),(31,41),(78,41)):
        d.point((x,y),fill=7);d.point((x+1,y+1),fill=2)
    d.rectangle((96,49,105,56),fill=1)
    d.line((97,50,104,50),fill=6);d.line((99,54,103,54),fill=12)
    return im


def leg(phase):
    im=Image.new('L',(32,48));d=D(im)
    knee=(12,15,18)[phase]
    ankle=(33,38,41)[phase]
    dx=(-2,0,2)[phase]
    d.polygon([(8,0),(22,0),(25,8),(22,knee+4),(10,knee+5),(6,9)],fill=1)
    d.polygon([(9,2),(21,2),(23,8),(20,knee+1),(11,knee+2),(8,8)],fill=4)
    d.line((8,8,9,2,21,2),fill=6)
    d.line((11,6,19,6),fill=2);d.line((11,8,19,8),fill=5)
    d.line((11,knee,13+dx,ankle,21+dx,ankle),fill=1,width=10)
    d.line((12,knee+2,14+dx,ankle),fill=4,width=6)
    d.line((11,knee+4,13+dx,ankle-1),fill=6,width=2)
    d.ellipse((8,knee-2,22,knee+8),fill=2,outline=5)
    d.ellipse((11,knee,19,knee+6),fill=4,outline=1)
    d.line((12,knee+2,18,knee+2),fill=9)
    d.polygon([(8+dx,ankle-1),(22+dx,ankle-1),(27+dx,ankle+3),
               (26+dx,ankle+6),(6+dx,ankle+6),(4+dx,ankle+3)],fill=1)
    d.polygon([(8+dx,ankle),(21+dx,ankle),(24+dx,ankle+3),
               (7+dx,ankle+3)],fill=4)
    d.line((8+dx,ankle,20+dx,ankle),fill=6)
    for x in (10,15,20):d.line((x+dx,ankle+3,x+dx,ankle+4),fill=14)
    return im


def turret(rocket,pose):
    im=Image.new('L',(16,16));d=D(im)
    d.polygon([(4,1),(11,1),(14,4),(14,10),(11,13),(4,13),(1,10),(1,4)],fill=1)
    d.polygon([(4,2),(10,2),(13,5),(12,10),(10,11),(4,11),(2,9),(2,4)],fill=4)
    d.line((2,7,2,4,4,2,10,2),fill=6)
    if pose=='destroyed':
        d.polygon([(4,4),(9,3),(12,7),(9,11),(3,8)],fill=2)
        d.line((6,5,9,10,13,12),fill=1,width=4)
        d.line((6,5,9,9,12,11),fill=5)
        d.point((5,8),fill=12);d.point((8,6),fill=13)
    elif rocket:
        if pose=='south':
            d.rectangle((4,5,11,13),fill=2,outline=1)
            d.line((5,5,10,5),fill=6)
            for x in (5,8,10):
                d.line((x,7,x,12),fill=5);d.point((x,13),fill=14)
        else:
            d.polygon([(5,4),(8,3),(14,9),(13,14),(8,13),(4,8)],fill=2,outline=1)
            for x,y in ((6,6),(8,5),(7,8)):
                d.line((x,y,x+4,y+4),fill=5);d.point((x+4,y+4),fill=14)
    else:
        end=(8,15) if pose=='south' else (14,14)
        d.line(((8,6),end),fill=1,width=4)
        d.line(((7,6),(end[0]-1,end[1]-1)),fill=6,width=2)
        d.point((7,8),fill=7);d.point(end,fill=1)
    return im


def reactor():
    im=Image.new('L',(32,32));d=D(im)
    d.polygon([(4,2),(27,2),(31,8),(29,24),(24,30),(7,30),(2,24),(1,8)],fill=1)
    d.line((2,21,2,8,5,3,26,3,30,8),fill=6,width=2)
    d.polygon([(4,7),(9,5),(8,24),(5,27),(3,21)],fill=4)
    d.polygon([(26,6),(29,9),(27,25),(23,27),(24,10)],fill=3)
    for x in (9,15,21):
        d.rectangle((x,8,x+3,23),fill=11)
        d.line((x+1,9,x+1,22),fill=13,width=2)
        d.line((x+1,10,x+1,19),fill=14)
        d.point((x+1,12),fill=15)
    d.line((7,25,24,25),fill=5,width=2)
    d.line((8,26,23,26),fill=9)
    return im


def muzzle(phase):
    im=Image.new('L',(16,16));d=D(im)
    d.polygon([(7,phase),(10,5),(14,3+phase),(11,8),(15-phase,12),
               (10,10),(8,15),(5,10),(1,12-phase),(4,7),(2+phase,3),(6,5)],fill=13)
    d.polygon([(7,3),(11,8),(8,12),(5,8)],fill=14)
    d.rectangle((7,6,8,9),fill=15)
    return im


def flame(phase):
    im=Image.new('L',(16,32));d=D(im)
    end=(19,31,23)[phase]
    d.polygon([(6,0),(9,0),(11,5),(13,9),(11,13),(14,end-5),(10,end-4),
               (8,end),(5,end-5),(2,end-3),(4,12),(2,8),(5,5)],fill=12)
    d.polygon([(7,0),(9,4),(8,8),(11,12),(8,end-5),(7,end-3),
               (5,end-9),(6,10),(4,8),(7,4)],fill=13)
    d.line((7,0,8,5,7,9,8,end-9),fill=14,width=2)
    d.line((7,1,7,6),fill=15)
    if phase!=1:d.point((10,end+2),fill=13)
    return im


def dust(phase):
    im=Image.new('L',(32,16));d=D(im)
    for x,y,r in ((4,9,2),(10,7,3),(16,10,3),(23,7,3),(28,9,2)):
        y+=((x+phase)%3)-1
        d.ellipse((x-r,y-1,x+r,y+2),fill=4)
        d.line((x-1,y,x+1,y),fill=5+phase%2)
        d.point((x,y-3),fill=14 if (x+phase)%3==0 else 6)
    d.point((5+phase*3,13),fill=6)
    return im


def launch(phase):
    im=drone(('straight','left','straight')[phase],phase)
    if phase<2:
        d=D(im)
        for x,y in ((1,7),(14,7),(4,2),(11,2)):
            d.point((x,y+phase),fill=7 if phase==0 else 10)
    return im


def boss():
    BOSS.mkdir(parents=True,exist_ok=True)
    palette=pal(BOSS_COLORS)
    frames={'body':torso(),'core_exposed':reactor()}
    mounts=[]
    for i,(corner,(x,y)) in enumerate(zip(('nw','ne','sw','se'),MOUNTS)):
        key='turret_'+corner
        variants={p:key+'_'+p for p in ('south','southeast','destroyed')}
        for p,fid in variants.items():frames[fid]=turret(i<2,p)
        mounts.append(dict(id=key,offset=[x,y],size=[16,16],hit_rect=[x,y,16,16],
                            independently_destructible=True,**variants))
    for i in range(3):
        frames[f'rotor_{i}']=leg(i)
        frames[f'flame_{i}']=flame(i)
        frames[f'spray_{i}']=dust(i)
        frames[f'deck_jet_{i}']=launch(i)
    for i in range(2):frames[f'muzzle_{i}']=muzzle(i)
    placement=dict(body='body',body_size=[112,64],palette='boss',turrets=mounts,
        core=dict(offset=[40,22],size=[32,32],hit_rect=[48,30,16,16],exposed_overlay='core_exposed'),
        rotors=[dict(id='leg_l',offset=[23,55],phase_offset=0),
                dict(id='leg_r',offset=[57,55],phase_offset=1)],
        rotor_frames=[f'rotor_{i}' for i in range(3)],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        flame=dict(frames=[f'flame_{i}' for i in range(3)],offset=[93,56]),
        spray=dict(frames=[f'spray_{i}' for i in range(3)],offsets=[[23,92],[57,92]]),
        catapult=dict(frames=[f'deck_jet_{i}' for i in range(3)],offset=[48,0]),
        draw_order=['spray','legs','body','core_if_exposed','turrets','flame','deck_jet'])
    save(BOSS/'placement.json',placement)
    save(BOSS/'indexed-source.json',[dict(id=fid,width=im.width,height=im.height,rows=encode(im))
          for fid,im in frames.items()])
    (BOSS/'palette.rgb').write_bytes(bytes(c for triplet in palette for c in triplet))

    def compose(phase,exposed=False,effect=None):
        canvas=Image.new('RGBA',(128,124),(51,56,62,255))
        def paste(key,xy):
            canvas.alpha_composite(rgba(frames[key],palette),(xy[0]+8,xy[1]+8))
        if effect=='step':
            for xy in placement['spray']['offsets']:paste(f'spray_{phase}',xy)
        for item in placement['rotors']:
            paste(f"rotor_{(phase+item['phase_offset'])%3}",item['offset'])
        paste('body',(0,0))
        if exposed:paste('core_exposed',placement['core']['offset'])
        for item in mounts:paste(item['destroyed' if exposed else 'south'],item['offset'])
        if effect=='flame':paste(f'flame_{phase}',placement['flame']['offset'])
        if effect=='launch':
            x,y=placement['catapult']['offset']
            paste(f'deck_jet_{phase}',(x,y+phase*16))
        return canvas
    sheet(BOSS/'boss-preview.png',[
        ('Waffen intakt',compose(0)),('Brust offen / Endphase',compose(1,True,'flame'))],2,3)
    for effect,labels in (
        ('step',('Schritt vorn','Schritt Mitte','Schritt hinten')),
        ('flame',('Flamme kurz','Flamme voll','Flamme ausklingend')),
        ('launch',('Drohne angedockt','Drohne hebt ab','Drohne im Flug')),
    ):
        sheet(BOSS/f'{effect}-phases.png',[(label,compose(i,effect=='flame',effect))
              for i,label in enumerate(labels)],3,2)
    samples=[(f'Staub {i+1}',rgba(frames[f'spray_{i}'],palette)) for i in range(3)]
    sheet(BOSS/'dust-phases.png',samples,3,4)
    frames_anim=[compose(i,effect='step').convert('RGB').resize((384,372),Image.Resampling.NEAREST)
                 for i in (0,1,2,1)]
    frames_anim[0].save(BOSS/'boss-animation.png',save_all=True,append_images=frames_anim[1:],
                        duration=155,loop=0)


if __name__=='__main__':
    enemies()
    boss()
