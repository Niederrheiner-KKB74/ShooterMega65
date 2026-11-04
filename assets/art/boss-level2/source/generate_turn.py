"""Draw a relit diagonal land cruiser from native polygon geometry."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'generated'


def project(x, y):
    return round(48 + (x-48-y+32)*0.58), round(48 + (x-48+y-32)*0.58)


def polygon(draw, points, fill):
    draw.polygon([project(x,y) for x,y in points], fill=fill)


def line(draw, points, fill, width=1):
    draw.line([project(x,y) for x,y in points], fill=fill, width=width)


def bevel(im, light, dark):
    original=im.copy()
    for y in range(1,im.height-1):
        for x in range(1,im.width-1):
            if original.getpixel((x,y)):
                if not original.getpixel((x-1,y)) or not original.getpixel((x,y-1)):
                    im.putpixel((x,y),light)
                elif not original.getpixel((x+1,y)) or not original.getpixel((x,y+1)):
                    im.putpixel((x,y),dark)


def body():
    im=Image.new('L',(96,96))
    d=ImageDraw.Draw(im)
    # Both tracks are drawn as diagonals with screen-space top-left highlights.
    for x in (0,72):
        polygon(d,[(x+5,0),(x+19,0),(x+23,6),(x+23,58),(x+18,63),
                   (x+4,63),(x,58),(x,7)],2)
    bevel(im,6,1)
    for x in (0,72):
        for y in range(5,60,5):
            line(d,[(x+2,y),(x+21,y)],4,3)
            line(d,[(x+2,y-1),(x+21,y-1)],7)
            line(d,[(x+3,y+2),(x+20,y+2)],1)
    hull=Image.new('L',(96,96))
    h=ImageDraw.Draw(hull)
    polygon(h,[(24,2),(71,2),(83,12),(82,49),(74,59),(60,63),
               (35,63),(21,59),(13,49),(12,13)],5)
    bevel(hull,8,2)
    im.paste(hull,mask=hull.point(lambda x:255 if x else 0))
    d=ImageDraw.Draw(im)
    polygon(d,[(24,9),(71,9),(75,17),(73,43),(64,55),(32,55),
               (22,45),(20,16)],4)
    for x in (21,65):
        for y in (12,44):
            polygon(d,[(x,y),(x+10,y),(x+10,y+10),(x,y+10)],3)
            line(d,[(x,y+10),(x,y),(x+10,y)],6)
            for j in range(2,10,3):
                line(d,[(x+2,y+j),(x+8,y+j)],2)
    polygon(d,[(34,21),(61,21),(65,26),(65,39),(58,44),(37,44),
               (31,39),(31,26)],2)
    polygon(d,[(36,23),(59,23),(62,27),(62,37),(57,41),(38,41),
               (34,37),(34,27)],6)
    line(d,[(34,37),(34,27),(36,23),(59,23)],8)
    line(d,[(38,41),(57,41),(62,37)],3)
    line(d,[(48,24),(48,40)],2,2)
    for x in (38,42,53,57):
        line(d,[(x,28),(x,35)],4)
    for x in (28,65):
        polygon(d,[(x,52),(x+3,52),(x+3,55),(x,55)],12)
    for x in range(38,60,4):
        line(d,[(x,54),(x-2,57)],13,2)
    for x in (33,58):
        polygon(d,[(x,8),(x+5,8),(x+5,17),(x,17)],3)
        for y in (9,12,15):line(d,[(x+1,y),(x+4,y)],7)
    for x in (23,68):
        line(d,[(x,23),(x,38)],2,4)
        line(d,[(x-1,24),(x-1,37)],7)
    line(d,[(40,9),(54,9),(57,12),(57,17)],2,3)
    line(d,[(40,8),(54,8),(57,11),(57,16)],7)
    for x,y in ((24,8),(70,8),(21,34),(74,34),(30,55),(65,55)):
        px,py=project(x,y)
        d.point((px,py),fill=9)
        d.point((px+1,py+1),fill=2)
    return im


def core():
    im=Image.new('L',(32,32))
    d=ImageDraw.Draw(im)
    d.polygon([(16,1),(30,14),(30,18),(17,30),(14,30),(1,17),(1,14),(14,1)],fill=2)
    d.line((1,15,14,2,17,2,29,14),fill=8,width=2)
    for shift in (-6,0,6):
        d.line((10+shift,10-shift,21+shift,21-shift),fill=10,width=4)
        d.line((10+shift,9-shift,21+shift,20-shift),fill=12,width=2)
        d.line((11+shift,9-shift,20+shift,18-shift),fill=14)
        d.point((12+shift,10-shift),fill=15)
    return im


def dust(phase):
    im=Image.new('L',(16,16))
    d=ImageDraw.Draw(im)
    # Separate opaque tufts and transparent gaps, with no solid rectangular edge.
    blobs=([(5,9,10,13),(8,5,13,11),(3,5,7,9),(1,10,4,12),(11,2,13,5)]
           if phase==0 else [(3,8,8,12),(7,3,12,8),(1,3,4,6),(10,10,14,13),(12,1,14,3)])
    for i,box in enumerate(blobs):
        d.ellipse(box,fill=(5,6,7,6,5)[i])
        x,y,x1,y1=box
        d.line((x+1,y+1,x1-1,y+1),fill=8 if i%2 else 9)
    for xy in ((2,1),(5,2),(14,7),(1,14),(8,14)):
        d.point(xy,fill=7)
    return im


def rows(im):
    return [''.join(format(im.getpixel((x,y)),'02x') for x in range(im.width))
            for y in range(im.height)]


def main():
    source=json.loads((OUT/'indexed-source.json').read_text())
    frames={f['id']:f for f in source}
    additions={'body_diag':body(),'core_exposed_diag':core(),'dust_0':dust(0),'dust_1':dust(1)}
    for key,im in additions.items():
        frames[key]=dict(id=key,width=im.width,height=im.height,rows=rows(im))
    source=list(frames.values())
    (OUT/'indexed-source.json').write_text(json.dumps(source,indent=2)+'\n')
    placement=json.loads((OUT/'placement.json').read_text())
    mounts=[]
    for t in placement['turrets']:
        x,y=t['offset']
        px,py=project(x+8,y+8)
        xy=[px-8,py-8]
        mounts.append(dict(t,offset=xy,hit_rect=[*xy,16,16]))
    placement['diag']=dict(body='body_diag',body_size=[96,96],turrets=mounts,
        core=dict(offset=[32,32],size=[32,32],exposed_overlay='core_exposed_diag',
                  hit_rect=[40,40,16,16]),
        dust=[[8,28],[38,66],[46,2],[72,38]],rotors=[],rotor_frames=[])
    (OUT/'placement.json').write_text(json.dumps(placement,indent=2)+'\n')
    pal=[tuple((OUT/'palette.rgb').read_bytes()[i:i+3]) for i in range(0,48,3)]
    def rgba(key):
        f=frames[key]
        im=Image.new('RGBA',(f['width'],f['height']))
        data=[int(row[x:x+2],16) for row in f['rows'] for x in range(0,len(row),2)]
        im.putdata([pal[v]+(255 if v else 0,) for v in data])
        return im
    def composite(layout,dust_phase=None,exposed=False):
        canvas=Image.new('RGBA',tuple(layout['body_size']),(66,53,43,255))
        def paste(key,xy):canvas.alpha_composite(rgba(key),tuple(xy))
        paste(layout['body'],[0,0])
        for rotor in layout.get('rotors',[]):
            key=layout['rotor_frames'][rotor['phase_offset']%3]
            paste(key,rotor['offset'])
        if exposed:paste(layout['core']['exposed_overlay'],layout['core']['offset'])
        for t in layout['turrets']:paste(t['destroyed' if exposed else 'south'],t['offset'])
        if dust_phase is not None:
            for xy in layout['dust']:paste('dust_'+str(dust_phase),xy)
        return canvas.resize((canvas.width*3,canvas.height*3),Image.Resampling.NEAREST)
    board=Image.new('RGB',(832,324),(28,28,31))
    draw=ImageDraw.Draw(board)
    layouts=[placement,placement['diag'],placement['side']]
    for x,label,layout in zip((8,312,616),('Senkrecht','Drehung 45 Grad','Waagerecht'),layouts):
        draw.text((x,6),label,fill='white')
        im=composite(layout,0 if 'dust' in layout else None)
        board.paste(im,(x,26+(288-im.height)//2))
    board.save(OUT/'boss-turn-preview.png')
    animated=[]
    sequence=[(0,None),(1,0),(1,1),(2,None),(1,1),(1,0)]
    for index,phase in sequence:
        canvas=Image.new('RGB',(320,324),(28,28,31))
        im=composite(layouts[index],phase)
        canvas.paste(im,((320-im.width)//2,26+(288-im.height)//2))
        ImageDraw.Draw(canvas).text((8,6),'Senkrecht - diagonal - waagerecht',fill='white')
        animated.append(canvas)
    animated[0].save(OUT/'boss-turn-animation.gif',save_all=True,
        append_images=animated[1:],duration=[700,180,180,700,180,180],loop=0,disposal=2)
    dustboard=Image.new('RGB',(280,152),(66,53,43))
    for i in range(2):
        dustboard.paste(rgba('dust_'+str(i)).resize((128,128),Image.Resampling.NEAREST),(i*140,20),
                        rgba('dust_'+str(i)).resize((128,128),Image.Resampling.NEAREST))
    dustboard.save(OUT/'dust-preview.png')


if __name__=='__main__':
    main()
