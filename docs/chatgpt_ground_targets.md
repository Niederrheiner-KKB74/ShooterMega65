# Auftrag an ChatGPT: zerstörbare Gebäude und Bodengeschütze (Stage 8)

Spiel: **Shooter65**, vertikaler Shooter für den MEGA65 (Repository `Niederrheiner-KKB74/ShooterMega65`).
Level 1 „Operation Kuestenwald“ nutzt das Tileset `assets/art/coastal-base/generated/`.

Gesucht wird **nur Grafik**. Bitte nichts am Programm, an `levels/` oder an anderen Assets ändern. Den Einbau ins Spiel,
die Platzierung im Level und das Verhalten übernimmt Claude.

## 1. Was geliefert werden soll

| Teil | Priorität | Inhalt |
|---|---|---|
| A | muss | **Zerstörte Varianten** der Gebäude-Tiles (Trümmer) |
| B | muss | **Leichtes Bodengeschütz** 16×16 als bewegliches Objekt: 8 Richtungen, Mündungsfeuer, Wrack |
| C | kann | **Schweres Bodengeschütz** 32×32 (z. B. Doppel-Flak oder Raketenwerfer), gleiche Ansichten wie B |
| D | kann | Zerstörte Varianten der großen Hallen (`complex_steel_*`, `complex_brick_*`) |

Alles kommt in **einen neuen Ordner** `assets/art/ground-targets/`:

```
assets/art/ground-targets/
  source/          beliebige Arbeitsdateien (optional)
  generated/
    ground-targets.json     alle Pixeldaten und Paletten (verbindlich, siehe Abschnitt 7)
    destroyed-sheet.png     Vorschau: jede intakte Gruppe neben ihrer zerstörten Variante, 1:1
    destroyed-sheet-4x.png  dieselbe Vorschau 4-fach vergrößert (nearest neighbour)
    ground-gun.png          Vorschau Teil B: alle Frames nebeneinander, 1:1 und 4-fach
    heavy-gun.png           Vorschau Teil C (falls geliefert)
```

Vor dem Pull Request bitte das Prüfskript laufen lassen und die Ausgabe in die PR-Beschreibung kopieren:

```sh
python3 tools/check_ground_targets.py
```

Es meldet Fehler (muss behoben werden) und Hinweise (bitte prüfen). Ein Pull Request darf keine Fehler enthalten.

## 2. Allgemeine Regeln

- **Pixelgenau**: 1 Bildpixel = 1 Spielpixel. Keine Kantenglättung, keine Verläufe, kein Weichzeichnen.
- **Draufsicht** wie das bestehende Tileset, Licht von oben links. Der Spieler fliegt nach oben.
- **Stil**: an das vorhandene Tileset angepasst (`assets/art/coastal-base/generated/terrain-sheet.png`), also gleiche
  Farbtöne, gleiche Pixeldichte, gleiche Kontur.
- **Farben sind Palettenindizes**, keine freien RGB-Werte. Jedes Tile und jedes Objekt benutzt genau eine Palette mit
  16 Einträgen.
- In **Landschafts-Tiles** (Teil A, D) ist **Index 0 verboten**: Index 0 zeigt dort die Hintergrundfarbe (Schwarz).
- In **Objekten** (Teil B, C) ist **Index 0 durchsichtig**. Alles, was sichtbar sein soll, braucht Index 1–15.

### Paletten

Die Paletten stehen in `assets/art/coastal-base/generated/manifest.json` unter `palettes`.

| Palette | Benutzt von | Regel |
|---|---|---|
| `structures` | fast alle Gebäude | **voll belegt**. Nur die vorhandenen 16 Farben benutzen, nichts ändern |
| `fixed_targets` | Bunker, Panzer, Bodengeschütze | Einträge **1–11 unverändert lassen** (die Panzer benutzen sie). Die freien Einträge **12–15** dürfen neue Farben bekommen, z. B. Ruß, Glut, dunkles Feuer |

