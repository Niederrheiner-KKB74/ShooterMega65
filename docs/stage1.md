# Stage 1 – Engine prototype

Branch `stage1-engine-prototype`. Release files are in `releases/stage1/`.

## What it does
- It sets up H320/V200 with 16-colour NCM tiles, a double-buffered RRB screen and a 40.5 MHz CPU.
- A placeholder landscape (meadows, forests, fields and a river with sandy banks; 512 map rows, looping)
  scrolls down at 0.5 px/frame with fine scrolling.
- The player plane is made of two 16-colour hardware sprites (32×24). Joystick **port 2** moves it in 8 directions, and fire
  gives continuous double shots.
- Waves of 6 planes snake down the screen and tanks drive on the ground; both fire at the player.
  Enemies, tanks, all shots and explosions are RRB pixies (up to 48 objects).
- Player shots destroy planes and tanks, which then explode. The player cannot be hit yet, and there is no HUD.
- The border turns red while the CPU builds the next frame, which shows the raster time used (debug).

All graphics are generated placeholders (`tools/make_assets.py`).

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
The output is `build/SHOOTER.PRG` and `build/SHOOTER65.D81`. The script checks the jar's SHA-256
(`5d854428…`), assembles the program, writes the D81 and reads the file back for verification.

## Start
- **D81**: mount it, then `LOAD "SHOOTER",8` and `RUN` (or `DLOAD "SHOOTER"` / `RUN`).
- **XEMU**: `xmega65 -prg SHOOTER.PRG`, or the D81 with `-8 SHOOTER65.D81 -autoload`.

The program does not return to BASIC. Use reset to leave.

## Verification so far
| Check | Result |
|---|---|
| Assembly (KickAss65CE02 5.25), PRG < `$C000`, D81 read-back | ✔ |
| XEMU (git master 2026-01, ROM 920395), headless screenshots | ✔ The image builds correctly, scrolling is 0.5 px/frame, the loop is locked to one frame (50 frames ↔ +50 frame counter), joystick movement and firing work, hits register (score counter), RRB overflow 0 |
| **Real MEGA65** | **open – please test** |

XEMU is not authoritative for RRB/GOTOX scaling and timing (Vyper rule 19). The points below need
a hardware test before Stage 1 can be declared stable.

## Hardware test checklist
1. The picture is stable, with no flicker and no black lines in pixies. This checks RRB double buffering with 85-token rows.
2. Scrolling is smooth. There is no jump every 8 pixels and no garbage row at the top or bottom edge.
   This checks TEXTYPOS fine scrolling with row 0 above the top border.
3. The left edge is clean: tiles start exactly at the border, and planes entering from the left are
   partially visible (no cropping errors). The right edge is clean too.
4. Pixie positions match the hardware: shots leave the plane's guns, and explosions appear where the target
   was. This checks GOTOX `x+16` in H320 / CHRXSCL 120.
5. The player sprite is 32×24, with correct colours and a transparent background, and sits in the right
   position. Moving it to all four edges must not leave the playfield. This checks 16-colour sprites,
   16-bit pointers and the extended height.
6. Raster time: the red border band should stay small. Note how high it reaches.
7. Joystick port 2: all 8 directions and fire work.

Please report what you see, ideally with a photo of anything unexpected, before Stage 1 is
marked `stage1-stable`.
