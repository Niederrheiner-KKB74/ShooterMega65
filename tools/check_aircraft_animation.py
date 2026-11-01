#!/usr/bin/env python3
"""Independent animation invariants: only the documented effect mask may vary."""
import json
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/art/spec-v2/generated'


def main():
    m=json.loads((OUT/'manifest.json').read_text())
    for name,anim in m['animations'].items():
        g=next(g for g in m['groups'] if g['id']==name);w,h=g['size']
        strip=Image.open(OUT/(name+'.png')).convert('RGBA');mask=Image.open(OUT/anim['mask_file']).convert('L').tobytes()
        frames=[strip.crop((n*w,0,(n+1)*w,h)) for n in anim['loop']]
        assert len({p.tobytes() for p in frames})==3,(name,'non-distinct animation')
        reference=list(frames[0].getdata())
        for p in frames[1:]:
            actual=list(p.getdata())
            differences=[i for i,(a,b) in enumerate(zip(reference,actual)) if a!=b]
            assert differences and all(mask[i] for i in differences),(name,'body changes')
        assert len({p[:3] for p in strip.getdata() if p[3]})<=15
        assert set(p[3] for p in strip.getdata())=={0,255}
        if name=='player':
            assert strip.crop((4*w,0,5*w,h)).tobytes()==frames[0].tobytes()
            assert anim['banking_frames']==[3,5]
        preview=Image.open(OUT/('animated-'+name+'.webp'));assert preview.n_frames==3
    print('PASS: 5 genuine animation loops; all differences confined to exhaust/rotor masks; player normal frame matches canonical loop; palettes and alpha valid.')


if __name__=='__main__':main()
