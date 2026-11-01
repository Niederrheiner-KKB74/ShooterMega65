#!/usr/bin/env python3
"""Minimal 1581 (D81) image writer with read-back verification.

Adapted from Vyper for MEGA65 (tools/build_stage3b1.py): track 40 holds header,
BAM and a chain of directory sectors (40/3, 40/4, …, 8 files each, max. 296 files), 254 payload bytes per sector.
"""
import struct

PRG, SEQ = 0x82, 0x81


def _pet(text, size):
    return text.upper().encode('ascii').ljust(size, b'\xa0')


def build_disk(entries, title='SHOOTER65', disk_id='S1'):
    """entries: list of (name, payload, kind). Returns the 819200-byte image."""
    ndir = max(1, (len(entries) + 7) // 8)
    if ndir > 37:
        raise ValueError('too many files')
    image = bytearray(80 * 40 * 256)
    used = {(40, s) for s in range(3 + ndir)}
    free = [(t, s) for t in range(1, 81) if t != 40 for s in range(40)]

    def put(t, s, data):
        off = ((t - 1) * 40 + s) * 256
        image[off:off + 256] = data

    dirs = [bytearray(256) for _ in range(ndir)]
    for k, d in enumerate(dirs):
        d[:2] = bytes((40, 4 + k)) if k + 1 < ndir else bytes((0, 255))
    for i, (name, payload, kind) in enumerate(entries):
        directory = dirs[i // 8]
        count = (len(payload) + 253) // 254
        chain, free = free[:count], free[count:]
        if len(chain) != count or not chain:
            raise ValueError('disk full or empty file')
        used.update(chain)
        for j, (t, s) in enumerate(chain):
            part = payload[j * 254:(j + 1) * 254]
            block = bytearray(256)
            block[:2] = bytes(chain[j + 1]) if j + 1 < count else bytes((0, len(part) + 1))
            block[2:2 + len(part)] = part
            put(t, s, block)
        off = 2 + (i % 8) * 32
        directory[off] = kind
        directory[off + 1:off + 3] = bytes(chain[0])
        directory[off + 3:off + 19] = _pet(name, 16)
        directory[off + 28:off + 30] = struct.pack('<H', count)
    for k, d in enumerate(dirs):
        put(40, 3 + k, d)
    header = bytearray(256)
    header[:4] = bytes((40, 3, 0x44, 0))
    header[4:20] = _pet(title, 16)
    header[20:29] = b'\xa0\xa0' + disk_id.encode('ascii')[:2].ljust(2, b' ') + b'\xa03D\xa0\xa0'
    put(40, 0, header)
    for index in range(2):
        bam = bytearray(256)
        link = (40, 2) if index == 0 else (0, 255)
        bam[:8] = bytes(link) + bytes((0x44, 0xbb)) + disk_id.encode('ascii')[:2].ljust(2, b' ') + bytes((0xc0, 0))
        for j in range(40):
            t = index * 40 + j + 1
            free_s = [s for s in range(40) if (t, s) not in used]
            o = 16 + j * 6
            bam[o] = len(free_s)
            for s in free_s:
                bam[o + 1 + s // 8] |= 1 << (s % 8)
        put(40, index + 1, bam)
    return bytes(image)


def read_file(image, name):
    """Follow the directory and sector chain; returns the payload (for verification)."""
    def get(t, s):
        off = ((t - 1) * 40 + s) * 256
        return image[off:off + 256]
    dt, ds = 40, 3
    entries = []
    while dt:
        d = get(dt, ds)
        entries += [d[2 + i * 32:2 + i * 32 + 32] for i in range(8)]
        dt, ds = d[0], d[1]
    for e in entries:
        off = 0
        d = e
        if d[off] and d[off + 3:off + 19] == _pet(name, 16):
            t, s = d[off + 1:off + 3]
            out, seen = bytearray(), set()
            while t:
                if (t, s) in seen:
                    raise ValueError('cyclic chain')
                seen.add((t, s))
                b = get(t, s)
                nt, ns = b[:2]
                out += b[2:256 if nt else ns + 1]
                t, s = nt, ns
            return bytes(out)
    raise KeyError(name)
