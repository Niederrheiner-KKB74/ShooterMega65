# Levelformat (JSON) – Anleitung für Leveldesign mit ChatGPT

Ein Level ist **eine JSON-Datei** in `levels/` (Beispiel: `levels/level01.json`). Beim Bauen erzeugt
`tools/build_level.py` daraus zwei Dateien auf der D81: `LnGFX` (Landschaftsgrafik) und `LnDAT`
(Karte, Ereignisse, Formationen, Bahnen). Das Programm lädt sie beim Start. Hintergründe zum Format
stehen in `docs/level_format.md`.

```sh
python3 tools/build_level.py levels/level01.json --name L1     # prüft und erzeugt nur den Level
python3 tools/build.py --kickass …                              # baut Spiel + alle Level + D81
```

Der Konverter prüft alle Angaben und meldet Fehler mit Zeile und Grund. Er erzeugt außerdem
`build/levels/l1_preview.png`: ein Bild des ganzen Levels mit dem Start unten, mit farbigen Markierungen
für die Ereignisse.

## Grundbegriffe

- Der Bildschirm ist 320×200 Pixel groß und scrollt mit 0,5 Pixel pro Frame (25 Pixel pro Sekunde, 50 Frames pro Sekunde).
- Die Karte besteht aus **Zeilen von 21 Tiles** zu je 16×16 Pixeln. Die erste Spalte (x = 0–15 Pixel der Karte)
  liegt unter dem linken Rand und ist **nicht sichtbar**.
- **Zeile 0 ist der Levelanfang** (unten). Die Zeilennummer steigt nach oben.
- **4 Minuten ≈ 375 Zeilen** (16 Pixel pro Zeile bei 25 Pixel pro Sekunde, also 0,64 s pro Zeile).
- Ein Ereignis mit `"row": R` wird ausgelöst, wenn Zeile R oben am Bildschirmrand erscheint. Neue Gegner starten
  oberhalb des sichtbaren Bereichs.

## Aufbau

```json
{
  "format": "shootermega65-level-1",
  "name": "Level 1",
  "tileset": "assets/art/spec-v2/generated",
  "scroll_speed": 0.5,
  "map": [ … ],
  "paths": { … },
  "formations": { … },
  "events": [ … ]
}
```

### `tileset`
Ordner mit den Landschaftsgrafiken. Er muss `terrain.ncm.bin`, `level-example.json` (Tile-Liste mit Palette)
und `manifest.json` (Paletten) enthalten. Erlaubte Tile-Nummern sind die `id`s aus `level-example.json`
(derzeit 0–61). Je Level gibt es höchstens 4 Landschaftspaletten.

### `map`
Liste von Zeilen, **beginnend mit dem Levelanfang**. Jede Zeile ist eine Liste von 21 Tile-Nummern.
Wiederholungen lassen sich kompakt schreiben:

```json
"map": [
  [0,3,0,3,0,3,6,21,18,21,18,21,18,21,26,27,18,21,18,21,18],
  {"repeat": 10, "rows": [ [ …21 Zahlen… ], [ …21 Zahlen… ] ]}
]
```

Grenzen:
- höchstens **256 verschiedene Zeilen** pro Level. Gleiche Zeilen werden automatisch nur einmal gespeichert.
- die Datei `LnDAT` darf höchstens **16 KB** groß sein. Jede verschiedene Zeile kostet 21 Byte, jede Kartenzeile
  1 Byte, jedes Ereignis 8 Byte. 256 verschiedene Zeilen belegen also 5,4 KB, der Rest reicht für mehrere tausend
  Kartenzeilen. Durch wiederverwendete Zeilen dürfen Level deutlich länger als 256 Zeilen sein. Für schöne Übergänge (Küste, Straße) müssen benachbarte Tiles
zueinander passen. Die Vorschau zeigt sofort, ob es stimmt.

