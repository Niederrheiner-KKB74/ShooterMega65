# Auftrag an ChatGPT: Level 3 „Offshore“ (Meer, Bohrinseln, Flugzeugträger)

Spiel: **Shooter65**, vertikaler Shooter für den MEGA65 (Repository `Niederrheiner-KKB74/ShooterMega65`).
**Basis-Branch ist `stage12`** (nicht `main`). Bitte den Pull Request gegen `stage12` stellen.

Level 1 (Küste, Wald, Basis) und Level 2 (Wüste, Canyon, Raffinerie) sind fertig. Level 3 spielt **auf dem offenen
Meer**: fast nur Wasser, unterbrochen von kleinen Inseln, Bohrinseln, Forschungsplattformen, Windkraftanlagen und
Antennen. Neu sind **eigene Gegner für dieses Level** (Schiffe und zwei Flugzeugtypen), **animierte Tiles** und ein
**Flugzeugträger** als Boss.

Gesucht sind **Grafik und die Karte**. Bitte nichts am Programm (`src/`), an `tools/` oder an Level 1/2 ändern.
Gegnerwellen, Schiffsrouten und das Verhalten der Gegner und des Bosses übernimmt Claude.

## 1. Übersicht

| Teil | Inhalt | Ordner / Datei |
|---|---|---|
| A | Meer-Tileset 16×16 mit animierten Tiles | `assets/art/level3/generated/` |
| B | Zerstörte Varianten der Gebäude und Plattformen | `assets/art/level3/generated/ground-targets.json` |
| C | Karte des Levels mit Shops, Boss und Levelende | `levels/level3.json` |
| D | Gegner von Level 3 (Schiffe, Flugzeuge) | `assets/art/enemies-level3/generated/` |
| E | Boss: Flugzeugträger | `assets/art/boss-level3/generated/` |

Vor dem Pull Request bitte prüfen und die Ausgabe in die PR-Beschreibung kopieren:

```sh
python3 tools/check_level3_art.py
```

Das Skript meldet Fehler (müssen behoben werden) und Hinweise. Ein Pull Request darf keine Fehler enthalten.
Es prüft auch die Karte mit dem echten Level-Konverter (`tools/build_level.py`).

## 2. Allgemeine Regeln (wie bisher)

- **Pixelgenau**: 1 Bildpixel = 1 Spielpixel. Keine Kantenglättung, keine Verläufe, kein Weichzeichnen.
- **Draufsicht**, Licht von oben links. Der Spieler fliegt nach oben.
- **Farben sind Palettenindizes** (0–15). Jedes Tile und jedes Objekt benutzt genau eine Palette mit 16 Einträgen.
- In **Landschafts-Tiles** ist **Index 0 verboten** (er zeigt die schwarze Hintergrundfarbe).
- In **Objekten** (Gegner, Boss) ist **Index 0 durchsichtig**.
- Stil und Pixeldichte wie Level 1 und 2.

**Wichtig: Abwechslung.** Bei Level 2 wirkten die Farben etwas eintönig, auf dem Meer ist die Gefahr noch größer.
Bitte bewusst variieren: tiefes Wasser (dunkel), offenes Wasser, flaches Wasser über Sand und Riffen (türkis),
Schaumkronen, Strömungslinien, Kielwasser-Spuren, Ölfilme um die Bohrinseln, Riffe und Sandbänke, Inseln mit Strand,
Felsen, Gras und Palmen. Große Wasserflächen nicht aus einem einzigen Tile, sondern aus mehreren Varianten mischen.

## 3. Teil A: Tileset

Format genau wie Level 2 (`assets/art/level2/generated/` als Vorlage): `terrain.ncm.bin` (je Tile 128 Byte: obere
Hälfte 16×8, dann untere; je Byte zwei Pixel, **unteres Nibble = linkes Pixel**), `level-example.json`
(`{"tiles": [{"id": 0, "name": "sea0", "palette": "water"}, …]}`, ids 0, 1, 2 … in Reihenfolge, Namen eindeutig),
`manifest.json` mit genau vier Paletten, dazu die Vorschauen `terrain-sheet.png` und `level-overview.png`.

