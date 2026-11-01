# Artwork v2 nach Claudes Spezifikation

Stand: 01.11.2026. Grundlage ist die unverändert archivierte Datei
`assets/art/spec-v2/source/artwork_spec.md` vom Nutzer, nicht eine neu erfundene
Formatbeschreibung. Dieser additive Grafik-PR baut auf der bisherigen Integration
auf. Er ändert weder Engine-Code noch vorhandene Assets oder Releases.

## Was überarbeitet wurde

| Vorgabe | Lieferung |
|---|---|
| Player 32×24 | 6 Frames, horizontales PNG; Nase nach oben |
| Kleine Gegner 16×16 | Jäger und Helikopter, je 3 Frames |
| Große Gegner 32×32 | Bomber und Panzerflugzeug, je 3 Frames; keine 24×24-Zwischenfassung mehr |
| Pixies: Breite ×16, Höhe ×8 | alle Gegner, Projektile und Explosionen erfüllen dies bereits im PNG |
| Schüsse typischerweise 16×8 | kurze Schüsse 16×8, lange 6×12-Motive in 16×16; eigentliche Schüsse bleiben 4 bzw. 6 Pixel breit |
| Explosionen 16×16 und 32×32, 4–8 Frames | jeweils 6 Frames |
| Landschaft 16×16 | alle 52 Referenzmotive direkt aus dem Original neu auf 16×16 reduziert |
| 2–4 Landschaftspaletten | vier gemeinsame Paletten: Wasser/Ufer, Natur, Bauten/Deko, feste Ziele mit Bodengrund |
| Feste Ziele mit zerstörter Version | Bunker 32×32 und Flak 16×16, jeweils passendes zerstörtes Gegenstück |
| Level 336 px breit; Höhe ×16; Beginn unten | editierbare 336×512-Beispielkarte; linke 16 Pixel sind ausdrücklich verborgen |
| Wiederholte Tiles, maximal 512 | 62 deduplizierte 16×16-Tiles einschließlich Zielvarianten; 21×32 Mapzellen |
| HUD 8×8/8×16 | 8×8-Ziffern 0–9 sowie Leben-Flugzeug, Spezialbombe und Schild |
| ≤15 Farben plus Transparenz pro Objekttyp | automatische Prüfung über den gesamten Animationsstreifen, nicht nur pro Einzelbild |
| Keine Kantenglättung, Unschärfe oder Dithering | NEAREST-Sampling, binäres Alpha, feste indizierte Paletten; Vorschauen ausschließlich pixelvervielfacht |

Das Paket enthält **111 Frames/Motive**. Boss, Personen und Sammelobjekte waren
im bisherigen Entwurf nicht enthalten und werden hier nicht als fertig geliefert
behauptet. Die Spezifikation nennt für solche späteren Motive zulässige Formate;
dieser PR überarbeitet den vorhandenen Satz und ergänzt HUD sowie feste Ziele.

## Gestaltungsstand und Herkunft

Flugzeuge, Projektile, Explosionen und die bisherigen Geländemotive stammen aus
dem vom Nutzer bereitgestellten Referenzboard. Es ist ein Entwurfsbild mit
uneinheitlichem Vergrößerungsraster, kein ursprünglicher Pixel-Atlas. Diese Daten
sind deshalb **neu gerasterte und farbreduzierte Rekonstruktionen**, keine
verlustfreie Rückgewinnung. Die überarbeiteten Größen werden erneut aus den
Originalausschnitten erzeugt, nicht aus den bereits verkleinerten v1-Bildern
hochskaliert. NEAREST vermeidet neue Mischfarben. Schwarzer Hintergrund wird
über die dokumentierte Schwelle als Transparenz interpretiert; dunkle Details
können dabei verloren gehen.

