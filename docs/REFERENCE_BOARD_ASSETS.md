# PNG-Referenzboard: konvertierte Assets und Übergabe an Claude

**Integrationsstand dieses Branches:** Player und die vier Luftgegner sind jetzt
über `tools/integrate_aircraft.py` in den normalen Build eingebunden. Die unten
beschriebene ursprüngliche Asset-Lieferung bleibt als Herkunftsdokumentation
erhalten. Aktuelle Nutzung, Tests und offene Hardwareprüfung:
`docs/stage1-aircraft.md`. Landschaft/Projektile/Explosionen bleiben Platzhalter.

Stand 31.10.2026. Diese Lieferung ersetzt die frei neu entworfenen Platzhalter
aus PR #1 durch **aus dem bereitgestellten PNG abgeleitete** Daten. Sie wird
separat auf Basis von `stage1-engine-prototype` angeboten. Keine bestehende
Engine-Datei und kein Stage-1-Release wird geändert.

## Herkunft und Grenzen

Original: `assets/art/reference-board/source/reference-board.png`, unverändert
übernommen aus `Deutsches Pixel-Art-Sprite-Referenzboard.png`, 1536×1024 RGB.
SHA-256: `4fc74bfe27d6cc11346d3a97247b7b6986e9d9da6bc5d642ac435852904f6ecf`.
Die Herkunft ist das vom Nutzer gelieferte Referenzboard; dies ist keine Aussage
über Rechte an dessen ursprünglicher Generierung. Vorhandene Repository-Lizenz
und vorhandene Dateien bleiben unberührt.

Das Board enthält Beschriftungen, unterschiedlich große Vergrößerungen, weiche
Kanten und viel mehr Farben als 15 pro Motiv. Es enthält **kein einheitliches
Original-Pixelraster**, das verlustfrei ausgeschnitten werden könnte. Die Exporte
sind reproduzierbare, automatisch rekonstruierte Niedrigauflösungsfassungen:
festgelegter Ausschnitt → schwarze Hintergrundmaske → flächengewichtete
BOX-Verkleinerung → höchstens 15 deckende Farben und Transparenz, ohne Dithering.
Farben und feine Details gehen dabei verloren. Es wurde nicht von Hand nachgezeichnet.
Eine spätere Pixel-Art-Nachbearbeitung ist sinnvoll; deren Quelle muss dann separat
gespeichert werden, da erneutes Konvertieren die automatisch generierten Dateien ersetzt.

Alle Ausschnitte und Parameter stehen in `source/crops.json` (PNG-Koordinaten,
rechte/untere Grenze exklusiv). Schwarze Pixel mit maximalem RGB-Kanal ≤24 werden
bei freigestellten Motiven als Hintergrund interpretiert. Nach Verkleinerung gilt
Alpha <96 als transparent, alle übrigen Pixel sind deckend. Das ist eine
**abgeleitete Maske**, kein aus der Quelle erhaltener Alpha-Kanal. Dunkle Details
können entfallen. Landschaftsquadrate bleiben deckend, Deko wird freigestellt.
Die Skalierung ist innerhalb einer Gruppe einheitlich; Motive werden zentriert
und unten ausgerichtet. Die Größenbeschriftungen im Board sind Zielgrößen und
keine verlässlichen Angaben zur tatsächlichen Anzahl der gezeichneten Pixel.

## Geprüfter Prototyp

Branch: `stage1-engine-prototype`, Commit
`e4fe5111babb5985333a8b337275ac665d08c536`.
Gelesen: `CLAUDE.md`, `docs/artwork_spec.md`, `docs/memory_map.md`,
`tools/make_assets.py`, `tools/build.py`, `src/layout.asm`, `src/pixie.asm`,
`src/player.asm`, `src/video.asm`, `src/objects.asm`.

Die wichtigen Unterschiede zum ersten Paket:

| Bereich | Aktuelle Engine | Lieferung |
|---|---|---|
| Player | Zwei 16×24-Hardware-Sprites, zusammen 32×24 | 24×24-Motiv mittig, links/rechts je 4 transparente Pixel; 6 Frames |
| Pixies | NCM, Breite Vielfaches 16, Höhe Vielfaches 8 | zentrierte Auffüllung, Spaltenstapel mit Leer-Glyphen |
| NCM-Bytes | linker Pixel LOW-Nibble | entsprechend gepackt |
| Hardware-Sprite-Bytes | linker Pixel HIGH-Nibble | separat entsprechend gepackt |
| RRB-Objektpalette | alle Objekte fest `$2f` | gemeinsame reduzierte Palette für Runtime-Varianten |
| Gelände | 16×16-Metatiles, zwei 16×8-Glyphen | zusätzlich aus Originalausschnitten gewonnene 16×16-Fassungen |