Grenzen:
- höchstens **128 Tiles**, **einschließlich der Animationsphasen** (die zerstörten Tiles aus Teil B zählen extra).
- genau diese vier Paletten:

| Palette | Verwendung in Level 3 | Regel |
|---|---|---|
| `water` | Meer in allen Tiefen, Schaum, Riffe unter Wasser, Kielwasser, Ölfilm, Brandung am Strand | **Nur Wasser.** Schiffe fahren **nur** auf Tiles dieser Palette, das Spiel erkennt Wasser genau daran. Bitte mit 15 Farben großzügig für Blau- und Türkistöne nutzen |
| `nature` | Strand, Sand, Felsen, Gras, Palmen, Vogelfelsen | frei wählbar |
| `structures` | Bohrinseln, Plattformen, Stege, Hubschrauberdecks, Windkraftanlagen, Antennen, Container, Tanks | frei wählbar |
| `fixed_targets` | Bodengeschütze und ihre Wracks | **muss exakt die Palette von Level 1 sein** (aus `assets/art/ground-targets/generated/ground-targets.json`, `palettes.fixed_targets`) |

Tile-Ideen: Meer (mehrere Varianten je Tiefe), Übergänge tief/flach in alle Richtungen mit Ecken, Riffe, Sandbänke,
kleine Inseln (2×2 bis 4×4 Tiles) mit Strand und Brandung, **Bohrinsel** (Plattform auf Stelzen, Bohrturm, Kran,
Abfackel-Kamin, Hubschrauberdeck), **Forschungsplattform** (Module, Antennenmast, Radarkuppel, Solarfelder),
**Windpark** (Windkraftanlagen auf Sockeln), **Antennen- und Funkmasten**, Bojen, Stege, Pipelines unter Wasser,
gegen Ende ein **Marinestützpunkt** (Kaimauer, Docks, Lagerhallen, Tanklager).

### Animierte Tiles (neu)

Einige Tiles werden im Spiel alle paar Frames ausgetauscht. Das ist Teil A, Datei `animations.json`:

```json
{"animations": [
  {"name": "turbine", "period": 6,
   "phases": [["turbine_a_0_0", "turbine_a_1_0", "turbine_a_0_1", "turbine_a_1_1"],
              ["turbine_b_0_0", "turbine_b_1_0", "turbine_b_0_1", "turbine_b_1_1"],
              ["turbine_c_0_0", "turbine_c_1_0", "turbine_c_0_1", "turbine_c_1_1"]]},
  {"name": "glitter", "period": 12, "phases": [["sea_glint_a"], ["sea_glint_b"]]}
]}
```

- `phases`: **2 bis 4 Phasen**, jede Phase listet **dieselbe Anzahl** Tile-Namen in derselben Reihenfolge. Das Spiel
  zeigt nacheinander Phase 1, 2, 3 … an der Stelle der Tiles aus Phase 1.
- `period`: Frames pro Phase, 4 bis 32 (50 Frames = 1 Sekunde).
- In der **Karte** kommen **nur die Tiles der ersten Phase** vor. Die Tiles der anderen Phasen stehen nur im Tileset.
- Ein Tile behält in allen Phasen **dieselbe Palette**. Animierte Tiles sind **nicht zerstörbar**.
- Höchstens **8 Animationen** und zusammen **24 animierte Tiles** (Tiles der ersten Phase). Alle Phasen zählen bei den
  128 Tiles mit.
- Gewünscht: **Rotor der Windkraftanlage** (z. B. 32×32 = 4 Tiles, 3 Phasen), **Glitzern auf dem Wasser** (2–3 Tiles,
  2–3 Phasen), **Flamme am Abfackel-Kamin** der Bohrinsel (1–2 Tiles, 3 Phasen), **Blinklicht an Antennen** (1 Tile,
  2 Phasen). Weitere gern, solange die Grenzen eingehalten werden.
