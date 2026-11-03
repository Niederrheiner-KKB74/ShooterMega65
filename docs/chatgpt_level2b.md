# Auftrag an ChatGPT: Level 2, Ergänzung (Landkreuzer quer, mehr Farbe und Grün)

Ergänzung zu PR #17 und #18. **Basis-Branch ist `stage9`.** Bitte den Pull Request gegen `stage9` stellen und nur
die unten genannten Dateien ändern. Format und Regeln wie in `docs/chatgpt_level2.md`.

Vor dem Pull Request bitte prüfen und die Ausgabe in die PR-Beschreibung kopieren:

```sh
python3 tools/check_level2_art.py
```

## 1. Teil A: Landkreuzer in Querfahrt (muss)

Der Landkreuzer ist ein Kettenfahrzeug und darf nur in Kettenrichtung fahren. Bisher gibt es ihn nur mit
senkrechten Ketten (Fahrt nach oben/unten). Für die Fahrt nach links und rechts braucht das Spiel eine zweite
Ansicht, **um 90° gedreht, mit waagerechten Ketten**. Beim Richtungswechsel hält der Boss an und wechselt die
Ansicht (er dreht sich auf der Stelle).

Neue Frames in `assets/art/boss-level2/generated/indexed-source.json` (gleiches Format, zwei Hex-Ziffern pro Pixel):

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body_side` | **64×96** | der Rumpf um 90° gedreht: Ketten oben und unten, Front nach links |
| `core_exposed_side` | 32×32 | der offene Motorraum in dieser Lage |
| `rotor_side_0`, `rotor_side_1`, `rotor_side_2` | je bis 32×32 | die drei Kettenphasen, waagerecht laufend |

- **Bitte neu schattieren statt nur drehen**: Das Licht kommt weiter von oben links. Ein einfach gedrehtes Bild
  hätte die Schatten auf der falschen Seite.
- Die vier Türme bleiben dieselben Frames (sie drehen sich ohnehin zum Spieler). Ihre Lage auf dem gedrehten
  Rumpf kommt in `placement.json` unter einem neuen Schlüssel `"side"`:

```json
"side": {
  "body": "body_side", "body_size": [64, 96],
  "turrets": [{"id": "turret_nw", "offset": [x, y]}, {"id": "turret_ne", "offset": [x, y]},
              {"id": "turret_sw", "offset": [x, y]}, {"id": "turret_se", "offset": [x, y]}],
  "core": {"offset": [x, y], "exposed_overlay": "core_exposed_side"},
  "rotors": [{"offset": [x, y], "phase_offset": 0}, … bis zu 4 …],
  "rotor_frames": ["rotor_side_0", "rotor_side_1", "rotor_side_2"]
}
```

- Gleiche Palette wie der bisherige Landkreuzer (`palette.rgb` bleibt unverändert).
- **Speicher**: Für den Boss stehen jetzt **324 Glyphen** zur Verfügung (bisher 162), für beide Ansichten
  zusammen. Formel wie bisher: Breite/16 × (Höhe/8 + 1) je Frame, plus 1; Südost-Ansichten zählen doppelt.
  Der Rumpf 64×96 kostet 4 × 13 = 52 Glyphen. Das Prüfskript rechnet nach.

## 2. Teil B: mehr Farbe und Grün in Wüste, Canyon und Oase (muss)

Level 2 wirkt farblich eintönig (fast nur Sand- und Brauntöne). Bitte:

- **Ufer-Vegetation**: Schilf, Büsche, Grasflecken und größere Palmengruppen an Fluss und Oase, kräftigeres Grün.
  Claude setzt zusätzlich die vorhandenen Palmen-Tiles (`palm0`–`palm3`) automatisch auf Sand neben dem Wasser
  (`tools/decorate_level2.py`). Neue Vegetations-Tiles daher bitte so gestalten, dass sie neben diesen Palmen
  und neben Ufer-Tiles passen.
- **Felsen und Sand mit mehr Abwechslung**: z. B. rötliche und dunkle Felsbänder, hellere Salzflächen,
  dunklere Schattenseiten der Canyonwände.
- **Palette `nature`**: Die Einträge 1, 9 und 10 werden von keinem Tile benutzt und dürfen neue Farben bekommen.
  Die übrigen Farben dürfen leicht angepasst werden, wenn alle Tiles weiterhin gut aussehen. Mehr Grün bitte.
  `fixed_targets` bleibt exakt wie bisher.
- **Platz für neue Tiles**: Das Tileset darf höchstens 128 Tiles haben (jetzt 126). Diese Tiles kommen in der
  Karte gar nicht vor und dürfen ersetzt werden (ids behalten oder neu durchnummerieren, dann auch die Karte und
  `ground-targets.json` anpassen): `cliff6`, `bank6`, `cliff9`, `bank9`, `road1`, `road3`, `road4`, `road6`,
  `road7`, `road9`, `road11`, `road12`, `road13`, `road14`, `pipe1`, `pipe2`, `pipe3`, `pipe4`, `pipe6`,
  `pipe8`, `pipe9`, `pipe11`, `pipe12`, `pipe14`, `pipe15`, `bridge_end`, `gravel`.
- **Karte `levels/level2.json`**: die neuen Tiles einsetzen. Wichtig: **höchstens 240 verschiedene Zeilen**,
  damit Platz für die automatisch gesetzten Palmen bleibt. Die Karte auf `stage9` enthält diese Palmen schon
  (256 Zeilen); sie dürfen entfernt werden, Claude setzt sie danach wieder. Gleiche Zeilen kosten fast nichts:
  Vegetation lieber in wiederkehrenden Zeilenmustern bündeln. Gebäude, Brücken, Shops, Boss und Levelende bleiben,
  wo sie sind. Formationen und Bodengegner setzt Claude danach neu (bitte `paths`, `formations` und alle
  `formation`/`ground`-Ereignisse weglassen, nur `shop`, `boss`, `end` behalten).

## 3. Checkliste für den Pull Request

- [ ] Basis-Branch `stage9`; nur `assets/art/level2/`, `assets/art/boss-level2/` und `levels/level2.json` geändert
- [ ] `python3 tools/check_level2_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Boss in beiden Ansichten (zusammengesetzt, Kettenanimation), Tileset, Level-Abschnitte
- [ ] Kurze Beschreibung: welche Tiles ersetzt wurden, welche Paletteneinträge neu sind
