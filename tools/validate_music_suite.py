"""Strict independent checks against docs/music_json.md; not the future game compiler."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NOTE=re.compile(r'^([A-G])([-#])([0-7])$')
WAVES={'triangle','saw','pulse','noise'}

def note_number(s):
    m=NOTE.fullmatch(s);assert m,f'invalid note {s!r}'
    n=int(m[3])*12+{'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}[m[1]]+(m[2]=='#')
    assert 0<=n<=95,s
    return n

def integer(v,lo,hi):assert type(v) is int and lo<=v<=hi,(v,lo,hi)

def validate(path):
    d=json.loads(path.read_text(encoding='utf-8'))
    assert set(d)<={'format','name','tempo','volume','filter','instruments','patterns','order','loop'}
    assert {'format','name','tempo','instruments','patterns','order','loop'}<=set(d)
    assert d['format']=='shootermega65-music-1' and isinstance(d['name'],str)
    integer(d['tempo'],1,31);integer(d.get('volume',15),0,15)
    if 'filter' in d:
        f=d['filter'];assert set(f)=={'mode','cutoff','resonance'}
        assert f['mode'] in {'lowpass','bandpass','highpass'};integer(f['cutoff'],0,2047);integer(f['resonance'],0,15)
    assert 1<=len(d['instruments'])<=32
    for name,i in d['instruments'].items():
        assert set(i)<={'wave','attack','decay','sustain','release','pulse','pulse_sweep','vibrato','arpeggio','wave_table','filter'},name
        for key in ('attack','decay','sustain','release'):integer(i[key],0,15)
        assert 'wave' in i or 'wave_table' in i
        if 'wave' in i:assert i['wave'] in WAVES
        if 'pulse' in i:integer(i['pulse'],0,4095)
        if 'pulse_sweep' in i:integer(i['pulse_sweep'],-255,255)
        if 'filter' in i:assert type(i['filter']) is bool
        if 'vibrato' in i:
            v=i['vibrato'];assert set(v)=={'delay','speed','depth'}
            integer(v['delay'],0,255);integer(v['speed'],1,15);integer(v['depth'],1,15)
        if 'arpeggio' in i:assert i['arpeggio'] and all(type(x) is int for x in i['arpeggio'])
        if 'wave_table' in i:
            assert i['wave_table']
            for wave,pitch in i['wave_table']:
                assert wave in WAVES
                if isinstance(pitch,str):note_number(pitch)
                else:assert type(pitch) is int
    pats=d['patterns'];assert 1<=len(pats)<=128
    for name,rows in pats.items():
        assert isinstance(rows,list) and 1<=len(rows)<=64,name
        for r in rows:
            assert isinstance(r,str)
            if r in ('...','off'):continue
            parts=r.split();note_number(parts.pop(0))
            if parts and parts[-1]=='>':parts.pop()
            assert len(parts)<=1,r
            if parts:assert parts[0] in d['instruments'],r
    order=d['order'];assert set(order)=={'voice1','voice2','voice3'}
    lengths=[];prefix=[]
    for voice,seq in order.items():
        assert isinstance(seq,list) and 1<=len(seq)<=128 and all(p in pats for p in seq),voice
        flat=[r for p in seq for r in pats[p]];lengths.append(len(flat))
        instrument=None;gate=False
        for r in flat:
            if r=='off':gate=False
            elif r!='...':
                parts=r.split();note_number(parts[0])
                names=[p for p in parts[1:] if p!='>']
                if names:instrument=names[0]
                assert instrument is not None,(voice,r)
                gate=True
        assert not gate,(voice,'gate must release before end / loop boundary')
        if d['loop'] is not None:
            integer(d['loop'],0,len(seq)-1);prefix.append(sum(len(pats[p]) for p in seq[:d['loop']]))
    assert len(set(lengths))==1,lengths
    if prefix:assert len(set(prefix))==1,'loop positions do not align'
    seconds=lengths[0]*d['tempo']/50
    limits={'level1':(60,120,True),'shop':(20,40,True),'game_over':(3,8,False),'level_clear':(3,8,False)}
    lo,hi,looped=limits[path.stem];assert lo<=seconds<=hi
    assert (d['loop'] is not None)==looped
    if looped:assert d['loop']==0
    return dict(name=d['name'],rows=lengths[0],tempo=d['tempo'],bpm=750/d['tempo'],seconds=seconds,
                patterns=len(pats),instruments=len(d['instruments']),loop=d['loop'])

def main():
    report={}
    for slug in ('level1','shop','game_over','level_clear'):
        r=validate(ROOT/'music'/(slug+'.json'));report[slug]=r
        print(f'PASS {slug}: {r["seconds"]:.2f}s, {r["rows"]} rows/voice, {r["patterns"]} patterns, loop={r["loop"]}')
    p=ROOT/'docs/music-validation.json';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
