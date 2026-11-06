"""Offshore aircraft poses drawn in screen coordinates at 16 x 16."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'assets/art/level3/source'))
import generate_vehicles as base

# Each entry describes the wing, fuselage, port float, starboard float,
# canopy and propeller for one individually drawn heading.
PLANES = {
 'north': ([(2,7),(13,7),(13,9),(2,9)],[(7,2),(8,2),(9,6),(8,13),(7,13),(6,6)],
           [(3,5),(4,5),(4,11),(3,11)],[(11,5),(12,5),(12,11),(11,11)],[(7,5),(8,6)],(7,2)),
 'northeast': ([(4,4),(12,11),(11,12),(3,6)],[(12,2),(13,3),(11,6),(5,12),(3,12),(4,10)],
               [(6,3),(7,4),(3,8),(2,7)],[(12,8),(13,9),(8,13),(7,12)],[(10,5),(9,6)],(12,2)),
 'east': ([(6,2),(8,2),(8,13),(6,13)],[(13,7),(13,8),(9,9),(2,8),(2,7),(8,6)],
          [(5,3),(11,3),(11,4),(5,4)],[(5,11),(11,11),(11,12),(5,12)],[(10,7),(9,8)],(13,7)),
 'southeast': ([(4,11),(11,4),(12,5),(5,12)],[(13,12),(12,13),(9,11),(3,5),(3,3),(5,4)],
               [(8,3),(9,2),(13,6),(12,7)],[(3,8),(4,7),(8,11),(7,13)],[(10,9),(11,10)],(13,12)),
 'south': ([(2,6),(13,6),(13,8),(2,8)],[(7,13),(8,13),(9,9),(8,2),(7,2),(6,9)],
           [(3,4),(4,4),(4,10),(3,10)],[(11,4),(12,4),(12,10),(11,10)],[(7,10),(8,9)],(8,13)),
 'southwest': ([(4,4),(12,11),(11,12),(3,6)],[(3,13),(2,12),(4,9),(10,3),(12,3),(11,5)],
               [(3,8),(2,7),(6,3),(7,4)],[(8,12),(7,11),(12,7),(13,8)],[(5,10),(6,9)],(3,13)),
 'west': ([(7,2),(9,2),(9,13),(7,13)],[(2,7),(2,8),(6,9),(13,8),(13,7),(7,6)],
          [(4,3),(10,3),(10,4),(4,4)],[(4,11),(10,11),(10,12),(4,12)],[(5,7),(6,8)],(2,8)),
 'northwest': ([(4,11),(11,4),(12,5),(5,12)],[(2,3),(3,2),(6,4),(12,10),(12,12),(10,11)],
               [(3,7),(4,6),(8,10),(7,12)],[(8,3),(9,2),(13,6),(12,7)],[(5,5),(6,6)],(2,3)),
}
# Each entry contains the cabin, boom, tail stabilizer, skids, glazing and hub.
HELICOPTERS = {
 'north': ([(6,2),(9,2),(10,4),(10,8),(9,9),(6,9),(5,7),(5,4)],
           [(7,8),(8,8),(8,13),(7,13)],[(6,13),(9,13)],[(4,4),(4,9)],[(11,4),(11,9)],[(6,3),(9,5)],(7,6)),
 'northeast': ([(10,2),(12,3),(13,5),(12,7),(9,9),(6,8),(6,6),(8,3)],
               [(7,7),(9,8),(4,13),(3,12)],[(2,11),(5,13)],[(5,5),(8,2)],[(10,10),(13,7)],[(9,4),(12,5)],(9,6)),
 'east': ([(13,6),(13,9),(11,10),(7,10),(6,9),(6,6),(8,5),(11,5)],
          [(7,7),(7,8),(2,8),(2,7)],[(2,6),(2,9)],[(7,4),(12,4)],[(7,11),(12,11)],[(10,6),(12,9)],(9,7)),
 'southeast': ([(13,10),(12,12),(10,13),(8,12),(6,9),(7,6),(9,6),(12,8)],
               [(8,7),(7,9),(2,4),(3,3)],[(2,5),(4,2)],[(10,5),(13,8)],[(5,10),(8,13)],[(10,9),(11,12)],(9,9)),
 'south': ([(6,13),(9,13),(10,11),(10,7),(9,6),(6,6),(5,8),(5,11)],
           [(7,7),(8,7),(8,2),(7,2)],[(6,2),(9,2)],[(4,6),(4,11)],[(11,6),(11,11)],[(6,10),(9,12)],(8,9)),
 'southwest': ([(5,13),(3,12),(2,10),(3,8),(6,6),(9,7),(9,9),(7,12)],
               [(8,8),(6,7),(11,2),(12,3)],[(10,2),(13,4)],[(7,13),(10,10)],[(2,8),(5,5)],[(3,9),(6,11)],(6,9)),
 'west': ([(2,6),(2,9),(4,10),(8,10),(9,9),(9,6),(7,5),(4,5)],
          [(8,7),(8,8),(13,8),(13,7)],[(13,6),(13,9)],[(3,4),(8,4)],[(3,11),(8,11)],[(3,6),(5,9)],(6,8)),
 'northwest': ([(2,5),(3,3),(5,2),(7,3),(9,6),(8,9),(6,9),(3,7)],
               [(7,8),(8,6),(13,11),(12,12)],[(11,13),(13,10)],[(5,2),(10,5)],[(2,7),(5,10)],[(3,4),(6,6)],(6,6)),
}
PROPELLERS = {
 'north': [((5,1),(9,1)),((6,0),(8,2)),((7,0),(7,2))],
 'northeast': [((11,1),(14,4)),((12,0),(12,3)),((11,2),(14,2))],
 'east': [((14,5),(14,9)),((13,6),(15,8)),((13,7),(15,7))],
 'southeast': [((11,14),(14,11)),((13,11),(13,15)),((12,13),(15,13))],
 'south': [((6,14),(10,14)),((7,13),(9,15)),((8,13),(8,15))],
 'southwest': [((1,11),(4,14)),((3,12),(3,15)),((1,13),(4,13))],
 'west': [((1,6),(1,10)),((0,7),(2,9)),((0,8),(2,8))],
 'northwest': [((1,4),(4,1)),((2,0),(2,4)),((0,2),(3,2))],
}


def outline(im):
    mask=im.point(lambda value:255 if value else 0)
    expanded=mask.filter(ImageFilter.MaxFilter(3))
    result=Image.new('L',im.size)
    result.paste(1,mask=expanded)
    result.paste(im,mask=mask)
    return result


def aircraft(group,pose,phase):
    im=Image.new('L',(16,16))
    draw=ImageDraw.Draw(im)
    if group=='seaplane':
        wing,hull,left,right,glass,nose=PLANES[pose]
        draw.polygon(wing,fill=3)
        for pontoon in (left,right):
            draw.polygon(pontoon,fill=7)
            draw.line((pontoon[-1],pontoon[0]),fill=5)
        draw.polygon(hull,fill=5)
        draw.line(glass,fill=8,width=2)
        draw.point(nose,fill=12)
        im=outline(im)
        ImageDraw.Draw(im).line(PROPELLERS[pose][phase],fill=7)
    else:
        cabin,boom,tail,skid_l,skid_r,glass,hub=HELICOPTERS[pose]
        draw.line(skid_l,fill=3)
        draw.line(skid_r,fill=3)
        draw.polygon(boom,fill=5)
        draw.line(tail,fill=5)
        draw.polygon(cabin,fill=5)
        draw.rectangle(glass,fill=8)
        draw.point(glass[0],fill=10)
        im=outline(im)
        draw=ImageDraw.Draw(im)
        cx,cy=hub
        dx,dy=((6,-1),(5,4),(1,6))[phase]
        draw.line((cx-dx,cy-dy,cx+dx,cy+dy),fill=7)
        draw.point(hub,fill=10)
    assert len(set(im.tobytes())-{0})<=6
    return im


def boat(group,pose,phase):
    original=base_boat(group,pose,phase)
    if group!='patrol_boat' or pose not in ('east','west'):
        return original
    project=base.heading(original,pose)
    hull=Image.new('L',original.size)
    ImageDraw.Draw(hull).polygon([project(x,y) for x,y in
        ((0,-15),(7,-10),(9,-3),(9,8),(6,12),(-6,12),(-9,8),
         (-9,-3),(-7,-10))],fill=255)
    im=Image.new('L',original.size)
    draw=ImageDraw.Draw(im)
    # Short bow crescents, then two continuous diverging wake trails aft.
    arcs=[[(29,12),(27,8),(23,6)],[(29,19),(27,23),(23,25)]]
    trails=[[(15,7),(9,6),(3,4-phase)],[(15,24),(9,25),(3,27+phase)]]
    def position(x,y):
        return (x,y) if pose=='east' else (31-x,y)
    for arc in arcs:
        draw.line([position(x,y) for x,y in arc],fill=7 if phase else 10)
    for trail in trails:
        draw.line([position(x,y) for x,y in trail],fill=10)
    im.paste(original,mask=hull)
    return im


base_boat=base.boat
base_sheet=base.sheet


def sheet(path,samples,columns,scale):
    if path.name in ('seaplane-preview.png','navy_heli-preview.png'):
        columns,scale=3,4
    base_sheet(path,samples,columns,scale)


if __name__=='__main__':
    base.aircraft=aircraft
    base.boat=boat
    base.sheet=sheet
    base.enemy_art()