- Die Windkraftanlagen stehen am besten in Gruppen (Windpark), damit eine Animation viele Anlagen bewegt: alle
  Anlagen mit denselben Tiles drehen sich gleich.

## 4. Teil B: zerstörbare Gebäude

Datei `ground-targets.json` im selben Ordner, Format **genau wie Level 2** (eine Hex-Ziffer pro Pixel, 16 Zeilen à
16 Zeichen, mit `kind`, `group`, `col`, `row`). Gebäude sind 32×32 (vier Tiles, `col`/`row` 0 oder 1), Hallen werden
Feld für Feld zerstört (`kind` = `hall`). **Höchstens 48 zerstörte Tiles.**

| `kind` | Treffer | Punkte | Belohnung | passt in Level 3 für |
|---|---|---|---|---|
| `hangar` | 16 | 500 | – | Lagerhalle am Stützpunkt, Wohnmodul |
| `depot` | 12 | 400 | $-Kapsel | Containerstapel, Verladekran |
| `checkpoint` | 8 | 200 | – | kleiner Leuchtturm, Wachposten auf einer Insel |
| `bunker` | 24 | 800 | große $-Kapsel | Kommandomodul einer Plattform |
| `radar` | 12 | 600 | – | Radarkuppel, Antennenmast, Funkmast |
| `fuel` | 10 | 500 | kleine $-Kapsel | Öltank, Bohrturm-Modul, Treibstofflager |
| `crates` | 4 | 150 | S-Kapsel | Fässer, Kisten auf einem Steg |
| `hall` | 4 je Feld | 50 je Feld | – | große Plattformdecks, Hallen am Kai |

Die äußeren 2 Pixel jedes Gebäudes bleiben wie beim Original. Das zerstörte Gebäude muss deutlich kaputt aussehen
(Trümmer, Brand, Ölfleck). Windkraftanlagen sind animiert und deshalb **nicht** zerstörbar.

## 5. Teil C: Karte `levels/level3.json`

Format wie Level 2 (`docs/level_json.md`):

```json
{
  "format": "shootermega65-level-1",
  "name": "Operation …",
  "tileset": "assets/art/level3/generated",
  "ground_targets": "assets/art/level3/generated",
  "scroll_speed": 0.5,
  "map": [ … ],
  "paths": {}, "formations": {},
  "events": [ … ]
}
```

- **21 Tile-Nummern pro Zeile**, Zeile 0 = Levelanfang (unten). Die linke Spalte (Spalte 0) ist unsichtbar.
- **etwa 375 Zeilen** (4 Minuten), **höchstens 256 verschiedene Zeilen**.
- Abschnitte als Vorschlag: offene See mit Inseln und Riffen (0–95), Ölfeld mit Bohrinseln (96–183),
  Forschungsplattformen und Windpark (184–279), Marinestützpunkt und Flottenverband (280–374).
- Schiffe brauchen **zusammenhängende Wasserflächen**: Zwischen Inseln und Plattformen immer genug offenes Wasser
  lassen (mindestens 3 Tiles breite Fahrrinnen).
- `events` (nach `row` sortiert), mindestens:
  - `{"row": 188, "type": "shop", "id": "mid"}` an einer ruhigen Stelle
  - `{"row": 352, "type": "boss"}`, davor **etwa 16 Zeilen offenes Wasser** ohne Plattformen, wo der Träger Platz hat
  - `{"row": 368, "type": "shop", "id": "end"}` und `{"row": 375, "type": "end"}`
- Optional: Bodengeschütze als `ground`-Ereignisse (`"enemy": "flak"` / `"heavy_flak"`) auf Inseln und Plattformen
  (nicht auf Wasser). **Keine Panzer**. Schiffe, Formationen und Flugbahnen setzt Claude.

## 6. Teil D: Gegner von Level 3 (neu)