Eine zerstörte Variante darf die Palette ihres intakten Tiles benutzen **oder** `fixed_targets`. So können Trümmer
von `structures`-Gebäuden die neuen Ruß- und Glutfarben aus 12–15 verwenden.

## 3. Teil A: zerstörte Gebäude (muss)

Für jede der folgenden 2×2-Gruppen (32×32 Pixel, vier Tiles zu 16×16) eine zerstörte Variante gleicher Größe:

| Gruppe | Tile-IDs (intakt) | Palette intakt |
|---|---|---|
| `hangar` | 61 62 63 64 | structures |
| `depot` | 65 66 67 68 | structures |
| `checkpoint` | 79 80 81 82 | structures |
| `bunker` | 83 84 85 86 | fixed_targets |
| `radar` | 90 91 92 93 | structures |
| `fuel` | 94 95 96 97 | structures |
| `crates` | 98 99 100 101 | structures |

Die Tile-Namen sind `<gruppe>_<spalte>_<zeile>`, also `hangar_0_0` (oben links), `hangar_1_0` (oben rechts),
`hangar_0_1` (unten links), `hangar_1_1` (unten rechts). Die zerstörte Variante heißt `<gruppe>_destroyed_<spalte>_<zeile>`.

Gestaltung:
- Die Trümmer bleiben **innerhalb des Grundrisses** (32×32). Eingestürztes Dach, verkohlte Wände, Schutt, Brandflecken.
- Der **Rand passt nahtlos** zur Umgebung: Die äußeren 2 Pixel jeder Gruppe sollen dem intakten Original möglichst
  gleichen (gleicher Boden, gleiche Wiese oder gleicher Beton). Das Spiel tauscht nur die vier Tiles aus, die
  Nachbar-Tiles bleiben.
- Das zerstörte Gebäude muss **deutlich anders** aussehen als das intakte (dunkler, kaputt). Das Prüfskript verlangt,
  dass sich mindestens 30 % der Pixel im Inneren ändern.
- Keine Animation. Feuer und Rauch erzeugt das Spiel mit den vorhandenen Explosionen.

Budget: Teil A ergibt 28 neue Tiles. Zusammen mit Teil D höchstens **64 neue Tiles**.

## 4. Teil B: leichtes Bodengeschütz 16×16 (muss)

Ein Flak-Geschütz auf einem Sockel. Es steht am Boden, scrollt mit der Landschaft, dreht sich zum Spieler und schießt.

| Frame | Inhalt |
|---|---|
| `n`, `ne`, `e`, `se`, `s`, `sw`, `w`, `nw` | Geschütz mit dem Rohr in die jeweilige Richtung (`n` = nach oben, `s` = nach unten zum unteren Bildrand) |
| `flash0`, `flash1` | Mündungsfeuer, zwei Phasen, **16×16 eigenes Bild**, wird vom Spiel an die Rohrspitze gesetzt |
| `wreck` | zerstörtes Geschütz: verbogenes Rohr, schwarzer Sockel. Bleibt liegen, bis es aus dem Bild scrollt |

Regeln:
- Größe genau **16×16**, Palette **`fixed_targets`**, Index 0 = durchsichtig.
- Der **Sockel** ist in allen 8 Richtungen **gleich** und liegt in der Bildmitte. Nur der Turm mit dem Rohr dreht sich.
  Sonst „wackelt“ das Geschütz beim Drehen.
- Alle 8 Richtungen **einzeln zeichnen**. Bitte nicht einfach spiegeln: Das Licht kommt von oben links, beim Spiegeln
  wäre es auf der falschen Seite.
- Zu jeder Richtung die **Rohrspitze** als Pixelkoordinate (x, y im 16×16-Bild) angeben. Dort erscheinen Mündungsfeuer
  und Schuss.
