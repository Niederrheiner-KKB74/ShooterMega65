"""Native shop Extra-Life and Exit; palette-compatible with make_shop.py."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw
import import_art

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'assets/art/shop'
OUT=BASE/'generated'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pal=import_art.HUD_PAL
    allowed=(1,2,3,4,5,6,7,8,10)
    ref=Image.open(BASE/'source/player-reference.png').convert('RGBA').crop((0,0,32,24))
    # Preserve actual straight-flight silhouette and proportions, nearest-neighbour only.
    bbox=ref.getbbox();mini=ref.crop(bbox);mini.thumbnail((14,14),Image.Resampling.NEAREST)
    life=Image.new('L',(16,16));x0=(16-mini.width)//2;y0=(16-mini.height)//2
    for y in range(mini.height):
        for x in range(mini.width):
            r,g,b,a=mini.getpixel((x,y))
            if a:
                index=min(allowed,key=lambda i:sum((v-w)**2 for v,w in zip((r,g,b),pal[i])))
                life.putpixel((x+x0,y+y0),index)
    exit=Image.new('L',(16,16));d=ImageDraw.Draw(exit)
    d.rectangle((0,1,15,14),fill=6,outline=2)
    # White doorway, running figure and right arrow in a green emergency-exit sign.
    d.rectangle((11,3,14,11),outline=2)
    d.rectangle((4,3,5,4),fill=2)
    d.line((5,6,7,7,8,6,9,6),fill=2,width=1)
    d.line((5,6,3,7,2,7),fill=2)
    d.line((5,6,4,9,2,11),fill=2,width=2)
    d.line((5,8,7,9,8,11),fill=2)
    d.line((7,13,13,13),fill=2);d.line((11,11,13,13,11,14),fill=2)
    icons=[];preview=Image.new('RGB',(430,190),(18,24,32));pd=ImageDraw.Draw(preview)
    for n,(name,title,p) in enumerate([('life','Extra-Life',life),('exit','Exit',exit)]):
        rgba=Image.new('RGBA',(16,16));rgba.putdata([tuple(pal[v])+(255 if v else 0,) for v in p.tobytes()])
        rgba.save(OUT/(name+'.png'))
        icons.append(dict(id=name,rows=[p.tobytes()[y*16:(y+1)*16].hex() for y in range(16)]))
        x=n*210+10;pd.text((x,8),title,fill='white');big=rgba.resize((128,128),Image.Resampling.NEAREST)
        preview.paste(big,(x,28),big);preview.paste(rgba,(x+150,90),rgba);pd.text((x+148,112),'1x',fill='white')
    (OUT/'indexed-source.json').write_text(json.dumps(icons,indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps(dict(palette=pal,allowed_hud_indices=list(allowed),size=[16,16],
        life_source='source/player-reference.png, first 32x24 frame; alpha crop, nearest-neighbour fit 14x14, nearest allowed HUD RGB',
        source_sha256=hashlib.sha256((BASE/'source/player-reference.png').read_bytes()).hexdigest(),
        player_source_commit='ea3d8458033c2db342eec3b93f099bae3cf2e6d7',
        exit_source='New native pixel drawing inspired by a green emergency-exit sign; no claim of standardized safety signage.',
        hardware_tested=False),indent=2)+'\n')
    preview.save(OUT/'preview.png')
    print('Extra-Life and Exit exported at 16x16 in allowed HUD colours.')

if __name__=='__main__':main()