Der Prototyp setzt `frame_base` als Byte voraus. Die 36 neuen RRB-Frames benötigen
159 Glyphen (=10176 Byte) inklusive Guards und passen in den vorgesehenen
16-KB-Bereich `$50000–$53fff`; alle Frame-Basen passen in ein Byte.
Die 52 Gelände-/Deko-Motive benötigen 104 Glyphen (=6656 Byte), ebenfalls innerhalb
der aktuellen Ein-Byte-Mapindizes. Das ersetzt keine PRG-Speicherprüfung: mehr
eingebettete Daten vergrößern den Staging-Bereich unter `$c000` und müssen vor
einer Integration durch den vorgeschriebenen Build samt Assembler-Guards geprüft werden.

## Inhalt

`generated/` enthält **94 Frames/Motive**, in horizontalen PNG-Streifen:

- Player: 3 Flammenzustände sowie Links/Normal/Rechts, 24×24 (6).
- Jäger, Bomber, Helikopter, Panzerflugzeug: jeweils 3 Frames, 16×16 bzw. 24×24 (12).
- Projektile: 12 Einzelbeispiele, 4×8 bzw. 6×12. Die drei grünen Schüsse und das
  rote Schusspaar sind getrennte Projektile aus dem Board, keine zugesicherte Animation.
- Explosionen: 6 Frames sowohl 16×16 als auch 24×24 (12).
- Meer, Ufer, Fels, Wald, Straße, Basis: jeweils 6 Tiles; dazu 16 Deko-Motive, 8×8 (52).

Namen ohne Zusatz (z. B. `fighter.png`) behalten die Ausrichtung des Boards bei:
Flugzeugnasen oben. Pro Objekttyp wird eine eigene Palette verwendet, damit
beispielsweise blaue und grüne Projektile unterscheidbar bleiben.

`*-rrb.png` zeigt die **tatsächlichen Runtime-Kandidaten** in der gemeinsamen
Objektpalette mit passender Auffüllung. Gegner sind hier um 180° nach unten
gedreht. Diese Varianten haben eine sichtbar stärkere Farbreduktion als die
Einzelfassungen. Für mehr Farbtreue müsste Claude pro Objekt den Palettenwert
setzen statt überall `PAL_OBJ` zu verwenden und zusätzliche Paletten einplanen.
`*-engine16.png` zeigt die 16×16-Metatiles; sie wurden erneut aus dem Original,
nicht aus den bereits reduzierten 8×8-Bildern abgeleitet. Keine fertige Levelmap,
kein Nahtlosigkeitsversprechen und keine erfundenen Zerstörungsvarianten.

### Rohformate und Quelldaten

- `indexed-source.json`: alle reduzierten Pixelraster; eine Zeile ist ein Hex-String
  mit **zwei Hex-Zeichen pro Indexbyte**, nicht ein Zeichen pro Pixel.
- `frames.indices.bin`: dieselben Raster hintereinander, zeilenweise, 1 Byte/Pixel.
- `frames.fcm.bin` / `frames.ncm.bin`: unabhängige Frames, Tiles zeilenweise von
  links oben; innerhalb des Tiles Zeilen von oben. FCM 8×8×1 Byte, NCM 16×8×4 Bit,
  jeweils 64 Byte/Tile. Rechts/unten transparent aufgefüllt. Keine Ladeheader.
- `manifest.json`: Größen, Paletten, Frame-Offsets/-Längen, Quellkoordinaten,
  SHA-256-Prüfsummen und Ergebnisse der Budgetprüfung. Die generischen Frames
  verwenden **pro Gruppe eine lokale Palette**, nicht schon globale FCM-Indizes.
- `palettes.rgb`: pro Palette 16 RGB888-Tripel, 48 Byte. Palette-Offsets im Manifest.
- `palettes.palregs.bin`: dieselben 48-Byte-Blöcke mit R-, G-, B-Ebene und
  vertauschten Nibbles für VIC-IV-Register. Kein vollständiger 256-Farben-Dump.

Index 0 ist transparent; Indizes 1–15 sind Farben. Für NCM muss der Colour-RAM-Wert
auf `$bank:f` gesetzt werden, damit der spezielle Wert 15 die letzte Farbe der
gewünschten Gruppe auswählt. FCM verwendet in diesen lokalen Daten kein `$ff`.
Für mehrere Gruppen gleichzeitig sind FCM-Indizes oder Palettenzuweisungen durch
die Engine anzupassen. Originalgrößen und aufgefüllte Runtime-Größen nicht verwechseln.

