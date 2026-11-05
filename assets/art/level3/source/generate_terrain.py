"""Build the indexed Offshore terrain, destruction art, animations and map."""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'assets/art/level3/generated'
D = ImageDraw.Draw
PALETTES = {
    'water': '000000 101e38 142c51 1a3f66 1d5276 226b89 278299 3399a2 4cb0ae 79c4b4 b4dac3 e1f0da 253844 2e474f 769b8d 4b7384',
    'nature': '000000 3399a2 79c4b4 e1f0da c59b65 e1ba7e f0d499 a57a54 614f45 837160 a79378 2e513b 476f45 65884d 8dab59 383a37',
    'structures': '000000 192934 2e4652 45606c 5e7880 84969a a3b3ad d8dacf a38e62 d9b86a ebd8a5 8c3f37 c45d40 e99548 546a57 273c44',
}
PALETTES = {key:[list(bytes.fromhex(color)) for color in colors.split()]
            for key,colors in PALETTES.items()}
PALETTES['fixed_targets'] = json.loads(
    (ROOT/'assets/art/ground-targets/generated/ground-targets.json').read_text()
)['palettes']['fixed_targets']
TILES, META, IDS, WRECKS, PAIRS, ANIM = [], [], {}, [], [], []


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n', encoding='ascii', newline='\n')


def rgb(im, palette):
    result = Image.new('RGB', im.size)
    result.putdata([tuple(PALETTES[palette][v]) for v in im.tobytes()])
    return result


def tile(name, palette, im):
    assert name not in IDS and im.size == (16,16) and min(im.tobytes()) > 0
    IDS[name] = len(TILES)
    META.append(dict(id=len(TILES),name=name,palette=palette))
    TILES.append(im)
    return name


