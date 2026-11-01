"""Independent asset constraints and packed-data round trips, no hardware claims."""
from collections import deque
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def decode(data,w,h,tw):
    result=bytearray(w*h)
    for y in range(h):
        for x in range(w):
            pos=((y//8)*(w//tw)+x//tw)*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)
            b=data[pos];result[y*w+x]=(b>>((x%2)*4))&15 if tw==16 else b
    return bytes(result)

def check_hashes(base):
    m=json.loads((base/'manifest.json').read_text())
    for name,r in m['files'].items():
        data=(base/name).read_bytes();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],name
    return m

def screens():
    base=ROOT/'assets/art/screens/generated';m=check_hashes(base)
    for name,w,h,limit in [('title',320,200,500),('game-over-full',320,200,500),('game-over-banner',256,64,100)]:
        meta=json.loads((base/(name+'.json')).read_text());raw=bytes.fromhex(''.join(meta['rows']));assert len(raw)==w*h and max(raw)<=15
        im=Image.open(base/(name+'.png'));assert im.mode=='P' and im.size==(w,h) and 'transparency' not in im.info
        assert im.tobytes()==raw and len(im.getpalette())==48,'PNG must have an actual 16-entry PLTE'
        pal=meta['palettes'][0];assert len(pal)==16 and len(meta['palettes'])==1
        assert im.convert('RGB').tobytes()==bytes(v for i in raw for v in pal[i])
        glyphs=(base/(name+'.ncm.bin')).read_bytes();assert len(glyphs)==meta['unique_tiles']*64 and meta['unique_tiles']<=limit
        assert len({glyphs[i:i+64] for i in range(0,len(glyphs),64)})==meta['unique_tiles']
        packedmap=(base/(name+'.map16.bin')).read_bytes();assert len(packedmap)==w//16*h//8*2
        assert (base/(name+'.palette-map.bin')).read_bytes()==bytes(w//16*h//8)
        assert len(meta['tile_map'])==h//8 and all(len(row)==w//16 for row in meta['tile_map'])
        result=bytearray(w*h)
        for ty,row in enumerate(meta['tile_map']):
            for tx,index in enumerate(row):
                n=ty*(w//16)+tx;assert int.from_bytes(packedmap[n*2:n*2+2],'little')==index
                assert 0<=index<meta['unique_tiles'] and meta['palette_map'][ty][tx]==0
                tile=decode(glyphs[index*64:(index+1)*64],16,8,16)
                for y in range(8):result[(ty*8+y)*w+tx*16:(ty*8+y)*w+tx*16+16]=tile[y*16:y*16+16]
        assert bytes(result)==raw
        assert (base/(name+'.palette.rgb')).read_bytes()==bytes(v for c in pal for v in c)
        assert (base/(name+'.palette.palregs.bin')).read_bytes()==bytes(c[ch]%16*16+c[ch]//16 for ch in range(3) for c in pal)
        if name=='title':assert raw[176*320:]==bytes(24*320) and meta['baked_text']=='Shooter65'
        elif name=='game-over-banner':
            assert min(raw)>0 and meta['baked_text'] is None
            assert all(raw[y*256+x]==1 for y in range(6,58) for x in range(64,192))
        else:assert meta['baked_text']=='GAME OVER'
    for name,sha in m['generated_sources'].items():assert hashlib.sha256((ROOT/'assets/art/screens/source'/name).read_bytes()).hexdigest()==sha
    print('PASS screens: native 320x200/256x64, 16-entry indexed PNGs, one palette, unique-tile budgets, full NCM/map/palette round trips and clear engine text fields.')

def closed_body(data,w,h):
    exterior=set();q=deque()
    for y in range(h):
        for x in range(w):
            if (x in (0,w-1) or y in (0,h-1)) and not data[y*w+x]:exterior.add((x,y));q.append((x,y))
    while q:
        x,y=q.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and not data[yy*w+xx] and (xx,yy) not in exterior:exterior.add((xx,yy));q.append((xx,yy))
    assert all(data[y*w+x] or (x,y) in exterior for y in range(h) for x in range(w)),'transparent enclosed hull hole'

def boss():
    base=ROOT/'assets/art/boss-level1/generated';m=check_hashes(base);pal=m['palette']
    assert len(pal)==16 and m['palette_count']==1 and m['body_size']==[96,64]
    records=json.loads((base/'indexed-source.json').read_text());assert len(records)==19
    byid={r['id']:r for r in records}
    raw=(base/'boss.indices.bin').read_bytes();nc=(base/'boss.ncm.bin').read_bytes();fc=(base/'boss.fcm.bin').read_bytes();rrb=(base/'boss.rrb.bin').read_bytes()
    assert len(rrb)==137*64==m['rrb_bytes'] and len(rrb)+(base/'palette.rgb').stat().st_size<=9*1024
    assert rrb[:64]==bytes(64)
    for r in records:
        name=r['id'];w,h=r['width'],r['height'];a=bytes.fromhex(''.join(r['rows']));assert len(a)==w*h and max(a)<=15 and w%16==0 and h%8==0
        im=Image.open(base/(name+'.png')).convert('RGBA');assert im.size==(w,h)
        assert im.tobytes()==bytes(v for i in a for v in (*pal[i],255 if i else 0))
        assert raw[r['indices_offset']:r['indices_offset']+w*h]==a
        assert decode(nc[r['ncm_offset']:r['ncm_offset']+w*h//2],w,h,16)==a
        assert decode(fc[r['fcm_offset']:r['fcm_offset']+w*h],w,h,8)==a
        for col in range(w//16):
            baseglyph=r['rrb_base']+col*(h//8+1);start=baseglyph*64
            part=decode(rrb[start:start+h//8*64],16,h,16)
            assert part==b''.join(a[y*w+col*16:y*w+col*16+16] for y in range(h))
            assert rrb[start+h//8*64:start+(h//8+1)*64]==bytes(64)
    body=bytes.fromhex(''.join(byid['body']['rows']));closed_body(body,96,64)
    place=json.loads((base/'placement.json').read_text());assert len(place['turrets'])==4 and len(place['rotors'])==4
    required=place['mechanic']['body_invulnerable_until'];assert set(required)=={t['id'] for t in place['turrets']}
    assert len(set(required))==4 and place['mechanic']['all_required_turrets_destroyed_state']=='body_vulnerable'
    assert place['mechanic']['defeat_condition']=='body_hp_reaches_zero_after_turrets'
    assert len({tuple(t['offset']) for t in place['turrets']})==4
    for t in place['turrets']:
        x,y=t['offset'];assert t['size']==[16,16] and t['independently_destructible'] and 0<=x<=80 and 0<=y<=48
        assert all(t[k] in byid for k in ('south','southeast','destroyed'))
        assert len({byid[t[k]]['rows'][0]+''.join(byid[t[k]]['rows'][1:]) for k in ('south','southeast','destroyed')})==3
    for part in place['rotors']:
        x,y=part['offset'];assert 0<=x<=64 and 0<=y<=32 and part['phase_offset'] in range(3)
    for name,w,h,count in [('rotor',32,32,3),('muzzle',16,16,2)]:
        strip=Image.open(base/(name+'-animation.png')).convert('RGBA');assert strip.size==(w*count,h)
        assert len({Image.open(base/f'{name}_{i}.png').tobytes() for i in range(count)})==count
        for i in range(count):assert strip.crop((i*w,0,(i+1)*w,h)).tobytes()==Image.open(base/f'{name}_{i}.png').convert('RGBA').tobytes()
    assert Image.open(base/'animated-boss.webp').n_frames==3
    # Rebuild a composition using delivered parts and offsets (not a flattened body).
    composed=Image.open(base/'body.png').convert('RGBA')
    for part in place['rotors']:
        im=Image.open(base/f'rotor_{part["phase_offset"]}.png').convert('RGBA');composed.alpha_composite(im,tuple(part['offset']))
    for part in place['turrets']:
        im=Image.open(base/(part['south']+'.png')).convert('RGBA');composed.alpha_composite(im,tuple(part['offset']))
    assert composed.tobytes()==Image.open(base/'assembled.png').convert('RGBA').tobytes()
    assert (base/'palette.rgb').read_bytes()==bytes(v for c in pal for v in c)
    print('PASS boss: 96x64 closed hull, four distinct independent turret placements/states, separate animated 32x32 rotors, 137 guarded glyphs / 8768 bytes, binary round trips and composed preview.')

if __name__=='__main__':screens();boss()
