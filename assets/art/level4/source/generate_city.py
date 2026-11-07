"""Build the native 16x16 terrain, ruins, animations and map of Iron City."""
import json
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'assets/art/level4/generated'
D = ImageDraw.Draw
PALETTE = {
 'streets':'000000 202630 2d343e 3a424a 485057 59616a 777973 96978b aba99a d7d3be dfb868 8c6655 b28e73 425457 596753 28373a',
 'ruins':'000000 2b282d 443b3a 605a53 777268 9b8976 bbaa91 717877 9c9d91 343e34 4e5d43 71845a 593c35 9f5037 d77739 f4ae59',
 'buildings':'000000 202733 343e48 555853 75796e 96998a bfc1ac e6dbbd 4b3336 79514d ac6650 d39770 294e60 4b7d8d 8bb9bd e2aa56',
}
PALETTE = {k:[list(bytes.fromhex(v)) for v in s.split()] for k,s in PALETTE.items()}
PALETTE['fixed_targets']=json.loads(
    (ROOT/'assets/art/ground-targets/generated/ground-targets.json').read_text()
)['palettes']['fixed_targets']
TILES, META, ID, WRECKS, PAIRS, ANIMS = [], [], {}, [], [], []


def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='ascii',newline='\n')


def add(name,palette,im):
    assert name not in ID and im.size==(16,16) and min(im.tobytes())>0
    ID[name]=len(TILES)
    META.append(dict(id=len(TILES),name=name,palette=palette))
    TILES.append(im)


def rgb(im,palette):
    out=Image.new('RGB',im.size)
    out.putdata([tuple(PALETTE[palette][p]) for p in im.tobytes()])
    return out


def grit(im,seed,colors,count):
    d=D(im);rng=random.Random(seed)
    for _ in range(count):
        d.point((rng.randrange(im.width),rng.randrange(im.height)),fill=rng.choice(colors))


def streets():
    # Edge bits are north, east, south, west. The sidewalk meets the block.
    for mask in range(16):
        im=Image.new('L',(16,16),3);d=D(im)
        grit(im,7,(2,4),7)
        for bit,box in enumerate(((0,0,15,2),(13,0,15,15),(0,13,15,15),(0,0,2,15))):
            if mask&(1<<bit):
                d.rectangle(box,fill=7)
                x,y,u,v=box
                d.line((x,y,u,y) if bit%2==0 else (x,y,x,v),fill=8)
                if bit==0:d.line((0,2,15,2),fill=5)
                if bit==1:d.line((13,0,13,15),fill=5)
                if bit==2:d.line((0,13,15,13),fill=5)
                if bit==3:d.line((2,0,2,15),fill=5)
        add(f'street{mask}','streets',im)
    for name in ('lane_v','lane_h','crosswalk','parking','plaza','bridge','asphalt_damage'):
        im=Image.new('L',(16,16),3);d=D(im)
        grit(im,17,(2,4),15)
        if name=='lane_v':d.line((7,2,7,9),fill=10);d.line((8,2,8,9),fill=5)
        elif name=='lane_h':d.line((2,7,9,7),fill=10);d.line((2,8,9,8),fill=5)
        elif name=='crosswalk':
            for x in range(1,16,4):d.rectangle((x,6,x+1,10),fill=9)
        elif name=='parking':
            for y in (1,7,13):d.line((3,y,13,y),fill=8)
            d.line((13,1,13,13),fill=7)
        elif name=='plaza':
            d.rectangle((0,0,15,15),fill=5)
            d.line((0,0,15,0),fill=7);d.line((0,0,0,15),fill=6)
            d.line((0,15,15,15),fill=4)
        elif name=='bridge':
            d.line((0,1,15,1),fill=8);d.line((0,14,15,14),fill=2)
            for x in (2,7,12):d.line((x,2,x,13),fill=4)
        else:
            d.line((3,0,6,5,5,8,12,15),fill=2)
            d.point((8,9),fill=7)
        add(name,'streets',im)


