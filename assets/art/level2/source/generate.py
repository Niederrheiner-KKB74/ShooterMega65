import json, math, random
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'assets/art/level2/generated'
BOSS = ROOT / 'assets/art/boss-level2/generated'
P = {
 'nature': ['000000','442c26','694032','895439','ab6c43','c08853','d39b5f','dfac70','efc184','f6d49d','985c3d','b9804d','53604a','78804f','98994f','403e34'],
 'water': ['000000','173940','20535a','277177','398c86','53a49a','82b9a1','c3d3a6','694032','895439','ab6c43','c08853','d39b5f','dfac70','efc184','b9804d'],
 'structures': ['000000','2e2727','49423e','635950','81766a','a69b86','c6bd9c','e9d9a8','277177','dfac70','a45235','d67c40','f2b95e','74533d','452c29','9d7454'],
}
P = {k:[list(bytes.fromhex(c)) for c in v] for k,v in P.items()}
P['fixed_targets'] = json.loads((ROOT/'assets/art/ground-targets/generated/ground-targets.json').read_text())['palettes']['fixed_targets']
tiles, meta, ids, damaged, pairs = [], [], {}, [], []
D = ImageDraw.Draw

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2)+'\n', encoding='ascii', newline='\n')

def raster(im, pal, alpha=False):
    out = Image.new('RGBA' if alpha else 'RGB', im.size)
    out.putdata([tuple(pal[i])+((255 if i else 0,) if alpha else ()) for i in im.tobytes()])
    return out

def add(name, pal, im):
    assert name not in ids and im.size == (16,16) and min(im.tobytes()) > 0
    ids[name] = len(tiles)
    meta.append(dict(id=len(tiles),name=name,palette=pal))
    tiles.append(im)
    return ids[name]

def material(x,y,seed=0):
    v = ((x*197+y*367+seed*691) ^ (x*y*53) ^ (x*x*17+y*y*19)) % 97
    return 6 if v < 8 else 8 if v > 88 else 7

def ground(seed=0, size=16):
    im=Image.new('L',(size,size))
    im.putdata([material(x,y,seed) for y in range(size) for x in range(size)])
    return im

# Tile corner order: NW, NE, SW, SE. Shared edges use the same interpolation.
def blend(mask,x,y):
    a,b,c,d=[int(bool(mask & (1<<i))) for i in range(4)]
    return (a*(15-x)*(15-y)+b*x*(15-y)+c*(15-x)*y+d*x*y)/225

for i in range(12):
    im=ground(i); d=D(im)
    if i in (3,4,5):
        d.line([(1,11),(5,8),(10,6),(14,6)],fill=11,width=2)
        d.line([(2,10),(6,7),(11,5),(14,5)],fill=8)
    elif i in (6,7,8):
        d.polygon([(3,11),(4,7),(8,3),(12,5),(13,10),(9,13)],fill=3)
        d.polygon([(4,8),(8,3),(12,5),(9,8)],fill=6)
        d.line((5,10,9,11,12,9),fill=4)
    elif i in (9,10,11):
        for x,y in [(4,5),(11,9),(7,13),(13,3)]:d.line((x,y,x+1,y),fill=11)
    add(f'sand{i}','nature',im)