def split(name, palette, im):
    names=[]
    for row in range(im.height//16):
        for col in range(im.width//16):
            box=(col*16,row*16,col*16+16,row*16+16)
            names.append(tile(f'{name}_{col}_{row}',palette,im.crop(box)))
    return names


def current(x, y, salt=0):
    return ((x*13+y*7+salt*31) ^ (x*y*3) ^ (y*y*5)) % 41


def water(base, variant=0):
    im=Image.new('L',(16,16),base)
    d=D(im)
    for y in range(16):
        for x in range(16):
            n=current(x,y,variant)
            if n<4:d.point((x,y),fill=max(1,base-1))
            elif n>36:d.point((x,y),fill=base+1)
    for x,y,w in ((2,4,5),(9,10,4),(4,14,3)):
        dy=(variant%5)-2
        if 1<=y+dy<15:
            d.line((x,y+dy,x+w,y+dy-1),fill=min(10,base+1))
            if variant%3==0:d.point((x+2,y+dy),fill=min(11,base+2))
    return im


def blend(mask,x,y):
    a,b,c,d=[bool(mask&(1<<i)) for i in range(4)]
    return (a*(15-x)*(15-y)+b*x*(15-y)+c*(15-x)*y+d*x*y)/225


def seas():
    for base,prefix in ((2,'deep'),(4,'sea'),(7,'shelf')):
        for variant in range(4):
            tile(f'{prefix}{variant}','water',water(base,variant+base))
    tile('blue','water',water(3,3))
    for mask in range(1,16):
        im=water(4,mask)
        for y in range(16):
            for x in range(16):
                v=blend(mask,x,y)
                if v>.36:
                    color=5 if v<.52 else 6 if v<.72 else 7
                    im.putpixel((x,y),color+(current(x,y,mask)>35))
        tile(f'edge{mask}','water',im)
    for i in range(3):
        im=water(7,i);d=D(im)
        for x,y in ((4,5),(10,9),(7,12)):
            d.polygon([(x-3,y),(x,y-3),(x+3,y-2),(x+4,y+1),(x,y+2)],fill=14)
            d.line((x-2,y-1,x,y-3,x+2,y-2),fill=9 if i==0 else 8)
            if i==2:d.point((x,y),fill=10)
        tile(f'reef{i}','water',im)
    for i in range(2):
        im=water(7,i+7);d=D(im)
        d.polygon([(2,9),(6,4),(12,3),(14,6),(11,9),(4,12)],fill=9)
        d.line((3,9,6,5,12,4),fill=10)
        d.line((5,10,10,8,13,6),fill=8)
        tile(f'bank{i}','water',im)
        im=water(4,i);d=D(im)
        d.polygon([(0,8),(4,5),(11,4),(15,6),(15,10),(9,9),(3,12)],fill=12)
        d.line((0,8,4,6,11,5,15,6),fill=13)
        d.line((2,9,8,7,12,8),fill=15)
        tile(f'oil{i}','water',im)
    for i in range(2):
        im=water(4,i);d=D(im)
        for side in (-1,1):
            d.line([(8+side*(1+i),1),(8+side*3,5),(8+side*5,10),(8+side*7,15)],fill=8)
            for y,x in ((6,3),(12,6)):d.point((8+side*x,y),fill=10)
        tile(f'wake{i}','water',im)
    im=water(5,4);d=D(im)
    d.line((0,12,15,4),fill=15,width=3);d.line((0,11,15,3),fill=6)
    tile('subsea_pipe','water',im)
    im=water(5,4);d=D(im)
    d.ellipse((4,6,12,10),fill=6);d.ellipse((6,4,9,8),fill=11)
    d.point((8,4),fill=14)
    tile('buoy','water',im)
    phases=[]
    for phase in range(3):
        names=[]
        for band in range(2):
            im=water(4+2*band,band+4);d=D(im)
            for x,y in ((3,5),(9,11),(12,3)):
                x=(x+phase*2)%13+1
                d.line((x-1,y,x+1,y),fill=9+int(phase==1))
                d.point((x,y),fill=11 if phase==1 else 10)
            names.append(tile(f'glint_{phase}_{band}','water',im))
        phases.append(names)
    ANIM.append(dict(name='glitter',period=12,phases=phases))


def island():
    # The wet fringe shares RGB entries with shelf water. Land itself is never
    # marked water, so even the small beach corners stay out of ship routes.
    for mask in range(1,16):
        im=Image.new('L',(16,16),1);d=D(im)
        for y in range(16):
            for x in range(16):
                v=blend(mask,x,y)
                if v>.72: i=5+(current(x,y,mask)>35)
                elif v>.53: i=5
                elif v>.45: i=6
                elif v>.39: i=3 if current(x,y,mask)%4 else 2
                elif v>.32: i=2
                else: i=1
                d.point((x,y),fill=i)
        tile(f'island{mask}','nature',im)
    for kind in ('grass','palm','rocks','palm_grove'):
        im=Image.new('L',(16,16),5);d=D(im)
        d.polygon([(2,6),(6,3),(12,4),(14,9),(11,13),(4,13)],fill=12)
        for x,y in ((3,7),(5,5),(10,6),(11,11),(5,11),(8,8)):
            d.line((x,y,x+1,y-1),fill=13)
        if kind in ('palm','palm_grove'):
            for x,y in (((7,7),) if kind=='palm' else ((5,6),(10,9))):
                d.line((x,y,x-1,y+5),fill=8,width=2)
                for dx,dy in ((-4,-1),(-3,-3),(0,-4),(4,-1),(3,3),(-1,3)):
                    d.line((x,y,x+dx,y+dy),fill=11,width=2)
                    d.line((x,y,x+dx,y+dy),fill=13)
                d.point((x,y),fill=14)
        if kind=='rocks':
            for x,y in ((3,7),(9,5),(9,11)):
                d.polygon([(x-2,y+1),(x-1,y-3),(x+2,y-2),(x+4,y+1),(x+1,y+3)],fill=8)
                d.polygon([(x-1,y-3),(x+2,y-2),(x+1,y),(x-2,y+1)],fill=10)
        tile(kind,'nature',im)


def decking():
    for name in ('deck','deck_l','deck_r','deck_top','deck_bottom','pier','quay','helipad','solar','bollards'):
        im=Image.new('L',(16,16),4);d=D(im)
        d.rectangle((0,1,15,14),fill=5)
        for x in (1,7,13):
            d.point((x,4),fill=6)
            d.point((x+1,11),fill=3)
        if name.startswith('deck_') or name=='quay':
            side={'deck_l':(0,0,2,15),'deck_r':(13,0,15,15),
                  'deck_top':(0,0,15,2),'deck_bottom':(0,13,15,15),'quay':(0,0,2,15)}[name]
            d.rectangle(side,fill=2)
            if name in ('deck_l','quay'):
                d.line((2,0,2,15),fill=9)
                for y in (1,8,14):d.rectangle((0,y,2,y+1),fill=1)
            elif name=='deck_r':d.line((13,0,13,15),fill=8)
            elif name=='deck_top':d.line((0,2,15,2),fill=9)
            else:d.line((0,13,15,13),fill=8)
        elif name=='pier':
            d.rectangle((4,0,11,15),fill=3)
            for y in (2,7,12):d.line((4,y,11,y),fill=7)
        elif name=='helipad':
            d.rectangle((1,1,14,14),fill=3,outline=9)
            d.line((5,5,5,10),fill=10);d.line((10,5,10,10),fill=10)
            d.line((5,7,10,7),fill=10)
        elif name=='solar':
            d.rectangle((1,2,14,13),fill=2,outline=7)
            for x in (4,8,12):d.line((x,3,x,12),fill=4)
            d.line((2,7,13,7),fill=5)
        elif name=='bollards':
            for x in (3,11):
                d.rectangle((x,4,x+2,10),fill=2);d.point((x,4),fill=9)
        tile(name,'structures',im)
    phases=[]
    for phase in range(3):
        im=Image.new('L',(32,32),3);d=D(im)
        d.rectangle((0,0,31,31),outline=2,width=2)
        d.ellipse((6,6,26,26),fill=4,outline=2)
        d.line((16,17,16,25),fill=6,width=3)
        for blade in range(3):
            a=math.radians(blade*120+phase*40)
            def point(r,p):
                return (round(16+r*math.cos(a+p)),round(15+r*math.sin(a+p)))
            d.polygon([point(2,0),point(9,-.22),point(14,0),point(9,.25)],fill=7)
            d.line([point(2,0),point(13,0)],fill=10)
        d.ellipse((14,13,18,17),fill=5,outline=7)
        d.point((15,14),fill=10)
        phases.append(split(f'turbine_{phase}','structures',im))
    ANIM.append(dict(name='turbine',period=6,phases=phases))
    for name,period,count in (('flare',7,3),('beacon',16,2)):
        phases=[]
        for phase in range(count):
            im=Image.new('L',(16,16),5);d=D(im)
            d.rectangle((5,7,10,13),fill=2)
            d.line((5,8,5,13),fill=7)
            d.rectangle((6,6,9,8),fill=1)
            if name=='flare':
                d.polygon([(6,7),(4+phase,3),(7,4),(8+phase,0),(10,4),(11,6),(9,8)],fill=12)
                d.polygon([(7,6),(8+phase,2),(9,6),(8,7)],fill=10)
            else:
                d.ellipse((5,3,10,8),fill=11 if phase==0 else 13,outline=2)
                if phase:d.point((7,4),fill=10)
            phases.append([tile(f'{name}_{phase}','structures',im)])
        ANIM.append(dict(name=name,period=period,phases=phases))


def hexrows(im):
    return [''.join(format(im.getpixel((x,y)),'x') for x in range(im.width))
            for y in range(im.height)]


def building(name,kind):
    im=Image.new('L',(32,32),5);d=D(im)
    d.polygon([(5,8),(24,6),(28,22),(25,27),(8,28)],fill=3)
    if name in ('drill','crane','mast'):
        d.rectangle((7,8,24,24),fill=4,outline=2)
        if name=='drill':
            d.polygon([(8,24),(14,4),(18,4),(24,24)],fill=1)
            for y in (9,13,17,21):d.line((13-(y-9)//3,y,19+(y-9)//3,y),fill=9,width=2)
            d.line((8,24,14,5,18,5,24,24),fill=10)
            d.line((11,19,20,15,13,12,18,8),fill=12)
        elif name=='crane':
            d.line((10,23,16,13,26,6),fill=1,width=5)
            d.line((9,22,15,12,26,5),fill=9,width=3)
            d.line((10,22,16,12,25,6),fill=10)
            d.line((26,7,25,18,22,18),fill=2)
        else:
            d.line((9,23,20,7),fill=2,width=3)
            d.arc((8,4,26,18),175,355,fill=7,width=3)
            d.line((12,15,22,8),fill=6);d.point((21,7),fill=12)
    elif name=='tank':
        d.rectangle((6,10,25,23),fill=2)
        d.ellipse((6,15,25,26),fill=3)
        d.ellipse((6,5,25,20),fill=6,outline=2)
        d.arc((7,6,24,19),155,325,fill=7,width=2)
        d.rectangle((13,9,18,13),fill=4)
        d.line((23,16,23,25),fill=9)
    elif name=='lighthouse':
        d.ellipse((9,7,23,23),fill=7,outline=3)
        d.ellipse((11,7,22,18),fill=11,outline=2)
        d.ellipse((13,9,19,15),fill=10)
        d.line((10,18,21,21),fill=6)
    elif name=='cargo':
        for x,y,c in ((5,7,12),(16,7,14),(8,17,9),(19,17,11)):
            d.rectangle((x,y,x+7,y+7),fill=c,outline=2)
            d.line((x+1,y+1,x+6,y+1),fill=10)
            d.line((x+3,y+2,x+3,y+6),fill=3)
    else:
        d.rectangle((5,6,26,24),fill=3,outline=2)
        d.rectangle((6,7,25,19),fill=6,outline=7)
        if name=='command':
            d.rectangle((9,9,22,16),fill=2,outline=5)
            d.line((10,10,21,10),fill=7)
            for x in (12,16,20):d.point((x,13),fill=9)
        else:
            for y in (9,12,15,18):d.line((7,y,24,y),fill=4)
        d.rectangle((9,20,20,24),fill=2);d.line((9,20,20,20),fill=9)
    wreck=im.copy();d=D(wreck)
    d.polygon([(5,10),(12,5),(24,7),(28,16),(24,25),(13,28),(5,23)],fill=2)
    d.ellipse((7,9,24,25),fill=1)
    # Preserve a recognizable silhouette in the wreck, plus local spill/debris.
    if name in ('drill','crane','mast'):
        d.line((7,20,16,15,23,23,27,21),fill=9 if name!='mast' else 6,width=2)
        d.line((10,22,16,16,20,20),fill=7)
        if name=='mast':d.arc((18,18,27,26),10,245,fill=7,width=2)
        else:d.line((13,16,17,22),fill=12)
    elif name in ('tank','lighthouse'):
        d.arc((7,7,24,24),35,305,fill=7,width=3)
        d.line((15,8,14,14,19,16,15,22),fill=11 if name=='lighthouse' else 6)
        d.line((20,21,26,25,29,24),fill=15,width=2)
    elif name=='cargo':
        for x,y in ((6,9),(18,8),(9,20),(21,19)):
            d.polygon([(x,y),(x+6,y+1),(x+5,y+5),(x+1,y+4)],fill=12)
            d.line((x+1,y,x+5,y+1),fill=9)
    else:
        d.line((5,21,5,7,24,7),fill=7,width=2)
        d.polygon([(8,9),(20,12),(16,19),(7,16)],fill=4)
        d.line((9,11,17,13),fill=6)
        d.line((16,24,25,12),fill=6,width=2)
    rng=random.Random(sum(map(ord,name)))
    for _ in range(12):
        x,y=rng.randrange(5,27),rng.randrange(6,27)
        if wreck.getpixel((x,y)) in (1,2):d.point((x,y),fill=rng.choice((4,6,11,13)))
    for y in range(32):
        for x in range(32):
            if min(x,y,31-x,31-y)<2:wreck.putpixel((x,y),im.getpixel((x,y)))
    names=split(name,'structures',im)
    PAIRS.append((name,im,wreck))
    for row in range(2):
        for col in range(2):
            cell=names[row*2+col]
            WRECKS.append(dict(name=f'{name}_destroyed_{col}_{row}',of=cell,
                palette='structures',kind=kind,group=name,col=col,row=row,
                pixels=hexrows(wreck.crop((col*16,row*16,col*16+16,row*16+16)))))


def hall():
    for i in range(3):
        im=Image.new('L',(16,16),4);d=D(im)
        for y in range(0,16,4):d.line((0,y,15,y),fill=6)
        d.line((0,0,0,15),fill=2);d.line((1,0,1,15),fill=5)
        if i==1:d.rectangle((4,4,11,11),fill=3,outline=7)
        if i==2:d.line((4,8,12,8),fill=9,width=2)
        broken=im.copy();d=D(broken)
        d.polygon([(3,5),(8,3),(13,6),(11,12),(4,13)],fill=1)
        d.line((3,11,12,4),fill=5,width=2);d.line((5,5,11,11),fill=3,width=2)
        d.point((8,7),fill=12)
        name=tile(f'hall{i}','structures',im)
        PAIRS.append((name,im,broken))
        WRECKS.append(dict(name=name+'_destroyed',of=name,palette='structures',
                           kind='hall',col=0,row=0,pixels=hexrows(broken)))


def make_map():
    rows=[]
    for y in range(375):
        band=(y//16)%5
        line=[]
        for x in range(21):
            n=(x*7+band*11+(x*band)%13)%29
            edge=min(x,20-x)
            if n==0 and edge>=4: name=f'glint_0_{band%2}'
            elif edge<1+((band+x//8)%3) and n%5!=0: name=f'deep{n%4}'
            elif edge<5 and n%4!=0: name='blue'
            else: name=f'sea{n%4}'
            line.append(IDS[name])
        rows.append(line)

    def put(x,y,name):
        assert 0<=x<=20 and 0<=y<375
        rows[y][x]=IDS[name]

    def mask_at(x,y,field):
        return sum(1<<i for i,(a,b) in enumerate(
            ((x,y+1),(x+1,y+1),(x,y),(x+1,y))) if field(a,b))

    def reef(xc,yc,rx,ry,land=False):
        def oval(x,y,scale=1):
            return ((x-xc)/(rx*scale))**2+((y-yc)/(ry*scale))**2<1
        for y in range(max(0,int(yc-ry)-1),min(375,int(yc+ry)+2)):
            for x in range(max(1,int(xc-rx)-1),min(21,int(xc+rx)+2)):
                mask=mask_at(x,y,oval)
                if not mask:continue
                if mask==15:
                    q=(x+2*(y//5))%9
                    if q<4:name=f'reef{q%3}'
                    elif q<6:name=f'bank{q%2}'
                    elif q==8:name='glint_0_1'
                    else:name=f'shelf{q%4}'
                else:name=f'edge{mask}'
                if land and x not in (9,10,11):
                    land_mask=mask_at(x,y,lambda a,b:oval(a,b,.55))
                    if land_mask:
                        name=f'island{land_mask}'
                        if land_mask==15 and (x+y)%3:
                            name=('grass','palm','rocks','palm_grove')[(x+y)%4]
                put(x,y,name)

    def stamp(name,x,y):
        for r in range(2):
            for c in range(2):put(x+c,y+1-r,f'{name}_{c}_{r}')

    def platform(x,y,w,h):
        for dy in range(h):
            for dx in range(w):
                name='deck'
                if dx==0:name='deck_l'
                elif dx==w-1:name='deck_r'
                elif dy==0:name='deck_bottom'
                elif dy==h-1:name='deck_top'
                put(x+dx,y+dy,name)

    for args in ((5,18,4.5,8,True),(16,39,5.0,9,True),(5,56,4.5,7,False),
                 (16,76,4.5,8,True),(4,86,3.5,6,True),(15,101,4,7,False),
                 (5,197,4.5,7,True),(16,254,4,8,True),(5,276,4,6,False)):
        reef(*args)
    stamp('lighthouse',4,17)
    stamp('mast',15,39)
    for x,y in ((12,24),(7,43),(18,64),(7,88),(12,185),(8,268)):
        put(x,y,'buoy')
    for x,y in ((2,109),(13,127),(3,148),(14,163)):
        platform(x,y,5,7+(x%3))
        stamp('drill',x+1,y+4)
        stamp('tank',x+2,y+1)
        put(x+3,y+5,'flare_0');put(x+1,y+2,'helipad')
        if x%2:
            put(x,y+3,'pier')
            put(x,y+4,'bollards')
        else:
            put(x+4,y+2,'pier')
            put(x+4,y+3,'bollards')
        for dx in range(1,4):
            put(x+dx,y-1,f'oil{dx%2}')
        for dy in (1,2,3,4):
            put(x-1,y+dy,'subsea_pipe')
    platform(13,203,7,8)
    stamp('command',14,207);stamp('mast',17,206)
    for x in range(14,19):put(x,204,'solar')
    put(18,209,'beacon_0');put(14,205,'helipad')
    platform(2,214,6,6)
    stamp('quarters',3,216);stamp('cargo',5,216)
    put(3,218,'beacon_0')
    for x,y in ((2,228),(6,230),(3,237),(6,242),(13,230),(17,232),
                (13,239),(17,242),(14,247)):
        stamp('turbine_0',x,y)
    for y in (227,235,246):
        for x in (2,4,6,13,15,17):put(x,y,'buoy')
    platform(1,283,6,42)
    platform(14,290,7,44)
    for y0,y1 in ((285,296),(304,316),(320,324)):
        for y in range(y0,y1):put(7,y,'deck_r')
    for y0,y1 in ((291,303),(309,320),(323,333)):
        for y in range(y0,y1):put(13,y,'quay')
    for x,y in ((2,289),(15,299),(3,308),(17,322)):
        stamp('cargo',x,y)
        stamp('crane',x+2,y+3)
    for x,y in ((3,298),(15,307),(4,318),(18,327)):
        stamp('tank',x,y)
    for x0,y0,w,h in ((2,303,4,4),(15,313,5,5),(2,320,4,3),(15,329,5,4)):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):put(x,y,f'hall{(x+y)%3}')
    stamp('command',17,292);stamp('quarters',4,284)
    for x,y in ((7,294),(7,311),(13,296),(13,321)):put(x,y,'bollards')
    for x,y in ((6,287),(19,303),(6,316),(14,325)):put(x,y,'helipad')
    for x0,y0,length in ((5,93,8),(12,116,8),(8,178,7),(12,217,7),
                          (8,282,9),(12,304,11),(8,324,10),(13,337,12)):
        for y in range(y0,y0+length):
            x=x0+(y-y0)//6
            if META[rows[y][x]]['palette']=='water':put(x,y,f'wake{y%2}')
    assert all(META[row[x]]['palette']=='water' for row in rows for x in (9,10,11))
    assert all(META[t]['palette']=='water' for row in rows[336:352] for t in row)
    return rows


def sheet(name, items, columns, cell, scale):
    width,height=cell
    im=Image.new('RGB',(columns*width,math.ceil(len(items)/columns)*height),(20,29,37))
    d=D(im)
    for i,(label,art) in enumerate(items):
        x=(i%columns)*width+3;y=(i//columns)*height+3
        d.text((x,y),label,fill='white')
        im.paste(art.resize((art.width*scale,art.height*scale),Image.Resampling.NEAREST),(x,y+16))
    im.save(OUT/name)


def main():
    seas();island();decking()
    for name,kind in (('drill','fuel'),('crane','depot'),('mast','radar'),('tank','fuel'),
                      ('lighthouse','checkpoint'),('cargo','crates'),('command','bunker'),
                      ('quarters','hangar')):
        building(name,kind)
    hall()
    assert len(TILES)<=128 and len(WRECKS)<=48
    OUT.mkdir(parents=True,exist_ok=True)
    binary=bytearray()
    for im in TILES:
        pixels=im.tobytes()
        binary.extend(pixels[i] | pixels[i+1]<<4 for i in range(0,256,2))
    (OUT/'terrain.ncm.bin').write_bytes(binary)
    write(OUT/'manifest.json',dict(palettes=PALETTES))
    write(OUT/'level-example.json',dict(tiles=META))
    write(OUT/'animations.json',dict(animations=ANIM))
    write(OUT/'ground-targets.json',dict(schema=1,destroyed_tiles=WRECKS))
    rows=make_map()
    level=dict(format='shootermega65-level-1',name='Operation Offshore',
        tileset='assets/art/level3/generated',ground_targets='assets/art/level3/generated',
        scroll_speed=.5,map='ROWS',paths={},formations={},events=[
          dict(row=188,type='shop',id='mid'),dict(row=352,type='boss'),
          dict(row=368,type='shop',id='end'),dict(row=375,type='end')])
    path=ROOT/'levels/level3.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(level,indent=2).replace('"ROWS"',
        '[\n'+',\n'.join('    '+json.dumps(row) for row in rows)+'\n  ]')+'\n',encoding='ascii',newline='\n')
    render=[rgb(im,t['palette']) for im,t in zip(TILES,META)]
    sheet('terrain-sheet.png',[(f"{t['id']} {t['name']}",im)
          for t,im in zip(META,render)],8,(110,53),2)
    phases=[]
    for anim in ANIM:
        for phase,names in enumerate(anim['phases']):
            side=2 if len(names)==4 else len(names)
            art=Image.new('RGB',(16*side,16*math.ceil(len(names)/side)))
            for i,name in enumerate(names):art.paste(render[IDS[name]],((i%side)*16,(i//side)*16))
            phases.append((f"{anim['name']} {phase+1}",art))
    sheet('animation-phases.png',phases,3,(112,120),3)
    pairs=[]
    for name,normal,broken in PAIRS:
        pair=Image.new('RGB',(normal.width*2+2,normal.height),(20,29,37))
        pair.paste(rgb(normal,'structures'),(0,0));pair.paste(rgb(broken,'structures'),(normal.width+2,0))
        pairs.append((name,pair))
    sheet('destroyed-sheet.png',pairs,4,(142,86),2)
    overview=Image.new('RGB',(320,6000))
    for y,row in enumerate(rows):
        for x,tid in enumerate(row[1:]):
            overview.paste(render[tid],(x*16,(374-y)*16))
    overview.save(OUT/'level-overview.png',optimize=True)
    board=Image.new('RGB',(4*328,1580),(20,29,37));d=D(board)
    sections=((0,96,'01 Offene See'),(96,184,'02 Oelfeld'),
              (184,280,'03 Forschung und Windpark'),(280,375,'04 Marinestuetzpunkt'))
    for i,(lo,hi,label) in enumerate(sections):
        x=i*328+4;d.text((x,5),label,fill='white')
        board.paste(overview.crop((0,(375-hi)*16,320,(375-lo)*16)),(x,24))
    board.save(OUT/'level-sections.png',optimize=True)
    print(f'{len(TILES)} terrain tiles, {len(WRECKS)} ruined tiles, {len(set(map(tuple,rows)))} distinct rows')


if __name__=='__main__':
    main()
