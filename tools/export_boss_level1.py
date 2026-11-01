"""Native 96x64 quadrotor boss, independently destructible turrets, bounded RRB pack."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/boss-level1';OUT=BASE/'generated'

def rgba(p,pal):
    out=Image.new('RGBA',p.size);out.putdata([tuple(pal[i])+(255 if i else 0,) for i in p.tobytes()]);return out

def body(cfg):
    p=Image.new('L',(96,64));d=ImageDraw.Draw(p)
    # Armoured octagonal nacelles, gear rims and load-bearing shoulder joints.
    # Shadow holes are painted with opaque index 1, never transparent index 0.
    for rotor_part in cfg['rotors']:
        x,y=rotor_part['offset'][0]+16,rotor_part['offset'][1]+16
        d.line((48,32,x,y),fill=1,width=17);d.line((48,32,x,y),fill=3,width=13)
        d.line((47,29,x-1,y-3),fill=5,width=4)
        jx,jy=(48+x)//2,(32+y)//2
        d.ellipse((jx-5,jy-5,jx+5,jy+5),fill=1,outline=6)
        d.ellipse((jx-3,jy-3,jx+3,jy+3),fill=4);d.point((jx-1,jy-2),fill=7)
        rim=[(x-9,y-15),(x+8,y-15),(x+15,y-8),(x+15,y+8),(x+8,y+15),(x-9,y+15),(x-15,y+8),(x-15,y-8)]
        d.polygon(rim,fill=1);d.line(rim+[rim[0]],fill=4,width=2)
        d.polygon([(x-8,y-14),(x+7,y-14),(x+10,y-11),(x-10,y-11)],fill=5)
        d.line((x-8,y-14,x+7,y-14),fill=7)
        d.polygon([(x-14,y-8),(x-11,y-10),(x-11,y+10),(x-14,y+7)],fill=6)
        d.polygon([(x+12,y-8),(x+14,y-6),(x+14,y+7),(x+11,y+10)],fill=2)
        d.polygon([(x-9,y+12),(x+8,y+12),(x+6,y+14),(x-7,y+14)],fill=11)
        d.line((x-7,y+12,x+6,y+12),fill=12)
        d.ellipse((x-12,y-12,x+12,y+12),fill=1,outline=5)
        d.ellipse((x-10,y-10,x+10,y+10),fill=2)
        for angle in range(0,360,45):
            a=math.radians(angle);xx=x+round(11*math.cos(a));yy=y+round(11*math.sin(a))
            d.point((xx,yy),fill=6 if angle>=180 else 4)
        for dx,dy in ((-11,-11),(11,-11),(-11,11),(11,11)):
            bx,by=x+dx,y+dy;d.rectangle((bx-1,by-1,bx+1,by+1),fill=1);d.point((bx-1,by-1),fill=7);d.point((bx,by),fill=5)
        d.line((x-5,y-7,x+6,y-7),fill=3);d.line((x-6,y+7,x+5,y+7),fill=3)
        d.ellipse((x-4,y-4,x+4,y+4),fill=3,outline=4)
    # Wider angular carapace; layered plates replace the earlier flat green slab.
    outline=[(38,4),(57,4),(63,10),(65,19),(72,27),(71,43),(62,53),(55,61),(48,63),(40,61),(33,53),(24,43),(23,27),(31,18),(32,10)]
    d.polygon(outline,fill=1)
    d.polygon([(38,6),(56,6),(61,11),(62,21),(69,28),(68,42),(59,51),(53,58),(48,60),(42,58),(36,51),(27,42),(26,28),(34,20),(35,11)],fill=3)
    d.line((38,6,56,6,61,11),fill=6,width=2)
    d.line((38,6,35,11,34,20,26,28,27,41),fill=5,width=2)
    d.line((69,28,68,42,59,51,53,58),fill=2,width=2)
    # Rear sensor slit and antennae, scaled like the red armoured aircraft.
    d.rectangle((42,5,53,9),fill=1);d.line((43,6,52,6),fill=11)
    d.point((44,6),fill=12);d.point((51,6),fill=12)
    d.line((40,1,40,5),fill=5);d.point((40,0),fill=11)
    d.line((55,2,55,5),fill=4);d.point((55,1),fill=7)
    # Red shoulder plates, bevels and exposed hydraulic pistons.
    left=[(29,25),(35,21),(39,25),(36,43),(32,48),(27,41)]
    right=[(58,21),(66,25),(69,40),(64,48),(59,43),(56,26)]
    d.polygon(left,fill=11);d.line((29,25,35,21,38,25),fill=12)
    d.polygon(right,fill=11);d.line((58,21,65,25),fill=6)
    d.line((28,29,28,39),fill=5);d.line((66,29,67,39),fill=2)
    for x in (30,62):
        d.rectangle((x,29,x+3,39),fill=1)
        for y in (30,33,36):d.line((x,y,x+2,y),fill=5);d.point((x,y),fill=6)
    for x in (35,59):
        d.line((x,27,x,41),fill=1,width=3);d.line((x-1,28,x-1,38),fill=6)
        d.rectangle((x-1,39,x+1,42),fill=4)
    # Two-piece reactor armour, still opaque and closed in stage one.
    d.polygon([(41,21),(54,21),(59,26),(58,40),(54,45),(41,45),(36,40),(36,26)],fill=1)
    d.line((41,21,54,21,59,26),fill=6);d.line((41,21,36,26,36,39),fill=5)
    d.polygon([(41,24),(46,24),(46,40),(42,42),(39,38),(39,27)],fill=4)
    d.polygon([(49,24),(54,24),(56,28),(55,38),(51,42),(49,40)],fill=3)
    d.line((41,24,46,24),fill=7);d.line((49,24,54,24),fill=5)
    for y in (28,32,36):
        d.line((40,y,44,y),fill=2);d.point((40,y),fill=6)
        d.line((51,y,54,y),fill=1);d.point((51,y),fill=4)
    d.line((47,25,47,39),fill=11);d.line((48,25,48,39),fill=1)
    d.rectangle((45,30,49,33),fill=1);d.line((46,31,48,31),fill=12)
    d.point((37,25),fill=7);d.point((57,39),fill=5)
    # Forward keel: angry visor, stacked chin armour and sharp nose.
    d.polygon([(37,47),(58,47),(56,55),(48,62),(40,55)],fill=2)
    d.polygon([(39,48),(56,48),(54,54),(48,59),(42,54)],fill=11)
    d.line((40,48,55,48),fill=6)
    d.polygon([(41,50),(54,50),(51,53),(44,53)],fill=1)
    d.line((43,51,46,51),fill=12);d.line((49,51,52,51),fill=12)
    d.line((44,56,48,60,52,56),fill=5)
    for x,y in ((28,27),(65,27),(28,42),(65,42),(38,46),(57,46),(44,12),(51,12)):
        d.point((x,y),fill=7);d.point((x+1,y+1),fill=1)
    # The four gun sockets remain separate from the detachable gun images.
    for turret_part in cfg['turrets']:
        x,y=turret_part['offset'][0]+8,turret_part['offset'][1]+8
        d.ellipse((x-7,y-7,x+7,y+7),fill=1,outline=4)
        d.arc((x-7,y-7,x+7,y+7),180,300,fill=6)
    return p

def rotor(phase):
    p=Image.new('L',(32,32));d=ImageDraw.Draw(p)
    # Four swept airfoils, not a thin stick; three 30-degree phase steps.
    blade=[(3,-1),(7,-2),(11,-4),(12,-2),(10,1),(5,2),(3,1)]
    for arm in range(4):
        angle=math.radians(phase*30+arm*90);c=math.cos(angle);s=math.sin(angle)
        points=[(16+round(x*c-y*s),16+round(x*s+y*c)) for x,y in blade]
        d.polygon([(x+1,y+1) for x,y in points],fill=1)
        d.polygon(points,fill=4 if arm%2 else 5)
        d.line(points[:4],fill=6)
        d.point(points[2],fill=7);d.point(points[3],fill=12)
    d.ellipse((12,12,19,19),fill=1,outline=6)
    d.ellipse((14,14,17,17),fill=3);d.point((14,14),fill=7)
    d.rectangle((15,15,16,16),fill=11)
    return p

def turret(mark,diagonal=False,destroyed=False):
    p=Image.new('L',(16,16));d=ImageDraw.Draw(p)
    d.polygon([(3,1),(12,1),(15,5),(15,11),(11,14),(3,14),(0,10),(0,5)],fill=1)
    d.ellipse((2,2,13,13),fill=2,outline=5)
    if destroyed:
        d.polygon([(3,3),(10,3),(13,7),(11,12),(4,12),(2,8)],fill=3)
        d.polygon([(5,4),(9,5),(11,8),(8,11),(4,8)],fill=1)
        d.line((3,4,7,7,4,11),fill=5);d.line((10,4,8,7,12,10),fill=2)
        d.rectangle((10,11,13,13),fill=4);d.point((10,11),fill=6)
        d.line((3,11,2,14),fill=1,width=2);d.point((3,12),fill=5)
        d.point((6,8),fill=11);d.point((8,7),fill=12);d.point((9,9),fill=11)
    else:
        d.polygon([(5,1),(10,1),(13,4),(12,9),(10,11),(4,10),(2,7),(2,4)],fill=1)
        d.polygon([(5,2),(10,2),(11,4),(11,8),(9,9),(4,8),(3,5)],fill=4)
        d.line((5,2,10,2,11,4),fill=7);d.line((4,3,3,5,4,8),fill=6)
        d.rectangle((5,4,10,6),fill=1);d.line((5,5,10,5),fill=11);d.point((6,5),fill=12)
        if diagonal:
            d.line((7,9,12,14),fill=1,width=3);d.line((10,6,15,11),fill=1,width=3)
            d.line((7,9,12,14),fill=6);d.line((10,6,15,11),fill=5)
            d.point((12,14),fill=1);d.point((15,11),fill=1)
        else:
            for x in (6,10):
                d.rectangle((x-1,8,x+1,15),fill=1);d.line((x,9,x,14),fill=6 if x==6 else 5)
                d.line((x-1,10,x+1,10),fill=3);d.line((x-1,13,x+1,13),fill=4)
                d.point((x,15),fill=1)
        d.point((2,5),fill=7);d.point((12,8),fill=2)
    # Distinct identification lights per physical turret, including its stump.
    for i in range(mark):d.point((4+i*2,2),fill=12 if not destroyed else 11)
    return p

def damaged_core():
    p=Image.new('L',(32,32));d=ImageDraw.Draw(p)
    d.polygon([(8,4),(23,4),(28,10),(28,23),(23,29),(8,29),(3,23),(3,10)],fill=1)
    d.line((8,4,23,4,28,10),fill=6)
    d.polygon([(6,10),(11,8),(9,15),(11,22),(7,26),(4,22)],fill=11)
    d.polygon([(23,8),(27,11),(26,22),(22,27),(23,19),(21,14)],fill=4)
    d.line((6,10,9,9,7,14),fill=12);d.line((23,8,26,11),fill=7)
    d.ellipse((9,9,23,25),fill=2,outline=5)
    for angle in range(0,360,45):
        a=math.radians(angle);x=16+round(7*math.cos(a));y=17+round(8*math.sin(a));d.point((x,y),fill=12)
    d.ellipse((11,11,21,23),fill=14);d.rectangle((14,13,18,21),fill=15)
    d.line((12,14,20,14),fill=7);d.line((12,19,20,19),fill=3)
    d.rectangle((15,15,17,18),fill=7)
    d.line((6,16,9,18,5,24),fill=5);d.line((26,15,23,19,27,25),fill=11)
    d.rectangle((9,27,13,29),fill=4);d.line((9,27,13,27),fill=6)
    d.rectangle((20,26,23,29),fill=2);d.point((20,26),fill=12)
    return p

def muzzle(phase):
    p=Image.new('L',(16,16));d=ImageDraw.Draw(p)
    d.polygon([(7,0),(9,5),(12,3),(10,8),(13,12),(9,10),(7,15),(6,10),(2,12),(5,7),(3,3),(6,5)],fill=12)
    if phase:d.polygon([(7,2),(9,7),(10,10),(7,12),(5,8)],fill=13)
    else:d.rectangle((6,5,8,10),fill=13)
    return p

def tile_ncm(p):
    a=p.tobytes();assert p.size==(16,8);return bytes(a[i]|a[i+1]<<4 for i in range(0,128,2))

def main():
    cfg=json.loads((BASE/'source/design.json').read_text());pal=cfg['palette'];OUT.mkdir(parents=True,exist_ok=True)
    assert cfg['body_size']==[96,64]
    images={'body':body(cfg),'core_exposed':damaged_core()}
    for i in range(3):images[f'rotor_{i}']=rotor(i)
    for t in cfg['turrets']:
        images[t['id']+'_south']=turret(t['mark'])
        images[t['id']+'_southeast']=turret(t['mark'],True)
        images[t['id']+'_destroyed']=turret(t['mark'],destroyed=True)
    for i in range(2):images[f'muzzle_{i}']=muzzle(i)
    raw=bytearray();nc=bytearray();fc=bytearray();rrb=bytearray(64);records=[]
    for name,p in images.items():
        w,h=p.size;rgba(p,pal).save(OUT/(name+'.png'))
        record=dict(id=name,width=w,height=h,palette='boss',indices_offset=len(raw),ncm_offset=len(nc),fcm_offset=len(fc),rrb_base=len(rrb)//64,
                    rows=[p.tobytes()[y*w:(y+1)*w].hex() for y in range(h)])
        records.append(record);raw.extend(p.tobytes())
        for y in range(0,h,8):
            for x in range(0,w,16):nc.extend(tile_ncm(p.crop((x,y,x+16,y+8))))
            for x in range(0,w,8):fc.extend(p.crop((x,y,x+8,y+8)).tobytes())
        for x in range(0,w,16):
            for y in range(0,h,8):rrb.extend(tile_ncm(p.crop((x,y,x+16,y+8))))
            rrb.extend(bytes(64))
    assert len(rrb)<=9*1024,(len(rrb),'boss graphics exceed spec budget')
    (OUT/'indexed-source.json').write_text(json.dumps(records,indent=2)+'\n')
    for name,data in [('boss.indices.bin',raw),('boss.ncm.bin',nc),('boss.fcm.bin',fc),('boss.rrb.bin',rrb),('palette.rgb',bytes(v for c in pal for v in c)),
                      ('palette.palregs.bin',bytes(c[ch]%16*16+c[ch]//16 for ch in range(3) for c in pal))]: (OUT/name).write_bytes(data)
    placement=dict(body='body',body_size=[96,64],palette='boss',turrets=[],
                   rotors=[dict(**r,role='visual_only',destructible=False,collidable=False) for r in cfg['rotors']],
                   core=cfg['core'],mechanic=cfg['mechanic'],draw_order=['body','rotors','exposed_core_if_unlocked','turrets','optional_muzzle'])
    for t in cfg['turrets']:
        placement['turrets'].append(dict(id=t['id'],offset=t['offset'],size=[16,16],south=t['id']+'_south',southeast=t['id']+'_southeast',destroyed=t['id']+'_destroyed',
                                        hit_rect=t['offset']+[16,16],independently_destructible=True))
    placement['rotor_frames']=['rotor_0','rotor_1','rotor_2'];placement['core']['exposed_overlay']='core_exposed'
    placement['muzzle']=dict(frames=['muzzle_0','muzzle_1'],south_offset_from_turret=[0,15],note='Optional effect may extend beyond body bounds; rotate with gun direction.')
    (OUT/'placement.json').write_text(json.dumps(placement,indent=2)+'\n')
    lines=['// Local indices and glyph bases. Choose/remap a boss bank before runtime import.']
    for i,r in enumerate(records):lines.append(f'.const BOSS_{r["id"].upper()} = {i}')
    for label,values in [('base_lo',[r['rrb_base']&255 for r in records]),('base_hi',[r['rrb_base']>>8 for r in records]),('w',[r['width']//16 for r in records]),('h',[r['height']//8 for r in records])]:
        lines.append('boss_'+label+': .byte '+','.join(str(v) for v in values))
    (OUT/'boss-frames.inc').write_text('\n'.join(lines)+'\n')
    # Horizontal strips only for actual animation: direction/death states stay separate.
    for prefix,count in [('rotor',3),('muzzle',2)]:
        w,h=images[prefix+'_0'].size;strip=Image.new('RGBA',(w*count,h))
        for i in range(count):strip.paste(rgba(images[f'{prefix}_{i}'],pal),(i*w,0))
        strip.save(OUT/(prefix+'-animation.png'))
    composites=[]
    for phase in range(3):
        p=images['body'].copy()
        for rotor_part in cfg['rotors']:
            r=images[f'rotor_{(phase+rotor_part["phase_offset"])%3}'];p.paste(r,tuple(rotor_part['offset']),r.point(lambda v:255 if v else 0))
        for t in cfg['turrets']:
            r=images[t['id']+'_south'];p.paste(r,tuple(t['offset']),r.point(lambda v:255 if v else 0))
        composites.append(rgba(p,pal))
    composites[0].save(OUT/'assembled.png')
    large=[p.resize((576,384),Image.Resampling.NEAREST) for p in composites]
    large[0].save(OUT/'animated-boss.webp',save_all=True,append_images=large[1:],duration=100,loop=0,lossless=True)
    p=images['body'].copy()
    for rotor_part in cfg['rotors']:
        r=images['rotor_0'];p.paste(r,tuple(rotor_part['offset']),r.point(lambda v:255 if v else 0))
    r=images['core_exposed'];p.paste(r,tuple(cfg['core']['offset']),r.point(lambda v:255 if v else 0))
    for t in cfg['turrets']:
        r=images[t['id']+'_destroyed'];p.paste(r,tuple(t['offset']),r.point(lambda v:255 if v else 0))
    dead=rgba(p,pal);dead.save(OUT/'all-turrets-destroyed.png')
    preview=Image.new('RGB',(1180,460),(18,24,32));d=ImageDraw.Draw(preview)
    d.text((12,8),'96x64 Quadrocopter / vier separate Tuerme',fill='white');preview.paste(large[0],(12,30),large[0])
    d.text((600,8),'Alle Tuerme zerstoert: Kern verwundbar',fill='white');enlarged=dead.resize((576,384),Image.Resampling.NEAREST);preview.paste(enlarged,(600,30),enlarged)
    d.text((12,430),f'{len(rrb)//64} guarded glyphs / {len(rrb)} bytes (< 9 KB); one palette; all art standalone.',fill=(180,205,210))
    preview.save(OUT/'preview.png')
    previous=BASE/'source/previous-assembled.png'
    if previous.exists():
        comparison=Image.new('RGB',(820,390),(18,24,32));cd=ImageDraw.Draw(comparison)
        cd.text((12,8),'Bisheriger Entwurf',fill='white');cd.text((420,8),'Neue schwere Panzerung',fill='white')
        old=Image.open(previous).convert('RGBA');oldlarge=old.resize((384,256),Image.Resampling.NEAREST)
        newlarge=composites[0].resize((384,256),Image.Resampling.NEAREST)
        comparison.paste(oldlarge,(12,30),oldlarge);comparison.paste(newlarge,(420,30),newlarge)
        comparison.paste(old,(150,310),old);comparison.paste(composites[0],(558,310),composites[0])
        cd.text((12,292),'1x: 96x64',fill=(180,205,210));cd.text((420,292),'1x: 96x64',fill=(180,205,210))
        comparison.save(OUT/'comparison.png')
    manifest=dict(schema=1,body_size=[96,64],palette=pal,palette_count=1,frames=len(records),rrb_glyphs=len(rrb)//64,rrb_bytes=len(rrb),budget_bytes=9*1024,
                  integrated=False,hardware_tested=False,provenance=cfg['provenance'])
    manifest['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Boss: 96x64 body, 4 distinct turrets (south/SE/destroyed), 3 rotor phases; {len(rrb)//64} glyphs / {len(rrb)} bytes.')

if __name__=='__main__':main()