- Das Mündungsfeuer darf hell sein (Gelb, Orange, Weiß aus den Einträgen 12–15 oder vorhandenen Farben).

## 5. Teil C: schweres Bodengeschütz 32×32 (kann)

Wie Teil B, aber **32×32**, z. B. Doppel-Flak oder Raketenwerfer, mit den Frames `n` … `nw`, `flash0`, `flash1`
(je 16×16) und `wreck` (32×32). Gleiche Regeln: Palette `fixed_targets`, fester Sockel, Rohrspitzen angeben.
Es hält mehr aus und schießt Salven. Wenn die Zeit knapp ist, lieber Teil A und B sorgfältig machen.

## 6. Teil D: große Hallen (kann)

Zerstörte Varianten der modularen Hallen: `complex_steel_plain`, `complex_steel_0_0` … `complex_steel_2_2` (IDs 106–115)
und `complex_brick_plain`, `complex_brick_0_0` … `complex_brick_2_2` (IDs 116–125). Name `<name>_destroyed`, z. B.
`complex_steel_1_1_destroyed`. Die Hallen bestehen aus diesen Kacheln in beliebiger Größe. Deshalb muss **jede
zerstörte Kachel neben jeder anderen zerstörten und jeder intakten Kachel** derselben Halle passen: gleiche
Wandlinien an den Kanten, Schäden zur Mitte hin.

## 7. Datenformat `ground-targets.json` (verbindlich)

Pixel als **Zeichenketten aus Hex-Ziffern**: ein Zeichen pro Pixel (`0`–`9`, `a`–`f` = Palettenindex), eine
Zeichenkette pro Bildzeile, von oben nach unten.

```json
{
  "schema": 1,
  "palettes": {
    "fixed_targets": [[0,0,0], [18,25,32], "... genau 16 Einträge [R,G,B], 1–11 unverändert ..."]
  },
  "destroyed_tiles": [
    {"name": "hangar_destroyed_0_0", "of": "hangar_0_0", "palette": "structures",
     "pixels": ["3456...16 Zeichen...", "... genau 16 Zeilen ..."]}
  ],
  "ground_gun": {
    "size": [16, 16],
    "palette": "fixed_targets",
    "frames": {
      "n":  ["16 Zeichen", "... 16 Zeilen ..."],
      "ne": ["..."], "e": ["..."], "se": ["..."], "s": ["..."], "sw": ["..."], "w": ["..."], "nw": ["..."],
      "flash0": ["..."], "flash1": ["..."], "wreck": ["..."]
    },
    "muzzle": {"n": [8, 1], "ne": [14, 2], "e": [15, 8], "se": [14, 14], "s": [8, 15],
               "sw": [1, 14], "w": [0, 8], "nw": [1, 1]}
  },
  "heavy_gun": { "... wie ground_gun, size [32, 32]; flash0/flash1 sind 16×16 ..." }
}
```

- `of` ist der Name des intakten Tiles aus `assets/art/coastal-base/generated/level-example.json`.
- `palette` ist `structures`, `nature`, `water` oder `fixed_targets` (Abschnitt 2).
- `palettes.fixed_targets` nur angeben, wenn die Einträge 12–15 neue Farben bekommen. Dann alle 16 Einträge.
- `heavy_gun` weglassen, wenn Teil C nicht geliefert wird.
- Die `muzzle`-Werte im Beispiel sind nur Platzhalter. Bitte die echten Rohrspitzen eintragen.

## 8. Checkliste für den Pull Request

- [ ] Nur neue Dateien unter `assets/art/ground-targets/`
- [ ] `python3 tools/check_ground_targets.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschaubilder 1:1 und 4-fach
- [ ] Teil A vollständig (7 Gruppen, 28 Tiles), Teil B vollständig (11 Frames + Rohrspitzen)
- [ ] Kurze Beschreibung, welche Teile (C, D) geliefert wurden und welche Farben in `fixed_targets` 12–15 neu sind
