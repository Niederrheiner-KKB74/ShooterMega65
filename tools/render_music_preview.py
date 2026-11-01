"""Deterministic score audition, NOT a SID emulator or hardware reference."""
import hashlib
import json
import math
from pathlib import Path
import wave
import numpy as np
from validate_music_suite import note_number,validate

ROOT=Path(__file__).resolve().parents[1];SR=22050;FRAME=SR//50
OUT=ROOT/'previews'
# Musical audition envelopes only; analog SID timing/model differences are not simulated.
ATTACK=[.002,.008,.016,.024,.038,.056,.068,.080,.100,.250,.5,.8,1,3,5,8]
DECAY=[.006,.024,.048,.072,.114,.168,.204,.240,.300,.750,1.5,2.4,3,9,15,24]

class Voice:
    def __init__(self,seed):
        self.rng=np.random.default_rng(seed);self.phase=0.;self.note=0;self.inst=None
        self.age=0;self.fx=0;self.gate=False;self.release_age=0;self.release_level=0.;self.last_env=0.
    def event(self,row,instruments):
        if row=='...':return
        if row=='off':
            if self.gate:self.release_level=self.last_env;self.release_age=0
            self.gate=False;return
        parts=row.split();legato=parts[-1]=='>'
        if legato:parts.pop()
        self.note=note_number(parts[0])
        if len(parts)>1:self.inst=instruments[parts[1]]
        if not legato or not self.gate:
            self.age=0;self.fx=0;self.phase=0.
        self.gate=True
    def frame(self):
        if self.inst is None:return np.zeros(FRAME)
        i=self.inst;t=(self.age+np.arange(FRAME))/SR
        attack=ATTACK[i['attack']];decay=DECAY[i['decay']];sustain=i['sustain']/15
        if self.gate:
            env=np.where(t<attack,t/attack,np.where(t<attack+decay,1-(1-sustain)*(t-attack)/decay,sustain))
        else:
            rt=(self.release_age+np.arange(FRAME))/SR
            env=self.release_level*np.maximum(0,1-rt/DECAY[i['release']]);self.release_age+=FRAME
        self.last_env=float(env[-1]);pitch=float(self.note);waveform=i.get('wave','triangle')
        if 'wave_table' in i:
            waveform,v=i['wave_table'][min(self.fx,len(i['wave_table'])-1)]
            pitch=note_number(v) if isinstance(v,str) else self.note+v
        elif 'arpeggio' in i:pitch+=i['arpeggio'][self.fx%len(i['arpeggio'])]
        v=i.get('vibrato')
        if v and self.fx>=v['delay']:
            pitch+=math.sin(2*math.pi*(self.fx-v['delay'])/(v['speed']*4))*v['depth']/8
        hz=440*2**((pitch+12-69)/12);ph=(self.phase+np.arange(FRAME)*hz/SR)%1
        self.phase=(self.phase+FRAME*hz/SR)%1
        if waveform=='triangle':osc=1-4*np.abs(ph-.5)
        elif waveform=='saw':osc=2*ph-1
        elif waveform=='pulse':
            width=i.get('pulse',2048)+self.fx*i.get('pulse_sweep',0)
            if 'pulse_sweep' in i:
                q=(width-256)%(2*3584);width=256+(q if q<=3584 else 7168-q)
            osc=np.where(ph<width/4096,1.,-1.)
        else:
            # Seeded white-noise approximation, not the SID's clocked noise LFSR.
            osc=self.rng.uniform(-1,1,FRAME)
        self.age+=FRAME;self.fx+=1
        return osc*np.clip(env,0,1)

def save(name,a):
    assert np.isfinite(a).all() and np.max(np.abs(a))<1,'clipping / invalid samples'
    pcm=np.rint(a*32767).astype('<i2')
    with wave.open(str(OUT/name),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())
    return dict(samples=len(a),seconds=len(a)/SR,peak=float(np.max(np.abs(a))),rms=float(np.sqrt(np.mean(a*a))),
                sha256=hashlib.sha256((OUT/name).read_bytes()).hexdigest())

def render(slug):
    path=ROOT/'music'/(slug+'.json');metadata=validate(path);d=json.loads(path.read_text(encoding='utf-8'))
    rows=[[r for p in d['order'][f'voice{i}'] for r in d['patterns'][p]] for i in range(1,4)]
    voices=[Voice(6500+i) for i in range(3)];chunks=[]
    for r in range(metadata['rows']):
        for v,pattern in zip(voices,rows):v.event(pattern[r],d['instruments'])
        for _ in range(d['tempo']):
            # Fixed gain across tracks: the shop's lower volume is retained.
            chunks.append(sum(v.frame()*g for v,g in zip(voices,(.29,.17,.27)))*d.get('volume',15)/15)
    audio=np.concatenate(chunks)
    assert len(audio)==round(metadata['seconds']*SR)
    assert np.max(np.abs(audio[-FRAME:]))<1e-9,'release tail did not finish'
    report=save(slug+'.wav',audio)
    if d['loop'] is not None:
        # This concatenation adds no fade or padding: auditions the actual wrap.
        assert abs(audio[-1]-audio[0])<1e-9
        seam=np.concatenate((audio[-4*SR:],audio[:4*SR]))
        report['loop_seam']=save(slug+'_loop_check.wav',seam)
        report['boundary_jump']=float(abs(audio[-1]-audio[0]))
    print(f'{slug}: {report["seconds"]:.2f}s, peak {report["peak"]:.3f}, RMS {report["rms"]:.3f}')
    return report

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    report={s:render(s) for s in ('level1','shop','game_over','level_clear')}
    (ROOT/'docs/music-preview-report.json').write_text(json.dumps(dict(sample_rate=SR,channels=1,pcm_bits=16,
        renderer='Approximate synthesis, not a SID emulator. No filter or analog quirks modeled.',tracks=report),indent=2)+'\n')
