# Auftrag an ChatGPT: Level 2 „Canyon und Raffinerie“

Spiel: **Shooter65**, vertikaler Shooter für den MEGA65 (Repository `Niederrheiner-KKB74/ShooterMega65`).
**Basis-Branch ist `stage8`** (nicht `main`). Bitte den Pull Request gegen `stage8` stellen.

Level 1 („Operation Kuestenwald“) ist fertig: Küste, Wald, Militärstraße, Basis. Level 2 soll sich deutlich
unterscheiden: **Wüste mit Felsen, ein Canyon mit Fluss, eine Oase mit Außenposten und am Ende eine
Ölraffinerie** als Basis des Gegners. Den Boss gibt es neu.

Gesucht sind **Grafik und die Karte**. Bitte nichts am Programm (`src/`), an `tools/` oder an Level 1 ändern.
Gegnerwellen (Formationen, Flugbahnen) und das Verhalten des Bosses übernimmt Claude.

## 1. Übersicht

| Teil | Inhalt | Ordner / Datei |
|---|---|---|
| A | Landschafts-Tileset 16×16 | `assets/art/level2/generated/` |
| B | Zerstörte Varianten der Gebäude | `assets/art/level2/generated/ground-targets.json` |
| C | Karte des Levels mit Shops, Boss und Levelende | `levels/level2.json` |
| D | Boss von Level 2 | `assets/art/boss-level2/generated/` |

Vor dem Pull Request bitte prüfen und die Ausgabe in die PR-Beschreibung kopieren:

```sh
python3 tools/check_level2_art.py
```

Das Skript meldet Fehler (müssen behoben werden) und Hinweise. Ein Pull Request darf keine Fehler enthalten.
Es prüft auch die Karte mit dem echten Level-Konverter (`tools/build_level.py`).

## 2. Allgemeine Regeln (wie bisher)

- **Pixelgenau**: 1 Bildpixel = 1 Spielpixel. Keine Kantenglättung, keine Verläufe, kein Weichzeichnen.
- **Draufsicht**, Licht von oben links. Der Spieler fliegt nach oben.
- **Farben sind Palettenindizes** (0–15). Jedes Tile und jedes Objekt benutzt genau eine Palette mit 16 Einträgen.
- In **Landschafts-Tiles** ist **Index 0 verboten** (er zeigt die schwarze Hintergrundfarbe).
- In **Objekten** (Boss) ist **Index 0 durchsichtig**.
- Stil und Pixeldichte wie Level 1 (`assets/art/coastal-base/generated/terrain-sheet.png`), aber mit eigenen Farben.

## 3. Teil A: Tileset

Format genau wie Level 1 (`assets/art/coastal-base/generated/` als Vorlage):

| Datei | Inhalt |
|---|---|
| `terrain.ncm.bin` | alle Tiles hintereinander, je **128 Byte**: obere Hälfte 16×8 (64 Byte), dann untere Hälfte (64 Byte). Je Bildzeile 8 Byte, jedes Byte zwei Pixel: **unteres Nibble = linkes Pixel** |
| `level-example.json` | `{"tiles": [{"id": 0, "name": "sand0", "palette": "nature"}, …]}`: ids 0, 1, 2 … in Reihenfolge, Namen eindeutig |
| `manifest.json` | `{"palettes": {"water": […], "nature": […], "structures": […], "fixed_targets": […]}}`: je 16 Einträge `[R, G, B]` |
| `terrain-sheet.png`, `level-overview.png` | Vorschauen: alle Tiles als Raster, der ganze Level als Bild |

Grenzen:
- höchstens **128 Tiles** (intakte Tiles; die zerstörten aus Teil B zählen extra).
- genau vier Paletten mit genau diesen Namen. Die Namen bestimmen, wofür das Spiel sie hält:

| Palette | Verwendung in Level 2 | Regel |
|---|---|---|
| `water` | Fluss im Canyon, Oasen-Teich, Uferkanten | **Nur Wasser und Ufer.** Panzer fahren nie auf Tiles dieser Palette, das Spiel erkennt Wasser genau daran. Trockenes Land nie in `water` |
| `nature` | Sand, Dünen, Felsen, Canyonwände, Geröll, Palmen | frei wählbar, 15 Farben |
| `structures` | Straßen, Pisten, Rohrleitungen, Zäune, Gebäude, Raffinerie | frei wählbar, 15 Farben |
| `fixed_targets` | Bunker, Panzer, Bodengeschütze | **muss exakt die Palette von Level 1 sein**, alle 16 Einträge (aus `assets/art/ground-targets/generated/ground-targets.json`, `palettes.fixed_targets`). Panzer, Geschütze und ihre Wracks benutzen sie |

