"""Convert generated scene sources to native 16-colour MEGA65 screen assets."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/screens';OUT=BASE/'generated'
PAL=[[13,20,35],[25,35,58],[41,54,83],[63,78,106],[89,105,129],[132,148,166],[198,208,213],[248,243,214],
     [8,41,107],[0,86,218],[68,166,245],[46,55,36],[112,121,65],[158,58,28],[247,117,20],[255,201,55]]
FONT={
 'S':['.####','#....','#....','.###.','....#','....#','####.'],
 'h':['#....','#....','####.','#...#','#...#','#...#','#...#'],
 'o':['.....','.....','.###.','#...#','#...#','#...#','.###.'],
 't':['..#..','..#..','#####','..#..','..#..','..#..','...##'],
 'e':['.....','.....','.###.','#...#','#####','#....','.####'],
 'r':['.....','.....','#.##.','##..#','#....','#....','#....'],
 '6':['.###.','#....','#....','####.','#...#','#...#','.###.'],
 '5':['#####','#....','#....','####.','....#','#...#','.###.'],
 'G':['.###.','#...#','#....','#.###','#...#','#...#','.###.'],
 'A':['.###.','#...#','#...#','#####','#...#','#...#','#...#'],
 'M':['#...#','##.##','#.#.#','#.#.#','#...#','#...#','#...#'],
 'E':['#####','#....','#....','####.','#....','#....','#####'],
 'O':['.###.','#...#','#...#','#...#','#...#','#...#','.###.'],
 'V':['#...#','#...#','#...#','#...#','#...#','.#.#.','..#..'],
 'R':['####.','#...#','#...#','####.','#.#..','#..#.','#...#'],
 'P':['####.','#...#','#...#','####.','#....','#....','#....'],
 'F':['#####','#....','#....','####.','#....','#....','#....'],
 'I':['#####','..#..','..#..','..#..','..#..','..#..','#####'],
 'H':['#...#','#...#','#...#','#####','#...#','#...#','#...#'],
 'C':['.###.','#...#','#....','#....','#....','#...#','.###.'],
 '0':['.###.','#...#','#..##','#.#.#','##..#','#...#','.###.'],
 ' ':['.....']*7}

def palette_image(a,pal):
    p=Image.fromarray(a.astype('uint8'),'P');p.putpalette([v for c in pal for v in c]+[0]*(768-len(pal)*3));return p

def quantize(im,pal,start=0):
    a=np.asarray(im.convert('RGB')).astype(np.int32);p=np.array(pal[start:],np.int32)
    diff=a[:,:,None,:]-p[None,None,:,:]
    return (np.argmin(np.sum(diff*diff*np.array([2,3,1]),axis=3),axis=2)+start).astype(np.uint8)

def text_mask(text,scale):
    p=Image.new('1',((len(text)*6-1)*scale,7*scale));d=ImageDraw.Draw(p)
    for i,c in enumerate(text):
        for y,row in enumerate(FONT[c]):
            for x,v in enumerate(row):
                if v=='#':d.rectangle(((i*6+x)*scale,y*scale,(i*6+x+1)*scale-1,(y+1)*scale-1),fill=1)
    return p

def title_text(a,text,y,scale,colors):
    mask=text_mask(text,scale);x=(a.shape[1]-mask.width)//2;m=np.array(mask,dtype=bool)
    for dy,dx in ((3,3),(2,2),(1,1),(0,-1),(0,1),(-1,0),(1,0)):
        region=a[y+dy:y+dy+mask.height,x+dx:x+dx+mask.width];region[m]=0
    for yy in range(mask.height):
        a[y+yy,x:x+mask.width][m[yy]]=colors[min(len(colors)-1,yy*len(colors)//mask.height)]

def flat_text(a,text,y,scale,color):
    mask=text_mask(text,scale);x=(a.shape[1]-mask.width)//2;m=np.array(mask,dtype=bool)
    a[y:y+mask.height,x:x+mask.width][m]=color

def ncm(a):
    b=a.tobytes();return bytes(b[i]|b[i+1]<<4 for i in range(0,128,2))

def export(name,a,pal,limit,safe_zones,role):
    h,w=a.shape;assert w%16==0 and h%8==0
    glyphs=[];lookup={};rows=[]
    for y in range(0,h,8):
        row=[]
        for x in range(0,w,16):
            b=ncm(a[y:y+8,x:x+16]);index=lookup.get(b)
            if index is None:index=len(glyphs);lookup[b]=index;glyphs.append(b)
            row.append(index)
        rows.append(row)
    assert len(glyphs)<=limit,(name,len(glyphs),limit)
    palette_image(a,pal).save(OUT/(name+'.png'),bits=4)
    (OUT/(name+'.ncm.bin')).write_bytes(b''.join(glyphs))
    (OUT/(name+'.map16.bin')).write_bytes(b''.join(i.to_bytes(2,'little') for row in rows for i in row))
    (OUT/(name+'.palette-map.bin')).write_bytes(bytes(w//16*h//8))
    (OUT/(name+'.palette.rgb')).write_bytes(bytes(v for c in pal for v in c))
    (OUT/(name+'.palette.palregs.bin')).write_bytes(bytes((c[ch]%16)*16+c[ch]//16 for ch in range(3) for c in pal))
    record=dict(id=name,width=w,height=h,tile_size=[16,8],palettes=[pal],tile_map=rows,palette_map=[[0]*(w//16) for _ in range(h//8)],
                rows=[a[y].tobytes().hex() for y in range(h)],unique_tiles=len(glyphs),glyph_bytes=len(glyphs)*64,
                baked_text={'title':'Shooter65','game-over-full':'GAME OVER','game-over-banner':None}[name],
                safe_zones=safe_zones,role=role,index0='background colour; PNG is opaque',integrated=False,hardware_tested=False)
    (OUT/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(f'{name}: {w}x{h}, {len(np.unique(a))} used palette indices, {len(glyphs)}/{limit} tiles, {len(glyphs)*64} glyph bytes')
    return record

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    scene=Image.open(BASE/'source/title-scene.png').resize((320,200),Image.Resampling.NEAREST)
    # Fit action between logo and engine text: no aircraft is hidden by the title.
    action=scene.crop((0,25,320,177)).resize((320,132),Image.Resampling.NEAREST)
    title=np.zeros((200,320),np.uint8);title[44:176]=quantize(action,PAL)
    title_text(title,'Shooter65',8,5,[7,6,10,9])
    title_meta=export('title',title,PAL,500,[dict(x=0,y=176,width=320,height=24,purpose='engine PRESS FIRE and high score')],'runtime title artwork; title baked, bottom text reserved')
    go=quantize(Image.open(BASE/'source/game-over-scene.png').resize((320,200),Image.Resampling.NEAREST),PAL)
    title_text(go,'GAME OVER',10,4,[7,15,14,13])
    export('game-over-full',go,PAL,500,[],'requested full-screen design alternative; NOT the specified runtime banner')
    # Runtime panel: two scene vignettes, open central text field, opaque index 1.
    bannerpal=[PAL[0],PAL[0]]+PAL[2:];banner=np.ones((64,256),np.uint8)
    original=Image.open(BASE/'source/game-over-scene.png').convert('RGB')
    # Crop from proportional native scene, then fit the wreck/ruin vignettes.
    scene=original.resize((320,200),Image.Resampling.NEAREST)
    wreck=scene.crop((34,83,223,182));wreck.thumbnail((60,46),Image.Resampling.NEAREST)
    wa=quantize(wreck,bannerpal,start=1);yy=61-wa.shape[0];banner[yy:yy+wa.shape[0],3:3+wa.shape[1]]=wa
    city=scene.crop((244,44,320,176)).resize((52,56),Image.Resampling.NEAREST)
    banner[4:60,200:252]=quantize(city,bannerpal,start=1)
    banner[0,:]=5;banner[63,:]=2;banner[:,0]=5;banner[:,255]=2
    banner[2,2:254]=3;banner[61,2:254]=3;banner[2:62,2]=3;banner[2:62,253]=3
    export('game-over-banner',banner,bannerpal,100,[dict(x=64,y=6,width=128,height=52,purpose='engine GAME OVER / score / PRESS FIRE')],'runtime banner decoration; all texts drawn by engine')
    preview=title.copy();flat_text(preview,'PRESS FIRE',180,1,7);flat_text(preview,'HI 000000',191,1,6)
    palette_image(preview,PAL).resize((960,600),Image.Resampling.NEAREST).save(OUT/'title-preview.png')
    palette_image(go,PAL).resize((960,600),Image.Resampling.NEAREST).save(OUT/'game-over-full-preview.png')
    bp=banner.copy();flat_text(bp,'GAME OVER',8,2,7);flat_text(bp,'SCORE 000000',30,1,6);flat_text(bp,'PRESS FIRE',46,1,15)
    palette_image(bp,bannerpal).resize((1024,256),Image.Resampling.NEAREST).save(OUT/'game-over-banner-preview.png')
    manifest=dict(schema=1,provenance='Scene layers generated using built-in image_gen from current aircraft references; deterministic nearest-neighbour/native palette conversion and custom pixel typography. Not hand-drawn originals.',
                  generated_sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'source').glob('*.png')},
                  game_over_fullscreen_alternative=True,runtime_game_over='game-over-banner',integrated=False,hardware_tested=False)
    manifest['files']={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
