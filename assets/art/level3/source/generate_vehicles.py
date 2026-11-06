"""Draw the Offshore aircraft, vessels and carrier in their native palettes."""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
ENEMY = ROOT/'assets/art/enemies-level3/generated'
BOSS = ROOT/'assets/art/boss-level3/generated'
D = ImageDraw.Draw
DIR8 = ('north','northeast','east','southeast','south','southwest','west','northwest')
DIR4 = DIR8[::2]
ENEMY_COLORS = {
    'air':'000000 15232b 29414e 476472 718d91 a8b7ac d8dfca eef1db 355a70 4d86a3 7fb1bd 8a3b35 c7593d ea874a f6bd64 fdf1a8',
    'heli':'000000 14232b 263944 41545c 65777d 9ba8a5 d1d8cb f2ead5 284e62 41798a 7ba7ae 7c3d37 b54a36 e78043 f2b958 f5dea0',
    'ships':'000000 132331 233c4d 395564 527584 718f94 9cb6b5 d5e0d3 254b68 387589 6ba6ab 7b3c35 c65a43 ef8650 f4bb67 fff0bb',
}
BOSS_COLORS = '000000 10212c 203746 324d5c 486776 688590 9aafb0 d5dfd5 244e69 407a91 73a8b2 743831 b84e3b e77f48 f7bd65 fff1bb'


def colors(text):
    return [tuple(bytes.fromhex(v)) for v in text.split()]


def rgba(im,palette):
    out=Image.new('RGBA',im.size)
    out.putdata([palette[v]+(255 if v else 0,) for v in im.tobytes()])
    return out


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='ascii',newline='\n')


def encode(im):
    return [''.join(f'{im.getpixel((x,y)):02x}' for x in range(im.width)) for y in range(im.height)]


def heading(im,pose):
    angle=math.radians(DIR8.index(pose)*45)
    cx=(im.width-1)/2;cy=(im.height-1)/2
    def project(x,y):
        return round(cx+x*math.cos(angle)-y*math.sin(angle)), round(cy+x*math.sin(angle)+y*math.cos(angle))
    return project


def bevel(im, outline, bright, shadow):
    """Select edge light in screen coordinates, independent of heading."""
    old=im.copy()
    for y in range(1,im.height-1):
        for x in range(1,im.width-1):
            if old.getpixel((x,y))!=outline:
                continue
            if not old.getpixel((x-1,y)) or not old.getpixel((x,y-1)):
                im.putpixel((x,y),bright)
            elif not old.getpixel((x+1,y)) or not old.getpixel((x,y+1)):
                im.putpixel((x,y),shadow)


def aircraft(group,pose,phase):
    im=Image.new('L',(16,16));p=heading(im,pose);d=D(im)
    def poly(points,color):d.polygon([p(x,y) for x,y in points],fill=color)
    def line(points,color,width=1):d.line([p(x,y) for x,y in points],fill=color,width=width)
    if group=='seaplane':
        # Twin light floats, broad navy wings, orange recognition tips.
        for side in (-1,1):
            poly([(side*4,-5),(side*5,-3),(side*5,4),(side*4,5),(side*3,3),(side*3,-2)],4)
            line([(side*4,-4),(side*4,3)],6)
        poly([(-7,-1),(-3,-2),(0,-2),(3,-2),(7,-1),(7,1),(2,2),(0,1),(-2,2),(-7,1)],8)
        line([(-6,-1),(-3,-1),(3,-1),(6,-1)],5)
        for side in (-1,1):line([(side*6,0),(side*7,0)],12)
        poly([(-3,5),(0,4),(3,5),(2,6),(-2,6)],4)
        poly([(0,-7),(2,-4),(2,0),(1,5),(0,7),(-1,5),(-2,0),(-2,-4)],5)
        line([(-1,-5),(-1,0),(0,4)],6)
        line([(0,-3),(0,-1)],8,2)
        d.point(p(0,-3),fill=10)
        # Short propeller traces change silhouette without moving the hull.
        if phase==0:line([(-2,-6),(2,-6)],6)
        elif phase==1:line([(-1,-7),(1,-5)],7)
        else:d.point(p(0,-7),fill=15)
    else:
        poly([(-3,-5),(0,-7),(3,-5),(3,-1),(2,2),(1,6),(0,7),(-1,6),(-2,2),(-3,-1)],4)
        poly([(-2,-5),(0,-6),(2,-5),(2,-2),(-2,-2)],8)
        d.point(p(-1,-5),fill=10)
        for side in (-1,1):
            line([(side*3,-3),(side*4,-2),(side*4,3)],2,2)
            line([(side*4,-3),(side*4,2)],6)
            d.point(p(side*4,0),fill=12)
        line([(-2,5),(2,5)],5)
        line([(0,1),(0,5)],6)
        # Three independent rotor sweeps; the hub remains fixed.
        angle=math.radians(phase*30+DIR8.index(pose)*45)
        for k in range(4):
            a=angle+math.pi*k/2
            end=(round(7.5+6.5*math.cos(a)),round(7.5+6.5*math.sin(a)))
            mid=(round(7.5+3.0*math.cos(a)),round(7.5+3.0*math.sin(a)))
            d.line(((8,8),mid,end),fill=3)
            d.line((mid,end),fill=5)
            d.point(end,fill=7)
        d.rectangle((7,7,8,8),fill=6)
    bevel(im,4,5,2)
    return im


