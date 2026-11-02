#!/usr/bin/env python3
"""Music and sound effects: JSON (docs/music_json.md) -> file MUSIC for the D81 + build/gen/music_const.inc.

All pieces of MUSIC_PIECES and the effects of music/sfx.json are packed into one file. The game loads it
to MUSIC_ADDR (bank 0); every address inside the data is the low 16 bits of an address in that bank.

File:      'SM', piece count, sfx count, piece header addresses (2 bytes each), sfx record addresses (2 each)
Piece:     0 tempo, 1 volume, 2 cutoff low 3 bits, 3 cutoff high 8 bits, 4 resonance << 4, 5 filter mode bits,
           6 loop index ($FF = ends), 7-9 order lengths, 10-15 order list addresses, 16-17 pattern table,
           18-19 instrument table
Instrument (16 bytes): AD, SR, waveform, pulse lo, pulse hi, sweep lo, sweep hi (signed), vibrato delay,
           vibrato speed, vibrato depth, arpeggio address (2), arpeggio length | $80 = filter, wave table
           address (2), wave table length
Wave table entry (2 bytes): waveform bits | 1 = absolute note, note (absolute 0-95 or signed offset)
Pattern:   $00-$5F note, $60-$7F instrument, $80 legato (next note), $81 off, $82 end, $C0-$FF wait 1-64 rows
SFX (12 bytes): AD, SR, pulse lo, pulse hi, base note, voice, priority, gate frames, wave table address (2),
           wave table length, 0
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUSIC_PIECES = ['level1', 'shop', 'game_over', 'level_clear', 'boss', 'title']       # order = MUS_* constants
MUSIC_ADDR = 0x0AC00          # bank 0 behind the program (Stage 8: $AC00-$BFFF, 5 KB; Stage 7: $A000; before $5E000)
MUSIC_MAX = 0xC000 - MUSIC_ADDR
SID_CLOCK = 1_000_000            # MEGA65 SID clock as emulated by XEMU (check the tuning on hardware: A-4 = 440 Hz)
WAVES = {'triangle': 0x10, 'saw': 0x20, 'pulse': 0x40, 'noise': 0x80}
FILTER_MODES = {'lowpass': 0x10, 'bandpass': 0x20, 'highpass': 0x40}
NOTE_RE = re.compile(r'^([A-G])([-#])([0-7])$')
NOTE_BASE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
INST_KEYS = {'wave', 'attack', 'decay', 'sustain', 'release', 'pulse', 'pulse_sweep', 'vibrato', 'arpeggio',
             'wave_table', 'filter'}
SFX_KEYS = {'note', 'attack', 'decay', 'sustain', 'release', 'pulse', 'wave_table', 'voice', 'priority', 'frames'}


class MusicError(Exception):
    pass


def note_number(text, where):
    m = NOTE_RE.match(text)
    if not m or (m.group(1) in 'EB' and m.group(2) == '#'):
        raise MusicError(f'{where}: "{text}" is not a note (C-4, C#4 … B-7)')
    return int(m.group(3)) * 12 + NOTE_BASE[m.group(1)] + (m.group(2) == '#')


def freq_table():
    out = []
    for n in range(96):
        f = 440.0 * 2 ** ((n - 57) / 12)                    # n 57 = A-4
        out.append(min(0xFFFF, round(f * 16777216 / SID_CLOCK)))
    return out


def rng(v, lo, hi, where):
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise MusicError(f'{where}: {v!r} must be a whole number {lo}…{hi}')
    return v


def wave_table(wt, where):
    out = bytearray()
    if not isinstance(wt, list) or not 1 <= len(wt) <= 64:
        raise MusicError(f'{where}: wave_table needs 1…64 entries')
    for k, e in enumerate(wt):
        w = f'{where} wave_table[{k}]'
        if not (isinstance(e, list) and len(e) == 2 and e[0] in WAVES):
            raise MusicError(f'{w}: expected ["pulse"|"saw"|"triangle"|"noise", tone]')
        if isinstance(e[1], str):
            out += bytes((WAVES[e[0]] | 1, note_number(e[1], w)))
        else:
            out += bytes((WAVES[e[0]], rng(e[1], -48, 48, w) & 0xFF))
    return out


def adsr(d, where):
    return (rng(d.get('attack', 0), 0, 15, where + ' attack') << 4 | rng(d.get('decay', 0), 0, 15, where + ' decay'),
            rng(d.get('sustain', 0), 0, 15, where + ' sustain') << 4 | rng(d.get('release', 0), 0, 15, where + ' release'))


class Blob:
    def __init__(self, base):
        self.data, self.base = bytearray(), base

    def addr(self):
        return (self.base + len(self.data)) & 0xFFFF

    def add(self, b):
        a = self.addr()
        self.data += b
        return a


def build_piece(path, blob, report):
    name = path.stem
    try:
        m = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise MusicError(f'{path.name}: JSON error {e}')
    allowed = {'format', 'name', 'tempo', 'volume', 'filter', 'instruments', 'patterns', 'order', 'loop'}
    if set(m) - allowed:
        raise MusicError(f'{name}: unknown fields {sorted(set(m) - allowed)}')
    if m.get('format') != 'shootermega65-music-1':
        raise MusicError(f'{name}: format must be "shootermega65-music-1"')
    tempo = rng(m.get('tempo', 6), 3, 31, f'{name} tempo')
    volume = rng(m.get('volume', 15), 0, 15, f'{name} volume')
    flt = m.get('filter') or {}
    if set(flt) - {'mode', 'cutoff', 'resonance'}:
        raise MusicError(f'{name} filter: unknown fields')
    cutoff = rng(flt.get('cutoff', 2047), 0, 2047, f'{name} filter cutoff')
    reso = rng(flt.get('resonance', 0), 0, 15, f'{name} filter resonance')
    mode = FILTER_MODES[flt['mode']] if flt else 0

    insts = m.get('instruments', {})
    if not 1 <= len(insts) <= 32:
        raise MusicError(f'{name}: 1…32 instruments needed')
    inst_id = {k: i for i, k in enumerate(insts)}
    recs = []
    for k, d in insts.items():
        w = f'{name} instrument {k}'
        if set(d) - INST_KEYS:
            raise MusicError(f'{w}: unknown fields {sorted(set(d) - INST_KEYS)}')
        ad, sr = adsr(d, w)
        wave = WAVES.get(d.get('wave', 'pulse'))
        if wave is None:
            raise MusicError(f'{w}: wave must be one of {list(WAVES)}')
        pulse = rng(d.get('pulse', 2048), 0, 4095, w + ' pulse')
        sweep = rng(d.get('pulse_sweep', 0), -255, 255, w + ' pulse_sweep') & 0xFFFF
        vib = d.get('vibrato') or {}
        vd = rng(vib.get('delay', 0), 0, 255, w + ' vibrato delay')
        vs = rng(vib.get('speed', 1), 1, 15, w + ' vibrato speed') if vib else 0
        vdep = rng(vib.get('depth', 0), 0, 15, w + ' vibrato depth') if vib else 0
        arp = d.get('arpeggio') or []
        if len(arp) > 16:
            raise MusicError(f'{w}: arpeggio has more than 16 steps')
        arp_a = blob.add(bytes(rng(x, -48, 48, w + ' arpeggio') & 0xFF for x in arp)) if arp else 0
        wt = d.get('wave_table')
        wt_a, wt_n = (blob.add(wave_table(wt, w)), len(wt)) if wt else (0, 0)
        filt = 0x80 if d.get('filter') else 0
        recs.append(bytes((ad, sr, wave, pulse & 255, pulse >> 8, sweep & 255, sweep >> 8, vd, vs, vdep,
                           arp_a & 255, arp_a >> 8, len(arp) | filt, wt_a & 255, wt_a >> 8, wt_n)))

    pats = m.get('patterns', {})
    if not 1 <= len(pats) <= 128:
        raise MusicError(f'{name}: 1…128 patterns needed')
    pat_id, pat_rows, pat_addr = {}, {}, []
    for k, rows in pats.items():
        w = f'{name} pattern {k}'
        if not isinstance(rows, list) or not 1 <= len(rows) <= 64:
            raise MusicError(f'{w}: 1…64 rows needed')
        out, wait = bytearray(), 0

        def flush():
            nonlocal wait
            while wait:
                n = min(wait, 64)
                out.append(0xC0 + n - 1)
                wait -= n
        for r, row in enumerate(rows):
            wr = f'{w} row {r}'
            if not isinstance(row, str):
                raise MusicError(f'{wr}: rows are texts')
            t = row.split()
            if t == ['...'] or t == []:
                wait += 1
                continue
            flush()
            if t == ['off']:
                out.append(0x81)
                continue
            legato = t[-1] == '>'
            if legato:
                t = t[:-1]
            if len(t) not in (1, 2):
                raise MusicError(f'{wr}: "{row}" – expected "C-4 instrument", "C-4", "...", "off"')
            if len(t) == 2:
                if t[1] not in inst_id:
                    raise MusicError(f'{wr}: unknown instrument "{t[1]}"')
                out.append(0x60 + inst_id[t[1]])
            if legato:
                out.append(0x80)
            out.append(note_number(t[0], wr))
        flush()
        out.append(0x82)
        pat_id[k] = len(pat_addr)
        pat_rows[k] = len(rows)
        pat_addr.append(blob.add(bytes(out)))

    order = m.get('order', {})
    if sorted(order) != ['voice1', 'voice2', 'voice3']:
        raise MusicError(f'{name}: order needs exactly voice1, voice2, voice3')
    loop = m.get('loop', 0)
    totals, loop_rows, ord_a = [], [], []
    for v in ('voice1', 'voice2', 'voice3'):
        lst = order[v]
        if not isinstance(lst, list) or not 1 <= len(lst) <= 128:
            raise MusicError(f'{name} order {v}: 1…128 entries needed')
        for p in lst:
            if p not in pat_id:
                raise MusicError(f'{name} order {v}: unknown pattern "{p}"')
        totals.append(sum(pat_rows[p] for p in lst))
        if loop is not None:
            if not isinstance(loop, int) or not 0 <= loop < len(lst):
                raise MusicError(f'{name}: loop {loop} outside the order list of {v}')
            loop_rows.append(sum(pat_rows[p] for p in lst[:loop]))
        ord_a.append(blob.add(bytes(pat_id[p] for p in lst)))
    if len(set(totals)) != 1:
        raise MusicError(f'{name}: the voices have different lengths {totals} rows')
    if loop is not None and len(set(loop_rows)) != 1:
        raise MusicError(f'{name}: loop {loop} starts at different rows {loop_rows} in the three voices')
    pt_a = blob.add(b''.join(bytes((a & 255, a >> 8)) for a in pat_addr))
    in_a = blob.add(b''.join(recs))
    hdr = bytes((tempo, volume, cutoff & 7, cutoff >> 3, reso << 4, mode, 0xFF if loop is None else loop,
                 len(order['voice1']), len(order['voice2']), len(order['voice3']))) + \
        b''.join(bytes((a & 255, a >> 8)) for a in ord_a + [pt_a, in_a])
    seconds = totals[0] * tempo / 50
    report.append(f'music {name}: {totals[0]} rows, {seconds:.1f} s, {len(insts)} instruments, {len(pats)} patterns'
                  + ('' if loop is None else ', loops'))
    return blob.add(hdr)


def build_sfx(path, blob):
    d = json.loads(path.read_text())
    if d.get('format') != 'shootermega65-sfx-1':
        raise MusicError('sfx.json: format must be "shootermega65-sfx-1"')
    names, addrs = [], []
    for k, s in d['sfx'].items():
        w = f'sfx {k}'
        if set(s) - SFX_KEYS:
            raise MusicError(f'{w}: unknown fields {sorted(set(s) - SFX_KEYS)}')
        ad, sr = adsr(s, w)
        wt = wave_table(s['wave_table'], w)
        wt_a = blob.add(wt)
        pulse = rng(s.get('pulse', 2048), 0, 4095, w + ' pulse')
        frames = rng(s.get('frames', len(s['wave_table'])), 1, 255, w + ' frames')
        rec = bytes((ad, sr, pulse & 255, pulse >> 8, note_number(s.get('note', 'C-4'), w),
                     rng(s.get('voice', 0), 0, 2, w + ' voice'), rng(s.get('priority', 1), 1, 255, w + ' priority'),
                     frames, wt_a & 255, wt_a >> 8, len(s['wave_table']), 0))
        names.append(k)
        addrs.append(blob.add(rec))
    return names, addrs


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = []
    pieces = [ROOT / 'music' / f'{p}.json' for p in MUSIC_PIECES]
    nsfx = len(json.loads((ROOT / 'music/sfx.json').read_text())['sfx'])
    hdr_len = 4 + 2 * len(pieces) + 2 * nsfx
    blob = Blob(MUSIC_ADDR + hdr_len)
    piece_a = [build_piece(p, blob, report) for p in pieces]
    sfx_names, sfx_a = build_sfx(ROOT / 'music/sfx.json', blob)
    data = b'SM' + bytes((len(pieces), len(sfx_names))) + \
        b''.join(bytes((a & 255, a >> 8)) for a in piece_a + sfx_a) + blob.data
    if len(data) > MUSIC_MAX:
        raise MusicError(f'MUSIC is {len(data)} bytes, maximum {MUSIC_MAX}')
    (out / 'MUSIC').write_bytes(data)
    ft = freq_table()
    semis = [ft[n + 1] - ft[n] if n < 95 else ft[95] - ft[94] for n in range(96)]
    lines = ['// generated by tools/build_music.py - do not edit',
             f'.const MUSIC_ADDR=${MUSIC_ADDR:x}', f'.const MUSIC_BYTES={len(data)}',
             f'.const MUSIC_PIECES={len(pieces)}', f'.const SFX_COUNT={len(sfx_names)}']
    lines += [f'.const MUS_{p.upper()}={i}' for i, p in enumerate(MUSIC_PIECES)]
    lines += [f'.const SFX_{n.upper()}={i}' for i, n in enumerate(sfx_names)]
    (out / 'music_const.inc').write_text('\n'.join(lines) + '\n')
    tl = ['// generated by tools/build_music.py - SID frequencies (clock %d Hz), C-0 … B-7' % SID_CLOCK,
          'freq_lo: .byte ' + ','.join(str(f & 255) for f in ft),
          'freq_hi: .byte ' + ','.join(str(f >> 8) for f in ft),
          'semi_lo: .byte ' + ','.join(str(f & 255) for f in semis),
          'semi_hi: .byte ' + ','.join(str(f >> 8) for f in semis)]
    (out / 'music_tables.inc').write_text('\n'.join(tl) + '\n')
    report.append(f'MUSIC {len(data)} bytes of {MUSIC_MAX}, {len(sfx_names)} sound effects')
    return report


if __name__ == '__main__':
    try:
        print('\n'.join(main(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'build/gen')))
    except MusicError as e:
        sys.exit(f'error: {e}')
