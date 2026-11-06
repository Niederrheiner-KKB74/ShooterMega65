"""Offshore aircraft poses drawn in screen coordinates at 16 x 16."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'assets/art/level3/source'))
import generate_vehicles as base

COLORS = {
    'air':'000000 11212d 204167 2e638c 4a9fbb 9ed9df e2f3df ffdf76 e69338 d54c34 fff3b4 75524a 173149 6c9eab d2e0c3 f9b54f',
    'heli':'000000 202821 354631 536440 71844d a7a771 d5c896 f3e3aa 263e40 446c6d 85b9ae d2e7cd b45339 eab34f 786744 f9d77b',
    'ships':'000000 142430 253b48 405867 5d7980 8e9e9b c2ccc0 e4e9da 254e63 427989 7bb6bc 793b37 c45640 f18a49 f7c466 fff0b0',
    'frigate':'000000 1b262d 2b3c47 455762 65767d 8c9c9c b7c1b7 e1e7d8 275267 3d788c 7cbbc1 793b36 b94a3e ee783e ffc36a fff1ae',
}

# Each entry describes the wing, fuselage, port float, starboard float,
# canopy and propeller for one individually drawn heading.
PLANES = {
 'north': ([(2,7),(13,7),(13,9),(2,9)],[(7,2),(8,2),(9,6),(8,13),(7,13),(6,6)],
           [(3,5),(4,5),(4,11),(3,11)],[(11,5),(12,5),(12,11),(11,11)],[(7,5),(8,6)],(7,2)),
 'northeast': ([(4,4),(12,11),(11,12),(3,6)],[(12,2),(13,3),(11,6),(5,12),(3,12),(4,10)],
               [(6,3),(7,4),(3,8),(2,7)],[(12,8),(13,9),(8,13),(7,12)],[(10,5),(9,6)],(12,2)),
 'east': ([(6,2),(8,2),(8,13),(6,13)],[(13,7),(13,8),(9,9),(2,8),(2,7),(8,6)],
          [(5,3),(11,3),(11,4),(5,4)],[(5,11),(11,11),(11,12),(5,12)],[(10,7),(9,8)],(13,7)),
 'southeast': ([(4,11),(11,4),(12,5),(5,12)],[(13,12),(12,13),(9,11),(3,5),(3,3),(5,4)],
               [(8,3),(9,2),(13,6),(12,7)],[(3,8),(4,7),(8,11),(7,13)],[(10,9),(11,10)],(13,12)),
 'south': ([(2,6),(13,6),(13,8),(2,8)],[(7,13),(8,13),(9,9),(8,2),(7,2),(6,9)],
           [(3,4),(4,4),(4,10),(3,10)],[(11,4),(12,4),(12,10),(11,10)],[(7,10),(8,9)],(8,13)),
 'southwest': ([(4,4),(12,11),(11,12),(3,6)],[(3,13),(2,12),(4,9),(10,3),(12,3),(11,5)],
               [(3,8),(2,7),(6,3),(7,4)],[(8,12),(7,11),(12,7),(13,8)],[(5,10),(6,9)],(3,13)),
 'west': ([(7,2),(9,2),(9,13),(7,13)],[(2,7),(2,8),(6,9),(13,8),(13,7),(7,6)],
          [(4,3),(10,3),(10,4),(4,4)],[(4,11),(10,11),(10,12),(4,12)],[(5,7),(6,8)],(2,8)),
 'northwest': ([(4,11),(11,4),(12,5),(5,12)],[(2,3),(3,2),(6,4),(12,10),(12,12),(10,11)],
               [(3,7),(4,6),(8,10),(7,12)],[(8,3),(9,2),(13,6),(12,7)],[(5,5),(6,6)],(2,3)),
}
# Each entry contains the cabin, boom, tail stabilizer, skids, glazing and hub.
HELICOPTERS = {
 'north': ([(6,2),(9,2),(10,4),(10,8),(9,9),(6,9),(5,7),(5,4)],
           [(7,8),(8,8),(8,13),(7,13)],[(6,13),(9,13)],[(4,4),(4,9)],[(11,4),(11,9)],[(6,3),(9,5)],(7,6)),
 'northeast': ([(10,2),(12,3),(13,5),(12,7),(9,9),(6,8),(6,6),(8,3)],
               [(7,7),(9,8),(4,13),(3,12)],[(2,11),(5,13)],[(5,5),(8,2)],[(10,10),(13,7)],[(9,4),(12,5)],(9,6)),
 'east': ([(13,6),(13,9),(11,10),(7,10),(6,9),(6,6),(8,5),(11,5)],
          [(7,7),(7,8),(2,8),(2,7)],[(2,6),(2,9)],[(7,4),(12,4)],[(7,11),(12,11)],[(10,6),(12,9)],(9,7)),
 'southeast': ([(13,10),(12,12),(10,13),(8,12),(6,9),(7,6),(9,6),(12,8)],
               [(8,7),(7,9),(2,4),(3,3)],[(2,5),(4,2)],[(10,5),(13,8)],[(5,10),(8,13)],[(10,9),(11,12)],(9,9)),
 'south': ([(6,13),(9,13),(10,11),(10,7),(9,6),(6,6),(5,8),(5,11)],
           [(7,7),(8,7),(8,2),(7,2)],[(6,2),(9,2)],[(4,6),(4,11)],[(11,6),(11,11)],[(6,10),(9,12)],(8,9)),
 'southwest': ([(5,13),(3,12),(2,10),(3,8),(6,6),(9,7),(9,9),(7,12)],
               [(8,8),(6,7),(11,2),(12,3)],[(10,2),(13,4)],[(7,13),(10,10)],[(2,8),(5,5)],[(3,9),(6,11)],(6,9)),
 'west': ([(2,6),(2,9),(4,10),(8,10),(9,9),(9,6),(7,5),(4,5)],
          [(8,7),(8,8),(13,8),(13,7)],[(13,6),(13,9)],[(3,4),(8,4)],[(3,11),(8,11)],[(3,6),(5,9)],(6,8)),
 'northwest': ([(2,5),(3,3),(5,2),(7,3),(9,6),(8,9),(6,9),(3,7)],
               [(7,8),(8,6),(13,11),(12,12)],[(11,13),(13,10)],[(5,2),(10,5)],[(2,7),(5,10)],[(3,4),(6,6)],(6,6)),
}
PROPELLERS = {
 'north': [((5,1),(9,1)),((6,0),(8,2)),((7,0),(7,2))],
 'northeast': [((11,1),(14,4)),((12,0),(12,3)),((11,2),(14,2))],
 'east': [((14,5),(14,9)),((13,6),(15,8)),((13,7),(15,7))],
 'southeast': [((11,14),(14,11)),((13,11),(13,15)),((12,13),(15,13))],
 'south': [((6,14),(10,14)),((7,13),(9,15)),((8,13),(8,15))],
 'southwest': [((1,11),(4,14)),((3,12),(3,15)),((1,13),(4,13))],
 'west': [((1,6),(1,10)),((0,7),(2,9)),((0,8),(2,8))],
 'northwest': [((1,4),(4,1)),((2,0),(2,4)),((0,2),(3,2))],
}
TAILS = dict(zip(base.DIR8,((7,13),(3,12),(2,7),(3,3),(8,2),(12,3),(13,8),(12,12))))


def outline(im):
    mask=im.point(lambda value:255 if value else 0)
    expanded=mask.filter(ImageFilter.MaxFilter(3))
    result=Image.new('L',im.size)
    result.paste(1,mask=expanded)
    result.paste(im,mask=mask)
    return result


def aircraft(group,pose,phase):
    im=Image.new('L',(16,16))
    draw=ImageDraw.Draw(im)
    if group=='seaplane':
        wing,_,left,right,glass,nose=PLANES[pose]
        draw.polygon(wing,fill=3)
        # Orange wing tips remain visible beside the two pale floats.
        edge=max(zip(wing,wing[1:]+wing[:1]),key=lambda p:
                 (p[0][0]-p[1][0])**2+(p[0][1]-p[1][1])**2)
        draw.line(edge,fill=4)
        for pontoon in (left,right):
            draw.polygon(pontoon,fill=13)
            draw.line((pontoon[-1],pontoon[0]),fill=14)
        if pose in ('north','south'):
            tips=((2,wing[0][1]),(13,wing[1][1]))
        elif pose in ('east','west'):
            tips=((wing[0][0],2),(wing[2][0],13))
        else:
            tips=edge
        for x,y in tips:
            draw.point((x,y),fill=8)
            draw.point((x,y+1 if y<13 else y-1),fill=7)
        draw.line((TAILS[pose],nose),fill=2,width=2)
        draw.line(glass,fill=5,width=2)
        draw.point(glass[0],fill=6)
        draw.point(nose,fill=9)
        im=outline(im)
        prop=[tuple(max(1,min(14,p)) for p in xy) for xy in PROPELLERS[pose][phase]]
        ImageDraw.Draw(im).line(prop,fill=10)
    else:
        cabin,boom,tail,skid_l,skid_r,glass,hub=HELICOPTERS[pose]
        draw.line(skid_l,fill=6)
        draw.line(skid_r,fill=14)
        draw.polygon(boom,fill=3)
        draw.line(tail,fill=13)
        draw.polygon(cabin,fill=4)
        draw.line((cabin[0],cabin[1]),fill=5)
        draw.rectangle(glass,fill=9)
        draw.point(glass[0],fill=11)
        im=outline(im)
        draw=ImageDraw.Draw(im)
        cx,cy=hub
        dx,dy=((6,-1),(5,4),(1,6))[phase]
        draw.line((cx-dx,cy-dy,cx+dx,cy+dy),fill=7)
        draw.point(hub,fill=6)
    return im


def boat(group,pose,phase):
    speed=group=='speedboat'
    size=16 if speed else 32
    im=Image.new('L',(size,size))
    project=base.heading(im,pose)
    draw=ImageDraw.Draw(im)
    def poly(points,color):
        draw.polygon([project(x,y) for x,y in points],fill=color)
    def line(points,color,width=1):
        draw.line([project(x,y) for x,y in points],fill=color,width=width)
    def dot(x,y,color):
        draw.point(project(x,y),fill=color)
    if speed:
        # Wake starts behind the transom; the two white tips pulse independently.
        for side in (-1,1):
            line([(side*2,3),(side*(3+phase%2),5),(side*(4+phase%2),7)],9)
            dot(side*(4+phase%2),6+phase//2,7)
            dot(side*3,-3+phase%2,10)
        dot(phase-2,7,10)
        poly([(0,-7),(2,-4),(3,1),(2,5),(-2,5),(-3,1),(-2,-4)],1)
        poly([(0,-5),(2,-2),(2,2),(1,4),(-1,4),(-2,2),(-2,-2)],5)
        line([(-1,-3),(-2,1),(-1,3)],7)
        line([(-1,0),(1,0)],8)
        line([(-1,3),(1,3)],12)
        dot(0,4,3)
    else:
        for side in (-1,1):
            line([(side*2,-13),(side*5,-11),(side*7,-8)],10)
            dot(side*(6+phase),-10,7)
            line([(side*3,11),(side*5,13),(side*7,15)],9)
            dot(side*(5+phase),14,7)
        poly([(0,-15),(3,-12),(5.5,-7),(5.5,9),(3,12),
              (-3,12),(-5.5,9),(-5.5,-7),(-3,-12)],1)
        poly([(0,-13),(3,-9),(4.5,-5),(4.5,8),(3,10),
              (-3,10),(-4.5,8),(-4.5,-5),(-3,-9)],5)
        line([(-3,-9),(-4,-4),(-4,7),(-3,9)],7)
        line([(5,-3),(5,7)],12)
        poly([(-3,3),(3,3),(4,5),(3,9),(-3,9),(-4,5)],3)
        line([(-3,4),(3,4)],6)
        line([(-2,5),(2,5)],8)
        line([(0,7),(0,10)],7)
        dot(-4,7,12);dot(4,7,10)
        dot(0,-11,7);dot(-2,10,6);dot(2,10,6)
        x,y=project(0,-2)
        draw.ellipse((x-3,y-3,x+3,y+3),fill=2,outline=6)
        draw.ellipse((x-1,y-1,x+1,y+1),fill=4)
    return im


def frigate(phase,wreck=False):
    im=Image.new('L',(32,64))
    draw=ImageDraw.Draw(im)
    if wreck:
        draw.polygon([(7,7),(20,4),(24,10),(26,39),(25,50),(20,60),
                      (13,54),(9,45),(5,16)],fill=1)
        draw.polygon([(8,9),(19,6),(22,11),(24,39),(23,48),(20,57),
                      (14,52),(11,43),(7,15)],fill=4)
        draw.line((8,9,7,15,11,43,14,52),fill=6)
        draw.line((22,13,24,36,23,46),fill=12)
        draw.polygon([(9,18),(19,12),(23,22),(22,43),(13,40)],fill=2)
        draw.line((11,25,18,28,15,37,23,40),fill=1,width=3)
        for x,y in ((13,20),(20,32),(16,44)):
            draw.polygon([(x-3,y+4),(x-2,y-2),(x,y),(x+2,y-5),(x+3,y+4)],fill=12)
            draw.line((x,y+3,x+1,y),fill=14,width=2)
            draw.point((x-1,y-5),fill=13)
        draw.line((5,39,7,44,9,46),fill=9)
        draw.line((25,23,28,26,29,30),fill=10)
        return im
    for side in (-1,1):
        draw.line((16+side*6,5,16+side*(8+phase),1),fill=10)
        draw.line((16+side*4,61,16+side*10,56,16+side*12,51),fill=10)
        draw.point((16+side*(11+phase),54-phase),fill=7)
    draw.polygon([(8,3),(23,3),(25,8),(25,43),(23,51),(16,63),
                  (9,51),(6,43),(6,8)],fill=1)
    draw.polygon([(9,5),(22,5),(23,9),(23,42),(21,50),(16,60),
                  (11,50),(8,42),(8,9)],fill=4)
    draw.line((9,5,8,9,8,42,11,50,16,60),fill=6)
    draw.line((24,12,24,43,21,52),fill=12)
    draw.rectangle((10,6,21,12),fill=2,outline=5)
    for x in (13,18):draw.line((x,7,x,11),fill=7)
    draw.line((13,9,18,9),fill=7)
    draw.polygon([(10,24),(20,24),(22,28),(21,36),(11,36),(9,31)],fill=2)
    draw.rectangle((11,25,20,31),fill=5,outline=6)
    draw.line((12,29,19,29),fill=8,width=2)
    draw.line((16,26,16,35),fill=7)
    draw.line((12,34,20,34),fill=5)
    draw.line((9,26,9,32),fill=14,width=2)
    draw.line((22,30,22,36),fill=13,width=2)
    for y in (16,44):
        draw.ellipse((12,y-4,20,y+4),fill=2,outline=6)
        draw.ellipse((14,y-2,18,y+2),fill=5)
    for x,y in ((9,13),(22,13),(11,49),(21,49),(16,55)):
        draw.point((x,y),fill=7)
    return im


def sheet(path,samples,phases):
    """Every pose on both representative water tones, at 4x."""
    columns=phases
    w=max(104,samples[0][1].width*4+8)
    h=samples[0][1].height*4+24
    rows=(len(samples)+columns-1)//columns
    board=Image.new('RGB',(2*columns*w,rows*h+20),(21,33,39))
    draw=ImageDraw.Draw(board)
    for half,water in enumerate(((20,49,79),(76,155,156))):
        start=half*columns*w
        draw.text((start+4,4),'Dunkles Wasser' if half==0 else 'Helles Wasser',fill='white')
        for i,(name,sprite) in enumerate(samples):
            x=start+(i%columns)*w
            y=20+(i//columns)*h
            draw.rectangle((x,y,x+w-1,y+h-1),fill=water)
            draw.text((x+4,y+3),name,fill='white' if half==0 else (14,35,42))
            art=sprite.resize((sprite.width*4,sprite.height*4),Image.Resampling.NEAREST)
            board.paste(art,(x+(w-art.width)//2,y+19),art)
    board.save(path)


def main():
    out=base.ENEMY
    out.mkdir(parents=True,exist_ok=True)
    palettes={key:base.colors(value) for key,value in COLORS.items()}
    base.save(out/'palettes.json',palettes)
    base.save(out/'placement.json',{'patrol_boat':{'guns':[[8,10]]},
                                    'frigate':{'guns':[[8,8],[8,36]]}})
    records=[]
    for group,poses,phases,pal in (
        ('seaplane',base.DIR8,3,'air'),('navy_heli',base.DIR8,3,'heli'),
        ('speedboat',base.DIR4,4,'ships'),('patrol_boat',base.DIR4,2,'ships'),
        ('frigate',('south','destroyed'),2,'frigate'),
    ):
        samples=[]
        for pose in poses:
            for phase in range(1 if pose=='destroyed' else phases):
                if pal in ('air','heli'):
                    im=aircraft(group,pose,phase)
                elif group=='frigate':
                    im=frigate(phase,pose=='destroyed')
                else:
                    im=boat(group,pose,phase)
                records.append(dict(group=group,pose=pose,phase=phase,width=im.width,
                                    height=im.height,palette=pal,rows=base.encode(im)))
                samples.append((f'{pose} / {phase}',base.rgba(im,palettes[pal])))
        sheet(out/f'{group}-preview.png',samples,3 if group=='frigate' else phases)
    base.save(out/'indexed-source.json',records)


if __name__=='__main__':
    main()