def neighborhood():
    for i in range(12):
        im=Image.new('L',(16,16),4 if i<9 else 3);d=D(im)
        if i<3:
            if i:
                d.polygon([(2,12),(4,7),(9,5),(13,9),(14,12),(10,14),(5,14)],fill=2)
                d.polygon([(3,11),(5,7),(10,6),(13,10),(9,12),(5,13)],fill=5)
                d.line((4,9,7,7,10,7),fill=6)
                d.line((7,12,11,9),fill=12)
            else:d.rectangle((0,0,15,15),fill=4)
        elif i==3:
            d.rectangle((0,0,15,15),fill=7)
        elif i==4:
            d.polygon([(3,8),(6,5),(11,5),(13,8),(11,12),(7,13),(4,11)],fill=3)
            d.polygon([(4,8),(7,6),(11,6),(12,8),(9,11),(6,11)],fill=2)
            d.line((4,8,7,6,10,6),fill=5)
        elif i==5:
            d.rectangle((1,1,14,14),fill=7,outline=3)
            d.line((1,6,6,7,8,11,13,12),fill=2)
            d.line((2,2,13,2),fill=8)
        elif i<9:
            d.rectangle((0,0,15,15),fill=10)
            d.line((1,0,1,15),fill=5,width=3)
            if i!=8:
                d.ellipse((5,5,14,13),fill=9)
                d.ellipse((4,2,12,10),fill=9)
                d.ellipse((4,2,10,8),fill=11)
                d.line((7,9,7,12),fill=5)
            else:d.line((3,8,15,8),fill=5,width=3)
        elif i==9:
            d.polygon([(4,4),(10,3),(12,9),(11,12),(6,13),(3,9)],fill=1)
            d.line((5,4,10,4,11,8),fill=13,width=2)
            d.rectangle((5,6,9,9),fill=7);d.point((10,11),fill=14)
        elif i==10:
            d.line((3,3,8,8,12,8,14,10),fill=2,width=2)
            d.point((13,9),fill=8)
        else:
            d.rectangle((3,4,12,12),fill=12,outline=2)
            d.line((4,5,10,5,10,7,6,9,5,11),fill=8)
        add(f'ruins{i}','ruins',im)


def street_details():
    for direction in range(4):
        im=TILES[ID[f'street{1<<direction}']].copy()
        # Rubble touches the sidewalk, leaving the driving lane clear.
        points=[(3,0),(12,0),(11,3),(8,5),(4,4)]
        transform=(
            lambda x,y:(x,y),lambda x,y:(15-y,x),
            lambda x,y:(x,15-y),lambda x,y:(y,x),
        )[direction]
        d=D(im)
        d.polygon([transform(x,y) for x,y in points],fill=11)
        d.line([transform(x,y) for x,y in ((4,1),(9,1),(11,2))],fill=12)
        d.point(transform(8,4),fill=8)
        add(f'rubble_curb{direction}','streets',im)
    im=TILES[ID['street8']].copy();d=D(im)
    d.line((1,10,6,12),fill=2,width=2)
    d.line((1,9,2,4,4,4),fill=9)
    d.point((4,5),fill=10)
    add('lamp_curb','streets',im)
    im=TILES[ID['street2']].copy();d=D(im)
    d.polygon([(10,3),(13,4),(13,11),(9,11),(8,7)],fill=2)
    d.line((10,4,12,5,12,8),fill=11)
    d.rectangle((9,6,11,8),fill=5)
    d.point((11,10),fill=10)
    add('wreck_curb','streets',im)
    for name,mask,shape in (
        ('shadow_n',1,((1,3),(13,3),(15,6),(6,7),(1,6))),
        ('shadow_w',8,((3,2),(5,4),(7,13),(3,15))),
    ):
        im=TILES[ID[f'street{mask}']].copy()
        D(im).polygon(shape,fill=2)
        add(name,'streets',im)


