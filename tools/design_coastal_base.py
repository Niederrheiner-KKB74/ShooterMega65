#!/usr/bin/env python3
"""Reproduce the four-minute coastal/forest/road/base level and native tiles."""
import hashlib
import json
import math
import re
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/coastal-base';OUT=BASE/'generated'
NAT=[[0,0,0],[13,54,94],[18,83,128],[40,126,168],[161,207,184],[146,114,65],[195,164,99],[228,202,135],[32,65,35],[51,90,42],[78,116,49],[20,49,29],[37,76,37],[73,106,45],[78,60,36],[107,120,112]]
MIL=[[0,0,0],[18,83,128],[40,126,168],[32,65,35],[51,90,42],[78,116,49],[55,62,67],[76,84,85],[143,150,139],[220,193,92],[208,211,190],[43,50,53],[107,115,115],[158,165,152],[159,66,46],[25,35,32]]


def ncm(p):
    a=p.tobytes();return bytes(a[i]|a[i+1]<<4 for i in range(0,len(a),2))


def rgba(p,pal):
    im=Image.new('RGBA',p.size);im.putdata([tuple(pal[i])+(255,) for i in p.getdata()]);return im


def grass(size,variant=0,military=False):
    im=Image.new('L',size)
    values=[]
    for y in range(size[1]):
        for x in range(size[0]):
            q=(x*17+y*29+variant*11)%53;v=8 if q<4 else 10 if q<8 else 9
            values.append(v-5 if military else v)
    im.putdata(values);return im


