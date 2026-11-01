"""Validate new detailed skin and preserve boss integration contract."""
import json
from pathlib import Path
from check_screen_boss_art import boss

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'assets/art/boss-level1'

def main():
    boss()  # independent alpha/palette/binary/placement checks shared with original delivery
    current=json.loads((BASE/'source/design.json').read_text())
    previous=json.loads((BASE/'source/previous-design.json').read_text())
    for field in ('body_size','turrets','rotors','core','mechanic'):
        assert current[field]==previous[field],('integration contract changed',field)
    changed=[i for i,(a,b) in enumerate(zip(current['palette'],previous['palette'])) if a!=b]
    assert changed==[11] and current['palette'][11]==[189,17,10]
    before=json.loads((BASE/'source/previous-layout.json').read_text())
    frames=json.loads((BASE/'generated/indexed-source.json').read_text())
    layout=[{k:r[k] for k in ('id','width','height','indices_offset','ncm_offset','fcm_offset','rrb_base')} for r in frames]
    assert layout==before['frames'],'frame IDs, offsets or local glyph bases changed'
    assert (BASE/'generated/boss.rrb.bin').stat().st_size==before['rrb_bytes']==8768
    assert (BASE/'generated/boss.rrb.bin').stat().st_size+(BASE/'generated/palette.rgb').stat().st_size==8816<9*1024
    print('PASS detail revision: 96x64, four separate turrets, unchanged IDs/positions/mechanic/frame layout, same 8768-byte glyph pack; one documented red palette-slot change.')

if __name__=='__main__':main()