Tile-Ideen: Sand in mehreren Varianten, Dünenkämme, Felsbrocken, Canyonkanten in alle Richtungen mit Ecken,
Flusswasser, Ufer, Brücke über den Fluss, Wüstenpiste, Asphaltstraße, Rohrleitungen (gerade, Kurve,
T-Stück), Zaun, Oase mit Palmen, Zelte, Wachturm, Funkmast. Für die Raffinerie: Öltanks, Pumpen, Kühltürme oder
Kamine, Lagerhallen, Verladeplatz, Hubschrauberlandeplatz. Übergänge (Sand zu Fels, Ufer, Straßenkreuzungen)
bitte vollständig, damit die Karte ohne harte Kanten aussieht.

## 4. Teil B: zerstörbare Gebäude

Datei `ground-targets.json` im selben Ordner, Format wie PR #15 (eine Hex-Ziffer pro Pixel, 16 Zeilen à 16 Zeichen),
**zusätzlich mit `kind`, `group`, `col`, `row`**:

```json
{
  "schema": 1,
  "destroyed_tiles": [
    {"name": "oiltank_destroyed_0_0", "of": "oiltank_0_0", "palette": "structures",
     "kind": "fuel", "group": "oiltank", "col": 0, "row": 0,
     "pixels": ["…16 Zeichen…", "… 16 Zeilen …"]}
  ]
}
```

- Gebäude sind **32×32** (vier Tiles, `col`/`row` 0 oder 1: Spalte und Zeile innerhalb des Gebäudes, 0/0 oben links),
  `group` ist der Name des Gebäudes (alle vier Zellen gleich). **Hallen** sind beliebig groß und werden Feld für Feld
  zerstört: `kind` = `hall`, `col` = 0, `row` = 0, kein `group`.
- `kind` legt Trefferpunkte, Punkte und Belohnung fest. Bitte die neuen Gebäude passend zuordnen:

| `kind` | Treffer | Punkte | Belohnung | passt für |
|---|---|---|---|---|
| `hangar` | 16 | 500 | – | Lagerhalle, Werkstatt, Kaserne |
| `depot` | 12 | 400 | $-Kapsel | Depot, Verladestation |
| `checkpoint` | 8 | 200 | – | Wachposten, Schranke, Zelt |
| `bunker` | 24 | 800 | große $-Kapsel | Bunker, Kommandostand |
| `radar` | 12 | 600 | – | Radar, Funkmast |
| `fuel` | 10 | 500 | kleine $-Kapsel | Öltank, Pumpe, Treibstofflager |
| `crates` | 4 | 150 | S-Kapsel | Kisten, Fässer |
| `hall` | 4 je Feld | 50 je Feld | – | große Raffineriehallen, Rohrbrücken |

- **höchstens 48 zerstörte Tiles** insgesamt (z. B. 8 Gebäude à 4 Tiles + 16 Hallenfelder).
- `palette` ist die Palette des intakten Tiles oder `fixed_targets` (für Ruß und Glut: deren Einträge 12–15).
- Die äußeren 2 Pixel jedes Gebäudes bleiben wie beim Original (die Nachbar-Tiles werden nicht getauscht).
  Hallenfelder müssen an jedes intakte und jedes zerstörte Nachbarfeld passen.
- Das zerstörte Gebäude muss deutlich kaputt aussehen (eingestürzt, verkohlt, Krater).

## 5. Teil C: Karte `levels/level2.json`

Format wie `levels/coastal_base.json` und `docs/level_json.md`. Pflichtfelder:

```json
{
  "format": "shootermega65-level-1",
  "name": "Operation …",
  "tileset": "assets/art/level2/generated",
  "ground_targets": "assets/art/level2/generated",
  "scroll_speed": 0.5,
  "map": [ … ],
  "paths": {}, "formations": {},
  "events": [ … ]
}
```

- **21 Tile-Nummern pro Zeile**, Zeile 0 = Levelanfang (unten). Die linke Spalte (Spalte 0) ist unsichtbar.
- **etwa 375 Zeilen** (4 Minuten), **höchstens 256 verschiedene Zeilen** (gleiche Zeilen kosten fast nichts).
- Abschnitte als Vorschlag: Wüsteneinflug (0–95), Canyon mit Fluss und Brücken (96–183), Oase und Außenposten
  (184–279), Raffinerie (280–374).