def building(name,kind,theme):
    im=Image.new('L',(32,32),3);d=D(im)
    d.polygon([(7,9),(25,5),(30,10),(30,27),(25,30),(8,30)],fill=2)
    if theme in ('brick','glass','industrial','guard'):
        wall,roof,edge={'brick':(9,10,11),'glass':(12,13,14),
                        'industrial':(4,5,7),'guard':(8,3,6)}[theme]
        d.rectangle((3,4,27,28),fill=wall,outline=2)
        d.rectangle((4,5,26,20),fill=roof,outline=edge)
        d.line((5,20,25,20),fill=wall,width=2)
        d.line((4,21,26,21),fill=edge)
        d.line((4,27,26,27),fill=2)
        for x in (6,11,16,21):
            d.rectangle((x,23,x+2,25),fill=2)
            d.line((x,23,x+1,23),fill=14 if theme=='glass' else 6)
        if theme=='glass':
            for x in (9,15,21):d.line((x,7,x,19),fill=12)
            d.line((6,16,15,7),fill=14,width=2)
            d.line((14,18,23,9),fill=14)
        elif theme=='industrial':
            for x in (6,13,20):
                d.polygon([(x,8),(x+4,6),(x+5,8),(x+5,18),(x,18)],fill=6)
                d.line((x,8,x,18),fill=3);d.line((x+1,8,x+1,17),fill=7)
            for x in (7,16):
                d.rectangle((x,23,x+6,27),fill=2)
                for y in (24,26):d.line((x+1,y,x+5,y),fill=5)
        else:
            d.rectangle((8,8,14,13),fill=wall,outline=edge)
            d.rectangle((18,12,22,16),fill=2,outline=6)
            d.line((19,13,21,13),fill=5)
        if name=='factory':
            for x in (9,17):
                d.rectangle((x,5,x+3,15),fill=3)
                d.ellipse((x-1,3,x+4,8),fill=1,outline=15)
        if name=='checkpoint':
            d.line((5,28,24,28),fill=15,width=2)
            for x in (8,14,20):d.line((x,27,x+1,28),fill=1)
    elif theme=='tank':
        for x,y in ((5,7),(15,13)):
            d.rectangle((x,y+4,x+10,y+13),fill=3)
            d.ellipse((x,y,x+10,y+9),fill=6,outline=2)
            d.arc((x+1,y+1,x+9,y+8),155,305,fill=7)
            d.point((x+5,y+3),fill=4)
    elif theme=='cargo':
        for x,y,c in ((5,7,10),(16,7,13),(6,17,15),(17,17,9)):
            d.rectangle((x,y,x+8,y+6),fill=c,outline=2)
            d.line((x+1,y+1,x+7,y+1),fill=7)
            for xx in (x+3,x+6):d.line((xx,y+2,xx,y+5),fill=3)
    else:
        d.rectangle((6,9,24,25),fill=3,outline=2)
        d.line((9,22,21,7),fill=2,width=3)
        d.arc((8,4,25,19),185,355,fill=7,width=3)
        d.line((12,15,21,8),fill=14)
    broken=im.copy();d=D(broken)
    d.polygon([(4,11),(11,5),(25,7),(28,18),(24,27),(10,28),(4,22)],fill=2)
    d.polygon([(6,13),(13,7),(23,10),(25,18),(21,25),(9,24)],fill=1)
    if theme=='tank':
        for x,y in ((5,8),(15,15)):
            d.arc((x,y,x+11,y+10),45,315,fill=6,width=2)
            d.line((x+7,y+2,x+5,y+7,x+9,y+10),fill=9)
    elif theme=='cargo':
        for x,y,c in ((6,8,10),(17,9,13),(8,20,15),(20,19,9)):
            d.polygon([(x,y),(x+7,y+1),(x+6,y+5),(x+1,y+4)],fill=c)
            d.line((x+1,y,x+6,y+1),fill=7)
    elif theme=='mast':
        d.line((8,11,17,16,24,23),fill=6,width=2)
        d.arc((17,16,27,26),15,270,fill=7,width=2)
    else:
        wall=11 if theme in ('brick','guard') else 6
        d.line((5,21,5,7,24,7),fill=wall,width=2)
        d.polygon([(8,10),(20,12),(16,19),(8,17)],fill=9 if theme=='brick' else 4)
        d.line((9,11,17,13),fill=wall)
        d.line((15,25,25,13),fill=5,width=2)
        if theme=='glass':
            d.line((8,20,11,18,12,21),fill=14)
    for x,y in ((7,19),(23,21),(13,25),(20,9),(5,15)):
        d.point((x,y),fill=10 if theme=='brick' else 6)
    for y in range(32):
        for x in range(32):
            if min(x,y,31-x,31-y)<2:broken.putpixel((x,y),im.getpixel((x,y)))
    PAIRS.append((name,im,broken))
    for row in range(2):
        for col in range(2):
            key=f'{name}_{col}_{row}'
            box=(col*16,row*16,col*16+16,row*16+16)
            add(key,'buildings',im.crop(box))
            if kind:
                WRECKS.append(dict(name=f'{name}_destroyed_{col}_{row}',of=key,kind=kind,
                    group=name,col=col,row=row,palette='buildings',pixels=hexrows(broken.crop(box))))