Spieler fliegt nach oben, Gegner nach unten. Nach der Ausrichtung erhalten
Flugzeugsilhouetten diskrete helle obere/linke und dunklere untere/rechte
Konturkanten; anschließend werden die Farben auf die gemeinsame Palette des
jeweiligen Typs reduziert. Die innere Schattierung bleibt vom Board abgeleitet.
Eine vollständig manuell überarbeitete Beleuchtung wird nicht behauptet.

HUD-Muster sind neu von Codex explizit als Pixelzeilen in `source/hud.json`
definiert. Bunker, Flak und Trümmer sind neue Code-Zeichnungen im Exporter,
mit festen Pixelkoordinaten und einer gemeinsamen Palette. Sie sind **nicht
aus dem Board extrahiert** und als erste stilistische Ergänzungen zu verstehen.
`indexed-source.json` hält jedes resultierende Pixelraster nachvollziehbar fest.
Die zweistelligen Hexwerte dort sind Indexbytes, nicht zwei einzelne Pixel.

Der Player hat den vorgeschriebenen 32×24-Rahmen. Das Motiv behält sein
Seitenverhältnis; transparente Ränder sind Teil des Formats und werden nicht
weggetrimmt. Dasselbe gilt für kleine Schüsse innerhalb ihrer Pixie-Rahmen.
Die sechs grünen/roten Schussbeispiele des Boards sind nicht automatisch als
zeitlich zusammengehörige Animation zu interpretieren: Frameanzahl und Muster
beschreiben gelieferte Varianten, keine neue Waffenlogik.

## Dateien und Reproduktion

Alles Neue liegt in `assets/art/spec-v2/`. Die Originalreferenz bleibt an ihrem
bisherigen Ort `assets/art/reference-board/source/reference-board.png`.
Der Exporter erwartet diese Datei, die im Basis-Branch bereits enthalten ist.

```sh
python -m pip install -r tools/spec-art-requirements.txt
python tools/export_spec_art.py
python tools/check_spec_art.py
```

Mit Python 3.12/Pillow 12.3.0 geprüft. `source/crops.json` enthält Ausschnitte,
Zielgrößen, gemeinsame Landschaftspaletten und die sichtbare Projektilgröße.
Die Spezifikationsdatei und das Original-PNG werden im Manifest per SHA-256
identifiziert. Export und Prüfung laufen ohne Assembler, Netzwerk oder ROM.

`generated/*.png` sind fertige Grafiken in Originalauflösung: pro Objekttyp
ein horizontaler Streifen mit gleich großen Frames. Labels stehen ausschließlich
in `preview-*.png`, nie in den Assets. `terrain-sheet.png` enthält ein 16×16-Raster
mit 13 Spalten; unbenutzte Felder am Ende sind transparent und keine weiteren Tiles.

Zusätzliche Daten für spätere Einbindung:

- `frames.indices.bin`, `indexed-source.json`: sämtliche Indexraster, zeilenweise.
- `frames.fcm.bin`: 8×8-Tiles, zeilenweise Tile-Reihenfolge, 64 Byte/Tile.
- `frames.ncm.bin`: 16×8-Tiles für Frames mit Breite ×16, jeweils 64 Byte,
  linker Pixel im unteren Nibble. HUD-Zeichen sind 8 Pixel breit und erhalten
  hier ausschließlich FCM-Daten; HUD-NCM-Packung wäre ein eigener Schritt.
- `rrb-pixies.bin`: 183 Glyphen einschließlich oberer/unterer Leer-Guards,
  Spaltenstapel wie im bisherigen Renderer. Zuordnung unter `rrb_frames` im
  Manifest. Die einzelnen Typen behalten ihre eigenen lokalen Paletten.
- `player.sprite.bin`: 6 Paare à 512 Byte, linke/rechte 16×24-Hälfte mit je
  192 Byte plus 64 Byte Auffüllung; linker Pixel im oberen Nibble.
