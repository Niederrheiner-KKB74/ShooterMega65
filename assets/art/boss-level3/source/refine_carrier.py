"""Export the long-hulled Offshore carrier and its assembled previews."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'assets/art/level3/source'))
import generate_vehicles as base

MOUNTS = ((4,13),(60,13),(4,77),(60,77))


def hull():
    im=Image.new('L',(80,128))
    d=ImageDraw.Draw(im)
    d.polygon([(7,3),(72,3),(77,8),(77,91),(73,103),(61,115),
               (40,127),(19,115),(7,103),(3,91),(3,8)],fill=1)
    d.polygon([(8,5),(71,5),(75,9),(75,90),(71,102),(60,113),
               (40,125),(20,113),(9,102),(5,90),(5,9)],fill=3)
    d.polygon([(10,8),(69,8),(72,11),(72,90),(68,101),(58,111),
               (40,122),(22,111),(12,101),(8,90),(8,11)],fill=4)
    d.line((8,89,8,11,10,8,69,8),fill=7)
    d.line((9,91,13,101,23,112,40,122),fill=6)
    d.line((73,12,73,90,69,101,59,112,40,123),fill=2,width=2)
    # Landing strip crosses the deck from the port quarter.
    d.polygon([(15,10),(28,10),(53,101),(42,113),(39,109),(13,21)],fill=2)
    d.line((15,11,13,21,39,109),fill=6)
    d.line((28,11,53,101),fill=6)
    for y in range(15,104,9):
        x=21+(y-15)*25//91
        d.line((x,y,x+1,y+4),fill=7)
    for y in (12,15,18):
        x=17+(y-12)//3
        d.line((x,y,x+7,y),fill=7)
    # Island superstructure and bridge glazing on the starboard side.
    d.polygon([(59,34),(69,34),(72,38),(72,65),(68,70),(58,68),(55,63),
               (55,40)],fill=2)
    d.polygon([(59,36),(68,36),(70,39),(70,64),(66,67),(59,65),(57,61),
               (57,40)],fill=5)
    d.line((57,60,57,40,59,36,68,36),fill=7)
    d.rectangle((58,51,69,56),fill=8,outline=1)
    for x in (59,63,67):d.line((x,52,x,55),fill=10)
    for y in (59,61,63):d.line((59,y,66,y),fill=3)
    d.point((68,64),fill=12)
    # Recessed elevator between the landing strip and the island.
    d.rectangle((24,45,53,74),fill=2,outline=1)
    d.rectangle((26,47,51,72),fill=4,outline=6)
    d.line((27,48,50,48),fill=7)
    d.line((38,49,38,71),fill=2,width=2)
    for y in (52,57,62,67):
        d.line((28,y,35,y),fill=5);d.line((41,y,49,y),fill=5)
    for x in (26,47):
        for y in (45,73):d.line((x,y,x+3,y),fill=14)
    # Straight catapult rails run from the elevator toward the narrow bow.
    d.polygon([(32,76),(47,76),(47,110),(40,119),(33,111)],fill=3)
    d.line((38,77,38,114),fill=7);d.line((41,77,41,116),fill=6)
    for x in (34,45):d.line((x,80,x,107),fill=5)
    for y in (81,86,91):
        for x in (33,44):d.point((x,y),fill=14)
    for x in range(34,46,3):d.line((x,110,x-1,112),fill=14)
    for x,y in MOUNTS:
        d.ellipse((x-1,y-1,x+16,y+16),fill=2)
        d.arc((x-1,y-1,x+16,y+16),145,315,fill=7)
    for y in (32,41,50,59,68,73):
        d.line((10,y,14,y),fill=6)
        d.point((69,y),fill=6)
    for x in (17,59):d.rectangle((x,6,x+2,7),fill=12)
    return im


def main():
    out=base.BOSS
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
        frames[f'spray_{i}']=base.spray(i)
        frames[f'deck_jet_{i}']=base.jet(i)
    for i in range(2):frames[f'muzzle_{i}']=base.flash(i)
    placement=dict(body='body',body_size=[80,128],palette='boss',turrets=turrets,
        core=dict(offset=[23,44],size=[32,32],hit_rect=[31,52,16,16],exposed_overlay='core_exposed'),
        rotors=[dict(id='radar',offset=[56,34],phase_offset=0)],
        rotor_frames=[f'rotor_{i}' for i in range(3)],
        muzzle=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15]),
        spray=dict(frames=[f'spray_{i}' for i in range(3)],offsets=[[3,-10],[45,-10],[6,111],[42,111]]),
        catapult=dict(frames=[f'deck_jet_{i}' for i in range(3)],offset=[32,92]),
        draw_order=['spray','body','radar','core_if_exposed','turrets','deck_jet'])
    base.save(out/'indexed-source.json',[dict(id=fid,width=im.width,height=im.height,
        rows=base.encode(im)) for fid,im in frames.items()])
    base.save(out/'placement.json',placement)

    def compose(phase,exposed=False,launch=False):
        canvas=Image.new('RGBA',(96,160),(24,64,86,255))
        def paste(key,xy):
            canvas.alpha_composite(base.rgba(frames[key],palette),(xy[0]+8,xy[1]+12))
        for xy in placement['spray']['offsets']:paste(f'spray_{phase}',xy)
        paste('body',(0,0))
        paste(f'rotor_{phase}',placement['rotors'][0]['offset'])
        if exposed:paste('core_exposed',placement['core']['offset'])
        for item in turrets:paste(item['destroyed' if exposed else 'south'],item['offset'])
        if launch:
            x,y=placement['catapult']['offset']
            paste(f'deck_jet_{phase}',(x,y+phase*15))
        return canvas

    base.sheet(out/'boss-preview.png',[('Traeger / Gefecht',compose(0)),
        ('Aufzug offen / Reaktor',compose(1,True))],2,3)
    base.sheet(out/'launch-phases.png',[(label,compose(i,launch=True))
        for i,label in enumerate(('Katapult / Dampf','Abheben','Im Flug'))],3,3)
    animation=[compose(i,launch=True).convert('RGB').resize((288,480),Image.Resampling.NEAREST)
               for i in range(3)]
    animation[0].save(out/'boss-animation.png',save_all=True,append_images=animation[1:],
                      duration=[230,140,180],loop=0)


if __name__=='__main__':
    main()