def hexrows(im):
    return [''.join(format(im.getpixel((x,y)),'x') for x in range(im.width)) for y in range(im.height)]


def roofs():
    for i in range(4):
        im=Image.new('L',(16,16),4 if i<2 else 9);d=D(im)
        roof,highlight=(5,7) if i<2 else (10,11)
        d.rectangle((0,0,15,10 if i%2 else 15),fill=roof)
        d.line((0,0,15,0),fill=highlight)
        for x in (1,8):
            d.polygon([(x,2),(x+5,1),(x+5,9 if i%2 else 15),
                       (x,10 if i%2 else 15)],fill=6 if i<2 else 11)
            d.line((x,2,x,9 if i%2 else 15),fill=3)
        if i%2:
            d.line((0,10,15,10),fill=highlight)
            d.rectangle((2,11,6,15),fill=2)
            d.rectangle((9,11,13,15),fill=2)
            for y in (12,14):
                d.line((3,y,5,y),fill=4);d.line((10,y,12,y),fill=4)
        name=f'hall{i}';add(name,'buildings',im)
        damaged=im.copy();d=D(damaged)
        d.polygon([(3,5),(9,3),(13,7),(11,12),(4,13)],fill=1)
        d.line((4,11,12,5),fill=6);d.line((6,5,11,11),fill=3)
        WRECKS.append(dict(name=name+'_destroyed',of=name,kind='hall',col=0,row=0,
                           palette='buildings',pixels=hexrows(damaged)))
        PAIRS.append((name,im,damaged))


def animations():
    for name,palette,period,count in (('fire','ruins',7,3),('smoke','buildings',9,3),
                                      ('beacon','buildings',18,2),('sign','buildings',12,3)):
        phases=[]
        for phase in range(count):
            im=Image.new('L',(16,16),3 if palette=='ruins' else 4);d=D(im)
            if name=='fire':
                d.polygon([(1,11),(4,4),(12,4),(15,10),(10,14),(3,14)],fill=2)
                d.line((3,12,9,9,12,12),fill=12,width=2)
                d.polygon([(4,11),(5+phase,6),(7,8),(8+phase,2),(10,7),(12,9),(10,12)],fill=13)
                d.polygon([(6,11),(8+phase,5),(9,9),(10,11)],fill=15)
                d.point((4+phase,4),fill=14)
            elif name=='smoke':
                d.rectangle((6,8,11,14),fill=2)
                d.ellipse((5,7,12,10),fill=1,outline=7)
                for j in range(3):
                    x=6+j+phase%2;y=(phase+2*j)%6
                    d.ellipse((x,y,x+3,y+2),fill=(5,6,3)[j])
            elif name=='beacon':
                d.rectangle((0,0,15,15),fill=13)
                d.line((3,0,3,15),fill=12)
                d.line((13,0,13,15),fill=12)
                d.rectangle((1,2,14,14),fill=12,outline=5)
                d.line((3,4,12,4),fill=14)
                d.rectangle((6,6,10,10),fill=8 if phase==0 else 15,outline=2)
                if phase:d.point((7,7),fill=7)
            else:
                d.rectangle((1,3,14,12),fill=2,outline=5)
                d.line((3,5,3,10,6,10),fill=(14,13,14)[phase])
                d.line((8,10,8,5,12,5,12,10,8,10),fill=(15,15,9)[phase])
                d.point((10,7),fill=14 if phase!=2 else 9)
            key=f'{name}_{phase}';add(key,palette,im);phases.append([key])
        ANIMS.append(dict(name=name,period=period,phases=phases))