- `palettes.rgb`: pro Palette 48 Byte RGB888. `palettes.palregs.bin`: gleiche
  Blöcke, aber planar R/G/B und mit vertauschten Nibbles für Registerzugriffe.
  Offsets, Größen und Hashes stehen im Manifest. Dies sind keine global schon
  auf den Prototyp abgestimmten 256-Farben-Paletten.

Index 0 bedeutet transparent. Bei NCM muss der Colour-RAM-Wert zur gewählten
16er-Palette passen und sein unteres Nibble `$f` sein, damit Index 15 die letzte
Palettenfarbe liefert. Die Dateien sind rohe Grafiken ohne PRG-Ladeheader.

## Beispielkarte und zerstörbare Ziele

`level-example.png` ist eine **Layout-/Artwork-Vorschau**, kein neuer fertig
integrierter Level. Sie verwendet nur vier Paletten und wiederholt die 62 Tiles.
Bunker und Flak sowie ihre Trümmer sind im Level auf deckendem Bodengrund
eingearbeitet; jedes zusammengesetzte Tile bleibt in einer einzigen Palette.
Standalone-PNGs bleiben zusätzlich transparent verfügbar.

`level-example.json` enthält die Map von oben nach unten, Tile-Metadaten und
Palettenzuordnungen. Der Level beginnt am unteren Bildrand. Die linke Tile-Spalte
wird regulär gefüllt; kein sichtbares Ziel ist auf diese verdeckte Spalte angewiesen.
`level-example.map16.bin` enthält 21×32 Little-Endian-16-Bit-Tile-IDs.
`level-example.palette.bin` enthält pro Zelle die lokale Paletten-ID 0–3.
`terrain.ncm.bin` enthält pro dedupliziertem 16×16-Tile die obere, dann die untere
16×8-Glyphe. Die Zielpaare haben gleiche Größen, Ausrichtung und Palette.

Die aktuelle Stage-1-Map zählt 8-Pixel-Glyphzeilen von unten nach oben und hat
ein anderes Layout. Die neue Metatile-Map darf deshalb nicht einfach anstelle
von `map.bin` geladen werden. Ein Level-Importer muss die Zeilenreihenfolge und
Palettenzuordnung ausdrücklich übersetzen. Eine vollständig nahtlose,
gestalterisch fertig redigierte Landschaft oder ein spielbares Leveldesign
wird durch diese Beispielkarte nicht zugesichert.

## Prüfungen und Grenze zur Engine-Integration

Geprüft: alle Framegrößen, horizontale Streifen, binäres Alpha, höchstens 15
deckende Farben pro vollständigem Streifen, Farbtreue zu den Indexdaten,
FCM-/NCM-Rückdekodierung, Player-Nibble-Reihenfolge, RRB-Guards,
intakt/zerstört-Paare, Tile-Deduplizierung, Kartenbreite/-höhe, Palette pro Tile,
maximal vier Landschaftspaletten und 512 Tiles sowie pixelgenauer Wiederaufbau
der Level-PNG aus den Binärdaten. Wiederholter Export ist unter gleicher
Pillow-Version byteidentisch. Diese Datenprüfung ersetzt keine visuelle
Endabnahme oder Messung von RRB-Rasterzeit auf Hardware.

**Nicht in die Engine integriert, nicht assembliert, nicht im Emulator oder
auf MEGA65-Hardware getestet.** Die vorherige Integration aus PR #3 bleibt
unverändert und benutzt weiterhin den bisherigen Asset-Satz. Die 183 RRB-Glyphen
dieses Gesamtpakets passen nominell in 16KB; das belegt nicht, dass alle Frames,
Paletten und neuen Terrain-/HUD-Daten zugleich in das begrenzte PRG-Staging
unter `$C000` passen. Vor einer nächsten Integration gezielt auswählen,
32×32-Kollisionsgeometrie aktualisieren, Palette-Budgets prüfen und die
vorhandenen Assembler-Guards beibehalten. Keine alten Release-Dateien wurden ersetzt.