### Prototyp-spezifische Kandidaten

- `rrb-pixies.bin`: Glyph 0 leer; pro Frame jede Spalte mit `h` Glyphen gefolgt
  von einer Leer-Glyphe, dann nächste Spalte. Die vorige Spalten-Guard dient als
  obere Leer-Glyphe. Genau das Layout aus `tools/make_assets.py`/`src/pixie.asm`.
- `rrb-frames.inc`: `ART_*`-Konstanten und `art_frame_base/w/h`-Tabellen. Die
  bestehenden `FR_*`-Werte und `frame_*`-Labels werden bewusst nicht überschrieben.
- `player-all.sprite.bin`: 6 Frames à 512 Byte. Pro Frame linke Hälfte: 192 Byte
  plus 64 Nullbytes, rechte Hälfte ebenso. Frame-Offsets 0,512,…,2560.
- `player-normal.sprite.bin`: 512 Byte für den beschrifteten Normal-Frame
  (Index 4), passend zur aktuellen DMA-Länge `$200`.
- `player.sprpal.bin`: 96 Byte, zweimal dieselben 16 Farben in der von
  `palette_init` erwarteten planaren, nibble-vertauschten 32-Farben-Struktur.
- `terrain16.ncm.bin`: pro Metatile zuerst obere, dann untere Glyph; ihre
  Indizes und Palette stehen unter `terrain_tiles` im Manifest.

## Reproduktion und Tests

Python 3.12 und Pillow 12.3.0 wurden verwendet. Von der Repository-Wurzel:

```sh
python -m pip install -r tools/reference-board-requirements.txt
python tools/convert_reference_board.py
python tools/check_reference_board.py
```

Test: alle 94 Raster aus FCM und NCM unabhängig zurückdekodiert, inklusive
Padding; PNGs gegen indexierte Daten verglichen; alle 36 RRB-Frames bei allen
acht vertikalen Teilzeilenpositionen einschließlich Guards geprüft; sechs
Hardware-Sprite-Paare mit entgegengesetzter Nibble-Reihenfolge und 256-Byte-Abstand
geprüft; Terrain und Palettenregisterdaten rückgeprüft; Dateihashes und Budgets
geprüft. Wiederholter Export muss unter derselben Pillow-Version byteidentisch sein.

**Nur Konvertierung und Datenprüfungen: nicht assembliert, nicht in XEMU
gestartet, nicht auf MEGA65-Hardware getestet.** Vorhandene Screenshots und
Release-Dateien des Prototyps belegen keinen Test dieser neuen Grafiken.

## Nächster Integrationsschritt für Claude

`tools/build.py` ruft momentan stets `make_assets.main()` auf und erzeugt seine
Platzhalter neu. Einfaches Kopieren nach `build/gen` wäre daher nicht dauerhaft.
In einem eigenen Integrationsschritt eine ausdrückliche Asset-Auswahl hinzufügen,
den Stage-1-Generator als Standard beibehalten und die neuen Dateien gezielt
nach dessen Palette-/Frame-Konvention übernehmen. Zunächst nur Player und
Jäger ersetzen. Ein Bodenpanzer wird im Board nicht geliefert; `FR_TANK`
darf nicht unbemerkt auf das Panzerflugzeug zeigen.

Weitere offene Anpassungen: Die Engine animiert bislang vier Explosionen über
20 Ticks. Sechs neue Frames brauchen angepasste Indizes/Timing. Breitere Gegner
brauchen passende Kollisionsboxen statt des pauschalen 16-Pixel-Verhaltens.
Objektpalette nach Bank 2 laden; Landschaftspaletten Wasser/Natur/Bauten sind
für Bank 1/3/4 vorgesehen, mit entsprechenden Map-Colour-Bytes. Die bestehende
Levelmap referenziert andere Tiles; ohne neue Map kann `tiles.bin` nicht einfach
ersetzt werden. Quelle liefert weder HUD noch Level noch zerstörte Gebäude.

Player kann zunächst mit dem 512-Byte-Normal-Frame und `player.sprpal.bin`
verwendet werden; zusätzliche Frames erfordern explizite Sprite-Pointer- oder
DMA-Umschaltung und dürfen nicht einfach in den reservierten 512-Byte-Bereich
geladen werden. Nach einer Integration über `python tools/build.py` mit dem
vorgeschriebenen KickAssembler bauen, PRG-Budget prüfen, Emulator-Smoke-Test
und anschließend Eigentümer-Test auf echter Hardware durchführen. Neue
Speicherbereiche wären zugleich in `docs/memory_map.md` zu dokumentieren.