def landmark(name):
    """A 48x48 city block with a roof, facade and cast shadow."""
    im=Image.new('L',(48,48),4);d=D(im)
    d.polygon([(7,11),(38,7),(45,14),(45,42),(16,45),(6,36)],fill=2)
    if name=='highrise':
        d.polygon([(5,9),(34,5),(41,12),(41,34),(35,40),(5,39)],fill=12)
        d.polygon([(6,9),(33,6),(39,12),(35,30),(6,32)],fill=13)
        d.line((6,31,6,10,33,6,39,12),fill=14,width=2)
        for x in (12,19,26,33):
            d.line((x,9,x,29),fill=12)
            d.line((x+1,32,x+1,37),fill=14)
        d.line((7,22,21,10),fill=14,width=3)
        d.line((20,28,35,15),fill=14,width=2)
        d.rectangle((18,12,28,19),fill=3,outline=6)
        d.line((19,13,26,13),fill=7)
        d.line((6,32,35,30),fill=2,width=2)
        for x in (8,14,20,26,32):
            d.rectangle((x,34,x+2,37),fill=13)
            d.point((x,34),fill=14)
    elif name=='citadel':
        d.polygon([(7,6),(37,6),(42,12),(42,35),(36,42),(9,42),(4,34),(4,12)],fill=2)
        d.polygon([(8,8),(36,8),(39,12),(39,33),(34,39),(10,39),(7,33),(7,12)],fill=5)
        d.line((7,31,7,12,9,8,35,8),fill=7,width=2)
        d.rectangle((12,12,34,30),fill=3,outline=6)
        d.rectangle((15,15,31,25),fill=12,outline=2)
        for x in (17,23,29):d.line((x,17,x,23),fill=14)
        d.rectangle((17,32,29,39),fill=2)
        for x in (9,33):
            d.rectangle((x,29,x+3,33),fill=15)
            d.point((x,29),fill=7)
        d.line((12,41,34,41),fill=8,width=2)
    else:
        d.rectangle((4,5,41,39),fill=8,outline=2)
        d.line((5,33,5,6,38,6),fill=11,width=3)
        d.polygon([(11,11),(34,8),(40,17),(35,33),(20,40),(9,28)],fill=1)
        d.polygon([(7,12),(24,15),(20,26),(8,23)],fill=10)
        d.line((8,13,21,16),fill=11)
        d.polygon([(29,16),(37,18),(35,30),(27,27)],fill=9)
        d.line((14,33,32,15),fill=6,width=2)
        d.line((18,38,35,27),fill=3,width=2)
        d.line((7,39,39,39),fill=10,width=2)
        for x in (9,16,24,32):d.rectangle((x,37,x+3,39),fill=1)
        for x,y in ((14,26),(24,31),(31,12),(34,34),(8,31)):
            d.line((x,y,x+3,y+1),fill=11)
            d.point((x,y+2),fill=15)
    for row in range(3):
        for col in range(3):
            add(f'{name}_{col}_{row}','buildings',im.crop((16*col,16*row,16*col+16,16*row+16)))


CROSS=(18,38,59,79,101,121,143,166,191,212,235,257,282,304,325)
SECTIONS=((0,96,'Vorstadt'),(96,184,'Industrie'),(184,280,'Innenstadt'),(280,375,'Festung'))


