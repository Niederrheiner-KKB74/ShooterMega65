"""Native indexed artwork for the refinery hover tank."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'generated'
PALETTE = [
    '000000', '131b21', '293134', '4b5050',
    '66594a', '8a8b7c', 'b5a27c', 'd4c39b',
    'eee1b3', '8e724e', '6b332b', 'b84729',
    'ec7a2f', 'ffc85f', 'fff3c4', 'b6b6a4',
]


def panel(draw, box, color=6):
    x, y, right, bottom = box
    draw.rectangle(box, fill=color, outline=1)
    draw.line((x+1,bottom-1,x+1,y+1,right-1,y+1),fill=7)
    draw.line((x+2,bottom-1,right-1,bottom-1,right-1,y+2),fill=4)
    for px,py in ((x+2,y+2),(right-2,y+2),(x+2,bottom-2)):
        draw.point((px,py),fill=8)


def body():
    im = Image.new('L',(112,80))
    draw = ImageDraw.Draw(im)
    # A single closed apron, with short radial folds rather than track links.
    draw.polygon([(15,3),(96,3),(106,10),(111,25),(110,59),
                  (102,72),(87,78),(24,78),(9,73),(1,60),(0,25),(5,12)],fill=1)
    draw.polygon([(16,5),(95,5),(104,12),(108,26),(107,58),
                  (99,69),(86,74),(25,74),(12,69),(4,58),(3,26),(8,14)],fill=2)
    draw.line((3,27,8,14,16,5,95,5,103,12),fill=5)
    draw.line((4,28,4,57,12,68,25,73),fill=3)
    draw.line((26,76,86,76,101,70,109,59),fill=1,width=2)
    for y in range(24,61,5):
        draw.line((1,y,6,y+1),fill=1)
        draw.point((3,y+1),fill=5)
        draw.line((105,y,110,y-1),fill=1)
        draw.point((106,y+1),fill=3)
    for x in range(20,94,6):
        draw.line((x,71,x-2,77),fill=1)
        draw.line((x+1,72,x,75),fill=3)
    draw.polygon([(16,9),(95,9),(102,17),(104,29),(102,55),
                  (94,67),(83,70),(29,70),(17,66),(9,54),(8,29),(11,18)],fill=4)
    draw.polygon([(18,10),(93,10),(100,18),(102,29),(99,53),
                  (92,64),(82,67),(30,67),(20,63),(12,53),(11,29),(14,19)],fill=6)
    draw.line((12,30,14,20,19,11,92,11,99,18),fill=8,width=2)
    draw.line((12,31,13,51,21,61,30,65),fill=7)
    draw.line((31,67,82,67,92,64,99,53),fill=4,width=2)
    # Sand camouflage consists of broad facets, separated by machined seams.
    draw.polygon([(14,32),(24,28),(35,33),(31,42),(17,47),(13,44)],fill=9)
    draw.polygon([(79,30),(96,33),(99,43),(89,47),(78,40)],fill=9)
    draw.polygon([(31,58),(40,53),(49,58),(46,66),(32,65)],fill=7)
    draw.polygon([(66,53),(80,55),(84,65),(70,66),(62,60)],fill=9)
    # Dark exhaust housings flank the rear turbines.
    for x in (7,97):
        draw.rectangle((x,17,x+7,28),fill=1)
        for y in (18,21,24,27):
            draw.line((x+1,y,x+5,y),fill=5)
        draw.point((x+1,17),fill=7)
    # Closed well surfaces sit underneath the animated fan overlays.
    for x in (18,62):
        draw.ellipse((x,3,x+31,34),fill=1)
        draw.ellipse((x+1,4,x+30,33),fill=4,outline=7)
        draw.ellipse((x+3,6,x+28,31),fill=2,outline=5)
    panel(draw,(49,10,60,29),5)
    for y in (14,17,20,23,26):
        draw.line((52,y,57,y),fill=1)
        draw.point((52,y-1),fill=7)
    # Raised central armor hatch, with recessed locking channels.
    draw.polygon([(43,35),(68,35),(73,41),(72,58),(66,65),
                  (45,65),(39,58),(39,41)],fill=1)
    draw.polygon([(45,36),(66,36),(71,42),(70,57),(65,62),
                  (46,62),(41,57),(41,42)],fill=5)
    draw.polygon([(46,38),(65,38),(69,43),(68,55),(64,60),
                  (47,60),(43,55),(43,43)],fill=6)
    draw.line((43,54,43,43,47,38,64,38,68,42),fill=8)
    draw.line((47,60,64,60,68,55),fill=4)
    draw.line((55,39,55,59),fill=3)
    for x in (48,61):
        draw.rectangle((x,44,x+2,53),fill=4)
        draw.line((x,44,x+2,44),fill=7)
    for y in (42,55):
        draw.rectangle((40,y,42,y+3),fill=3)
        draw.rectangle((69,y,71,y+3),fill=3)
    # Turret bearing rings stay visible around each independent 16x16 turret.
    for x,y in ((9,31),(87,31),(18,52),(78,52)):
        draw.ellipse((x-1,y-1,x+16,y+16),fill=1)
        draw.arc((x-1,y-1,x+16,y+16),140,310,fill=7)
    # Front projector / nozzle is visibly connected to the central fuel manifold.
    panel(draw,(46,64,65,73),4)
    draw.rectangle((50,67,61,76),fill=1)
    draw.rectangle((51,68,60,73),fill=3)
    draw.line((51,68,60,68),fill=7)
    draw.rectangle((53,72,58,76),fill=10)
    draw.line((54,74,57,74),fill=12)
    for x in (37,68):
        draw.line((x,65,x+5,65),fill=1,width=3)
        draw.line((x,64,x+4,64),fill=7)
    for x in (29,77):
        draw.rectangle((x,68,x+4,70),fill=10)
        draw.line((x+1,68,x+3,68),fill=11)
    for x,y in ((18,18),(93,18),(17,48),(94,48),(32,62),(79,62),
                (37,35),(75,35)):
        draw.point((x,y),fill=8)
        draw.point((x+1,y+1),fill=4)
    # Short yellow/black hazard ticks mark the front hatch locking rail.
    for x in (45,49,61,65):
        draw.line((x,62,x-1,64),fill=13)
    return im


def fan(phase):
    im = Image.new('L',(32,32))
    draw = ImageDraw.Draw(im)
    draw.ellipse((0,0,31,31),fill=1)
    draw.ellipse((1,1,30,30),fill=4,outline=7)
    draw.arc((1,1,30,30),140,310,fill=8)
    draw.ellipse((3,3,28,28),fill=2,outline=5)
    draw.ellipse((5,5,26,26),fill=1)
    center=15.5
    for blade in range(5):
        angle=math.radians(blade*72+phase*24)
        points=[]
        for radius,offset in ((3,-12),(11,-30),(11,5),(6,25)):
            a=angle+math.radians(offset)
            points.append((round(center+radius*math.cos(a)),
                           round(center+radius*math.sin(a))))
        draw.polygon(points,fill=5)
        # Screen-space upper-left edge accents, independently for every phase.
        draw.line(points[:2],fill=7)
    draw.ellipse((12,12,19,19),fill=3,outline=1)
    draw.arc((12,12,19,19),140,310,fill=8)
    draw.rectangle((15,14,16,16),fill=6)
    for x,y in ((5,5),(25,5),(5,25),(25,25)):
        draw.point((x,y),fill=8)
    return im


def turret(corner, pose):
    im = Image.new('L',(16,16))
    draw = ImageDraw.Draw(im)
    draw.polygon([(4,1),(11,1),(14,4),(14,10),(10,13),(4,13),(1,10),(1,4)],fill=1)
    draw.polygon([(4,2),(10,2),(13,5),(12,10),(10,11),(4,11),(2,9),(2,4)],fill=6)
    draw.line((2,7,2,4,4,2,10,2,12,4),fill=8)
    draw.line((4,11,10,11,12,9),fill=4)
    draw.rectangle((5,4,9,7),fill=4)
    draw.line((5,4,9,4),fill=7)
    draw.point((3,8),fill=11)
    draw.point((11,5),fill=8)
    if corner in ('sw','se'):
        draw.point((10,3),fill=5)
    if pose == 'destroyed':
        draw.polygon([(4,4),(9,3),(12,7),(9,11),(3,8)],fill=2)
        draw.line((7,6,9,10,13,12),fill=1,width=4)
        draw.line((6,6,9,10,12,11),fill=5)
        draw.point((5,8),fill=10)
        draw.point((8,6),fill=11)
    else:
        end=(8,15) if pose=='south' else (14,14)
        draw.line(((8,7),end),fill=1,width=4)
        draw.line(((7,7),(end[0]-1,end[1]-1)),fill=5,width=2)
        draw.line(((7,8),(8,10)),fill=3,width=3)
        draw.point((7,8),fill=7)
        draw.point(end,fill=1)
    return im


def core():
    im=Image.new('L',(32,32))
    draw=ImageDraw.Draw(im)
    draw.polygon([(5,1),(26,1),(31,7),(30,24),(24,31),(5,30),(0,23),(0,7)],fill=1)
    draw.line((1,21,1,7,5,2,25,2,30,7),fill=7,width=2)
    # Hinged hatch fragments remain around the dark machinery well.
    draw.polygon([(3,5),(10,2),(8,10),(3,14)],fill=6)
    draw.line((3,12,4,6,9,3),fill=8)
    draw.polygon([(24,2),(29,7),(28,16),(23,10)],fill=4)
    for x in (9,15,21):
        draw.rectangle((x,9,x+3,23),fill=10)
        draw.rectangle((x+1,10,x+2,22),fill=12)
        draw.line((x+1,11,x+1,20),fill=13)
        draw.point((x+1,12),fill=14)
    draw.line((5,25,25,25),fill=3,width=3)
    draw.line((5,24,25,24),fill=5)
    for x in (6,25):
        draw.line((x,14,x,21),fill=7)
    draw.point((7,27),fill=11)
    return im


def muzzle(phase):
    im=Image.new('L',(16,16))
    draw=ImageDraw.Draw(im)
    points=([(7,0),(10,5),(14,3),(11,8),(15,12),(10,10),(8,15),
             (5,10),(1,12),(4,7),(2,3),(6,5)] if phase==0 else
            [(8,1),(10,6),(13,5),(11,10),(12,14),(8,11),(5,14),
             (5,10),(1,8),(5,6),(3,2),(7,5)])
    draw.polygon(points,fill=12)
    draw.polygon([(7,3),(11,8),(8,12),(5,8)],fill=13)
    draw.rectangle((7,6,8,9),fill=14)
    return im


def flame(phase):
    im=Image.new('L',(16,32))
    draw=ImageDraw.Draw(im)
    shapes=[
        [(6,0),(9,0),(10,5),(13,7),(11,10),(14,14),(10,13),
         (8,21),(6,16),(3,17),(4,11),(2,8),(5,7)],
        [(6,0),(9,0),(10,5),(13,8),(11,12),(14,17),(11,20),
         (12,26),(9,24),(7,31),(5,26),(2,27),(4,21),(1,18),
         (4,14),(2,10),(5,5)],
        [(6,0),(9,0),(9,4),(11,6),(9,9),(12,11),(10,15),
         (8,13),(6,18),(4,16),(5,12),(3,10),(6,6)],
    ]
    draw.polygon(shapes[phase],fill=11)
    if phase==1:
        draw.polygon([(6,1),(9,1),(9,7),(11,10),(8,13),(11,18),
                      (8,23),(7,27),(5,21),(3,18),(6,15),(4,11),(7,6)],fill=12)
        draw.polygon([(7,0),(8,0),(9,6),(7,10),(9,15),(7,23),
                      (5,17),(7,13),(5,10),(7,5)],fill=13)
        draw.line((7,0,8,5,7,9),fill=14,width=2)
        draw.point((12,29),fill=12)
        draw.point((3,30),fill=13)
    else:
        draw.polygon([(7,0),(9,3),(7,7),(10,11),(8,15),(6,12),
                      (5,8),(7,5)],fill=12)
        draw.polygon([(7,0),(8,0),(8,5),(6,9),(8,13),(7,15),
                      (5,9),(7,4)],fill=13)
        draw.line((7,0,7,6),fill=14)
        if phase==2:
            draw.ellipse((9,22,11,24),fill=12)
            draw.point((4,27),fill=13)
    return im


def spray(phase):
    im=Image.new('L',(32,16))
    draw=ImageDraw.Draw(im)
    centers=[
        [(5,9,3),(11,7,4),(18,9,4),(24,6,3),(29,9,1)],
        [(3,7,2),(9,9,4),(16,5,4),(23,8,4),(28,4,2)],
        [(4,5,2),(10,6,3),(17,9,3),(25,6,3),(29,11,1)],
    ]
    for i,(x,y,radius) in enumerate(centers[phase]):
        draw.ellipse((x-radius,y-radius//2,x+radius,y+radius//2),fill=5)
        draw.ellipse((x-radius+1,y-radius//2,x+radius-1,y),fill=15)
        draw.line((x-1,y-1,x+1,y-1),fill=7 if i%2 else 6)
    for x,y in ((2+phase,2),(8+phase,12),(21-phase,2),(27-phase,13)):
        draw.point((x,y),fill=15)
    return im


def encode(im):
    return [''.join(format(im.getpixel((x,y)),'02x') for x in range(im.width))
            for y in range(im.height)]


def save_json(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    images={'body':body()}
    mounts=[]
    for corner,offset in zip(('nw','ne','sw','se'),((9,31),(87,31),(18,52),(78,52))):
        key='turret_'+corner
        for pose in ('south','southeast','destroyed'):
            images[key+'_'+pose]=turret(corner,pose)
        mounts.append(dict(id=key,offset=list(offset),size=[16,16],
            south=key+'_south',southeast=key+'_southeast',destroyed=key+'_destroyed',
            hit_rect=[*offset,16,16],independently_destructible=True))
    images['core_exposed']=core()
    for phase in range(3):
        images['rotor_'+str(phase)]=fan(phase)
        images['flame_'+str(phase)]=flame(phase)
        images['spray_'+str(phase)]=spray(phase)
    for phase in range(2):
        images['muzzle_'+str(phase)]=muzzle(phase)
    save_json(OUT/'indexed-source.json',[
        dict(id=key,width=im.width,height=im.height,rows=encode(im))
        for key,im in images.items()])
    palette=[tuple(bytes.fromhex(color)) for color in PALETTE]
    (OUT/'palette.rgb').write_bytes(bytes(value for color in palette for value in color))
    placement=dict(body='body',body_size=[112,80],palette='boss',turrets=mounts,
        core=dict(offset=[40,35],size=[32,32],exposed_overlay='core_exposed',
                  hit_rect=[48,43,16,16]),
        rotors=[dict(id='fan_l',offset=[18,3],phase_offset=0),
                dict(id='fan_r',offset=[62,3],phase_offset=1)],
        rotor_frames=['rotor_0','rotor_1','rotor_2'],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        flame=dict(frames=['flame_0','flame_1','flame_2'],offset=[48,77]),
        spray=dict(frames=['spray_0','spray_1','spray_2'],
                   offsets=[[-16,39],[96,39],[8,-7],[72,-7]]),
        draw_order=['body','rotors','core_if_exposed','turrets','flame','spray'],
        mechanic=dict(body_invulnerable_until=[m['id'] for m in mounts],
                      final_phase='core_exposed and intermittent flamethrower',
                      implementation='Art layout; behavior and timings configured by game'))
    save_json(OUT/'placement.json',placement)
    previews(images,palette,placement)


def previews(images,palette,placement):
    def rgba(key):
        im=images[key]
        result=Image.new('RGBA',im.size)
        result.putdata([palette[v]+(255 if v else 0,) for v in im.tobytes()])
        return result

    def compose(phase,exposed=False,fire=False,sand=False):
        # World origin of body is (20,16), leaving room for all effects.
        canvas=Image.new('RGBA',(152,132),(57,55,49,255))
        def paste(key,offset):
            canvas.alpha_composite(rgba(key),(offset[0]+20,offset[1]+16))
        paste('body',[0,0])
        for rotor in placement['rotors']:
            frame='rotor_'+str((phase+rotor['phase_offset'])%3)
            paste(frame,rotor['offset'])
        if exposed:
            paste('core_exposed',placement['core']['offset'])
        for turret_info in placement['turrets']:
            key=turret_info['destroyed' if exposed else 'south']
            paste(key,turret_info['offset'])
        if fire:
            paste('flame_'+str(phase),placement['flame']['offset'])
        if sand:
            for offset in placement['spray']['offsets']:
                paste('spray_'+str(phase),offset)
        return canvas.convert('RGB')

    board=Image.new('RGB',(928,424),(23,28,32))
    draw=ImageDraw.Draw(board)
    for x,exposed,title in ((4,False,'Hover-Panzer / vier Tuerme aktiv'),
                             (468,True,'Endphase / Reaktor und Flammenwerfer')):
        draw.text((x+8,5),title,fill='white')
        image=compose(1,exposed,exposed,True)
        board.paste(image.resize((456,396),Image.Resampling.NEAREST),(x,24))
    board.save(OUT/'boss-preview.png')
    for name,exposed,fire in (('boss-animation.png',False,False),
                              ('boss-flame-animation.png',True,True)):
        frames=[compose(i,exposed,fire,True).resize((456,396),Image.Resampling.NEAREST)
                for i in range(3)]
        frames[0].save(OUT/name,save_all=True,append_images=frames[1:],
                       duration=120,loop=0)
    flames=Image.new('RGB',(1384,424),(23,28,32))
    draw=ImageDraw.Draw(flames)
    for i,label in enumerate(('Aufflackern','Voller Strahl','Ausklingen')):
        x=i*460+4
        draw.text((x+8,5),label,fill='white')
        im=compose(i,True,True,False).resize((456,396),Image.Resampling.NEAREST)
        flames.paste(im,(x,24))
    flames.save(OUT/'flame-phases.png')
    # Inspect every source frame as native pixels and 4x nearest-neighbor.
    ordered=list(images)
    columns=6
    cellw,cellh=144,160
    atlas=Image.new('RGB',(columns*cellw,math.ceil(len(ordered)/columns)*cellh),(23,28,32))
    draw=ImageDraw.Draw(atlas)
    for i,key in enumerate(ordered):
        im=rgba(key)
        scale=1 if key=='body' else 4
        x=(i%columns)*cellw+4
        y=(i//columns)*cellh+20
        label=key.replace('turret_','t_').replace('southeast','SE').replace('destroyed','wreck')
        draw.text((x,y-16),label,fill='white')
        preview=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        atlas.paste(preview,(x,y),preview)
    atlas.save(OUT/'frame-sheet.png')


if __name__=='__main__':
    main()
