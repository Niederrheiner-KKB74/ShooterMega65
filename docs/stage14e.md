# Stage 14e – test cheat F, stronger drone banking

Branch `stage14`, release files in `releases/stage14e/`. Includes Stages 14c and 14d.

## What is new
- **Test cheat F** (owner's request, like C for credits): Shot IV, the missile, 9 invulnerability shields and
  full shield energy at once.
- **Heavy drone**: banking much stronger: on the lowered side the rotors are small, dark and pulled in, on the raised
  side larger and further out; the hull moves 1–2 px to the side. Rotors still turn calmly, the eye does not blink.

## Verification so far
| Check | Result |
|---|---|
| Assembly; D81 read back | ✔ |
| XEMU: key F → shot level 4, missile, 9 shields, shield energy 48 (full) | ✔ |
| Real MEGA65 | open |

## Hardware test checklist
1. In the game press F: Shot IV and missile active, 9 shields in the HUD, shield bar full.
2. Level 4: the drones tilt clearly in curves.
3. The open points of Stages 14c/14d (restart after dying at the boss, walker).