for mask in range(1,16):
    im=ground(mask)
    for y in range(16):
        for x in range(16):
            v=blend(mask,x,y)
            if v>.78:
                seam=(y+x//4+(x//6)%2)%8
                i=3 if seam==0 else 6 if seam==1 else 4+int((x*3+y*5)%11==0)
            elif v>.65: i=2+int((x+y)%5==0)
            elif v>.52: i=3+int((x+2*y)%5==0)
            elif v>.43: i=5+int((x+y)%4==0)
            else: continue
            im.putpixel((x,y),i)
    add(f'cliff{mask}','nature',im)
    im=Image.new('L',(16,16))
    for y in range(16):
        for x in range(16):
            v=blend(mask,x,y)
            i=(2+(x+2*y)%9//4 if v>.72 else 4 if v>.54 else 7 if v>.44
               else 15 if v>.38 else {6:12,7:13,8:14}[material(x,y,mask)])
            if v>.8 and (x-2*y)%13==0:i=5
            im.putpixel((x,y),i)
    add(f'bank{mask}','water',im)

for i in range(4):
    im=ground(i); d=D(im)
    for x,y in [(5,5),(11,10)][:1+i%2]:
        d.line((x+1,y+2,x+4,y+5),fill=11,width=2)
        d.line((x,y,x-1,y+4),fill=3,width=2)
        for dx,dy in [(-4,-1),(-3,-3),(1,-4),(4,-2),(4,1),(0,3)]:
            d.line((x,y,x+dx,y+dy),fill=12,width=2)
            d.point((x+dx,y+dy),fill=13)
        d.point((x,y),fill=14)
    add(f'palm{i}','nature',im)

# Direction bits N E S W. Each connection reaches the same span at the edge.
for style in ('road','pipe'):
    for mask in range(1,16):
        im=Image.new('L',(16,16),9); d=D(im)
        if style=='road':
            segments=[(3,0,12,8),(8,3,15,12),(3,8,12,15),(0,3,8,12)]
            d.rectangle((3,3,12,12),fill=4)
            for i,box in enumerate(segments):
                if mask&(1<<i):d.rectangle(box,fill=4)
            for i,box in enumerate([(4,0,11,8),(8,4,15,11),(4,8,11,15),(0,4,8,11)]):
                if mask&(1<<i):d.rectangle(box,fill=3)
            d.rectangle((4,4,11,11),fill=3)
            for i,seg in enumerate([(7,0,7,3),(12,7,15,7),(7,12,7,15),(0,7,3,7)]):
                if mask&(1<<i):d.line(seg,fill=7)
        else:
            for i,(x,y) in enumerate([(7,0),(15,7),(7,15),(0,7)]):
                if mask&(1<<i):
                    d.line((7,7,x,y),fill=2,width=6)
                    d.line((7,7,x,y),fill=5,width=4)
                    d.line((6,6,x-int(i%2==0),y-int(i%2==1)),fill=7)
            d.rectangle((5,5,9,9),fill=4,outline=2);d.line((5,5,8,5),fill=7)
        add(f'{style}{mask}','structures',im)

for variant in ('bridge','bridge_end'):
    im=Image.new('L',(16,16),8 if variant=='bridge' else 9);d=D(im)
    d.rectangle((0,3,15,12),fill=2);d.rectangle((0,4,15,11),fill=4)
    for x in (1,5,9,13):d.line((x,4,x,11),fill=5)
    for y in (3,12):d.line((0,y,15,y),fill=6)
    for x in (2,10):d.line((x,7,x+3,7),fill=7)
    if variant=='bridge_end':d.line((7,3,7,12),fill=6)
    add(variant,'structures',im)
for name in ('yard','fence','gravel'):
    im=Image.new('L',(16,16),9 if name!='yard' else 5);d=D(im)
    if name=='fence':
        d.line((0,8,15,8),fill=2,width=3);d.line((0,7,15,7),fill=6)
        for x in (2,10):d.line((x,5,x,10),fill=4)
    else:
        for x,y in ((2,3),(9,5),(13,13),(5,11)):d.point((x,y),fill=4 if name=='yard' else 15)
    add(name,'structures',im)

def ruin(im,seed,rim=2):
    out=im.copy();d=D(out);w,h=im.size;r=random.Random(seed)
    d.polygon([(2,h//3),(w//3,2),(w-4,4),(w-3,h//2),(w-5,h-4),(5,h-3)],fill=13)
    d.polygon([(4,h//2),(w//3,4),(w-6,6),(w-4,h//2),(w-7,h-5),(6,h-5)],fill=14)
    for _ in range(w):
        x,y=r.randrange(3,w-4),r.randrange(3,h-4)
        d.line((x,y,x+r.randrange(1,4),y+r.randrange(0,2)),fill=r.choice([2,4,5,10,15]))
    d.line((4,h-5,w-5,4),fill=2,width=2)
    d.line((5,h-5,w-5,5),fill=5)
    for y in range(h):
        for x in range(w):
            if min(x,y,w-1-x,h-1-y)<rim:out.putpixel((x,y),im.getpixel((x,y)))
    return out

def building(name,kind,seed):
    im=Image.new('L',(32,32),9);d=D(im)
    d.polygon([(5,9),(26,7),(29,27),(8,29)],fill=13)
    if name in ('oiltank','chimney'):
        d.rectangle((6,10,25,23),fill=2);d.ellipse((6,14,25,27),fill=3)
        d.ellipse((6,5,25,20),fill=4,outline=2);d.ellipse((7,6,24,18),fill=6,outline=5)
        d.arc((8,7,23,17),175,310,fill=7,width=2)
        d.rectangle((13,8,19,14),fill=1 if name=='chimney' else 5,outline=4)
        d.line((24,17,24,26),fill=11);d.line((25,17,25,26),fill=2)
    elif name=='pump':
        d.rectangle((5,8,26,24),fill=4,outline=2)
        d.line((7,20,23,11),fill=2,width=5);d.line((7,18,23,9),fill=11,width=3)
        d.line((8,17,22,9),fill=12);d.rectangle((11,18,16,23),fill=6)
        d.line((22,15,26,15,26,27),fill=5,width=2)
    elif name=='mast':
        d.rectangle((5,5,25,25),fill=5,outline=3);d.line((9,22,22,6),fill=2,width=3)
        d.arc((6,5,25,20),185,357,fill=7,width=3);d.line((9,17,22,8),fill=6)
        d.point((22,6),fill=11)
    elif name=='crates':
        for x,y in ((5,7),(17,6),(9,18),(20,18)):
            d.rectangle((x,y,x+7,y+7),fill=10,outline=2)
            d.line((x,y,x+7,y,x+7,y+7),fill=12)
            d.line((x+1,y+6,x+6,y+1),fill=13)
    elif name=='tent':
        d.polygon([(4,23),(8,8),(22,6),(27,20),(22,25)],fill=6,outline=2)
        d.polygon([(12,9),(22,6),(27,20),(21,21)],fill=15)
        d.line((8,8,12,9,21,21,22,25),fill=7)
        d.polygon([(12,13),(16,21),(9,22)],fill=2)
    else:
        d.rectangle((4,6,26,26),fill=3,outline=2)
        d.rectangle((5,7,25,20),fill=5,outline=7)
        for y in (9,12,15,18):d.line((6,y,24,y),fill=4)
        d.rectangle((8,21,19,26),fill=2);d.line((9,21,18,21),fill=10)
        for x in (7,23):d.rectangle((x,8,x+2,11),fill=6)
        if name=='loading':d.line((22,19,22,27),fill=12,width=2)
        if name=='command':d.rectangle((11,10,19,14),fill=3,outline=6)
    wreck=ruin(im,seed)
    pairs.append((name,im,wreck))
    for row in range(2):
        for col in range(2):
            box=(16*col,16*row,16*(col+1),16*(row+1))
            key=f'{name}_{col}_{row}'
            add(key,'structures',im.crop(box))
            damaged.append(dict(name=f'{name}_destroyed_{col}_{row}',of=key,palette='structures',
                                kind=kind,group=name,col=col,row=row,
                                pixels=hexrows(wreck.crop(box),1)))

def hexrows(im,n):
    return [''.join(format(im.getpixel((x,y)),f'0{n}x') for x in range(im.width))
            for y in range(im.height)]

for seed,(name,kind) in enumerate([('tent','checkpoint'),('mast','radar'),('command','bunker'),
    ('crates','crates'),('oiltank','fuel'),('pump','fuel'),('workshop','hangar'),
    ('loading','depot'),('chimney','fuel')]):
    building(name,kind,seed)

for i in range(4):
    im=Image.new('L',(16,16),4);d=D(im)
    for y in (0,4,8,12):d.line((0,y,15,y),fill=5)
    d.line((0,0,0,15),fill=2);d.line((1,0,1,15),fill=6)
    if i==1:d.rectangle((4,3,12,12),fill=3,outline=6)
    if i==2:d.rectangle((5,3,10,13),fill=2);d.line((5,4,10,4),fill=7)
    if i==3:d.line((4,7,13,7),fill=10,width=2)
    name=f'hall{i}';add(name,'structures',im);wreck=ruin(im,50+i)
    pairs.append((name,im,wreck))
    damaged.append(dict(name=name+'_destroyed',of=name,palette='structures',kind='hall',
                        col=0,row=0,pixels=hexrows(wreck,1)))
im=Image.new('L',(16,16),4);d=D(im);d.rectangle((2,2,13,13),outline=7)
d.line((5,5,5,10),fill=12);d.line((10,5,10,10),fill=12);d.line((5,7,10,7),fill=12)
add('helipad','structures',im)
assert len(tiles)<=128 and len(damaged)<=48

def map_level():
    rows=[]
    for y in range(375):
        # Reuse every terrain row in pairs, keeping the level's row dictionary in budget.
        band=(y//2)%23
        line=[]
        for x in range(21):
            sand=((x*7+band*3)^(x*band))%13
            i=sand if sand<12 else 0
            if (y<96 or 184<=y<280) and i>=6 and (x+band)%4:i%=6
            line.append(ids[f'sand{i}'])
        rows.append(line)
    def put(x,y,name):rows[y][x]=ids[name]
    def patch(y0,y1,field,kind):
        # Map row 0 is south; image corners face north first.
        for y in range(y0,y1):
            for x in range(1,21):
                mask=sum(1<<i for i,(a,b) in enumerate([(x,y+1),(x+1,y+1),(x,y),(x+1,y)])
                         if field(a,b))
                if mask:put(x,y,f'{kind}{mask}')
    patch(74,197,lambda x,y: (x<4+2*math.sin(y/12) or x>17+2*math.sin(y/14))
          and 76<y<195,'cliff')
    def river(x,y):
        center=10+3.0*math.sin(y/17)+1.3*math.sin(y/7)
        return 95<y<184 and abs(x-center)<2.3+0.6*math.sin(y/8)
    patch(94,184,river,'bank')
    for y in (118,158):
        wet=[x for x in range(1,21) if meta[rows[y][x]]['palette']=='water']
        for x in range(min(wet)-2,max(wet)+3):
            put(x,y,'bridge' if x in wet else 'road10')
        put(min(wet)-3,y,'road2')
        put(max(wet)+3,y,'road8')
    def oasis(x,y):return ((x-10.5+.7*math.sin(y/4))/4.2)**2+((y-222)/15)**2<1
    patch(206,238,oasis,'bank')
    for y in range(201,242):
        for x in range(3,18):
            if (x*17+y*13)%19<2 and 1.1<((x-10.5)/5)**2+((y-222)/17)**2<2:
                if meta[rows[y][x]]['palette']=='nature':put(x,y,f'palm{(x+y)%4}')
    def place(name,x,y):
        for row in range(2):
            for col in range(2):put(x+col,y+1-row,f'{name}_{col}_{row}')
    for name,x,y in [('crates',5,54),('tent',14,72),('tent',4,205),('mast',15,213),
        ('command',14,239),('crates',6,245),('workshop',7,260),('loading',13,269)]:
        place(name,x,y)
    for y in range(279,347):
        put(10,y,'road5')
        for x in (2,19):put(x,y,'pipe5')
    for y in (288,306,326,345):
        for x in range(3,19):put(x,y,'road10' if x!=10 else 'road15')
    for y in (294,314,335):
        for x in range(3,19):put(x,y,'pipe10' if x!=10 else 'road5')
        put(2,y,'pipe7');put(19,y,'pipe13')
    for name,x,y in [('oiltank',4,290),('oiltank',6,290),('pump',13,290),('chimney',16,297),
        ('workshop',4,309),('loading',13,309),('crates',16,309),('oiltank',4,321),
        ('pump',7,321),('chimney',15,321),('command',5,337),('oiltank',15,337)]:
        place(name,x,y)
    for x0,y0,w,h in ((4,298,5,6),(13,315,5,5),(12,337,3,6),(4,327,5,6)):
        for y in range(y0,y0+h):
            for x in range(x0,x0+w):put(x,y,f'hall{(x+2*y)%4}')
    for y in (282,343):
        for x in range(3,18):
            if x not in (9,10,11):put(x,y,'fence')
    for x,y in ((15,282),(12,328),(5,318)):put(x,y,'helipad')
    # Straight approach to the broad, empty boss apron.
    for y in range(347,366):
        for x in range(3,18):put(x,y,'yard')
    return rows

def make_boss():
    pal=[list(bytes.fromhex(c)) for c in ['000000','191c22','303138','474349','65594e','837362',
        'a28b70','c2aa83','e3c79b','f2deb2','5b332b','994434','db5935','f29746','ffd26a','fff0b7']]
    body=Image.new('L',(96,64));d=D(body)
    for x in (0,72):
        d.polygon([(x+5,0),(x+19,0),(x+23,6),(x+23,58),(x+18,63),(x+4,63),(x,58),(x,7)],fill=1)
        d.rectangle((x+2,7,x+21,56),fill=2)
        for y in range(5,60,5):
            d.line((x+2,y,x+21,y),fill=4,width=2)
            d.line((x+3,y,x+10,y),fill=6)
    d.polygon([(24,2),(71,2),(83,12),(82,49),(74,59),(60,63),(35,63),(21,59),(13,49),(12,13)],fill=1)
    d.polygon([(25,4),(70,4),(80,14),(79,47),(71,58),(59,61),(37,61),(24,57),(16,47),(15,14)],fill=5)
    d.polygon([(24,9),(71,9),(75,17),(73,43),(64,55),(32,55),(22,45),(20,16)],fill=4)
    d.line((16,15,25,5,69,5,78,13),fill=8,width=2)
    d.line((16,15,16,45,24,56),fill=7,width=2)
    d.line((25,57,36,61,59,61,72,56,79,47),fill=2,width=2)
    for x in (21,65):
        for y in (12,44):
            d.rectangle((x,y,x+10,y+10),fill=3,outline=6)
            for j in range(2,10,2):d.line((x+2,y+j,x+8,y+j),fill=2)
    d.polygon([(34,21),(61,21),(65,26),(65,39),(58,44),(37,44),(31,39),(31,26)],fill=2)
    d.polygon([(36,23),(59,23),(62,27),(62,37),(57,41),(38,41),(34,37),(34,27)],fill=6,outline=8)
    d.line((48,24,48,40),fill=2,width=2)
    for x in (38,42,53,57):d.line((x,28,x,35),fill=4)
    for x in (28,65):
        d.rectangle((x,52,x+3,55),fill=12,outline=10)
    for x in (33,58):
        d.rectangle((x,8,x+5,17),fill=3,outline=5)
        for y in (9,11,13,15):d.line((x+1,y,x+4,y),fill=7)
    for x in (23,68):
        d.line((x,23,x,38),fill=2,width=4)
        d.line((x-1,24,x-1,37),fill=7)
        for y in (25,34):d.line((x-2,y,x+1,y),fill=5)
    d.line((40,9,54,9,57,12,57,17),fill=2,width=3)
    d.line((40,8,54,8,57,11,57,16),fill=7)
    d.rectangle((42,45,54,50),fill=2,outline=5)
    for x in (44,47,50,53):d.line((x,46,x,49),fill=6)
    for x in range(38,60,4):d.line((x,54,x-2,57),fill=13,width=2)
    for x,y in [(24,8),(70,8),(21,34),(74,34),(30,55),(65,55),(36,20),(59,20)]:
        d.point((x,y),fill=9);d.point((x,y+1),fill=2)
    frames={'body':body}
    positions=[(22,8),(58,8),(22,39),(58,39)]
    turrets=[]
    for part,(x,y) in zip(('nw','ne','sw','se'),positions):
        key=f'turret_{part}'
        turrets.append(dict(id=key,offset=[x,y],size=[16,16],hit_rect=[x,y,16,16],
                            independently_destructible=True,**{k:key+'_'+k for k in ('south','southeast','destroyed')}))
        for pose in ('south','southeast','destroyed'):
            im=Image.new('L',(16,16));g=D(im)
            g.polygon([(4,1),(11,1),(14,4),(14,9),(11,12),(4,12),(1,9),(1,4)],fill=1)
            g.polygon([(4,2),(10,2),(13,5),(12,9),(10,11),(4,11),(2,8),(2,4)],fill=5)
            g.line((2,5,5,2,10,2),fill=8)
            g.rectangle((5,4,10,7),fill=3,outline=6)
            g.point((3,8),fill=12);g.point((11,4),fill=9)
            if pose=='destroyed':
                g.polygon([(4,4),(9,3),(12,7),(8,10),(3,8)],fill=2)
                g.line((7,6,9,10,13,12),fill=3,width=3)
                g.line((6,6,9,10,12,11),fill=6);g.point((5,7),fill=12)
            else:
                end=(8,15) if pose=='south' else (14,14)
                g.line(((8,7),end),fill=1,width=4)
                g.line(((7,7),(end[0]-1,end[1])),fill=7,width=2)
                g.line(((7,8),(8,10)),fill=4,width=3);g.point(end,fill=1)
            frames[key+'_'+pose]=im
    core=Image.new('L',(32,32));d=D(core)
    d.polygon([(5,6),(25,6),(29,11),(29,21),(24,26),(7,26),(3,21),(3,11)],fill=1)
    d.line((4,12,8,7,24,7,28,11),fill=7,width=2)
    for x in (8,14,20):
        d.rectangle((x,10,x+3,21),fill=12,outline=10)
        d.line((x+1,11,x+1,20),fill=14);d.point((x+1,13),fill=15)
    d.line((7,23,24,23),fill=6,width=2);frames['core_exposed']=core
    rotors=[]
    for i,(x,y) in enumerate(((3,9),(77,9),(3,31),(77,31))):
        rotors.append(dict(id=f'rotor_{i}',offset=[x,y],phase_offset=i%3,
                           role='visual_only',destructible=False,collidable=False))
    for phase in range(3):
        im=Image.new('L',(16,24));d=D(im)
        for y in range(24):
            i=(y+phase*2)%6
            d.line((1,y,6,y),fill=[3,5,7,4,2,2][i]);d.line((8,y,13,y),fill=[2,4,6,4,2,1][i])
        frames[f'rotor_{phase}']=im
    for phase in range(2):
        im=Image.new('L',(16,16));d=D(im)
        d.polygon([(7,0),(9,5),(14,3),(11,8),(15,12),(10,11),(8,15),(5,10),(1,12),(4,7),(2,3),(6,5)],
                  fill=12 if phase else 13)
        d.polygon([(7,3),(11,8),(8,12),(5,8)],fill=14)
        d.rectangle((7,6,8,9),fill=15);frames[f'muzzle_{phase}']=im
    place=dict(body='body',body_size=[96,64],palette='boss',turrets=turrets,rotors=rotors,
        core=dict(offset=[32,16],size=[32,32],hit_rect=[40,24,16,16],exposed_overlay='core_exposed'),
        rotor_frames=[f'rotor_{i}' for i in range(3)],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        draw_order=['body','rotors','exposed_core_if_unlocked','turrets','optional_muzzle'])
    BOSS.mkdir(parents=True,exist_ok=True)
    save_json(BOSS/'placement.json',place)
    save_json(BOSS/'indexed-source.json',[dict(id=k,width=i.width,height=i.height,rows=hexrows(i,2))
                                          for k,i in frames.items()])
    (BOSS/'palette.rgb').write_bytes(bytes(v for rgb in pal for v in rgb))
    def composite(phase,dead=False):
        canvas=Image.new('RGBA',body.size,(79,56,42,255))
        def layer(k,xy):
            im=raster(frames[k],pal,True);canvas.alpha_composite(im,tuple(xy))
        layer('body',(0,0))
        for item in rotors:layer(f'rotor_{(phase+item["phase_offset"])%3}',item['offset'])
        if dead:layer('core_exposed',(32,16))
        for item in turrets:layer(item['destroyed' if dead else 'south'],item['offset'])
        return canvas.convert('RGB').resize((384,256),Image.Resampling.NEAREST)
    intact, wreck = composite(0), composite(0,True)
    card=Image.new('RGB',(784,282),(32,30,30));card.paste(intact,(4,22));card.paste(wreck,(396,22))
    d=D(card);d.text((5,4),'Landkreuzer / Einsatzbereit',fill='white')
    d.text((396,4),'Vier Tuerme zerstoert / Motorraum offen',fill='white')
    card.save(BOSS/'boss-preview.png')
    anim=[composite(i) for i in range(3)]
    anim[0].save(BOSS/'boss-animation.png',save_all=True,append_images=anim[1:],duration=115,loop=0)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    save_json(OUT/'manifest.json',dict(palettes=P))
    save_json(OUT/'level-example.json',dict(tiles=meta))
    save_json(OUT/'ground-targets.json',dict(schema=1,destroyed_tiles=damaged))
    binary=bytearray()
    for im in tiles:
        pixels=list(im.tobytes())
        binary.extend(pixels[i] | pixels[i+1]<<4 for i in range(0,256,2))
    (OUT/'terrain.ncm.bin').write_bytes(binary)
    rows=map_level()
    level=dict(format='shootermega65-level-1',name='Operation Canyon und Raffinerie',
        tileset='assets/art/level2/generated',ground_targets='assets/art/level2/generated',
        scroll_speed=0.5,map=rows,paths={},formations={},events=[
        dict(row=188,type='shop',id='mid'),dict(row=358,type='boss'),
        dict(row=368,type='shop',id='end'),dict(row=375,type='end')])
    # Compact rows keep the map legible in reviews.
    path=ROOT/'levels/level2.json';path.parent.mkdir(exist_ok=True)
    level['map']='__ROWS__'
    path.write_text(json.dumps(level,indent=2).replace('"__ROWS__"',
        '[\n'+',\n'.join('    '+json.dumps(row) for row in rows)+'\n  ]')+'\n',encoding='ascii')
    color=[raster(im,P[t['palette']]) for im,t in zip(tiles,meta)]
    sheet=Image.new('RGB',(8*112,math.ceil(len(tiles)/8)*48),(39,31,28));d=D(sheet)
    for i,im in enumerate(color):
        x=i%8*112;y=i//8*48
        sheet.paste(im.resize((32,32),Image.Resampling.NEAREST),(x+2,y+2))
        d.text((x+37,y+3),str(i),fill='white');d.text((x+2,y+34),meta[i]['name'],fill='white')
    sheet.save(OUT/'terrain-sheet.png')
    overview=Image.new('RGB',(320,6000))
    for y,row in enumerate(rows):
        for x,i in enumerate(row[1:]):overview.paste(color[i],(x*16,(374-y)*16))
    overview.save(OUT/'level-overview.png', optimize=True)
    board=Image.new('RGB',(4*332,1516),(33,26,24));d=D(board)
    for i,(low,high,title) in enumerate([(0,96,'01 Wuesteneinflug'),(96,184,'02 Canyon'),
                                         (184,280,'03 Oase'),(280,375,'04 Raffinerie')]):
        d.text((i*332+4,4),title,fill='white')
        board.paste(overview.crop((0,(375-high)*16,320,(375-low)*16)),(i*332+4,20))
    board.save(OUT/'level-sections.png',optimize=True)
    gallery=Image.new('RGB',(6*139,3*86),(35,28,24));d=D(gallery)
    for i,(name,a,b) in enumerate(pairs):
        x=i%6*139;y=i//6*86
        d.text((x+3,y+3),name,fill='white')
        for j,im in enumerate((a,b)):
            gallery.paste(raster(im,P['structures']).resize((64,64),Image.Resampling.NEAREST),(x+3+j*67,y+17))
    gallery.save(OUT/'destroyed-sheet.png')
    make_boss()

if __name__=='__main__':
    main()
