#!/usr/bin/env python3
"""Check palette, dimensions, belt-only animation and binary round trips."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_tanks import frame,DIRECTIONS

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/ground-vehicles';OUT=BASE/'generated'


def decode(data,tw):
    values=[]
    for y in range(16):
        for x in range(16):
            at=((y//8)*(16//tw)+x//tw)*64+(y%8)*8+(x%tw)//(2 if tw==16 else 1)
            b=data[at];values.append((b>>((x%2)*4))&15 if tw==16 else b)
    return bytes(values)


def main():
    m=json.loads((OUT/'manifest.json').read_text());cfg=json.loads((BASE/'source/tank.json').read_text())
    assert m['frame_size']==[16,16] and len(m['frames'])==16 and len(m['palette'])==16
    assert m['palette']==cfg['palette'] and not m['integrated'] and not m['hardware_tested']
    for name,info in m['files'].items():
        data=(OUT/name).read_bytes();assert len(data)==info['bytes'] and hashlib.sha256(data).hexdigest()==info['sha256'],name
    raw=(OUT/'tank.indices.bin').read_bytes();ncm=(OUT/'tank.ncm.bin').read_bytes();fcm=(OUT/'tank.fcm.bin').read_bytes();rrb=(OUT/'tank.rrb.bin').read_bytes()
    assert len(raw)==4096 and len(ncm)==2048 and len(fcm)==4096 and len(rrb)==49*64
    assert rrb[:64]==bytes(64)
    used=set()
    for direction in DIRECTIONS:
        strip=Image.open(OUT/('tank_'+direction+'.png')).convert('RGBA');assert strip.size==(64,16)
        allpix=list(strip.getdata());assert set(p[3] for p in allpix)=={0,255}
        used.update(p[:3] for p in allpix if p[3])
        baseline,mask=frame(direction,0);a=baseline.tobytes();mask=mask.tobytes()
        assert len({frame(direction,n)[0].tobytes() for n in range(4)})==4
        assert frame(direction,4)[0].tobytes()==a
        for phase in range(4):
            p=frame(direction,phase)[0].tobytes()
            assert all(av==pv or mask[i] for i,(av,pv) in enumerate(zip(a,p)))
            expected=[tuple(m['palette'][v])+(255 if v else 0,) for v in p]
            assert list(strip.crop((phase*16,0,phase*16+16,16)).getdata())==expected
        anim=Image.open(OUT/('tank_'+direction+'.webp'));assert anim.n_frames==4
    assert len(used)<=15
    for r in m['frames']:
        expected=frame(r['direction'],r['phase'])[0].tobytes()
        assert raw[r['indices_offset']:r['indices_offset']+256]==expected
        assert decode(ncm[r['ncm_offset']:r['ncm_offset']+128],16)==expected
        assert decode(fcm[r['fcm_offset']:r['fcm_offset']+256],8)==expected
        base=r['rrb_base'];assert decode(rrb[base*64:(base+2)*64],16)==expected
        assert rrb[(base-1)*64:base*64]==bytes(64) and rrb[(base+2)*64:(base+3)*64]==bytes(64)
        assert r['palette_byte']==0x4f
    reg=(OUT/'palette.palregs.bin').read_bytes()
    assert reg==bytes(((c[ch]&15)<<4)|(c[ch]>>4) for ch in range(3) for c in m['palette'])
    print(f'PASS: 16 frames, four directions, four belt-only phases, {len(used)} shared opaque colours, exact FCM/NCM/RRB decode and guards, palette register encoding, animated previews.')


if __name__=='__main__':main()