def boat(group,pose,phase):
    size=(16,16) if group=='speedboat' else (32,32)
    im=Image.new('L',size);p=heading(im,pose);d=D(im)
    def poly(points,color):d.polygon([p(x,y) for x,y in points],fill=color)
    def line(points,color,width=1):d.line([p(x,y) for x,y in points],fill=color,width=width)
    if group=='speedboat':
        for side in (-1,1):
            line([(side*2,-3),(side*3,0),(side*4,3+phase%2),(side*(5+phase%2),6)],10)
            d.point(p(side*(4+phase%2),5),fill=7)
            d.point(p(side*3,6+phase%2),fill=9+phase%2)
        poly([(0,-7),(3,-4),(3,2),(2,5),(-2,5),(-3,2),(-3,-4)],2)
        poly([(0,-6),(2,-3),(2,2),(1,4),(-2,4),(-2,-3)],6)
        poly([(-1,-2),(1,-2),(1,1),(-1,1)],8)
        line([(-2,3),(2,3)],12)
        d.point(p(0,5),fill=14)
        d.point(p((phase%3)-1,7),fill=7)
    else:
        for side in (-1,1):
            line([(side*4,-10),(side*8,-6),(side*10,1),(side*12,6+phase),
                  (side*(13+phase),12)],10)
            for x,y in ((9,-4),(11,4),(14,10)):
                d.point(p(side*x,y+phase),fill=7)
        poly([(0,-15),(7,-10),(9,-3),(9,8),(6,12),(-6,12),(-9,8),
              (-9,-3),(-7,-10)],1)
        poly([(0,-13),(6,-9),(8,-2),(8,7),(5,11),(-5,11),(-8,7),
              (-8,-2),(-6,-9)],5)
        line([(-6,-8),(-7,-2),(-7,7),(-5,10)],7)
        poly([(-5,2),(5,2),(6,7),(4,9),(-4,9),(-6,7)],3)
        line([(-4,3),(4,3)],6)
        line([(-4,5),(4,5)],8,2)
        for side in (-1,1):d.point(p(side*6,7),fill=12)
        d.line([p(-5,10),p(5,10)],4)
        cx,cy=p(0,-2)
        d.ellipse((cx-5,cy-5,cx+5,cy+5),fill=3,outline=6)
        d.ellipse((cx-3,cy-3,cx+3,cy+3),fill=2)
        line([(-3,13),(-5,15)],10)
        line([(3,13),(5,15)],7 if phase else 10)
    bevel(im,5,6,3)
    return im


