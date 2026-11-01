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
    a = ap.parse_args()
    out = Path(a.out).resolve()
    jar = find_kickass(a.kickass)
    digest = hashlib.sha256(jar.read_bytes()).hexdigest()
    if digest != KICKASS_SHA256 and not a.allow_other_kickass:
        sys.exit(f'unexpected KickAssembler build {digest}; pass --allow-other-kickass to continue')

    import_art.main(ROOT / 'build/gen')        # artwork v2 (assets/art/spec-v2)
    prg = out / f'{PRG_NAME}.PRG'
    out.mkdir(parents=True, exist_ok=True)
    # A failed assembly must not leave a previous build looking current.
    prg.unlink(missing_ok=True)
    (out / 'SHOOTER65.D81').unlink(missing_ok=True)
    run = subprocess.run(['java', '-jar', str(jar), str(ROOT / 'src/main.asm'), '-o', str(prg),
                          '-symbolfile', '-odir', str(out), '-showmem'],
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
    image = d81.build_disk([(PRG_NAME, data, d81.PRG)])
    if d81.read_file(image, PRG_NAME) != data:
        sys.exit('D81 verification failed')
    disk = out / 'SHOOTER65.D81'
    disk.write_bytes(image)
    print(f'{prg.name}: {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()[:16]}')
    print(f'{disk.name}: verified ({PRG_NAME} {len(data)} bytes)')


if __name__ == '__main__':
    main()

