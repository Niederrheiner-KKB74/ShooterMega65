#!/usr/bin/env python3
"""Score for the four pieces of ShooterMega65 (Stage 5), written by Claude.

Writes music/level1.json, music/shop.json, music/game_over.json, music/level_clear.json in the format of
docs/music_json.md. The score below is the source: melodies as (note, length in rows), chords per bar,
bass/drum styles per section. Each voice is cut into 64-row patterns; identical patterns are stored once.

  level1       "Coastal Run" – D minor, 125 BPM (tempo 6, 16 rows per bar), 44 bars, loops to bar 5
  shop         "Supply Depot" – F major, ~107 BPM (tempo 7), 16 bars, laid back, loops
  game_over    D minor, 2 bars, falling line, ends
  level_clear  D major fanfare, 3 bars, ends
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAT = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
NAMES = ['C-', 'C#', 'D-', 'D#', 'E-', 'F-', 'F#', 'G-', 'G#', 'A-', 'A#', 'B-']


def num(n):
    """'D5', 'Bb4', 'F#3' -> note number (C-0 = 0)."""
    name, octv = n[:-1], int(n[-1])
    name = FLAT.get(name, name)
    return octv * 12 + [x.rstrip('-') for x in NAMES].index(name)


def name(k):
    return f'{NAMES[k % 12]}{k // 12}'


class Voice:
    def __init__(self):
        self.rows, self.inst = [], None

    def note(self, n, length, inst, legato=False):
        k = num(n) if isinstance(n, str) else n
        t = name(k)
        if inst != self.inst:
            t += ' ' + inst
            self.inst = inst
        if legato:
            t += ' >'
        self.rows.append(t)
        self.rows += ['...'] * (length - 1)

    def off(self, length):
        self.rows.append('off')
        self.rows += ['...'] * (length - 1)

    def rest(self, length):
        self.rows += ['...'] * length

    def melody(self, items, inst, legato_runs=False):
        """items: (note, length) / ('-', length) = off / ('.', length) = hold."""
        for n, length in items:
            if n == '-':
                self.off(length)
            elif n == '.':
                self.rest(length)
            else:
                self.note(n, length, inst, legato=legato_runs and length <= 2)


QUALITY = {'m': 'arp_min', '': 'arp_maj', '7': 'arp_dom7', 'maj7': 'arp_maj7', 'm7': 'arp_min7', 'sus': 'arp_sus'}


def chord(sym):
    """'Dm' -> (root name, quality)."""
    root = sym[0] + (sym[1] if len(sym) > 1 and sym[1] in '#b' else '')
    return root, sym[len(root):]


def build(name_, tempo, volume, voices, loop_row, instruments, out):
    pats, order = {}, {}
    seen = {}
    lens = {len(v.rows) for v in voices}
    assert len(lens) == 1, f'{name_}: voices differ {[len(v.rows) for v in voices]}'
    for vi, v in enumerate(voices, 1):
        lst = []
        for i in range(0, len(v.rows), 64):
            chunk = v.rows[i:i + 64]
            # a chunk must carry its instrument on the first note: patterns can be reused anywhere
            key = tuple(chunk)
            if key not in seen:
                pid = f'v{vi}_{len([p for p in pats if p.startswith(f"v{vi}_")]):02d}'
                seen[key] = pid
                pats[pid] = chunk
            lst.append(seen[key])
        order[f'voice{vi}'] = lst
    doc = {'format': 'shootermega65-music-1', 'name': name_, 'tempo': tempo, 'volume': volume,
           'instruments': instruments, 'patterns': pats, 'order': order,
           'loop': None if loop_row is None else loop_row // 64}
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')


def fix_instruments(v):
    """Every 64-row chunk starts its first note with an explicit instrument (patterns are shared)."""
    cur = None
    for i, r in enumerate(v.rows):
        t = r.split()
        if i % 64 == 0:
            cur_at_start = cur
            need = True
        if t and t[0] not in ('...', 'off'):
            if len(t) >= 2 and t[1] != '>':
                cur = t[1]
                need = False
            elif need:
                v.rows[i] = ' '.join([t[0], cur] + t[1:])
                need = False
    return v


# ============================================================== instruments
LEVEL_INST = {
    'lead':     {'wave': 'pulse', 'attack': 0, 'decay': 9, 'sustain': 9, 'release': 6, 'pulse': 1400,
                 'pulse_sweep': 20, 'vibrato': {'delay': 10, 'speed': 2, 'depth': 2}},
    'lead_saw': {'wave': 'saw', 'attack': 0, 'decay': 8, 'sustain': 8, 'release': 7,
                 'vibrato': {'delay': 8, 'speed': 2, 'depth': 3}},
    'arp_min':  {'wave': 'pulse', 'attack': 0, 'decay': 6, 'sustain': 7, 'release': 3, 'pulse': 900,
                 'pulse_sweep': 12, 'arpeggio': [0, 3, 7, 12]},
    'arp_maj':  {'wave': 'pulse', 'attack': 0, 'decay': 6, 'sustain': 7, 'release': 3, 'pulse': 900,
                 'pulse_sweep': 12, 'arpeggio': [0, 4, 7, 12]},
    'arp_sus':  {'wave': 'pulse', 'attack': 0, 'decay': 6, 'sustain': 7, 'release': 3, 'pulse': 900,
                 'pulse_sweep': 12, 'arpeggio': [0, 5, 7, 12]},
    'bass':     {'wave': 'pulse', 'attack': 0, 'decay': 7, 'sustain': 6, 'release': 2, 'pulse': 2200,
                 'pulse_sweep': -24},
    'bass_long': {'wave': 'pulse', 'attack': 0, 'decay': 10, 'sustain': 9, 'release': 6, 'pulse': 2048,
                  'pulse_sweep': 10},
    'kick':     {'attack': 0, 'decay': 7, 'sustain': 0, 'release': 0,
                 'wave_table': [['pulse', 'G-3'], ['triangle', 'D-3'], ['triangle', 'A-2'], ['triangle', 'E-2'],
                                ['triangle', 'C-2'], ['triangle', 'A-1']]},
    'snare':    {'attack': 0, 'decay': 8, 'sustain': 0, 'release': 0, 'pulse': 1600,
                 'wave_table': [['noise', 'C-7'], ['pulse', 'G-4'], ['noise', 'A-6'], ['noise', 'G-6'],
                                ['noise', 'F-6'], ['noise', 'E-6']]},
    'hat':      {'attack': 0, 'decay': 3, 'sustain': 0, 'release': 0, 'wave_table': [['noise', 'C-7']]},
}


def bass_drums(v, root, style):
    """One bar (16 rows) on voice 3: bass and drums share the voice."""
    r = num(root)
    lo, hi = r, r + 12
    if style == 'drive':          # kick, bass, snare, octave …
        v.note('C4', 2, 'kick'); v.note(lo, 2, 'bass'); v.note('C4', 2, 'snare'); v.note(hi, 2, 'bass')
        v.note(lo, 2, 'bass'); v.note('C4', 2, 'kick'); v.note('C4', 2, 'snare'); v.note(hi, 2, 'bass')
    elif style == 'drive_fill':   # last bar of a phrase: snare roll
        v.note('C4', 2, 'kick'); v.note(lo, 2, 'bass'); v.note('C4', 2, 'snare'); v.note(hi, 2, 'bass')
        v.note('C4', 1, 'snare'); v.note('C4', 1, 'snare'); v.note('C4', 2, 'snare')
        v.note('C4', 1, 'snare'); v.note('C4', 1, 'snare'); v.note('C4', 1, 'snare'); v.note('C4', 1, 'snare')
    elif style == 'bass_only':    # intro: pulsing eighths
        for k in range(8):
            v.note(hi if k % 4 == 2 else lo, 2, 'bass')
    elif style == 'half':         # breakdown: kick on 1 and 3, long bass
        v.note('C4', 2, 'kick'); v.note(lo, 6, 'bass_long'); v.note('C4', 2, 'kick'); v.note(lo + 7, 6, 'bass_long')
    else:
        raise ValueError(style)


def arps(v, sym, style, octave=4):
    root, q = chord(sym)
    n = f'{root}{octave}'
    inst = {'m': 'arp_min', '': 'arp_maj', 'sus': 'arp_sus'}[q]
    if style == 'push':           # 3 + 3 + 2 syncopation, twice
        v.note(n, 3, inst); v.note(n, 3, inst); v.note(n, 2, inst)
        v.note(n, 3, inst); v.note(n, 3, inst); v.note(n, 2, inst)
    elif style == 'hold':
        v.note(n, 16, inst)
    elif style == 'stab':         # breakdown: short chords on the beat
        for _ in range(4):
            v.note(n, 2, inst); v.off(2)
    else:
        raise ValueError(style)


def level1():
    lead, harm, low = Voice(), Voice(), Voice()
    # ---- intro (bars 1-4): bass, chord pulses, lead pickup
    for c in ('Dm', 'Dm', 'Bb', 'C'):
        arps(harm, c, 'push')
    for root in ('D2', 'D2', 'Bb1', 'C2'):
        bass_drums(low, root, 'bass_only')
    lead.rest(32)
    lead.melody([('.', 8), ('D5', 2), ('E5', 2), ('F5', 2), ('G5', 2), ('A5', 12), ('-', 4)], 'lead', True)

    # ---- A (bars 5-12)
    A = [('D5', 4), ('A4', 2), ('D5', 2), ('F5', 4), ('E5', 2), ('D5', 2),
         ('F5', 6), ('D5', 2), ('Bb4', 4), ('C5', 4),
         ('E5', 4), ('G5', 4), ('E5', 2), ('C5', 2), ('E5', 4),
         ('A5', 8), ('G5', 2), ('F5', 2), ('E5', 4),
         ('D5', 4), ('A4', 2), ('D5', 2), ('F5', 4), ('A5', 4),
         ('Bb5', 6), ('A5', 2), ('F5', 4), ('D5', 4),
         ('E5', 4), ('G5', 2), ('F5', 2), ('E5', 4), ('C5', 4),
         ('C#5', 8), ('E5', 4), ('A5', 4)]
    A_chords = ['Dm', 'Bb', 'C', 'Am', 'Dm', 'Bb', 'C', 'A']
    A_bass = ['D2', 'Bb1', 'C2', 'A1', 'D2', 'Bb1', 'C2', 'A1']

    def section_a():
        lead.melody(A, 'lead', True)
        for c in A_chords:
            arps(harm, c, 'push')
        for i, r in enumerate(A_bass):
            bass_drums(low, r, 'drive_fill' if i == 7 else 'drive')
    section_a()

    # ---- A' (bars 13-20): higher, faster figures
    lead.melody([('A5', 2), ('G5', 2), ('F5', 2), ('E5', 2), ('F5', 4), ('D5', 4),
                 ('D5', 2), ('F5', 2), ('Bb5', 4), ('A5', 4), ('F5', 4),
                 ('C6', 6), ('A5', 2), ('F5', 4), ('A5', 4),
                 ('G5', 8), ('E5', 4), ('C5', 4),
                 ('D5', 4), ('F5', 2), ('A5', 2), ('D6', 8),
                 ('C6', 2), ('Bb5', 2), ('A5', 2), ('G5', 2), ('F5', 4), ('D5', 4),
                 ('E5', 4), ('F5', 2), ('G5', 2), ('E5', 4), ('C5', 4),
                 ('A4', 4), ('C#5', 4), ('E5', 4), ('G5', 4)], 'lead', True)
    for c in ('Dm', 'Bb', 'F', 'C', 'Dm', 'Bb', 'C', 'A'):
        arps(harm, c, 'push')
    for i, r in enumerate(('D2', 'Bb1', 'F2', 'C2', 'D2', 'Bb1', 'C2', 'A1')):
        bass_drums(low, r, 'drive_fill' if i == 7 else 'drive')

    # ---- B (bars 21-28): sawtooth lead, long notes, chords held
    lead.melody([('G5', 8), ('Bb5', 4), ('A5', 4),
                 ('F5', 8), ('D5', 4), ('A4', 4),
                 ('Bb4', 4), ('D5', 4), ('F5', 4), ('Bb5', 4),
                 ('A5', 6), ('G5', 2), ('E5', 8),
                 ('G5', 4), ('A5', 2), ('Bb5', 2), ('D6', 8),
                 ('C6', 4), ('A5', 4), ('F5', 4), ('D5', 4),
                 ('Eb5', 4), ('G5', 4), ('Bb5', 4), ('Eb6', 4),
                 ('C#6', 8), ('E6', 4), ('A5', 4)], 'lead_saw')
    for c in ('Gm', 'Dm', 'Bb', 'C', 'Gm', 'Dm', 'Eb', 'A'):
        arps(harm, c, 'hold')
    for i, r in enumerate(('G1', 'D2', 'Bb1', 'C2', 'G1', 'D2', 'Eb2', 'A1')):
        bass_drums(low, r, 'drive_fill' if i in (3, 7) else 'drive')

    # ---- breakdown (bars 29-32)
    lead.melody([('D5', 4), ('-', 4), ('F5', 4), ('-', 4),
                 ('E5', 4), ('-', 4), ('G5', 4), ('-', 4),
                 ('A5', 16),
                 ('A5', 4), ('G5', 4), ('F5', 4), ('E5', 4)], 'lead')
    for c in ('Bb', 'C', 'Dm', 'Dm'):
        arps(harm, c, 'stab')
    for r in ('Bb1', 'C2', 'D2', 'D2'):
        bass_drums(low, r, 'half')

    # ---- A'' (bars 33-40) = A, then turnaround (bars 41-44)
    section_a()
    lead.melody([('D5', 4), ('F5', 4), ('Bb5', 4), ('A5', 4),
                 ('G5', 4), ('E5', 4), ('C5', 4), ('E5', 4),
                 ('C#5', 8), ('E5', 8),
                 ('A5', 12), ('-', 4)], 'lead')
    for c in ('Bb', 'C', 'A', 'A'):
        arps(harm, c, 'push')
    for i, r in enumerate(('Bb1', 'C2', 'A1', 'A1')):
        bass_drums(low, r, 'drive_fill' if i == 3 else 'drive')
    vs = [fix_instruments(v) for v in (lead, harm, low)]
    build('Coastal Run', 6, 15, vs, 64, LEVEL_INST, ROOT / 'music/level1.json')


SHOP_INST = {
    'flute':  {'wave': 'triangle', 'attack': 2, 'decay': 9, 'sustain': 10, 'release': 8,
               'vibrato': {'delay': 14, 'speed': 3, 'depth': 3}},
    'arp_maj7': {'wave': 'pulse', 'attack': 1, 'decay': 8, 'sustain': 5, 'release': 6, 'pulse': 2048,
                 'pulse_sweep': 6, 'arpeggio': [0, 0, 4, 4, 7, 7, 11, 11]},
    'arp_min7': {'wave': 'pulse', 'attack': 1, 'decay': 8, 'sustain': 5, 'release': 6, 'pulse': 2048,
                 'pulse_sweep': 6, 'arpeggio': [0, 0, 3, 3, 7, 7, 10, 10]},
    'arp_dom7': {'wave': 'pulse', 'attack': 1, 'decay': 8, 'sustain': 5, 'release': 6, 'pulse': 2048,
                 'pulse_sweep': 6, 'arpeggio': [0, 0, 4, 4, 7, 7, 10, 10]},
    'walk':   {'wave': 'triangle', 'attack': 0, 'decay': 9, 'sustain': 4, 'release': 3},
}


def shop():
    lead, harm, low = Voice(), Voice(), Voice()
    chords = ['Fmaj7', 'Gm7', 'Am7', 'Bbmaj7', 'Gm7', 'C7', 'Fmaj7', 'Fmaj7'] * 2
    walks = [('F2', 'A2', 'C3', 'E3'), ('G2', 'Bb2', 'D3', 'F3'), ('A2', 'C3', 'E3', 'G3'), ('Bb2', 'D3', 'F3', 'A3'),
             ('G2', 'A2', 'Bb2', 'B2'), ('C3', 'E3', 'G3', 'E3'), ('F2', 'C3', 'A2', 'C3'), ('F2', 'G2', 'A2', 'C3')] * 2
    for c in chords:
        root, q = chord(c)
        harm.note(f'{root}3', 14, {'maj7': 'arp_maj7', 'm7': 'arp_min7', '7': 'arp_dom7'}[q])
        harm.off(2)
    for w in walks:
        for n in w:
            low.note(n, 4, 'walk')
    lead.melody([('A5', 8), ('G5', 4), ('F5', 4),
                 ('Bb5', 6), ('A5', 2), ('G5', 8),
                 ('C6', 4), ('A5', 4), ('E5', 8),
                 ('D6', 8), ('C6', 4), ('A5', 4),
                 ('G5', 8), ('A5', 4), ('Bb5', 4),
                 ('C6', 4), ('Bb5', 4), ('G5', 4), ('E5', 4),
                 ('F5', 16),
                 ('-', 8), ('C5', 4), ('E5', 4),
                 ('C6', 4), ('A5', 4), ('F5', 4), ('A5', 4),
                 ('D6', 6), ('C6', 2), ('Bb5', 8),
                 ('E6', 4), ('C6', 4), ('A5', 8),
                 ('F6', 8), ('D6', 4), ('Bb5', 4),
                 ('A5', 4), ('Bb5', 4), ('C6', 4), ('D6', 4),
                 ('E6', 8), ('C6', 4), ('Bb5', 4),
                 ('A5', 16),
                 ('-', 12), ('C5', 4)], 'flute')
    vs = [fix_instruments(v) for v in (lead, harm, low)]
    build('Supply Depot', 7, 12, vs, 0, SHOP_INST, ROOT / 'music/shop.json')


JINGLE_INST = {
    'lead': {'wave': 'pulse', 'attack': 0, 'decay': 10, 'sustain': 10, 'release': 9, 'pulse': 1400,
             'vibrato': {'delay': 8, 'speed': 2, 'depth': 3}},
    'brass': {'wave': 'saw', 'attack': 1, 'decay': 9, 'sustain': 10, 'release': 9,
              'vibrato': {'delay': 10, 'speed': 2, 'depth': 2}},
    'arp_min': LEVEL_INST['arp_min'] | {'release': 9},
    'arp_maj': LEVEL_INST['arp_maj'] | {'release': 9},
    'bass': {'wave': 'pulse', 'attack': 0, 'decay': 10, 'sustain': 10, 'release': 9, 'pulse': 2048},
}


def game_over():
    lead, harm, low = Voice(), Voice(), Voice()
    lead.melody([('A5', 4), ('G5', 4), ('F5', 4), ('E5', 4), ('D5', 14), ('-', 2)], 'lead')
    harm.note('Bb3', 8, 'arp_maj'); harm.note('A3', 8, 'arp_maj'); harm.note('D3', 14, 'arp_min'); harm.off(2)
    low.note('Bb1', 8, 'bass'); low.note('A1', 8, 'bass'); low.note('D1', 14, 'bass'); low.off(2)
    build('Game Over', 9, 15, [lead, harm, low], None, JINGLE_INST, ROOT / 'music/game_over.json')


def level_clear():
    lead, harm, low = Voice(), Voice(), Voice()
    lead.melody([('A4', 2), ('D5', 2), ('F#5', 2), ('A5', 2), ('F#5', 2), ('A5', 2), ('D6', 4),
                 ('E6', 4), ('D6', 2), ('C#6', 2), ('D6', 8),
                 ('A6', 14), ('-', 2)], 'brass')
    harm.note('D4', 16, 'arp_maj'); harm.note('A3', 16, 'arp_maj'); harm.note('D4', 14, 'arp_maj'); harm.off(2)
    for n in ('D2', 'A1', 'D2', 'A1'):
        low.note(n, 4, 'bass')
    low.note('A1', 8, 'bass'); low.note('E2', 8, 'bass'); low.note('D2', 14, 'bass'); low.off(2)
    build('Level Clear', 6, 15, [lead, harm, low], None, JINGLE_INST, ROOT / 'music/level_clear.json')


if __name__ == '__main__':
    (ROOT / 'music').mkdir(exist_ok=True)
    level1(); shop(); game_over(); level_clear()
    print('music/level1.json, shop.json, game_over.json, level_clear.json written')
