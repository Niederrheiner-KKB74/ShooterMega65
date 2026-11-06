"""Apply the Offshore water and wind-park revision to a Stage 13b snapshot."""
import argparse
import json
import math
import random
import re
from pathlib import Path

from PIL import Image, ImageDraw

ART = Path('assets/art/level3/generated')
MAP = Path('levels/level3.json')
CYCLE = dict(palette='water',first=9,count=4,period=6)
WATER = ('000000 101e38 142c51 1a3f66 1d5276 226b89 278299 429da2 '
         '9ec6a9 2d6c86 357b92 4a93a4 3d8498 263a47 b8ac8f e1f0da')
STATIC_REMAP = bytes((0,1,2,3,4,5,6,7,7,8,15,15,13,3,8,5))+bytes(range(16,256))
WIND_LAYOUT = [(x,y) for y in (228,236) for x in (2,7,13,18)]+[(7,244)]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path,obj):
    path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')


def decode(data):
    return Image.frombytes('L',(16,16),bytes(p for b in data for p in (b&15,b>>4)))


def encode(im):
    data=im.tobytes()
    return bytes(data[i] | data[i+1]<<4 for i in range(0,256,2))


def open_water(name):
    return name=='blue' or name.startswith(('sea','deep','shelf'))


def wave_art(im,variant,shore=False):
    # Break the surface into two uneven arcs. A phase offset applies to
    # the entire arc, keeping each crest coherent as it moves upward.
    rng = random.Random(6502 + 157 * variant)
    upper,lower = rng.randrange(1,6),rng.randrange(8,12)
    left,right = rng.randrange(3,5),rng.randrange(11,13)
    if variant % 2:
        upper,lower = lower,upper
    arcs = (
        (left,upper,(3,6,5,3),rng.randrange(4)),
        (right,lower,(2,4,4,2),rng.randrange(4)),
    )
    for center,top,widths,phase in arcs:
        bend = rng.choice((-1,1))
        for offset,width in enumerate(widths):
            index = 9 + (3-offset+phase) % 4
            start = center - width // 2
            for x in range(start,start + width):
                y = top + offset + (bend * (x-center) > 1)
                if not shore or im.getpixel((x,y))<=5:
                    im.putpixel((x,y),index)


def turbine(sea,phase):
    im=Image.new('L',(32,64))
    for y in range(0,64,16):
        for x in (0,16):im.paste(sea,(x,y))
    d=ImageDraw.Draw(im)
    # Long shadow to the lower right, and a small offshore service platform.
    d.line((17,49,27,56),fill=3,width=2)
    d.ellipse((9,49,23,58),outline=7)
    d.arc((8,48,24,59),30,155,fill=15)
    d.ellipse((12,50,20,56),fill=13)
    d.rectangle((13,43,18,53),fill=13)
    d.rectangle((14,43,17,51),fill=14)
    d.line((14,45,14,50),fill=15)
    d.polygon([(10,44),(12,42),(20,42),(22,44),(20,47),(12,47)],fill=13)
    d.line((10,44,12,42,20,42,22,44),fill=14)
    d.line((12,44,20,44),fill=15)
    # One-pixel ladder beside the monopile.
    d.line((19,45,19,54),fill=14)
    d.line((21,45,21,53),fill=13)
    for y in (46,48,50,52):d.point((20,y),fill=15)
    d.line((16,43,16,15),fill=13,width=3)
    d.line((15,41,15,15),fill=14)
    d.line((16,40,16,16),fill=15)
    d.polygon([(14,8),(17,8),(19,10),(19,15),(17,17),(14,16),(13,14),(13,10)],fill=14,outline=13)
    d.line((14,14,14,10,15,9,17,9),fill=15)
    # Vertical rotor foreshortened into a 29 x 7 pixel projection.
    for blade in range(3):
        angle=math.radians((7,42,83)[phase]+120*blade)
        end=(round(16+14.5*math.cos(angle)),round(17+3.5*math.sin(angle)))
        start=(round(16+2*math.cos(angle)),round(17+math.sin(angle)))
        d.line((start,end),fill=14,width=2)
        d.line((start,end),fill=15)
    d.ellipse((14,16,18,19),fill=14,outline=13)
    d.point((15,16),fill=15)
    return im