Level 3 bekommt **eigene Gegnergrafiken**. Sie ersetzen in diesem Level die Flugzeuge und Panzer der ersten beiden
Level. Datei `assets/art/enemies-level3/generated/indexed-source.json`: eine Liste von Frames im Format der
bisherigen Gegner (`assets/art/enemy-views/generated/indexed-source.json`):

```json
[{"group": "seaplane", "pose": "south", "phase": 0, "width": 16, "height": 16, "palette": "air",
  "rows": ["00000000…", …]}, …]
```

`rows` mit **zwei Hex-Ziffern pro Pixel**, Index 0 durchsichtig. Die Größen sind **fest**:

| `group` | Gegner | `pose` | `phase` | Größe | Palette |
|---|---|---|---|---|---|
| `seaplane` | Flugtyp 1: kleines Wasserflugzeug/Marinejäger mit Schwimmern, fliegt in Formationen | `north`, `northeast`, `east`, `southeast`, `south`, `southwest`, `west`, `northwest` | 0–2 (Propeller, Auspuff) | 16×16 | `air` |
| `navy_heli` | Flugtyp 2: Marinehubschrauber, bleibt kurz stehen und feuert | dieselben 8 Richtungen | 0–2 (Rotor) | 16×16 | `heli` |
| `speedboat` | kleines Schnellboot, schnell, fährt auf Routen | `north`, `east`, `south`, `west` | 0–3 (Bugwelle, Kielwasser) | 16×16 | `ships` |
| `patrol_boat` | Patrouillenboot mit einem Geschütz | `north`, `east`, `south`, `west` | 0–1 (Bugwelle) | 32×32 | `ships` |
| `frigate` | Fregatte, groß und langsam, zwei Geschütze, Front nach unten | `south` | 0–1 (Bugwelle, Kielwasser) | 32×64 | `ships` |
| `frigate` | Wrack der Fregatte (brennend, Schlagseite) | `destroyed` | 0 | 32×64 | `ships` |

- Die **Geschütze** auf Patrouillenboot und Fregatte zeichnet das Spiel selbst darüber (das leichte Bodengeschütz aus
  Level 1, drehbar). Bitte dort nur einen runden Sockel malen und in `placement.json` die Lage angeben:

```json
{"patrol_boat": {"guns": [[8, 6]]}, "frigate": {"guns": [[8, 8], [8, 36]]}}
```

  (linke obere Ecke des 16×16-Geschützes; beim Patrouillenboot für die Ansicht `south`, das Spiel dreht den Punkt).
- `palettes.json`: `{"air": [16 × [R,G,B]], "heli": […], "ships": […]}`. Für die Schiffe Grau, Marineblau, Weiß für
  Gischt und Kielwasser, etwas Rot/Orange für Lichter und Warnstreifen.
- Kielwasser und Bugwelle gehören ins Schiffsbild (an den Rändern durchsichtig), damit die Schiffe auf dem Wasser
  sichtbar fahren.
- Speicher: Flugzeuge, Patrouillenboot und Fregatte teilen sich **324 Glyphen**, das Schnellboot hat **48 eigene**.
  Mit den Größen oben passt alles (279 und 48). Das Prüfskript rechnet nach.
- Vorschauen: jeder Gegner in allen Richtungen und Phasen (`*-preview.png`).

## 7. Teil E: Boss – Flugzeugträger

Format wie die bisherigen Bosse (`assets/art/boss-level2/generated/` als Vorlage): `indexed-source.json` (Frames mit
`id`, `width`, `height`, `rows`, zwei Hex-Ziffern pro Pixel), `palette.rgb` (48 Byte), `placement.json`, Vorschauen.

