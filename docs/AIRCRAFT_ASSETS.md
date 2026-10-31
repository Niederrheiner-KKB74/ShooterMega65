# Flugzeug-Assets – Übergabe an Claude

## Status und Herkunft (31.10.2026)

Repository-Prüfung: `main` bei Commit `68a5d8a713a25ebfb1cd566ae007ee8ded791c2c`
enthielt ausschließlich README.md und LICENSE. Die Branch-Abfrage lieferte nur main.
Ein Prototyp, dessen Sprache, Buildsystem, Speicherbelegung oder Pixie-Renderer
konnte deshalb nicht geprüft werden. Bestehende Dateien werden nicht geändert.

Die Datei `/mnt/data/a_clean_pixel_art_sprite_sheet_poster_on_a_black_b.png`
war in dieser Sitzung nicht verfügbar. Der referenzierte Chat lieferte keinen
abrufbaren Bildanhang. **Diese Grafiken sind neu, von Codex manuell als Pixelraster
definierte Ersatzentwürfe anhand der Textbeschreibung. Keine Extraktion und keine
bildgetreue Rekonstruktion des früheren Sprite-Sheets.** Sie sind vorläufige
Quelldaten zur weiteren Gestaltung; eine Übereinstimmung mit dem Original wird
nicht behauptet. Keine Sky-Force-Spielgrafiken wurden übernommen.

## Inhalt und Reproduktion

`assets/aircraft/source/aircraft.json` ist die maßgebliche, editierbare Quelle:
pro Zeile exakt 16 oder 24 Zeichen; `.` = transparenter Index 0, `1`–`e` =
Palettenindex. Index `f` ist reserviert und wird in den gelieferten Bildern nicht
benutzt. Eine gemeinsame Palette mit 16 RGB-Einträgen, Index 0 transparent.
Player: blau/silbern, 24×24, Nase oben. Gegner: roter Scout und grün/blauer
Interceptor je 16×16; grüner Bomber und rot/silberner Heavy je 24×24, Nase unten.
Jeweils ein statisches Bild, noch keine Animationen oder Kollisionsmasken.

Ab Repository-Wurzel mit Node.js 18 oder neuer, ohne Zusatzpakete:

```sh
node tools/convert-sprites.mjs
node tools/check-sprites.mjs
```

Generierte Einzel-PNGs haben Originalauflösung und echte Transparenz. `sheet.png`
ist eine Übersicht; `preview-6x.png` vergrößert exakt per Pixelwiederholung.
Jedes Bild liegt zusätzlich als zeilenweiser 8-Bit-Indexstrom `.indices.bin` vor.
`palette.rgb` enthält 16 RGB-Tripel (48 Byte, RGB888), **keinen direkt ladbaren
VIC-IV-Palettenregisterdump**. Registerformat, Palette-Bank und ggf. Nibble-Tausch
muss die Engine beim Laden behandeln. `manifest.json` enthält Größen, Ausrichtung,
Dateinamen, Tile-Geometrie, Bytezahlen und SHA-256-Prüfsummen der Tile-Dateien.

## Tile-Formate für FCM/NCM

Die Binärdateien enthalten nur Zeichengrafik, keinen PRG-Ladeheader, keine
Screen-/Colour-RAM-Daten, keine GOTOX-Kommandos und keine Sprite-Registerdaten.
Es sind Bausteine für RRB-/Zeichen-basierte Pixies, keine fertigen VIC-II-Sprites.
Jede Datei beginnt mit einem eigenen lokalen Tile 0. Tiles stehen zeilenweise:
erst alle Tiles der oberen Tile-Zeile von links nach rechts, dann nächste Zeile.
Innerhalb eines Tiles: Zeilen von oben nach unten, Bytes von links nach rechts.

| Format | Tile | Byte/Tile | 16×16 | 24×24 |
|---|---|---:|---:|---:|
| FCM | 8×8, 1 Byte/Pixel | 64 | 2×2 = 256 Byte | 3×3 = 576 Byte |
| NCM | 16×8, 2 Pixel/Byte | 64 | 1×2 = 128 Byte | 2×3 = 384 Byte |

NCM: linker Pixel in Bits 0–3, rechter in Bits 4–7 (`3,a` => `$a3`). 24 Pixel
breite Bilder werden rechts mit acht transparenten Pixeln auf 32 Pixel ergänzt.
Sichtbare und gespeicherte Breite stehen getrennt im Manifest. Dies darf weder
Spielposition noch Kollisionsbreite verändern. Kein stilles Halbieren der Breite.
FCM nutzt hier dieselben Indizes 0–14. NCM-Wert `$f` und FCM-Wert `$ff` sind laut
Referenz besondere Farbwerte; diese Assets vermeiden beide.

Technische Grundlage: [MEGA65 Chipset Reference](https://files.mega65.org/files/m/mega65-chipset-reference_cnFcKB.pdf),
Ausgabe 20.10.2026, Kapitel VIC-IV, Druckseiten 40–42 (PDF-Seiten 53–55):
FCM/NCM-Zeichen benötigen je 64 Byte; NCM hat 16×8 statt 8×8 Pixel.

## Einbindung, sobald der Prototyp vorhanden ist

1. Zuerst dessen Renderer, Asset-Layout, Palette und freie Chip-RAM-Bereiche prüfen.
2. Gewähltes Tile-Format 64-Byte-ausgerichtet in erreichbares Chip-RAM laden.
   Bei SEAM/FCM sind Zeichenadressen aus Basisadresse/64 plus lokalem Tileindex
   abzuleiten. Nicht einfach einen beliebigen Zeichensatzpointer voraussetzen.
3. Passende FCM-/NCM-Attribute und bei NCM die 16er-Palettengruppe konfigurieren;
   die mitgelieferte Palette erwartet Gruppe 0. Index 0 muss im gewählten
   RRB-Layer als durchsichtig behandelt werden. PNG-Alpha allein stellt keine
   Hardwaretransparenz her. Keine Alpha-Blending-Attribute für diese Indizes setzen.
4. RRB/GOTOX, vertikale Positionierung und die rechte NCM-Auffüllung an den
   vorhandenen Pixie-Renderer anpassen. Keine Speicheradressen werden hier festgelegt.
5. Zunächst ein Bild über farbigem Hintergrund testen, danach alle Typen und
   Bildschirmränder bei 320×200. Palettenfarben, Nibble-Reihenfolge, Transparenz,
   Pixie-Überlagerung und NCM-Breite im Emulator und auf echter Hardware prüfen.

**Nicht hardware- oder emulatorgetestet.** Der lokale Test prüft alle Pixel durch
unabhängiges Dekodieren der beiden Tile-Formate einschließlich Padding sowie
Dateigrößen. Dies belegt Datenkonsistenz, keine funktionsfähige Engine-Integration.
Die Originalgrafik kann später als zusätzliche Referenz ergänzt werden; sie wird
nicht benötigt, um diese bewusst getrennten Ersatzdaten zu reproduzieren.

Diese Ergänzungen werden unter der vorhandenen Repository-Lizenz (GPL-3.0)
bereitgestellt. Die vorhandene LICENSE bleibt unverändert.