def replace_map(source,rows):
    # Keep the original serialization of events, paths, formations and headers.
    key=re.search(r'"map"\s*:\s*',source)
    assert key is not None
    offset=key.end()
    _,end=json.JSONDecoder().raw_decode(source[offset:])
    return source[:offset]+'[\n'+',\n'.join(
        '    '+json.dumps(row) for row in rows)+'\n  ]'+source[offset+end:]


def windpark(rows,old_turbines):
    originals=[]
    for y,row in enumerate(rows):
        for x,name in enumerate(row):
            if name=='turbine_0_0_1':
                originals.append((x,y))
    assert len(originals)==len(WIND_LAYOUT)==9
    # Restore open water under the former footprints.
    for x,y in originals:
        for dy in (0,1):
            for dx in (0,1):
                assert rows[y+dy][x+dx] in old_turbines
                rows[y+dy][x+dx]='sea0'
    for x,y in WIND_LAYOUT:
        # A matched water collar extends the tile pattern around the pylon.
        for yy in range(y-1,y+5):
            for xx in range(x-1,x+3):
                if open_water(rows[yy][xx]):
                    rows[yy][xx]='sea0'
        for image_row in range(4):
            for col in range(2):
                yy=y+3-image_row
                assert open_water(rows[yy][x+col]),(x,yy,rows[yy][x+col])
                if image_row<2:
                    name=f'turbine_0_{col}_{image_row}'
                else:
                    name=f'turbine_base_{col}_{image_row-2}'
                rows[yy][x+col]=name
    assert all(not rows[y][x].startswith('turbine')
               for y in range(len(rows)) for x in (9,10,11))


def rgb(im,palette):
    out=Image.new('RGB',im.size)
    out.putdata([tuple(palette[p]) for p in im.tobytes()])
    return out


def render_map(rows,render,lo,hi):
    im=Image.new('RGB',(320,(hi-lo)*16))
    for y in range(lo,hi):
        for x,index in enumerate(rows[y][1:]):
            im.paste(render[index],(x*16,(hi-1-y)*16))
    return im