def make_map():
    road=[]
    for y in range(375):
        # Adjacent stretches overlap by three columns at the offsets.
        center=9 if y<39 else 10 if y<80 else 11 if y<167 else 9 if y<213 else 10
        west=any(a<=y<=b for a,b in ((0,38),(59,101),(121,166),(191,235),(257,304),(325,374)))
        east=any(a<=y<=b for a,b in ((18,59),(79,121),(143,191),(212,257),(282,325)))
        row=[abs(x-center)<=2 or (west and x in (3,4)) or (east and x in (16,17))
             or any(abs(y-c)<=1 for c in CROSS) or (336<=y<366 and 3<=x<=17)
             for x in range(21)]
        road.append(row)
    rows=[]
    for y in range(375):
        row=[]
        for x in range(21):
            if road[y][x]:
                mask=0
                for i,(xx,yy) in enumerate(((x,y+1),(x+1,y),(x,y-1),(x-1,y))):
                    if 0<=xx<21 and 0<=yy<375 and not road[yy][xx]:mask|=1<<i
                if 336<=y<366:
                    name=f'street{mask}' if mask else 'plaza'
                elif y in CROSS:
                    name='lane_h' if x not in (3,4,8,9,10,11,12,16,17) else 'crosswalk'
                    if y==143 and x in (5,6,7):name='bridge'
                elif not mask and x in (9,10,11) and y%2==0:
                    name='lane_v'
                elif not mask and x in (6,14) and (y//4)%4==1:
                    name='parking'
                else:name=f'street{mask}'
                if name=='street0' and (x+3*((y//12)%3))%19==0:name='asphalt_damage'
            else:
                # Broad paving tones unify a block instead of lining every
                # column with little debris marks.
                band=(y//12)%3
                k=3 if (x//6+band+(y>=184))%3==0 else 0
                name=f'ruins{k}'
            row.append(name)
        rows.append(row)

    def free(x,y,w,h):
        return (1<=x and x+w<=21 and 0<=y and y+h<=336 and
                all(rows[yy][xx].startswith('ruins') for yy in range(y,y+h)
                    for xx in range(x,x+w)))

    # Large silhouettes break up the small repeated buildings.
    for name,start,left in (
        ('collapse',10,True),('collapse',43,False),('collapse',70,True),
        ('collapse',113,False),('citadel',154,False),
        ('highrise',197,False),('highrise',220,True),('collapse',240,True),
        ('highrise',265,False),('citadel',289,True),('citadel',314,False),
    ):
        candidates=((x,y) for y in range(start,start+6)
                    for x in (range(1,7) if left else range(18,12,-1)))
        position=next(((x,y) for x,y in candidates if free(x,y,3,3)),None)
        if position is None:continue
        x,y=position
        for r in range(3):
            for c in range(3):
                tile='beacon_0' if name=='highrise' and (c,r)==(1,1) else f'{name}_{c}_{r}'
                rows[y+2-r][x+c]=tile

    for start,left in ((23,True),(49,False),(84,True),(194,False),(269,True)):
        candidates=((x,y) for y in range(start,start+5)
                    for x in (range(1,7) if left else range(18,12,-1)))
        position=next(((x,y) for x,y in candidates if free(x,y,2,3)),None)
        if position:
            x,y=position
            for dy,pair in enumerate(((6,8),(8,7),(7,8))):
                for dx,t in enumerate(pair):rows[y+dy][x+dx]=f'ruins{t}'

    # Stamp whole buildings only into block interiors; row 0 faces north.
    schemes=(
        ('tenement','checkpoint','tenement','warehouse','checkpoint','tenement'),
        ('factory','tank','depot','pallet','warehouse','factory','hall0'),
        ('tower','tower','radar','tenement','tower','hall2'),
        ('hangar','factory','checkpoint','tank','radar','hall1'),
    )
    for y in range(6,334,6):
        section=0 if y<96 else 1 if y<184 else 2 if y<280 else 3
        choices=schemes[section]
        for x in (1,5,7,12,14,18):
            if (not free(x,y,2,2) or (x+y//6)%7==0 or
                any(rows[yy][xx] in ('ruins6','ruins7','ruins8')
                    for yy in (y,y+1) for xx in (x,x+1))):continue
            name=choices[(x*3+y//6)%len(choices)]
            for r in range(2):
                for c in range(2):
                    rows[y+1-r][x+c]=f'hall{2*int(name=="hall2")+r}' if name.startswith('hall') else f'{name}_{c}_{r}'
            if name in ('factory','warehouse') and (x+y//6)%3==0:
                for start in (x+2,x-2):
                    if free(start,y,2,2):
                        for r in range(2):
                            for c in range(2):rows[y+1-r][start+c]=f'hall{r}'
                        break
    for y in range(10,336,13):
        for x in (2,6,14,19):
            if free(x,y,1,1) and (x+y)%3==0:rows[y][x]='ruins9'
    for y in range(13,336,17):
        for x in (2,6,14,19):
            if free(x,y,1,1) and rows[y][x] in ('ruins0','ruins3') and (x+y)%5==0:
                rows[y][x]='ruins5' if y>=96 else 'ruins1'
    # Street details stay in the existing collision palette.
    for y in range(1,335):
        for x in range(1,20):
            tile=rows[y][x]
            if not tile.startswith('street'):continue
            for direction,(xx,yy) in enumerate(((x,y+1),(x+1,y),(x,y-1),(x-1,y))):
                if tile==f'street{1<<direction}' and rows[yy][xx].startswith('collapse'):
                    rows[y][x]=f'rubble_curb{direction}'
                    break
            else:
                if tile=='street8' and y%24==9 and x%3==0:rows[y][x]='lamp_curb'
                elif tile=='street2' and y%48==15 and x%4==2:rows[y][x]='wreck_curb'
                elif tile=='street1' and rows[y+1][x].startswith(('tower','highrise','citadel')):
                    rows[y][x]='shadow_n'
                elif tile=='street8' and rows[y][x-1].startswith(('tower','highrise','citadel')):
                    rows[y][x]='shadow_w'
    for y in range(7,336,7):
        for x in (2,6,8,13,15,19):
            if not free(x,y,1,1):continue
            names=('fire_0','fire_0','smoke_0','fire_0') if y<184 else ('beacon_0','sign_0','fire_0','beacon_0')
            if (x+y)%3:rows[y][x]=names[(x*5+y)%4]
    # Ensure all four phase-zero tiles are represented, including chimney smoke.
    assert all(any(a['phases'][0][0] in row for row in rows) for a in ANIMS)
    return [[ID[name] for name in row] for row in rows]


def sheet(path,items,columns,width,height,scale):
    board=Image.new('RGB',(columns*width,math.ceil(len(items)/columns)*height),(23,28,34))
    d=D(board)
    for i,(name,im) in enumerate(items):
        x=i%columns*width+4;y=i//columns*height+3
        d.text((x,y),name,fill='white')
        board.paste(im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST),(x,y+17))
    board.save(path)


def main():
    streets();neighborhood();street_details()
    for entry in (
        ('tenement',None,'brick'),('warehouse','hangar','industrial'),
        ('factory','bunker','industrial'),('tank','fuel','tank'),
        ('depot','depot','cargo'),('pallet','crates','cargo'),
        ('radar','radar','mast'),('checkpoint','checkpoint','guard'),
        ('hangar','hangar','industrial'),('tower',None,'glass'),
    ):building(*entry)
    roofs();animations()
    for name in ('highrise','citadel','collapse'):landmark(name)
    assert len(TILES)<=126 and len(WRECKS)<=48
    OUT.mkdir(parents=True,exist_ok=True)
    save_json(OUT/'manifest.json',dict(palettes=PALETTE))
    save_json(OUT/'level-example.json',dict(tiles=META))
    save_json(OUT/'ground-targets.json',dict(schema=1,destroyed_tiles=WRECKS))
    save_json(OUT/'animations.json',dict(animations=ANIMS))
    binary=bytearray()
    for im in TILES:
        px=im.tobytes()
        binary.extend(px[i] | px[i+1]<<4 for i in range(0,256,2))
    (OUT/'terrain.ncm.bin').write_bytes(binary)
    rows=make_map()
    assert len(set(map(tuple,rows)))<=256,len(set(map(tuple,rows)))
    path=ROOT/'levels/level4.json'
    source=path.read_text(encoding='utf-8')
    key=re.search(r'"map"\s*:\s*',source)
    assert key
    start=key.end()
    _,end=json.JSONDecoder().raw_decode(source[start:])
    encoded='[\n'+',\n'.join('    '+json.dumps(row) for row in rows)+'\n  ]'
    path.write_text(source[:start]+encoded+source[start+end:],encoding='utf-8',newline='\n')
    render=[rgb(im,t['palette']) for im,t in zip(TILES,META)]
    sheet(OUT/'terrain-sheet.png',[(f"{t['id']} {t['name']}",im)
          for t,im in zip(META,render)],8,116,54,2)
    sheet(OUT/'animation-phases.png',[(f"{a['name']} {i+1}",render[ID[p[0]]])
          for a in ANIMS for i,p in enumerate(a['phases'])],3,96,88,4)
    pairs=[]
    for name,intact,broken in PAIRS:
        pair=Image.new('RGB',(intact.width*2+2,intact.height),(23,28,34))
        pair.paste(rgb(intact,'buildings'),(0,0))
        pair.paste(rgb(broken,'buildings'),(intact.width+2,0))
        pairs.append((name,pair))
    sheet(OUT/'destroyed-sheet.png',pairs,4,141,87,2)
    overview=Image.new('RGB',(320,6000))
    for y,row in enumerate(rows):
        for x,t in enumerate(row[1:]):overview.paste(render[t],(x*16,(374-y)*16))
    overview.save(OUT/'level-overview.png',optimize=True)
    board=Image.new('RGB',(1312,1560),(23,28,34));d=D(board)
    for i,(lo,hi,label) in enumerate(SECTIONS):
        x=i*328+4;d.text((x,4),label,fill='white')
        board.paste(overview.crop((0,(375-hi)*16,320,(375-lo)*16)),(x,20))
    board.save(OUT/'level-sections.png',optimize=True)
    for name,start in (('vorstadt',38),('industrie',146),('innenstadt',196),('festung',289)):
        bottom=(375-start)*16
        overview.crop((0,bottom-200,320,bottom)).save(OUT/f'{name}-320x200.png')
    print(f'{len(TILES)} tiles, {len(WRECKS)} damaged variants, {len(set(map(tuple,rows)))} row patterns')


if __name__=='__main__':
    main()