def frigate(phase,wreck=False):
    im=Image.new('L',(32,64));d=D(im)
    if not wreck:
        for side in (-1,1):
            for y in range(1,58,6):
                x=16+side*(12+(y+phase)%3)
                d.line((x,y,x+side,y+3),fill=10)
                d.point((x,y+phase),fill=7)
        d.line((8,2,12,0),fill=10);d.line((23,2,20,0),fill=7)
    if wreck:
        hull=[(7,6),(22,3),(27,11),(30,46),(25,56),(19,61),(9,54),(5,26)]
    else:
        hull=[(7,5),(24,5),(27,10),(28,44),(25,55),(16,63),(7,55),(4,44),(5,10)]
    d.polygon(hull,fill=1)
    if wreck:
        d.polygon([(8,8),(21,5),(25,12),(28,45),(23,54),(19,58),(10,52),(7,25)],fill=4)
        d.line((8,11,8,25,11,49,18,55),fill=6)
        d.polygon([(8,20),(21,14),(26,28),(21,44),(12,40)],fill=2)
        d.line((8,25,17,28,14,38,25,44),fill=1,width=3)
        for x,y in ((12,22),(20,31),(15,41)):
            d.polygon([(x-3,y+4),(x-2,y-2),(x,y),(x+2,y-5),(x+3,y+4)],fill=12)
            d.line((x,y+3,x+1,y),fill=14,width=2)
            d.point((x-1,y-5),fill=13)
    else:
        d.polygon([(8,7),(23,7),(25,11),(26,44),(23,54),(16,60),(9,54),(6,44),(7,11)],fill=5)
        d.line((8,8,7,12,7,43,10,53),fill=7)
        d.line((22,54,16,59),fill=3)
        d.rectangle((9,23,23,37),fill=3,outline=2)
        d.rectangle((10,24,22,32),fill=6,outline=7)
        d.line((11,29,21,29),fill=8,width=2)
        d.rectangle((13,33,18,36),fill=1,outline=4)
        for x,y in ((16,16),(16,44)):
            d.ellipse((x-6,y-6,x+6,y+6),fill=3,outline=6)
            d.ellipse((x-4,y-4,x+4,y+4),fill=2)
        d.line((14,54,16,56,18,54),fill=7)
        d.point((9,34),fill=12);d.point((22,34),fill=12)
        d.line((5,53,9,57,13,60),fill=10)
        d.line((27,53,23,58-phase,19,61),fill=7 if phase else 10)
    return im


def enemy_art():
    ENEMY.mkdir(parents=True,exist_ok=True)
    palettes={key:colors(value) for key,value in ENEMY_COLORS.items()}
    save(ENEMY/'palettes.json',palettes)
    save(ENEMY/'placement.json',{'patrol_boat':{'guns':[[8,10]]},
                                  'frigate':{'guns':[[8,8],[8,36]]}})
    records=[]
    for group,poses,phases,pal in (
        ('seaplane',DIR8,3,'air'),('navy_heli',DIR8,3,'heli'),
        ('speedboat',DIR4,4,'ships'),('patrol_boat',DIR4,2,'ships'),
        ('frigate',('south','destroyed'),2,'ships'),
    ):
        samples=[]
        for pose in poses:
            for phase in range(1 if pose=='destroyed' else phases):
                if pal!='ships':im=aircraft(group,pose,phase)
                elif group=='frigate':im=frigate(phase,pose=='destroyed')
                else:im=boat(group,pose,phase)
                records.append(dict(group=group,pose=pose,phase=phase,width=im.width,
                                    height=im.height,palette=pal,rows=encode(im)))
                samples.append((f'{pose} / {phase}',rgba(im,palettes[pal])))
        sheet(ENEMY/f'{group}-preview.png',samples,4 if group!='frigate' else 3,3)
    save(ENEMY/'indexed-source.json',records)