### `paths` – Flugbahnen
Benannte Befehlslisten. Geschwindigkeiten in **Pixel pro Frame**, Vielfache von 0,25, Bereich −31,75 … 31,75.
Positive `dy` bedeuten nach unten, positive `dx` nach rechts.

| Befehl | Bedeutung |
|---|---|
| `["move", frames, dx, dy]` | `frames` lang mit konstanter Geschwindigkeit fliegen |
| `["sine", amplitude, period, cycles, dy]` | Schlangenlinie: seitlich ±`amplitude` Pixel, Periode in Frames, Anzahl Perioden, dabei `dy` nach unten |
| `["aim", frames, speed]` | `frames` lang seitlich auf den Spieler zusteuern (`speed` Pixel pro Frame) |
| `["wait", frames]` | in der Luft stehen bleiben |
| `["fire"]` | einen Schuss abgeben (Art hängt vom Gegner ab) |
| `["loop", n]` … `["endloop"]` | Abschnitt n-mal wiederholen (nicht verschachtelt) |
| `["end"]` | mit der letzten Geschwindigkeit weiterfliegen, bis der Gegner das Bild verlässt |

Gegner verschwinden automatisch, wenn sie den Bildschirm verlassen. Zusätzlich schießen sie gelegentlich
zufällig. Beispiel:

```json
"paths": {
  "snake": [["sine", 48, 128, 3, 1], ["end"]],
  "dive":  [["move", 48, 0, 1.5], ["aim", 40, 1], ["fire"], ["move", 127, 0, 2.5], ["end"]]
}
```

### `formations`
Benannte Gruppen gleicher Gegner, die nacheinander dieselbe Bahn fliegen.

| Feld | Bedeutung |
|---|---|
| `enemy` | `fighter`, `helicopter` (16×16), `bomber`, `armoured` (32×32) |
| `count` | Anzahl 1–8 |
| `path` | Name einer Bahn |
| `delay` | Frames zwischen zwei Mitgliedern (Standard 16) |
| `x`, `y` | Startpunkt in Pixeln, linke obere Ecke (Standard x = 144, y = −32, also über dem Bildschirm) |

Wird eine Formation komplett abgeschossen, lässt der letzte Gegner eine $-Kapsel fallen.

### `events`
**Nach `row` sortierte** Liste.

| `type` | Felder | Wirkung |
|---|---|---|
| `formation` | `formation`, optional `x`, `mirror` (true/false) | Formation starten. `mirror` spiegelt Bahn und Startpunkt (von links ↔ von rechts) |
| `ground` | `enemy`: `tank`, `x` (0–304), `dir`: `north`/`east`/`south`/`west` | Panzer am oberen Rand absetzen |
| `speed` | `value` (Pixel pro Frame, 0–4) | Scrollgeschwindigkeit ändern (0 = Stillstand, z. B. für den Boss) |
| `shop` | `id`: `mid` oder `end` | Shop (Overlay folgt in Stage 3b) |
| `boss` | `id` | Endgegner (folgt) |
| `end` | – | Levelende (vorerst: Level beginnt von vorn) |

Fehlt `end`, setzt der Konverter es an das Kartenende.

## Hinweise für gutes Leveldesign
- Höchstens etwa 20 Luftgegner und 10 Bodengegner gleichzeitig. Bei mehr kommen keine neuen Objekte dazu.
- Pro 8-Pixel-Bildzeile sind höchstens etwa 30 Gegnerbreiten zu je 16 Pixeln möglich. Formationen nicht alle auf
  derselben Höhe starten lassen.
- Zwischen zwei großen Formationen etwa 7–10 Zeilen Abstand lassen (4–6 Sekunden).
- Panzer sollten auf Land abgesetzt werden (`x` über Landtiles). Wasser wird nicht automatisch geprüft.
- Shop `mid` etwa in der Levelmitte, `end` kurz vor dem Ende, danach `end`.
