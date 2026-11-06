"""Export the long-hulled Offshore carrier and its assembled previews."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'assets/art/level3/source'))
import generate_vehicles as base

MOUNTS = ((27,9),(107,8),(27,31),(107,32))


def hull():
    im=Image.new('L',(128,56))
    d=ImageDraw.Draw(im)
    # Box stern, long parallel sides and a sharp west-facing prow.
    d.polygon([(0,28),(11,17),(26,8),(42,3),(123,3),(127,7),
               (127,49),(123,53),(42,53),(26,48),(11,39)],fill=1)
    d.polygon([(3,28),(13,18),(27,10),(42,5),(122,5),(125,8),
               (125,48),(122,51),(42,51),(27,46),(13,38)],fill=3)
    d.polygon([(7,28),(16,20),(29,12),(43,7),(120,7),(123,10),
               (123,46),(120,49),(43,49),(29,44),(16,36)],fill=4)
    d.line((7,28,16,20,29,12,43,7,120,7),fill=7)
    d.line((7,28,16,36,29,44,43,49),fill=6)
    d.line((43,50,120,50,124,47,124,9),fill=2,width=2)

    # Angled landing area runs from the stern toward port.
    d.polygon([(121,29),(121,42),(40,46),(26,42),(21,37),
               (40,35)],fill=2)
    d.line((121,29,40,35,21,37),fill=6)
    d.line((121,42,40,46,26,42),fill=6)
    for x in range(45,118,10):
        y=40-(x-45)//17
        d.line((x,y,x+4,y),fill=7)
    for x in (116,118,120):
        d.line((x,31,x,39),fill=7)
    # The catapult track stays on the centerline, forward of the elevator.
    d.polygon([(9,28),(19,23),(47,23),(47,32),(19,33)],fill=3)
    d.line((12,28,46,28),fill=7)
    d.line((16,30,46,30),fill=6)
    for x in range(19,43,5):
        d.point((x,24),fill=14);d.point((x,32),fill=14)
    d.line((15,26,17,28,15,30),fill=14)
    # Forward starboard island with radome, bridge glazing and exhausts.
    d.polygon([(82,9),(102,9),(106,13),(106,23),(102,27),
               (84,26),(80,21),(80,13)],fill=2)
    d.polygon([(83,10),(101,10),(104,13),(104,22),(101,24),
               (84,24),(82,21),(82,13)],fill=5)
    d.line((82,21,82,13,84,10,100,10),fill=7)
    d.rectangle((83,15,89,21),fill=8,outline=1)
    for y in (16,18,20):d.point((84,y),fill=10)
    for x in (97,100,102):d.line((x,18,x,22),fill=3)
    d.point((102,23),fill=12)
    # Elevator cover matches the 32x32 reactor overlay at (48,12).
    d.rectangle((49,13,78,42),fill=2,outline=1)
    d.rectangle((51,15,76,40),fill=4,outline=6)
    d.line((52,16,75,16),fill=7)
    d.line((63,17,63,39),fill=2,width=2)
    for y in (20,25,30,35):
        d.line((53,y,60,y),fill=5);d.line((66,y,74,y),fill=5)
    for x in (51,72):
        for y in (13,41):d.line((x,y,x+3,y),fill=14)
    for x,y in MOUNTS:
        d.ellipse((x-1,y-1,x+16,y+16),fill=2)
        d.arc((x-1,y-1,x+16,y+16),145,315,fill=7)
    for x in (46,58,72,85,98,120):
        d.point((x,9),fill=7)
        d.point((x,47),fill=6)
    for y in (20,35):d.rectangle((121,y,123,y+2),fill=12)
    return im


def spray(phase):
    im=Image.new('L',(32,16));d=ImageDraw.Draw(im)
    for side in (-1,1):
        path=[(2,8+side),(8,8+side*(2+phase)),(16,8+side*4),
              (23,8+side*(5+phase)),(29,8+side*6)]
        d.line(path,fill=9)
        d.line(path[1:3],fill=10)
        d.point(path[1],fill=7)
        d.point((25+phase,8+side*5),fill=10)
    return im


def launch_jet(phase):
    if phase==2:
        return base.jet(2)
    im=Image.new('L',(16,16));d=ImageDraw.Draw(im)
    if phase==0:
        for x,y in ((11,5),(13,7),(12,10),(14,11),(10,12)):
            d.line((x,y,x+1,y),fill=7)
    else:
        d.line((11,6,15,6),fill=13);d.line((12,9,15,9),fill=14)
    d.polygon([(0,7),(4,6),(7,5),(10,2),(12,2),(11,6),(14,7),
               (14,8),(11,9),(12,13),(10,13),(7,10),(4,9),(0,8)],fill=2)
    d.polygon([(1,7),(5,7),(8,6),(11,3),(10,7),(13,7),(13,8),
               (10,8),(11,12),(8,9),(5,8),(1,8)],fill=6)
    d.line((3,7,5,7,7,6),fill=7)
    d.point((5,8),fill=8)
    d.point((11,3),fill=12);d.point((11,12),fill=12)
    return im


def main():
    out=base.BOSS
    out.mkdir(parents=True,exist_ok=True)
    palette=base.colors(base.BOSS_COLORS)
    frames={'body':hull(),'core_exposed':base.elevator()}
    turrets=[]
    for corner,(x,y) in zip(('nw','ne','sw','se'),MOUNTS):
        key='turret_'+corner
        poses={pose:key+'_'+pose for pose in ('south','southeast','destroyed')}
        for pose,fid in poses.items():frames[fid]=base.deck_turret(pose)
        turrets.append(dict(id=key,offset=[x,y],size=[16,16],hit_rect=[x,y,16,16],
                            independently_destructible=True,**poses))
    for i in range(3):
        frames[f'rotor_{i}']=base.radar(i)
        frames[f'spray_{i}']=spray(i)
        frames[f'deck_jet_{i}']=launch_jet(i)
    for i in range(2):frames[f'muzzle_{i}']=base.flash(i)
    placement=dict(body='body',body_size=[128,56],palette='boss',turrets=turrets,
        core=dict(offset=[48,12],size=[32,32],hit_rect=[56,20,16,16],exposed_overlay='core_exposed'),
        rotors=[dict(id='radar',offset=[89,9],phase_offset=0)],
        rotor_frames=[f'rotor_{i}' for i in range(3)],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        spray=dict(frames=[f'spray_{i}' for i in range(3)],offsets=[[-11,13],[-11,26],[109,13],[109,27]]),
        catapult=dict(frames=[f'deck_jet_{i}' for i in range(3)],offset=[18,20]),
        draw_order=['spray','body','radar','core_if_exposed','turrets','deck_jet'])
    base.save(out/'indexed-source.json',[dict(id=fid,width=im.width,height=im.height,
        rows=base.encode(im)) for fid,im in frames.items()])
    base.save(out/'placement.json',placement)
    (out/'palette.rgb').write_bytes(bytes(c for rgb in palette for c in rgb))

    def compose(phase,exposed=False,launch=False):
        canvas=Image.new('RGBA',(168,84),(24,64,86,255))
        def paste(key,xy):
            canvas.alpha_composite(base.rgba(frames[key],palette),(xy[0]+18,xy[1]+8))
        for xy in placement['spray']['offsets']:paste(f'spray_{phase}',xy)
        paste('body',(0,0))
        paste(f'rotor_{phase}',placement['rotors'][0]['offset'])
        if exposed:paste('core_exposed',placement['core']['offset'])
        for item in turrets:paste(item['destroyed' if exposed else 'south'],item['offset'])
        if launch:
            x,y=placement['catapult']['offset']
            paste(f'deck_jet_{phase}',(x-phase*15,y+(12 if phase==2 else 0)))
        return canvas

    base.sheet(out/'boss-preview.png',[('Traeger / Gefecht',compose(0)),
        ('Aufzug offen / Reaktor',compose(1,True))],2,3)
    base.sheet(out/'launch-phases.png',[(label,compose(i,launch=True))
        for i,label in enumerate(('Katapult / Dampf','Abheben','Im Flug'))],3,3)
    base.sheet(out/'radar-wake-phases.png',[(f'Radar {i+1}',base.rgba(frames[f'rotor_{i}'],palette))
        for i in range(3)]+[(f'Gischt {i+1}',base.rgba(frames[f'spray_{i}'],palette)) for i in range(3)],3,4)
    animation=[compose(i,launch=True).convert('RGB').resize((504,252),Image.Resampling.NEAREST)
               for i in range(3)]
    animation[0].save(out/'boss-animation.png',save_all=True,append_images=animation[1:],
                      duration=[230,140,180],loop=0)


if __name__=='__main__':
    main()
