# Operation Kuestenwald – test candidate

Build from this branch:

```sh
python tools/build.py --level levels/coastal_base.json --out build/coastal-game --kickass /path/to/KickAss65CE02-5.25.jar
```

The D81 contains SHOOTER plus the new L1GFX/L1DAT. Existing Stage-3 releases are
unchanged. Program: 29537 bytes, end exclusive `$9360`. Level: 375 rows,
240 seconds nominal scrolling / approximately 232 seconds until the end event
because the initial viewport already shows map rows.

Native coastline/forest/roads/bridge/base artwork and the medieval shield/gold
coins are included. Sources, parameters and data checks are in this branch;
see [the design and validation notes](../../docs/COASTAL_BASE_LEVEL.md).

Assembled with the pinned KickAss65CE02 5.25; all D81 files read back and compared.
Not newly emulator- or hardware-tested. Mount D81, `LOAD "SHOOTER",8`, `RUN`.
Joystick port 2, X or RUN/STOP exits. Check SHA256SUMS.txt before transferring.
