# Auftrag an ChatGPT: Landkreuzer, Zwischenansicht für die Drehung

Ergänzung zu PR #19. **Basis-Branch ist `stage9`.** Bitte den Pull Request gegen `stage9` stellen und nur
`assets/art/boss-level2/` ändern. Format und Regeln wie in `docs/chatgpt_level2.md` und `docs/chatgpt_level2b.md`.

## Worum es geht

Der Landkreuzer (Boss von Level 2) fährt nur in Kettenrichtung. Zwischen Fahrt nach unten/oben (Ansicht `body`,
Ketten senkrecht, Front unten) und Fahrt zur Seite (Ansicht `body_side`, Ketten waagerecht, Front links) hält er
an und dreht sich um 90°. Bisher springt das Bild dabei von einer Ansicht zur anderen, das wirkt abrupt.

Neu: Das Spiel zeigt während der Drehung eine **Zwischenansicht um 45° gedreht** (Front nach **unten links**)
und lässt dabei **Staub** an den Ketten aufwirbeln. Die Drehung läuft dann so: senkrecht → diagonal → waagerecht
und zurück: waagerecht → diagonal → senkrecht.

## Neue Frames

In `assets/art/boss-level2/generated/indexed-source.json` (gleiches Format, zwei Hex-Ziffern pro Pixel):

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body_diag` | höchstens **96×96** | der Rumpf um 45° gedreht, Front nach unten links, Ketten diagonal. Wenn nötig etwas gestaucht, damit er in 96×96 passt. Licht weiter von oben links, also neu schattieren, nicht nur drehen |
| `core_exposed_diag` | 32×32 | der offene Motorraum in dieser Lage (für Drehungen in der Endphase) |
| `dust_0`, `dust_1` | je 16×16 | aufgewirbelter Sand, zwei Phasen (hell, locker, an den Rändern durchsichtig) |

- Dieselbe Palette wie bisher (`palette.rgb` bleibt unverändert). Für den Staub die hellen Sand- und Grautöne
  der Palette verwenden.
- In `placement.json` ein neuer Schlüssel `"diag"` wie `"side"`: `body_size`, die vier `turrets` mit `offset`
  (linke obere Ecke auf dem diagonalen Rumpf), `core` mit `offset`, dazu `"dust": [[x, y], …]` mit 2 bis 4
  Positionen (linke obere Ecke eines 16×16-Staubbilds) an den Kettenenden, wo der Staub entsteht. `rotors` darf
  leer bleiben, die Ketten stehen während der Drehung still.

## Speicher

Für den Boss stehen **324 Glyphen** zur Verfügung, die beiden bisherigen Ansichten brauchen 229 (gezählt
mit den Rotoren des Quadrocopters, die das Spiel für beide Bosse gleich groß anlegt). Für die neuen Frames
bleiben **95 Glyphen**: `body_diag` mit 96×96 kostet 6 × 13 = 78, `core_exposed_diag` 10, zwei Staubbilder je 3.
Das sind zusammen 94. Das Prüfskript rechnet nach.

## Checkliste für den Pull Request

- [ ] Basis-Branch `stage9`; nur `assets/art/boss-level2/` geändert
- [ ] `python3 tools/check_level2_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschau: die drei Ansichten nebeneinander (senkrecht, diagonal, waagerecht), dazu der Staub