Idee: ein **Flugzeugträger** des Gegners, Draufsicht, **Bug nach unten**. Er fährt langsam von oben ins Bild und
gleitet träge hin und her. Vier Geschütztürme an den Ecken des Decks, Inselaufbau mit Radar, Flugdeck mit
Markierungen. Nach den Türmen öffnet sich ein **Aufzug im Flugdeck** und gibt den Hangar mit dem Reaktor frei
(`core_exposed`). Zwischendurch startet er **kleine Jets** vom Katapult.

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body` | höchstens **96×128**, empfohlen **96×112** | Rumpf mit Flugdeck, Bug unten. Index 0 im Rumpf durchsichtig, Rumpf geschlossen |
| `turret_nw/ne/sw/se_south`, `…_southeast`, `…_destroyed` | je 16×16 | vier Geschütztürme wie bisher |
| `core_exposed` | 32×32 | geöffneter Deckaufzug mit glühendem Reaktor im Hangar |
| `rotor_0`, `rotor_1`, `rotor_2` | je bis 32×32 | drei Phasen der **drehenden Radarschirme** am Inselaufbau (1 bis 4 Stellen) |
| `muzzle_0`, `muzzle_1` | je 16×16 | Mündungsfeuer |
| `spray_0`, `spray_1`, `spray_2` | je **32×16** | Bugwelle und Kielwasser, drei Phasen, an den Rändern durchsichtig |
| `deck_jet_0`, `deck_jet_1`, `deck_jet_2` | je **16×16** | kleiner Jet beim Start, Front nach unten: auf dem Katapult (mit Dampf), abhebend, im Flug |

`placement.json` wie beim Hover-Panzer, aber ohne `flame`:

```json
{
  "body": "body", "body_size": [96, 112], "palette": "boss",
  "turrets": [{"id": "turret_nw", "offset": [x, y], "size": [16, 16], "south": "turret_nw_south",
               "southeast": "turret_nw_southeast", "destroyed": "turret_nw_destroyed"}, … vier …],
  "core": {"offset": [x, y], "size": [32, 32], "exposed_overlay": "core_exposed"},
  "rotors": [{"id": "radar", "offset": [x, y], "phase_offset": 0}, … 1 bis 4 …],
  "rotor_frames": ["rotor_0", "rotor_1", "rotor_2"],
  "muzzle": {"frames": ["muzzle_0", "muzzle_1"], "south_offset_from_turret": [0, 15]},
  "spray": {"frames": ["spray_0", "spray_1", "spray_2"], "offsets": [[x, y], …]},
  "catapult": {"frames": ["deck_jet_0", "deck_jet_1", "deck_jet_2"], "offset": [x, y]}
}
```

- `spray.offsets`: 2 bis 4 Stellen (Bugwelle vorn unten, Kielwasser hinten), auch teilweise außerhalb des Rumpfs.
- `catapult.offset`: wo der Jet auf dem Deck startet (linke obere Ecke des 16×16-Bildes).
- **Eine Palette**, 15 Farben plus Durchsichtig, auch für Jets und Wasser.
- Speicher: höchstens **324 Glyphen**. Ein Frame kostet Breite/16 × (Höhe/8 + 1) Glyphen, dazu kommt 1;
  Südost-Ansichten zählen doppelt. Das Spiel legt jeden Frame so groß an wie beim größten Boss (der Rumpf also
  mindestens 112 breit). Mit Rumpf 96×112: etwa 245 Glyphen. Das Prüfskript rechnet nach.

## 8. Checkliste für den Pull Request

- [ ] Basis-Branch `stage12`; nur neue Dateien in `assets/art/level3/`, `assets/art/enemies-level3/`,
      `assets/art/boss-level3/` und `levels/level3.json`
- [ ] `python3 tools/check_level3_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Tile-Raster, ganzer Level, Animationen (alle Phasen nebeneinander), Gebäude intakt/zerstört,
      alle Gegner in allen Richtungen und Phasen, Boss zusammengesetzt (Türme intakt und zerstört, Aufzug offen),
      Radar, Bugwelle, Jet-Start
- [ ] Kurze Beschreibung: Abschnitte des Levels, welche Gebäude welchem `kind` entsprechen, die Animationen, Idee
      des Bosses