def main():
    cfg=json.loads((BASE/'source/design.json').read_text());OUT.mkdir(parents=True,exist_ok=True)
    palettes=dict(water=NAT,nature=NAT,structures=MIL,fixed_targets=cfg['fixed_targets_palette'])
    tiles=[];names={}
    def add(name,p,pal):
        assert p.size==(16,16) and max(p.tobytes())<16 and min(p.tobytes())>0
        names[name]=len(tiles);tiles.append(dict(name=name,image=p,palette=pal));return names[name]
    for variant in range(3):
        sea=Image.new('L',(16,16),2);d=ImageDraw.Draw(sea)
        for y in range(16):
            for x in range(16):
                q=(x*7+y*13+variant*17)%67
                if q<5:d.point((x,y),fill=1)
                elif q==10:d.line((x,y,min(x+2,15),y),fill=3)
        add('sea'+str(variant),sea,'water');add('grass'+str(variant),grass((16,16),variant),'nature')
    for variant in range(6):
        p=grass((16,16),variant%3);d=ImageDraw.Draw(p)
        centres=[(5,5),(11,10)] if variant<3 else [(7,8)]
        for cx,cy in centres:
            d.rectangle((cx,cy+2,cx+1,cy+5),fill=14)
            d.ellipse((cx-4,cy-3,cx+4,cy+4),fill=11)
            d.ellipse((cx-3,cy-3,cx+3,cy+2),fill=12)
            d.ellipse((cx-2,cy-3,cx+1,cy),fill=13)
        add('forest'+str(variant),p,'nature')
    # Marching-square coast: matching corner signs guarantee compatible borders.
    for mask in range(1,15):
        p=Image.new('L',(16,16));a=[8 if mask&(1<<i) else -8 for i in range(4)]
        for y in range(16):
            for x in range(16):
                u=(x+.5)/16;v=(y+.5)/16
                dist=(a[0]*(1-u)+a[1]*u)*(1-v)+(a[2]*(1-u)+a[3]*u)*v
                q=(x*17+y*29)%53
                value=(1 if q<4 else 3 if q==10 else 2) if dist<-1 else 4 if dist<0 else 7 if dist<1 else 6 if dist<3 else 8 if q<4 else 10 if q<8 else 9
                p.putpixel((x,y),value)
        add('coast'+str(mask),p,'water')
    # Road blocks: 32x32 geometry split into four 16x16 tiles.
    # N/E/S/W bits: 1,2,4,8. Curbs are painted before interiors to join cleanly.
    road_masks=(5,10,3,6,9,12,7,15,1,4)
    for mask in road_masks:
        p=grass((32,32),0,True);d=ImageDraw.Draw(p)
        outer={1:(6,0,25,19),2:(12,6,31,25),4:(6,12,25,31),8:(0,6,19,25)}
        inner={1:(8,0,23,18),2:(13,8,31,23),4:(8,13,23,31),8:(0,8,18,23)}
        for bit,box in outer.items():
            if mask&bit:d.rectangle(box,fill=8)
        for bit,box in inner.items():
            if mask&bit:d.rectangle(box,fill=7)
        if mask&5:
            for y in range(0,32,8):
                if (y<14 and mask&1) or (y>16 and mask&4):d.line((15,y,15,min(y+3,31)),fill=9)
        if mask&10:
            for x in range(0,32,8):
                if (x<14 and mask&8) or (x>16 and mask&2):d.line((x,15,min(x+3,31),15),fill=9)
        for yy in range(2):
            for xx in range(2):add(f'road{mask}_{xx}_{yy}',p.crop((xx*16,yy*16,xx*16+16,yy*16+16)),'structures')
    # Bridge and land approaches: deck and rail alignment match road NS edges.
    for kind in ('bridge','bridge_enter','bridge_exit'):
        p=Image.new('L',(32,32),1) if kind=='bridge' else grass((32,32),0,True);d=ImageDraw.Draw(p)
        if kind=='bridge_enter':d.rectangle((0,0,31,7),fill=1);d.rectangle((0,8,31,10),fill=8)
        if kind=='bridge_exit':d.rectangle((0,11,31,31),fill=1);d.rectangle((0,8,31,10),fill=8)
        d.rectangle((6,0,25,31),fill=8);d.rectangle((8,0,23,31),fill=7)
        for y in range(0,32,8):d.line((15,y,15,y+3),fill=9)
        if kind=='bridge':
            for y in range(0,32,4):d.rectangle((5,y,6,y+1),fill=10);d.rectangle((25,y,26,y+1),fill=10)
        for yy in range(2):
            for xx in range(2):add(f'{kind}_{xx}_{yy}',p.crop((xx*16,yy*16,xx*16+16,yy*16+16)),'structures')
    # Native base blocks: four roof/concrete/helipad tiles each.
    for kind in ('hangar','depot','helipad','concrete'):
        p=Image.new('L',(32,32),12);d=ImageDraw.Draw(p)
        if kind in ('hangar','depot'):
            d.rectangle((1,2,30,30),fill=11);d.rectangle((2,2,28,27),fill=12)
            d.line((2,2,28,2),fill=13,width=2);d.line((2,2,2,27),fill=13)
            for y in (8,15,22):d.line((4,y,27,y),fill=11)
            d.rectangle((11,25,21,31),fill=6)
            if kind=='depot':d.rectangle((9,8,22,20),fill=14);d.line((12,14,19,14),fill=10);d.line((16,11,16,17),fill=10)
        elif kind=='helipad':
            d.rectangle((2,2,29,29),outline=9,width=2);d.line((11,9,11,22),fill=10,width=2);d.line((21,9,21,22),fill=10,width=2);d.line((11,15,21,15),fill=10,width=2)
        else:
            d.line((0,0,31,0),fill=13);d.line((0,0,0,31),fill=13);d.line((31,0,31,31),fill=11);d.line((0,31,31,31),fill=11)
        for yy in range(2):
            for xx in range(2):add(f'{kind}_{xx}_{yy}',p.crop((xx*16,yy*16,xx*16+16,yy*16+16)),'structures')
    for orient in ('h','v'):
        p=grass((16,16),0,True);d=ImageDraw.Draw(p)
        if orient=='h':
            d.line((0,7,15,7),fill=11);d.line((0,6,15,6),fill=8)
            for x in (2,10):d.line((x,4,x,9),fill=13)
        else:
            d.line((7,0,7,15),fill=11);d.line((6,0,6,15),fill=8)
            for y in (2,10):d.line((4,y,9,y),fill=13)
        add('fence_'+orient,p,'structures')
    # Checkpoint stop line and guard posts, aligned to the NS road geometry.
    checkpoint=grass((32,32),0,True);d=ImageDraw.Draw(checkpoint)
    d.rectangle((6,0,25,31),fill=8);d.rectangle((8,0,23,31),fill=7)
    for y in (0,8,24):d.line((15,y,15,y+3),fill=9)
    d.line((8,18,23,18),fill=10)
    for x in (0,27):
        d.rectangle((x,12,x+4,21),fill=11);d.rectangle((x,12,x+3,19),fill=12);d.line((x,12,x+3,12),fill=13)
    for yy in range(2):
        for xx in range(2):add(f'checkpoint_{xx}_{yy}',checkpoint.crop((xx*16,yy*16,xx*16+16,yy*16+16)),'structures')
    bunker=Image.new('L',(32,32),3);d=ImageDraw.Draw(bunker)
    d.rectangle((2,5,29,27),fill=2);d.rectangle((3,5,27,24),fill=4)
    d.line((3,5,27,5),fill=6,width=2);d.line((3,5,3,24),fill=5)
    d.rectangle((7,12,24,18),fill=1);d.line((7,11,24,11),fill=6);d.rectangle((12,24,20,31),fill=2)
    for yy in range(2):
        for xx in range(2):add(f'bunker_{xx}_{yy}',bunker.crop((xx*16,yy*16,xx*16+16,yy*16+16)),'fixed_targets')
    # Guaranteed opaque road-compatible spawn surface, useful for checkpoints.
    assert len(tiles)<=126, len(tiles)
    rows=[]
    def shore(r):
        if r<96:return 5+[0,0,1,1,2,2,1,1][(r//8)%8]
        if r<120:return max(-2,5-(r-96)//3)
        return -2
    def land(c,r):
        # Width-limited river; bridge deck is applied afterward.
        if 210<=r<=217:return False
        return c>=shore(r)
    for r in range(375):
        row=[]
        for c in range(21):
            # Image top corresponds to r+1; TL/TR/BL/BR signs in map coordinates.
            mask=int(land(c,r+1))|int(land(c+1,r+1))<<1|int(land(c,r))<<2|int(land(c+1,r))<<3
            if mask==0:name='sea'+str((c+r)%3)
            elif mask==15:
                dense=120<=r<184 or (r<280 and c>8 and (c+r//12)%4!=0)
                name='forest'+str((c+r)%6) if dense else 'grass'+str((c+r)%3)
            else:name='coast'+str(mask)
            row.append(names[name])
        rows.append(row)
    for centre in (110,154):
        for r in range(centre-2,centre+3):
            for c in range(12,16):rows[r][c]=names['grass'+str((r+c)%3)]
    def block(name,c,r):
        # Top source half goes at map row r+1 (map starts at bottom).
        for yy in range(2):
            for xx in range(2):
                if 0<=r+1-yy<375 and 0<=c+xx<21:rows[r+1-yy][c+xx]=names[f'{name}_{xx}_{yy}']
    # Connected 32px road, block centres x=13..14 for the long forest corridor.
    for r in range(160,374,2):block('road5',13,r)
    block('road1',13,158)
    for r in range(210,218,2):block('bridge',13,r)
    block('bridge_enter',13,208);block('bridge_exit',13,216)
    # A looped military diversion / turn tiles, later rejoining the main road.
    block('road7',13,238);block('road9',17,238)
    for c in (15,):block('road10',c,238)
    for r in range(240,254,2):block('road5',17,r)
    block('road12',17,254);block('road7',13,254)
    block('road10',15,254)
    # Forest outposts and checkpoint: clearings are intentional, not random tiles.
    block('depot',17,150);block('depot',9,194);block('hangar',17,226)
    block('checkpoint',13,230);block('bunker',7,238)
    # Base courtyard: repeating concrete with an aligned road through the gate.
    for r in range(282,374,2):
        for c in range(3,20,2):block('concrete',c,r)
    for r in range(282,374,2):block('road5',13,r)
    for c in range(3,20):rows[281][c]=names['fence_h']
    block('checkpoint',13,280)
    for r in range(282,375):rows[r][2]=names['fence_v'];rows[r][20]=names['fence_v']
    for r in (296,320,344,364):
        for c in (5,9,17):block('hangar' if (c+r)%3 else 'depot',c,r)
    for r in (306,334,356):block('helipad',6,r)
    block('bunker',9,288);block('bunker',17,332);block('bunker',9,368)
    # Cross-road and top exit inside the base, clear of placed buildings.
    for c in range(3,20,2):block('road10',c,338)
    block('road15',13,338)
    # Safe events with first contact delayed until beyond the initially visible rows.
    paths={
      'coast_swoop':[['move',48,0,1.5],['move',48,1,1.25],['fire'],['move',96,0,2],['end']],
      'forest_snake':[['sine',28,96,2,1.5],['end']],
      'heli_patrol':[['move',60,0,1.5],['wait',35],['fire'],['move',80,0,1.5],['move',100,0,2],['end']],
      'bomber_pass':[['move',100,0,1],['fire'],['move',127,0,1.5],['end']],
      'armour_push':[['move',90,0,.75],['fire'],['move',127,0,1.5],['end']],
    }
    forms={
      'scouts':dict(enemy='fighter',count=4,path='coast_swoop',delay=20,x=40,y=-24),
      'forest_fighters':dict(enemy='fighter',count=5,path='forest_snake',delay=20,x=142,y=-24),
      'helis':dict(enemy='helicopter',count=3,path='heli_patrol',delay=30,x=185,y=-24),
      'bombers':dict(enemy='bomber',count=3,path='bomber_pass',delay=40,x=144,y=-40),
      'armoured':dict(enemy='armoured',count=3,path='armour_push',delay=44,x=144,y=-40),
    }
    waves=[(20,'scouts'),(34,'scouts'),(48,'forest_fighters'),(62,'scouts'),(76,'bombers'),(90,'scouts'),
           (106,'forest_fighters'),(120,'helis'),(134,'forest_fighters'),(148,'scouts'),(162,'bombers'),(176,'helis'),
           (198,'scouts'),(212,'bombers'),(226,'forest_fighters'),(240,'armoured'),(254,'helis'),(268,'bombers'),
           (288,'forest_fighters'),(302,'armoured'),(316,'helis'),(330,'bombers'),(344,'armoured'),(358,'forest_fighters')]
    events=[dict(row=r,type='formation',formation=f,mirror=bool(i%2)) for i,(r,f) in enumerate(waves)]
    for r,direction in [(110,'west'),(154,'south'),(194,'east'),(224,'south'),(250,'west'),(294,'south'),(322,'south'),(350,'east')]:
        events.append(dict(row=r,type='ground',enemy='tank',x=13*16-16,dir=direction))
    events += [dict(row=188,type='shop',id='mid'),dict(row=368,type='shop',id='end'),dict(row=375,type='end')]
    events.sort(key=lambda e:e['row'])
    # Compact adjacent repeated map blocks when present; retain designer row order.
    packed=[];r=0
    while r<len(rows):
        best=None
        for period in range(1,13):
            blockrows=rows[r:r+period]
            if len(blockrows)!=period:continue
            n=1
            while rows[r+n*period:r+(n+1)*period]==blockrows:n+=1
            saving=(n-1)*period-2
            if n>1 and saving>0 and (best is None or saving>best[0]):best=(saving,period,n)
        if best:
            _,period,n=best;packed.append(dict(repeat=n,rows=rows[r:r+period]));r+=period*n
        else:packed.append(rows[r]);r+=1
    level=dict(format='shootermega65-level-1',name='Operation Kuestenwald',tileset='assets/art/coastal-base/generated',scroll_speed=.5,map=packed,paths=paths,formations=forms,events=events,
               design_notes=dict(sections=cfg['sections'],nominal_seconds=240,first_contact_row=20,ground_spawn_surface='road / land',boss='none; unsupported in Stage 3a'))
    text=json.dumps(level,indent=2)
    text=re.sub(r'\[\n(?:\s+\d+,?\n){21}\s*\]',lambda m:json.dumps(json.loads(m.group(0))),text)
    (ROOT/'levels/coastal_base.json').write_text(text+'\n')
    # Exact exporter contract expected by build_level.py.
    terrain=bytearray();meta=[];atlas=Image.new('RGBA',(16*12,16*math.ceil(len(tiles)/12)))
    tile_sources=[]
    for i,t in enumerate(tiles):
        p=t['image'];terrain.extend(ncm(p.crop((0,0,16,8)))+ncm(p.crop((0,8,16,16))))
        meta.append(dict(id=i,name=t['name'],palette=t['palette']))
        atlas.paste(rgba(p,palettes[t['palette']]),(i%12*16,i//12*16))
        tile_sources.append(dict(id=i,name=t['name'],palette=t['palette'],rows=[p.tobytes()[y*16:(y+1)*16].hex() for y in range(16)]))
    atlas.save(OUT/'terrain-sheet.png');(OUT/'terrain.ncm.bin').write_bytes(terrain)
    (OUT/'level-example.json').write_text(json.dumps(dict(tiles=meta),indent=2)+'\n')
    (OUT/'indexed-source.json').write_text(json.dumps(tile_sources,indent=2)+'\n')
    manifest=dict(schema=1,palettes=palettes,tile_count=len(tiles),provenance='New deterministic native pixel tiles and transitions; existing fixed_targets palette retained for tanks.',hardware_tested=False)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Clean map and readable four-column overview, each section starts at its bottom.
    clean=Image.new('RGBA',(336,375*16))
    for r,row in enumerate(rows):
        for c,t in enumerate(row):clean.paste(rgba(tiles[t]['image'],palettes[tiles[t]['palette']]),(c*16,(374-r)*16))
    clean.save(OUT/'level-clean.png')
    overview=Image.new('RGB',(4*354,1620),(18,24,32));draw=ImageDraw.Draw(overview)
    for i,s in enumerate(cfg['sections']):
        crop=clean.crop((0,(374-s['end'])*16,336,(375-s['start'])*16)).convert('RGB')
        overview.paste(crop,(i*354+8,50));draw.text((i*354+8,8),f"{i+1}. {s['name']}",fill='white');draw.text((i*354+8,26),f"rows {s['start']}..{s['end']} / START BELOW",fill=(170,190,210))
    overview.save(OUT/'level-overview.png')
    print(f'{len(tiles)} tiles, {len(set(tuple(row) for row in rows))} distinct rows, {len(events)} events, nominal 240s')


if __name__=='__main__':main()