def previews(out,tiles,images,manifest,rows,wind,animations,ids):
    palettes=manifest['palettes']
    render=[rgb(images[t['name']],palettes[t['palette']]) for t in tiles]
    sheet=Image.new('RGB',(880,math.ceil(len(tiles)/8)*53),(20,29,37))
    draw=ImageDraw.Draw(sheet)
    for t,im in zip(tiles,render):
        index=t['id'];x=index%8*110+3;y=index//8*53+3
        draw.text((x,y),f"{index} {t['name']}",fill='white')
        sheet.paste(im.resize((32,32),Image.Resampling.NEAREST),(x,y+16))
    sheet.save(out/'terrain-sheet.png')
    overview=render_map(rows,render,0,len(rows))
    overview.save(out/'level-overview.png',optimize=True)
    sections=Image.new('RGB',(1312,1580),(20,29,37));draw=ImageDraw.Draw(sections)
    for i,(lo,hi,label) in enumerate(((0,96,'01 Offene See'),(96,184,'02 Oelfeld'),
        (184,280,'03 Forschung und Windpark'),(280,375,'04 Marinestuetzpunkt'))):
        x=i*328+4
        draw.text((x,5),label,fill='white')
        sections.paste(overview.crop((0,(375-hi)*16,320,(375-lo)*16)),(x,24))
    sections.save(out/'level-sections.png',optimize=True)
    park=render_map(rows,render,222,252)
    park.save(out/'windpark-preview.png',optimize=True)
    board=Image.new('RGB',(336,354),(20,29,37));draw=ImageDraw.Draw(board)
    for phase,im in enumerate(wind):
        x=phase*112+3
        draw.text((x,3),f'Windrad {phase+1}',fill='white')
        board.paste(rgb(im,palettes['water']).resize((96,192),Image.Resampling.NEAREST),(x,19))
    for i,anim in enumerate(a for a in animations if a['name']!='turbine'):
        for phase,names in enumerate(anim['phases']):
            x=phase*112+3;y=218+i*66
            draw.text((x,y),f"{anim['name']} {phase+1}",fill='white')
            board.paste(render[ids[names[0]]].resize((48,48),Image.Resampling.NEAREST),(x,y+15))
    board.save(out/'animation-phases.png')
    frames=[]
    colors=palettes['water'][9:13]
    for phase in range(4):
        pal=palettes['water'][:]
        pal[9:13]=colors[-phase:]+colors[:-phase]
        phase_render=[rgb(images[t['name']],pal if t['palette']=='water'
                      else palettes[t['palette']]) for t in tiles]
        im=render_map(rows,phase_render,31,49)
        frames.append(im.resize((640,576),Image.Resampling.NEAREST))
    frames[0].save(out/'water-cycle.gif',save_all=True,append_images=frames[1:],
                   duration=120,loop=0,disposal=2,optimize=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True,help='Unmodified Stage 13b snapshot')
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[4])
    args=parser.parse_args()
    src=args.base/ART;out=args.out/ART
    assert src.resolve()!=out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    manifest=read(src/'manifest.json')
    manifest['palettes']['water']=[list(bytes.fromhex(c)) for c in WATER.split()]
    metadata=read(src/'level-example.json')
    tiles=metadata['tiles']
    raw=(src/'terrain.ncm.bin').read_bytes()
    assert len(raw)==128*len(tiles)
    animations=read(src/'animations.json')['animations']
    old_wind=next(a for a in animations if a['name']=='turbine')
    wind_names={n for names in old_wind['phases'] for n in names}
    removed=[t['id'] for t in tiles if t['name'].startswith('glint_')]
    assert len(removed)==6
    original_names=[t['name'] for t in tiles]
    images={}
    for t in tiles:
        name=t['name'];i=t['id']
        if i in removed or name in wind_names:
            continue
        im=decode(raw[128*i:128*(i+1)])
        if t['palette']=='water':
            im=Image.frombytes('L',im.size,im.tobytes().translate(STATIC_REMAP))
            if open_water(name) or name.startswith('edge'):
                wave_art(im,i,shore=name.startswith('edge'))
        images[name]=im
    wind=[turbine(images['sea0'],i) for i in range(3)]
    for phase,names in enumerate(old_wind['phases']):
        for i,name in enumerate(names):
            x=i%2*16;y=i//2*16
            images[name]=wind[phase].crop((x,y,x+16,y+16))
    for i in range(4):
        x=i%2*16;y=32+i//2*16
        name=f'turbine_base_{i%2}_{i//2}'
        images[name]=wind[0].crop((x,y,x+16,y+16))
        tiles[removed[i]]=dict(id=removed[i],name=name,palette='water')
    for tile in tiles:
        if tile['name'] in wind_names:tile['palette']='water'
    # Recycle the last two entries into the remaining holes. All other IDs stay put.
    for index in removed[4:]:
        moved=tiles.pop()
        tiles[index]=dict(moved,id=index)
    ids={t['name']:t['id'] for t in tiles}
    assert [t['id'] for t in tiles]==list(range(124))
    animations=[a for a in animations if a['name']!='glitter']
    text=(args.base/MAP).read_text(encoding='utf-8')
    level=json.loads(text)
    old_rows=[[original_names[i] for i in row] for row in level['map']]
    names=[[('sea0' if name=='glint_0_0' else 'shelf0') if name.startswith('glint_') else name
            for name in row] for row in old_rows]
    before_park=[row[:] for row in names]
    windpark(names,wind_names)
    assert all(a==b for i,(a,b) in enumerate(zip(names,before_park)) if not 184<=i<280)
    rows=[[ids[name] for name in row] for row in names]
    assert len(rows)==375 and len(set(map(tuple,rows)))<=256,len(set(map(tuple,rows)))
    (args.out/MAP).parent.mkdir(parents=True,exist_ok=True)
    (args.out/MAP).write_text(replace_map(text,rows),encoding='utf-8',newline='\n')
    write(out/'manifest.json',manifest)
    write(out/'level-example.json',metadata)
    write(out/'animations.json',dict(animations=animations,cycle=CYCLE))
    (out/'terrain.ncm.bin').write_bytes(b''.join(encode(images[t['name']]) for t in tiles))
    previews(out,tiles,images,manifest,rows,wind,animations,ids)
    print(f'{len(tiles)} tiles; {len(set(map(tuple,rows)))} row patterns; {len(WIND_LAYOUT)} turbines.')


if __name__=='__main__':
    main()