- `events` (nach `row` sortiert), mindestens:
  - `{"row": 188, "type": "shop", "id": "mid"}` in einer ruhigen Gegend
  - `{"row": 358, "type": "boss"}`, davor etwa 10 Zeilen ohne Gebäude oder Hindernisse, wo der Boss Platz hat
  - `{"row": 368, "type": "shop", "id": "end"}` und `{"row": 375, "type": "end"}`
- Optional: Vorschläge für Bodengegner als `ground`-Ereignisse, also Panzer (`"enemy": "tank"`, mit `dir`) und
  Geschütze (`"enemy": "flak"` / `"heavy_flak"`) auf passendem Land (nicht auf Wasser, nicht auf Gebäuden).
  Formationen und Flugbahnen bitte leer lassen, die baut Claude.
- Zerstörbare Gebäude sollen verteilt vorkommen, am dichtesten in der Raffinerie. Der Fluss soll Brücken haben,
  damit Panzer ihn überqueren können (Brücken nicht in der Palette `water`).

## 6. Teil D: Boss

Format **genau wie Level 1** (`assets/art/boss-level1/generated/` als Vorlage): `indexed-source.json`
(Liste von Frames mit `id`, `width`, `height`, `rows`, **zwei Hex-Ziffern pro Pixel**), `palette.rgb`
(48 Byte: 16 × R, G, B), `placement.json` (Lage der Teile), dazu PNG-Vorschauen (zusammengesetzt, Animation).

Idee für Level 2: ein **schwerer Landkreuzer**, also ein riesiges Kettenfahrzeug der Raffinerie-Wache (oder ein
anderer bodengebundener Boss, der zur Wüste passt). Das Spiel lässt ihn wie den Quadrocopter seitlich fahren.

Bestandteile (die Frame-`id`s sind verbindlich):

| Frame-`id` | Größe | Inhalt |
|---|---|---|
| `body` | höchstens **128×80**, empfohlen 96–112 × 64 | Rumpf, Draufsicht, Front nach unten. Index 0 im Rumpf ist durchsichtig, der Rumpf muss geschlossen sein |
| `turret_nw/ne/sw/se_south`, `…_southeast`, `…_destroyed` | je 16×16 | vier Waffentürme: Rohr nach Süden, nach Südosten (Südwesten spiegelt das Spiel), zerstört |
| `core_exposed` | 32×32 | der Schwachpunkt (z. B. offener Motorraum, Reaktor), erscheint, wenn alle vier Türme zerstört sind |
| `rotor_0`, `rotor_1`, `rotor_2` | je bis 32×32 | drei Animationsphasen für bis zu 4 bewegte Teile (beim Landkreuzer z. B. Ketten, Auspuffrauch, Radarschüssel) |
| `muzzle_0`, `muzzle_1` | je 16×16 | Mündungsfeuer |

- **Eine Palette**, 15 Farben plus Durchsichtig. Ein heller Treffer-Blitz wird automatisch daraus erzeugt.
- **Speicher**: höchstens **162 Glyphen**. Ein Frame kostet Breite/16 × (Höhe/8 + 1) Glyphen, dazu kommt 1;
  Südost-Ansichten zählen doppelt. Level 1 braucht 149 (Rumpf 96×64 = 54). Das Prüfskript rechnet nach.
- `placement.json` wie Level 1: `turrets` (genau 4, `offset` = linke obere Ecke im Rumpf), `core`
  (`offset`), `rotors` (bis zu 4, `offset`, `phase_offset`), `muzzle` (`south_offset_from_turret`).

## 7. Checkliste für den Pull Request

- [ ] Basis-Branch `stage8`; nur neue Dateien in `assets/art/level2/`, `assets/art/boss-level2/` und `levels/level2.json`
- [ ] `python3 tools/check_level2_art.py` ohne Fehler, Ausgabe in der PR-Beschreibung
- [ ] Vorschauen: Tile-Raster, ganzer Level, Gebäude intakt/zerstört, Boss zusammengesetzt und animiert
- [ ] Kurze Beschreibung: Abschnitte des Levels, welche Gebäude welchem `kind` entsprechen, Idee des Bosses
