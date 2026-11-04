"""Check opaque hull, all required hover-tank frames and effect attachment."""
import collections
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'generated'


def main():
    source=json.loads((OUT/'indexed-source.json').read_text())
    frames={frame['id']:frame for frame in source}
    assert len(frames)==len(source), 'duplicate frame IDs'
    required={'body','core_exposed','muzzle_0','muzzle_1'}
    required.update(f'{prefix}_{phase}' for prefix in ('rotor','flame','spray') for phase in range(3))
    required.update(f'turret_{corner}_{pose}' for corner in ('nw','ne','sw','se')
                    for pose in ('south','southeast','destroyed'))
    assert set(frames)==required, 'missing or obsolete frame IDs'
    assert len((OUT/'palette.rgb').read_bytes())==48
    pixels={}
    for key,frame in frames.items():
        width,height=frame['width'],frame['height']
        assert len(frame['rows'])==height and all(len(row)==width*2 for row in frame['rows'])
        values=[[int(row[x:x+2],16) for x in range(0,len(row),2)] for row in frame['rows']]
        assert all(0<=value<16 for row in values for value in row)
        pixels[key]=values
    hull=pixels['body']
    width,height=frames['body']['width'],frames['body']['height']
    queue=collections.deque()
    exterior=set()
    for y in range(height):
        for x in range(width):
            if (x in (0,width-1) or y in (0,height-1)) and hull[y][x]==0:
                exterior.add((x,y))
                queue.append((x,y))
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<width and 0<=ny<height and hull[ny][nx]==0 and (nx,ny) not in exterior:
                exterior.add((nx,ny))
                queue.append((nx,ny))
    assert all(hull[y][x] or (x,y) in exterior for y in range(height) for x in range(width)), 'hull transparency hole'
    placement=json.loads((OUT/'placement.json').read_text())
    assert placement['body_size']==[112,80]
    assert 'side' not in placement and 'diag' not in placement
    for item in placement['turrets']:
        x,y=item['offset']
        assert hull[y+8][x+8]>0, 'turret center outside hull'
        assert x>=0 and y>=0 and x+16<=width and y+16<=height
    for item in placement['rotors']:
        x,y=item['offset']
        assert 0<=x<=width-32 and 0<=y<=height-32
    fx,fy=placement['flame']['offset']
    assert hull[fy-1][fx+7]>0, 'flame is detached from nozzle'
    for prefix in ('flame','spray'):
        assert len({tuple(frames[f'{prefix}_{i}']['rows']) for i in range(3)})==3
        for i in range(3):
            image=pixels[f'{prefix}_{i}']
            assert all(row[0]==row[-1]==0 for row in image), 'effect reaches side edge'
            assert sum(value==0 for row in image for value in row)>len(image)*len(image[0])//2
    assert len(placement['spray']['offsets'])==4
    print('PASS: 25 required frames, one 16-color palette, closed opaque hull, turret/fan placements, attached flame and transparent effect edges.')


if __name__=='__main__':
    main()
