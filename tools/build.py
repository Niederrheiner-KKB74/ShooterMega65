#!/usr/bin/env python3
"""Build ShooterMega65: generate assets, assemble with KickAssembler, write PRG + D81.

Usage:
  python3 tools/build.py [--kickass PATH] [--out DIR]

The KickAssembler jar (KickAss65CE02-5.25.jar) is not part of the repository.
It is looked up via --kickass, the KICKASS_JAR environment variable or
tools/bin/KickAss65CE02-5.25.jar, and its SHA-256 is checked.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import d81            # noqa: E402
import make_assets    # noqa: E402
import import_art     # noqa: E402
import build_level    # noqa: E402
import make_shop      # noqa: E402
import build_music    # noqa: E402
import make_screens   # noqa: E402

LEVELS = [('L1', 'levels/coastal_base.json')]   # (file prefix on the disk, source)

KICKASS_SHA256 = '5d8544280dae2d018c79151d8c7b877eca1fb994096e54ca380b26d0cd79f847'
PRG_NAME = 'SHOOTER'


def find_kickass(arg):
    for cand in (arg, os.environ.get('KICKASS_JAR'), ROOT / 'tools/bin/KickAss65CE02-5.25.jar'):
        if cand and Path(cand).is_file():
            return Path(cand)
    sys.exit('KickAssembler not found: use --kickass or KICKASS_JAR (KickAss65CE02-5.25.jar)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--kickass')
    ap.add_argument('--out', default=str(ROOT / 'build'))
    ap.add_argument('--allow-other-kickass', action='store_true')
    ap.add_argument('--level', help='build this level JSON as L1 instead of the default test level')
    ap.add_argument('--test-credits', action='store_true', help='test build: start with 999 credits (shop tests)')
    ap.add_argument('--define', action='append', default=[], help='test build: extra KickAssembler symbol (e.g. BOSS_TEST)')
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    jar = find_kickass(a.kickass)
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    if digest != KICKASS_SHA256 and not a.allow_other_kickass:
        sys.exit(f'unexpected KickAssembler build {digest}; pass --allow-other-kickass to continue')

    import_art.main(ROOT / 'build/gen')        # artwork v2 (assets/art/spec-v2)
    print('\n'.join(make_shop.main(ROOT / 'build/gen')))     # shop overlay (Stage 3b)
    shop = (ROOT / 'build/gen/SHOP').read_bytes()
    try:
        print('\n'.join(build_music.main(ROOT / 'build/gen')))   # music + sound effects (Stage 5)
    except build_music.MusicError as e:
        sys.exit(f'music: {e}')
    music = (ROOT / 'build/gen/MUSIC').read_bytes()
    pixies = (ROOT / 'build/gen/PIXIES').read_bytes()
    print('\n'.join(make_screens.main(ROOT / 'build/gen')))  # title + game-over banner (Stage 7)
    title = (ROOT / 'build/gen/TITLE').read_bytes()
    gover = (ROOT / 'build/gen/GOVER').read_bytes()
    boss = (ROOT / 'build/gen/L1BOSS').read_bytes()
    level_files = []
    selected_levels = [('L1', a.level)] if a.level else LEVELS
    for name, src in selected_levels:
        try:
            gfx, dat, report = build_level.build(ROOT / src, out / 'levels', name)
        except build_level.LevelError as e:
            sys.exit(f'{src}: {e}')
        print('\n'.join(report))
        level_files += [(name + 'GFX', gfx, d81.SEQ), (name + 'DAT', dat, d81.SEQ),
                        (name + 'DEST', (out / 'levels' / f'{name}DEST').read_bytes(), d81.SEQ)]
        # Stage 7c: L1BOSS lives in attic RAM, LnDAT alone has the 16 KB level buffer (checked by build_level)
        if name == 'L1':
            level_files.append((name + 'BOSS', boss, d81.SEQ))
    pixies2 = (ROOT / 'build/gen/PIXIES2').read_bytes()  # heavy gun (Stage 8), loaded to $52800
    prg = out / f'{PRG_NAME}.PRG'
    out.mkdir(parents=True, exist_ok=True)
    # A failed assembly must not leave a previous build looking current.
    prg.unlink(missing_ok=True)
    (out / 'SHOOTER65.D81').unlink(missing_ok=True)
    defines = (['-define', 'TEST_CREDITS'] if a.test_credits else []) + [x for d in a.define for x in ('-define', d)]
    run = subprocess.run(['java', '-jar', str(jar), str(ROOT / 'src/main.asm'), '-o', str(prg),
                          '-symbolfile', '-odir', str(out), '-showmem'] + defines,
                         cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = run.stdout
    (out / 'assembly.txt').write_text(log)
    if run.returncode or 'Error' in log:
        print(log)
        sys.exit('assembly failed')
    for line in log.splitlines():
        if 'code ends' in line or line.startswith('  $') or 'Memory' in line:
            print(line)
    data = prg.read_bytes()
    if data[:2] != b'\x01\x20':
        sys.exit('PRG must load at $2001')
    # music test program for the same disk: keys 1-4 play the pieces, T = 440 Hz tuning tone
    mt = out / 'MUSICTEST.PRG'
    run2 = subprocess.run(['java', '-jar', str(jar), str(ROOT / 'src/main.asm'), '-o', str(mt), '-odir', str(out),
                           '-define', 'MUSIC_TEST'] + defines, cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if run2.returncode or 'Error' in run2.stdout:
        print(run2.stdout)
        sys.exit('assembly of MUSICTEST failed')
    files = [(PRG_NAME, data, d81.PRG), ('MUSICTEST', mt.read_bytes(), d81.PRG), ('SHOP', shop, d81.SEQ), ('MUSIC', music, d81.SEQ), ('PIXIES', pixies, d81.SEQ), ('PIXIES2', pixies2, d81.SEQ), ('TITLE', title, d81.SEQ), ('GOVER', gover, d81.SEQ)] + level_files
    image = d81.build_disk(files)
    for fname, payload, _ in files:
        if d81.read_file(image, fname) != payload:
            sys.exit(f'D81 verification failed: {fname}')
    disk = out / 'SHOOTER65.D81'
    disk.write_bytes(image)
    print(f'{prg.name}: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()[:16]}')
    print(f'{disk.name}: verified (' + ', '.join(f'{n} {len(p)}' for n, p, _ in files) + ' bytes)')


if __name__ == '__main__':
    main()


