"""Original three-voice score, authored for docs/music_json.md; no external samples."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'music'

LEAD=dict(wave='pulse',attack=0,decay=6,sustain=8,release=2,pulse=1200,pulse_sweep=5,
          vibrato=dict(delay=12,speed=4,depth=2))
BASS=dict(wave='triangle',attack=0,decay=5,sustain=7,release=1)
CHORDS={
 'Em':('E-2','E-4','minor'), 'C':('C-2','C-4','major'),
 'G':('G-2','G-3','major'), 'D':('D-2','D-4','major'),
 'Am':('A-2','A-3','minor'), 'B':('B-1','B-3','dominant')}
PHRASES={
 'Em':['E-5','G-5','B-5','A-5','G-5','F#5'],
 'C':['E-5','G-5','E-5','D-5','C-5','E-5'],
 'G':['B-4','D-5','G-5','F#5','D-5','B-4'],
 'D':['A-4','D-5','F#5','E-5','D-5','F#5'],
 'Am':['A-4','C-5','E-5','G-5','E-5','C-5'],
 'B':['D#5','F#5','B-5','A-5','F#5','D#5']}

def blank(n):return ['...']*n

def put(rows,row,note,inst,duration):
    assert row+duration<len(rows)
    rows[row]=f'{note} {inst}';rows[row+duration]='off'

def write(slug,name,tempo,volume,instruments,patterns,order,loop):
    OUT.mkdir(parents=True,exist_ok=True)
    doc=dict(format='shootermega65-music-1',name=name,tempo=tempo,volume=volume,
             instruments=instruments,patterns=patterns,order=order,loop=loop)
    (OUT/(slug+'.json')).write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def level():
    inst=dict(lead=LEAD,bass=BASS)
    for kind,arp in [('minor',[0,3,7]),('major',[0,4,7]),('dominant',[0,4,7,10])]:
        inst[kind]=dict(wave='saw',attack=0,decay=5,sustain=3,release=1,arpeggio=arp)
    inst.update(
      kick=dict(attack=0,decay=6,sustain=0,release=0,pulse=2048,
                wave_table=[['triangle',12],['triangle',4],['triangle',-5],['triangle',-12]]),
      snare=dict(attack=0,decay=6,sustain=0,release=0,
                 wave_table=[['noise','C-7'],['pulse',0],['noise','A-6'],['noise','F-6']]),
      hat=dict(attack=0,decay=3,sustain=0,release=0,wave_table=[['noise','C-7']]))
    sections=[['Em','C','G','D'],['Em','C','Am','B'],['Em','C','G','D'],['Em','C','Am','B'],
              ['C','G','Am','Em'],['C','D','B','B'],['Em','C','G','D'],['Em','C','Am','B'],
              ['Am','C','Em','D'],['C','D','B','B'],['Em','C','G','D'],['C','D','B','B']]
    patterns={};order={f'voice{i}':[] for i in range(1,4)}
    for s,chords in enumerate(sections):
        voices=[blank(64) for _ in range(3)]
        for bar,chord in enumerate(chords):
            root,arp,kind=CHORDS[chord];offset=bar*16
            phrase=PHRASES[chord][:]
            if s in (2,3,6,7,10):phrase[1],phrase[3]=phrase[3],phrase[1]
            if s in (4,8):
                # Lower, more spacious middle section; return restores the hook.
                for k in range(len(phrase)):phrase[k]=phrase[k][:-1]+str(int(phrase[k][-1])-1)
            timing=[(0,3),(4,1),(6,1),(8,3),(12,1),(14,1)]
            if s in (4,8):timing=[(0,5),(6,1),(8,5),(14,1)]
            for k,(row,dur) in enumerate(timing):put(voices[0],offset+row,phrase[k], 'lead',dur)
            for row in (2,6,10,14):put(voices[1],offset+row,arp,kind,1)
            for row in range(16):
                if row in (0,8):event='C-2 kick'
                elif row in (4,12):event='C-3 snare'
                elif row in (2,6,10,14):event='C-7 hat'
                else:event=root+' bass'
                voices[2][offset+row]=event
            voices[2][offset+15]='off'
        # No intro/outro: the dominant at the end resolves into opening Em.
        for i,rows in enumerate(voices,1):
            key=f's{s:02d}_v{i}';patterns[key]=rows;order[f'voice{i}'].append(key)
    write('level1','Coastal Assault – Küstenwald',6,14,inst,patterns,order,0)

def shop():
    inst=dict(bell=dict(wave='triangle',attack=1,decay=7,sustain=4,release=3),
              pad_major=dict(wave='pulse',pulse=2304,attack=2,decay=6,sustain=3,release=2,arpeggio=[0,4,7]),
              pad_minor=dict(wave='pulse',pulse=2304,attack=2,decay=6,sustain=3,release=2,arpeggio=[0,3,7]),bass=BASS)
    chords=[['G','Em','Am','D'],['G','C','Am','D'],['Em','C','Am','D']]
    melodies=[['G-4','B-4','A-4','F#4'],['B-4','G-4','E-4','F#4'],['E-4','G-4','A-4','F#4']]
    patterns={};order={f'voice{i}':[] for i in range(1,4)}
    for s,section in enumerate(chords):
        voices=[blank(64) for _ in range(3)]
        for bar,chord in enumerate(section):
            o=bar*16;root,arp,kind=CHORDS[chord];note=melodies[s][bar]
            put(voices[0],o,note,'bell',6);put(voices[0],o+8,PHRASES[chord][4][:-1]+'4','bell',5)
            put(voices[1],o+2,arp,'pad_minor' if kind=='minor' else 'pad_major',4)
            put(voices[1],o+10,arp,'pad_minor' if kind=='minor' else 'pad_major',4)
            put(voices[2],o,root,'bass',6);put(voices[2],o+8,root,'bass',6)
        for i,rows in enumerate(voices,1):
            key=f'shop{s}_v{i}';patterns[key]=rows;order[f'voice{i}'].append(key)
    write('shop','Safe Harbour – Zwischenstopp',8,10,inst,patterns,order,0)

def jingles():
    inst=dict(lead=dict(wave='pulse',pulse=1536,attack=1,decay=6,sustain=7,release=3),
              low=dict(wave='triangle',attack=0,decay=6,sustain=6,release=3),
              minor=dict(wave='triangle',attack=0,decay=7,sustain=5,release=3,arpeggio=[0,3,7]),
              major=dict(wave='triangle',attack=0,decay=7,sustain=5,release=3,arpeggio=[0,4,7]))
    for slug,title,tempo,notes,chords,roots,mode in [
      ('game_over','Last Flight – Game Over',6,
       [(0,'E-5',5),(6,'D-5',3),(10,'B-4',5),(16,'A-4',5),(22,'G-4',3),(26,'F#4',3),(30,'F-4',1),(32,'E-4',10)],
       ['C-4','B-3','E-3'],['C-2','B-1','E-2'],'minor'),
      ('level_clear','Clear Skies – Level geschafft',5,
       [(0,'E-5',2),(3,'G#5',2),(6,'B-5',2),(9,'E-6',5),(16,'D#6',2),(19,'B-5',2),(22,'F#5',2),(25,'D#6',3),(32,'E-6',10)],
       ['E-4','B-3','E-4'],['E-2','B-1','E-2'],'major')]:
        voices=[blank(48) for _ in range(3)]
        for row,note,dur in notes:put(voices[0],row,note,'lead',dur)
        for bar,(chord,root) in enumerate(zip(chords,roots)):
            harmony='major' if slug=='game_over' and bar<2 else mode
            put(voices[1],bar*16,chord,harmony,12)
            put(voices[2],bar*16,root,'low',12)
        patterns={f'j_v{i}':rows for i,rows in enumerate(voices,1)}
        write(slug,title,tempo,12,inst,patterns,{f'voice{i}':[f'j_v{i}'] for i in range(1,4)},None)

if __name__=='__main__':
    level();shop();jingles();print('Composed level1 92.16s, shop 30.72s, game_over 5.76s, level_clear 4.80s.')
