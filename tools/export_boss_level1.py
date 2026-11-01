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
    # Closed structural arms, not transparent black shading.
    for rotor_part in cfg['rotors']:
        x,y=rotor_part['offset'][0]+16,rotor_part['offset'][1]+16
        d.line((48,32,x,y),fill=1,width=14);d.line((48,32,x,y),fill=3,width=10)
        d.line((47,30,x-1,y-2),fill=5,width=3)
        d.ellipse((x-14,y-14,x+14,y+14),fill=1,outline=4,width=2)
        d.arc((x-14,y-14,x+14,y+14),180,290,fill=6,width=2)
        d.ellipse((x-11,y-11,x+11,y+11),fill=2,outline=3)
        for bx,by in ((x-10,y-10),(x+10,y-10),(x-10,y+10),(x+10,y+10)):d.point((bx,by),fill=12)
        d.rectangle((x-2,y-2,x+2,y+2),fill=5)
    outline=[(35,12),(60,12),(69,24),(69,43),(60,54),(35,54),(26,43),(26,24)]
    d.polygon(outline,fill=1)
    d.polygon([(36,14),(59,14),(66,25),(66,42),(58,51),(37,51),(29,42),(29,25)],fill=4)
    d.line((36,14,59,14,66,25),fill=6,width=2)
    d.line((36,14,29,25,29,42),fill=5,width=2)
    d.polygon([(38,18),(57,18),(62,26),(62,41),(56,47),(39,47),(33,41),(33,26)],fill=8)
    d.polygon([(40,20),(55,20),(59,27),(59,39),(54,44),(41,44),(36,39),(36,27)],fill=9)
    # Armoured centre hatch: shut until the four turrets have been destroyed.
    d.rectangle((40,25,55,40),fill=1);d.rectangle((42,26,53,38),fill=3)
    d.line((42,26,53,26),fill=6);d.line((48,27,48,38),fill=2)
    for y in (29,33,37):d.line((43,y,46,y),fill=5);d.line((50,y,52,y),fill=5)
    for x in (36,58):
        d.rectangle((x,24,x+1,38),fill=1)
        for y in (25,29,33):d.point((x,y),fill=12)
    for x in (31,61):
        d.rectangle((x,28,x+2,40),fill=2)
        for y in (29,32,35,38):d.line((x,y,x+2,y),fill=6)
    d.line((40,21,55,21),fill=10);d.point((38,23),fill=7);d.point((57,23),fill=7)
    d.polygon([(40,46),(55,46),(51,51),(44,51)],fill=11)
    d.line((43,47,52,47),fill=12)
    # Four independently drawn turret beds; actual guns are separate assets.
    for turret_part in cfg['turrets']:
        x,y=turret_part['offset'][0]+8,turret_part['offset'][1]+8
        d.ellipse((x-7,y-6,x+7,y+6),fill=1,outline=5)
    return p

def rotor(phase):
    p=Image.new('L',(32,32));d=ImageDraw.Draw(p);angle=math.radians(phase*60)
    dx=round(11*math.cos(angle));dy=round(11*math.sin(angle));cx=16;cy=16
    d.line((cx-dx+1,cy-dy+1,cx+dx+1,cy+dy+1),fill=2,width=3)
    d.line((cx-dx,cy-dy,cx+dx,cy+dy),fill=5,width=3)
    d.line((cx-dx,cy-dy-1,cx+dx,cy+dy-1),fill=6)
    d.point((cx-dx,cy-dy),fill=7);d.point((cx+dx,cy+dy),fill=4)
    d.ellipse((13,13,18,18),fill=3,outline=6);d.rectangle((15,15,16,16),fill=12)
    return p

def turret(mark,diagonal=False,destroyed=False):
    p=Image.new('L',(16,16));d=ImageDraw.Draw(p)
    d.polygon([(3,1),(12,1),(15,5),(15,11),(11,14),(3,14),(0,10),(0,5)],fill=1)
    d.ellipse((2,2,13,13),fill=3,outline=6)
    if destroyed:
        d.polygon([(3,4),(9,3),(12,7),(10,12),(4,11),(2,8)],fill=2)
        d.line((4,4,8,7,5,11),fill=1,width=2);d.line((10,5,7,9),fill=5)
        d.point((6,8),fill=11);d.point((8,7),fill=12);d.rectangle((11,10,13,11),fill=4)
    else:
        d.ellipse((4,3,11,10),fill=9,outline=10)
        if diagonal:
            d.line((7,9,12,14),fill=1,width=3);d.line((10,6,15,11),fill=1,width=3)
            d.line((7,9,12,14),fill=6);d.line((10,6,15,11),fill=5)
        else:
            for x in (6,10):
                d.rectangle((x-1,8,x+1,15),fill=1);d.line((x,9,x,14),fill=6 if x==6 else 5)
        d.rectangle((6,4,9,6),fill=4);d.point((6,4),fill=7)
    # Distinct identification lights per physical turret, including its stump.
    for i in range(mark):d.point((4+i*2,2),fill=12 if not destroyed else 11)
    return p

def damaged_core():
    p=Image.new('L',(32,32));d=ImageDraw.Draw(p)
    d.polygon([(7,4),(24,4),(29,11),(29,23),(23,29),(8,29),(3,23),(3,11)],fill=1)
    d.line((7,4,24,4,29,11),fill=5,width=2)
    d.ellipse((9,9,23,24),fill=2,outline=11)
    d.ellipse((11,11,21,22),fill=14);d.rectangle((14,13,18,20),fill=15)
    d.line((6,11,11,13,8,18,12,22,7,27),fill=11)
    d.line((24,8,21,12,25,18,22,25),fill=12)
    d.rectangle((6,27,9,28),fill=5);d.rectangle((24,22,26,24),fill=4)
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
    manifest=dict(schema=1,body_size=[96,64],palette=pal,palette_count=1,frames=len(records),rrb_glyphs=len(rrb)//64,rrb_bytes=len(rrb),budget_bytes=9*1024,
                  integrated=False,hardware_tested=False,provenance=cfg['provenance'])
    manifest['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Boss: 96x64 body, 4 distinct turrets (south/SE/destroyed), 3 rotor phases; {len(rrb)//64} glyphs / {len(rrb)} bytes.')

if __name__=='__main__':main()
