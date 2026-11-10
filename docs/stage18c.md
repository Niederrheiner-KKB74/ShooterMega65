# Stage 18c – fixes: tanks in the forest, sea in an island, sound effects after Game Over

Branch `stage18`, release files in `releases/stage18c/`. Includes Stages 18 and 18b.

## What is fixed
- **Level 1:** tanks no longer drive over the tree tops. They turn in front of the forest as in front of water, and
  every tank starts in a small clearing (the forests are a little smaller there).
- **Level 3:** the animated sea in the reef ring of an island (just below the island with the turbines nearby) is
  now shallow reef water like the rest of the ring.
- **Sound:** after Game Over or after the last level, the sound effects were silent in the next game. Cause: saving
  the highscore switches all sound chips off, including the volume of the effects chips; the music sets its
  volume again with every piece, the effects did not. Now the effects volume is restored after the disk access.

## Verification so far
| Check | Result |
|---|---|
| Assembly; all levels built (L1 314 rows, tanks blocked from tile 110 on; the others 0) | ✔ |
| XEMU level 1: tanks on the meadow and in the clearings, none on the trees (screenshots) | ✔ |
| Level 3 island: map rendered offline | ✔ |
| Sound effects after Game Over | not testable in XEMU (audio); hardware test |
| Real MEGA65 | open |

## Hardware test checklist
1. Level 1: tanks only in open ground, also when they change direction near a forest.
2. Level 3: the island with the turbines below it has no animated rectangle any more.
3. Game Over -> new game: sound effects (shots, explosions, collecting) are heard; music too.
4. All four levels completed -> new game: sound effects are heard.
5. Stage 18b checklist, if not done yet.