def sheet(path,samples,columns,scale):
    cellw=max(112,max(im.width for _,im in samples)*scale+8)
    cellh=max(im.height for _,im in samples)*scale+24
    board=Image.new('RGB',(cellw*columns,cellh*math.ceil(len(samples)/columns)),(23,42,55))
    draw=D(board)
    for i,(label,im) in enumerate(samples):
        x=(i%columns)*cellw+4;y=(i//columns)*cellh+3
        draw.text((x,y),label,fill='white')
        art=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        board.paste(art,(x,y+16),art if art.mode=='RGBA' else None)
    board.save(path)


TURRETS=((8,12),(72,12),(12,77),(68,77))


def carrier():
    im=Image.new('L',(96,112));d=D(im)
    d.polygon([(14,3),(81,3),(90,10),(94,22),(94,70),(86,86),(70,102),
               (48,111),(26,102),(10,86),(2,70),(1,22),(6,10)],fill=1)
    d.polygon([(15,6),(80,6),(88,12),(91,23),(91,69),(83,85),(68,99),
               (48,108),(27,99),(13,84),(5,69),(4,23),(8,13)],fill=3)
    d.polygon([(16,8),(79,8),(86,14),(88,24),(88,67),(80,82),(67,96),
               (48,104),(29,96),(16,82),(8,67),(7,24),(11,15)],fill=4)
    d.line((7,24,11,15,16,8,79,8,86,14),fill=7,width=2)
    d.line((7,25,8,67,16,82,29,96),fill=6)
    d.line((29,97,48,105,68,97,81,83,89,67),fill=2,width=2)
    # Angled landing strip and straight launch rail to the bow.
    d.polygon([(19,13),(35,12),(57,92),(50,100),(41,99),(17,24)],fill=2)
    d.line((20,14,17,24,41,98),fill=7)
    d.line((35,13,56,91),fill=6)
    for y in range(19,90,9):
        x=25+(y-19)//4
        d.line((x,y,x+1,y+4),fill=7,width=2)
    d.polygon([(43,67),(56,67),(57,97),(48,103),(43,98)],fill=3)
    d.line((49,68,49,101),fill=7);d.line((51,68,51,100),fill=5)
    for x in (45,54):d.line((x,69,x,96),fill=6)
    for x in (17,78):
        for y in range(28,77,8):
            d.line((x,y,x+4,y),fill=2,width=2)
            d.point((x,y),fill=6)
    # Raised starboard island with bridge windows, vents and radar foundation.
    d.polygon([(66,29),(79,28),(85,34),(85,63),(79,69),(65,66),(62,55),(62,36)],fill=2)
    d.polygon([(65,34),(78,30),(83,35),(82,61),(78,65),(67,63),(64,55)],fill=5)
    d.line((65,52,65,35,78,31,82,35),fill=7)
    d.rectangle((67,48,80,54),fill=8,outline=1)
    for x in (68,72,76,79):d.line((x,49,x,52),fill=10)
    for y in (57,59,61):d.line((68,y,77,y),fill=3)
    d.point((80,57),fill=12)
    # Recessed elevator in the middle of the flight deck.
    d.rectangle((31,39,60,68),fill=2,outline=1)
    d.rectangle((33,41,58,66),fill=4,outline=6)
    d.line((34,42,57,42),fill=7)
    d.line((45,43,45,65),fill=2,width=2)
    for y in (48,52,56,60):
        d.line((35,y,40,y),fill=5);d.line((49,y,56,y),fill=5)
    for x in (33,54):
        for y in (39,66):
            d.line((x,y,x+3,y),fill=14)
    for x,y in TURRETS:
        d.ellipse((x-1,y-1,x+16,y+16),fill=2)
        d.arc((x-1,y-1,x+16,y+16),145,315,fill=7)
    # Stern strobes and yellow/black launch warning near bow.
    for x in (24,72):d.rectangle((x,7,x+2,8),fill=12)
    for x in range(39,59,4):d.line((x,97,x-1,100),fill=14)
    d.line((43,106,48,108,53,106),fill=6)
    for x,y in ((13,32),(82,23),(13,64),(79,70),(25,88),(68,89)):
        d.point((x,y),fill=7);d.point((x+1,y+1),fill=2)
    return im


def deck_turret(pose):
    im=Image.new('L',(16,16));d=D(im)
    d.polygon([(4,1),(11,1),(14,4),(14,10),(10,13),(4,13),(1,10),(1,4)],fill=1)
    d.polygon([(4,2),(10,2),(13,5),(12,10),(10,11),(4,11),(2,9),(2,4)],fill=5)
    d.line((2,7,2,4,4,2,10,2),fill=7)
    d.rectangle((5,4,10,7),fill=3)
    d.point((3,7),fill=12)
    if pose=='destroyed':
        d.polygon([(4,4),(9,3),(12,7),(9,11),(3,8)],fill=2)
        d.line((7,6,9,10,13,12),fill=1,width=4)
        d.line((6,6,9,10,12,11),fill=5)
        d.point((5,8),fill=12);d.point((8,6),fill=13)
    else:
        end=(8,15) if pose=='south' else (14,14)
        d.line(((8,7),end),fill=1,width=4)
        d.line(((7,7),(end[0]-1,end[1]-1)),fill=6,width=2)
        d.point((7,8),fill=7);d.point(end,fill=1)
    return im


def elevator():
    im=Image.new('L',(32,32));d=D(im)
    d.rectangle((1,1,30,30),fill=1,outline=6,width=2)
    d.line((2,29,2,2,29,2),fill=7)
    d.rectangle((4,4,27,27),fill=2)
    d.line((5,5,5,26,26,26),fill=4,width=2)
    for y in (7,24):
        d.line((8,y,24,y),fill=5)
        for x in (8,13,18,23):d.point((x,y),fill=14)
    for x in (9,15,21):
        d.rectangle((x,10,x+3,22),fill=11)
        d.line((x+1,11,x+1,21),fill=13,width=2)
        d.line((x+1,12,x+1,18),fill=14)
        d.point((x+1,13),fill=15)
    d.line((4,26,27,26),fill=6,width=2)
    return im


def radar(phase):
    im=Image.new('L',(16,16));d=D(im)
    d.ellipse((4,5,11,12),fill=2,outline=5)
    d.line((8,5,8,11),fill=6,width=2)
    spans=[[(2,4),(13,4)],[(4,2),(11,8)],[(7,1),(8,10)]]
    p,q=spans[phase]
    d.line((p,q),fill=1,width=4)
    d.line((p,q),fill=6,width=2)
    d.point(p,fill=7);d.point(q,fill=12)
    d.point((8,7),fill=10)
    return im


def flash(phase):
    im=Image.new('L',(16,16));d=D(im)
    points=[(7,0),(10,5),(14,3),(11,8),(15,12),(10,10),(8,15),
            (5,10),(1,12),(4,7),(2,3),(6,5)]
    if phase:points=[(7,1),(10,6),(13,5),(10,9),(12,13),(8,11),
                     (5,14),(5,10),(1,8),(5,6),(3,2)]
    d.polygon(points,fill=13)
    d.polygon([(7,3),(11,8),(8,12),(5,8)],fill=14)
    d.rectangle((7,6,8,9),fill=15)
    return im


def spray(phase):
    im=Image.new('L',(32,16));d=D(im)
    for side in (-1,1):
        bend=[(15+side*(2+phase),2),(15+side*(6+phase),5),
              (15+side*(10+phase),8),(15+side*(12+phase),11)]
        d.line(bend,fill=9,width=2)
        d.line(bend[1:3],fill=10)
        for x,y in ((5,3),(8,7),(12,11)):
            d.point((15+side*x,y+phase),fill=7)
    return im


def jet(phase):
    im=Image.new('L',(16,16));d=D(im)
    if phase<2:
        for x,y in ((5,2),(9,3),(3,4),(12,1),(6,1)):
            d.line((x,y,x+1,y),fill=6 if phase else 7)
    if phase>0:
        d.line((6,0,6,4),fill=13)
        d.line((9,0,9,4),fill=14)
    d.polygon([(7,1),(9,3),(10,6),(14,10),(14,12),(10,11),(8,15),
               (6,11),(2,12),(2,10),(6,6)],fill=2)
    d.polygon([(7,3),(9,4),(10,7),(13,10),(9,9),(8,14),(7,10),(3,10),
               (6,7)],fill=6)
    d.line((7,4,7,7,8,12),fill=7)
    d.point((8,9),fill=8)
    d.point((3,10),fill=12);d.point((13,10),fill=12)
    return im


def boss_art():
    BOSS.mkdir(parents=True,exist_ok=True)
    palette=colors(BOSS_COLORS)
    frames={'body':carrier(),'core_exposed':elevator()}
    mounts=[]
    for corner,(x,y) in zip(('nw','ne','sw','se'),TURRETS):
        key='turret_'+corner
        poses={pose:key+'_'+pose for pose in ('south','southeast','destroyed')}
        for pose,fid in poses.items():frames[fid]=deck_turret(pose)
        mounts.append(dict(id=key,offset=[x,y],size=[16,16],hit_rect=[x,y,16,16],
                           independently_destructible=True,**poses))
    for phase in range(3):
        frames[f'rotor_{phase}']=radar(phase)
        frames[f'spray_{phase}']=spray(phase)
        frames[f'deck_jet_{phase}']=jet(phase)
    for phase in range(2):frames[f'muzzle_{phase}']=flash(phase)
    placement=dict(body='body',body_size=[96,112],palette='boss',turrets=mounts,
        core=dict(offset=[30,38],size=[32,32],hit_rect=[38,46,16,16],exposed_overlay='core_exposed'),
        rotors=[dict(id='radar',offset=[65,29],phase_offset=0)],
        rotor_frames=[f'rotor_{i}' for i in range(3)],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        spray=dict(frames=[f'spray_{i}' for i in range(3)],offsets=[[9,-6],[55,-6],[7,93],[57,93]]),
        catapult=dict(frames=[f'deck_jet_{i}' for i in range(3)],offset=[42,76]),
        draw_order=['spray','body','radar','core_if_exposed','turrets','deck_jet'])
    save(BOSS/'indexed-source.json',[dict(id=fid,width=im.width,height=im.height,
          rows=encode(im)) for fid,im in frames.items()])
    save(BOSS/'placement.json',placement)
    (BOSS/'palette.rgb').write_bytes(bytes(c for triplet in palette for c in triplet))

    def compose(phase,exposed=False,launch=False):
        canvas=Image.new('RGBA',(112,144),(24,64,86,255))
        def paste(key,xy):
            canvas.alpha_composite(rgba(frames[key],palette),(xy[0]+8,xy[1]+12))
        for xy in placement['spray']['offsets']:paste(f'spray_{phase}',xy)
        paste('body',(0,0))
        paste(f'rotor_{phase}',placement['rotors'][0]['offset'])
        if exposed:paste('core_exposed',placement['core']['offset'])
        for t in mounts:paste(t['destroyed' if exposed else 'south'],t['offset'])
        if launch:
            x,y=placement['catapult']['offset']
            paste(f'deck_jet_{phase}',(x,y+phase*14))
        return canvas
    sheet(BOSS/'boss-preview.png',[('Traeger / Gefecht',compose(0)),
              ('Aufzug offen / Reaktor',compose(1,True))],2,3)
    sheet(BOSS/'launch-phases.png',[(label,compose(i,False,True))
          for i,label in enumerate(('Katapult / Dampf','Abheben','Im Flug'))],3,3)
    sheet(BOSS/'radar-wake-phases.png',[(f'Radar {i+1}',rgba(frames[f'rotor_{i}'],palette))
          for i in range(3)]+[(f'Gischt {i+1}',rgba(frames[f'spray_{i}'],palette)) for i in range(3)],3,4)
    animation=[compose(i,False,True).convert('RGB').resize((336,432),Image.Resampling.NEAREST)
               for i in range(3)]
    animation[0].save(BOSS/'boss-animation.png',save_all=True,append_images=animation[1:],
                      duration=[230,140,180],loop=0)


if __name__=='__main__':
    enemy_art()
    boss_art()
