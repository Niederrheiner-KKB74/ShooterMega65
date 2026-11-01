"""Regression checks for authored score, strict failures and deterministic exports."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
from validate_music_suite import validate

ROOT=Path(__file__).resolve().parents[1]

def main():
    names=('level1','shop','game_over','level_clear')
    before={n:hashlib.sha256((ROOT/'music'/(n+'.json')).read_bytes()).hexdigest() for n in names}
    subprocess.run([sys.executable,str(ROOT/'tools/compose_music_suite.py')],check=True)
    assert before=={n:hashlib.sha256((ROOT/'music'/(n+'.json')).read_bytes()).hexdigest() for n in names}
    original=json.loads((ROOT/'music/level1.json').read_text(encoding='utf-8'))
    mutations=[]
    bad=copy.deepcopy(original);bad['unknown']=1;mutations.append(bad)
    bad=copy.deepcopy(original);bad['patterns']['s00_v1'][0]='H-5 lead';mutations.append(bad)
    bad=copy.deepcopy(original);bad['order']['voice2'].pop();mutations.append(bad)
    bad=copy.deepcopy(original);bad['loop']=99;mutations.append(bad)
    bad=copy.deepcopy(original);bad['patterns']['s00_v1'][0]='E-5 missing';mutations.append(bad)
    bad=copy.deepcopy(original);bad['patterns']['s00_v1']=['...']*65;mutations.append(bad)
    scratch=ROOT/'work';scratch.mkdir(exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='music-check-',dir=scratch));p=tmp/'level1.json'
    try:
        for bad in mutations:
            p.write_text(json.dumps(bad),encoding='utf-8')
            try:validate(p)
            except (AssertionError,KeyError):pass
            else:raise AssertionError('validator accepted malformed score')
    finally:
        p.unlink(missing_ok=True);tmp.rmdir()
    report=json.loads((ROOT/'docs/music-preview-report.json').read_text())
    for name in names:
        score=validate(ROOT/'music'/(name+'.json'));r=report['tracks'][name]
        p=ROOT/'previews'/(name+'.wav')
        assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
        with wave.open(str(p)) as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,22050)
            assert w.getnframes()==round(score['seconds']*22050)
        assert 0<r['peak']<1 and r['rms']>.01
        if score['loop'] is not None:
            assert r['boundary_jump']==0
            p=ROOT/'previews'/(name+'_loop_check.wav')
            assert hashlib.sha256(p.read_bytes()).hexdigest()==r['loop_seam']['sha256']
    assert report['tracks']['shop']['rms']<report['tracks']['level1']['rms']/2
    print('PASS: four scores, six malformed-input rejections, reproducible composition, WAV durations/hashes, no clipping and loop sample boundaries.')

if __name__=='__main__':main()
