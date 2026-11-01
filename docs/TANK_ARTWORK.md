# Panzer – 16×16, horizontale/vertikale Bewegung und Kettenanimation

Neue Code-Pixelgrafik von Codex, 01.11.2026. Keine Extraktion aus dem früheren
Referenzboard und keine Behauptung einer hardwaregetesteten Grafik. Grundlage:
`artwork_spec.md` des Nutzers bzw. `docs/artwork_spec.md` im Repository.

Die Panzer sind als olive/grüne Bodenfahrzeuge mit grauen Ketten gestaltet,
passend zur bisherigen Militärgrafik. Lichtkanten werden nach dem Ausrichten
der Geometrie aus Bildsicht oben/links gesetzt. Es wird nicht ein fertig
beleuchtetes Bild gedreht, wodurch sonst die Lichtquelle mitdrehen würde.

## Gelieferte Varianten

| Datei | Fahrtrichtung | Größe | Frames |
|---|---|---|---|
| `tank_north.png` | oben | 16×16 | 4 horizontal, Streifen 64×16 |
| `tank_east.png` | rechts | 16×16 | 4 horizontal, Streifen 64×16 |
| `tank_south.png` | unten | 16×16 | 4 horizontal, Streifen 64×16 |
| `tank_west.png` | links | 16×16 | 4 horizontal, Streifen 64×16 |

Das Rohr zeigt in Fahrtrichtung. Ein unabhängig drehender Turm ist nicht Teil
dieses Satzes. Alle Frames haben denselben 16×16-Rahmen; Position/Hitbox dürfen
beim Animieren nicht anhand eines wechselnden Alpha-Bounding-Box neu berechnet werden.

Kettenfolge: 0 → 1 → 2 → 3 → 0. Die sichtbare Lauffläche wandert relativ zum
Fahrzeug nach hinten, entgegen der Fahrtrichtung. Beide Ketten laufen geradeaus
gleich schnell. Bei Stillstand den aktuellen Frame halten. Als Vorschlag:
100 ms/Frame bzw. fünf Spielticks bei 50Hz. Das Vorschautempo ist keine Änderung
an der Bewegungsgeschwindigkeit der Engine. Für Rückwärtsfahrt mit unverändertem
Rohr die Framefolge umkehren; für eine Richtungsänderung den passenden Streifen
wählen. Stationäre Drehungen mit gegenläufigen Ketten wären eigene Animationen.

`tank_atlas.png` enthält vier Zeilen (N/E/S/W), je vier Frames. Ausschließlich
`preview.png` hat Beschriftungen und Vergrößerung (8× ohne Interpolation).
`tank_<richtung>.webp` sind verlustfreie animierte 8×-Vorschauen; die Engine soll
die PNGs/Indexdaten verwenden, nicht WebP laden.

## Palette: keine zusätzliche Bank erforderlich

Der aktuelle `stage2`-Branch bei Commit
`f320c8449e27ca31bd619e259b55de0c96595bdd` belegt bereits alle 16 Text-Palettenbänke.
Der Platzhalter-Panzer teilt sich Bank 12 mit HUD und Bonusobjekten.

**Dieser neue Satz verwendet exakt die vorhandene `fixed_targets`-Palette aus
`assets/art/spec-v2/generated/manifest.json`, derzeit Bank 4.** Alle 16 Frames
teilen diese eine Palette. Der Panzer nutzt nur eine Teilmenge der maximal
15 deckenden Farben. Transparenz ist Index 0 mit echtem Alpha 0; alle sichtbaren
Pixel haben Alpha 255. Keine Halbdurchsichtigkeit, kein Dithering oder Antialiasing.
Die übrigen Farben der Bank bleiben unangetastet; bestehende feste Ziele müssen
für die Panzer nicht umgefärbt und HUD/Bonusfarben nicht geändert werden.

Der mitgelieferte Colour-RAM-Vorschlag ist `$4f`: obere Hälfte 4 für die Bank,
untere Hälfte `$f`, damit der spezielle NCM-Index 15 die letzte Bankfarbe auswählt.
`palette.rgb` enthält 16 RGB888-Tripel (48 Byte), `palette.palregs.bin` dieselben
Farben planar R/G/B und mit vertauschten Nibbles. Die Registerdaten sind für
Vergleich/Import, kein neu zu belegender globaler 256-Farben-Palettensatz.

## Quelle, Formate und Reproduktion

Dateien unter `assets/art/ground-vehicles/`:

- `source/tank.json`: Palette, referenzierter Stage-2-Stand und Animationstempo.
- Pixelgeometrie, Materialzuordnung und Kettenmuster: `tools/export_tanks.py`.
- `generated/indexed-source.json`: sämtliche resultierenden Pixelzeilen, zwei
  Hex-Zeichen pro Indexbyte, zur Prüfung und weiteren Bearbeitung.
- `tank.indices.bin`: 16 Frames à 256 Byte, zeilenweise Pixel; Reihenfolge
  N0…N3, E0…E3, S0…S3, W0…W3.
- `tank.ncm.bin`: dieselbe Reihenfolge, 128 Byte/Frame (obere/untere 16×8-Glyphe),
  linker Pixel im unteren Nibble. Insgesamt 2048 Byte.
- `tank.fcm.bin`: 256 Byte/Frame, vier 8×8-Tiles in Zeilenreihenfolge. Insgesamt
  4096 Byte. Indizes sind lokal zur geteilten Palette; bei gemeinsamem FCM-Atlas
  müssen globale Palettenindizes durch den Importer zugeordnet werden.
- `tank.rrb.bin`: Glyph 0 leer, pro Frame obere Glyphe, untere Glyphe, Leer-Guard.
  Insgesamt 49 Glyphen/3136 Byte. Layout wie im bisherigen Pixie-Renderer.
- `tank-frames.inc`: optionale `TANK_<RICHTUNG>_<PHASE>`-Konstanten, lokale
  Glyph-Basen, Breite/Höhe und `$4f`-Palette; nicht automatisch eingebunden.
- `manifest.json`: alle Frame-Offsets, Palette, Herkunft, Größen und Prüfsummen.

```sh
python -m pip install -r tools/tank-art-requirements.txt
python tools/export_tanks.py
python tools/check_tanks.py
```

Mit Python 3.12/Pillow 12.3.0 geprüft. Der Export ist deterministisch; gleiches
Pillow erzeugt beim Wiederholen byteidentische Dateien. Der Prüfer verifiziert
Dimensionen, eine gemeinsame Palette für alle Frames, binäres Alpha, vier
unterschiedliche und zyklische Phasen, unveränderten Rumpf/Turm während der
Animation, FCM/NCM/RRB-Rückdekodierung, Guards und Palettenregisterformat.

## Einbindung durch Claude

Dies ist eine reine Asset-Ergänzung auf Basis des aktuellen `stage2`-Branches.
Engine, aktuelle Releases und vorhandene Panzer werden in diesem PR nicht geändert.
`tools/import_art.py` erzeugt bislang den Platzhalter unter dem Namen `TANK`
in Bank 12. Zum Austausch die neuen Frames explizit importieren, auf Bank 4
verweisen und den Animationsindex nach Fahrtrichtung und Wegstrecke/Zeit wählen.
16×16 und die vorhandene Pixie-/Hitbox-Geometrie bleiben passend.

Nicht einfach alle `tank.rrb.bin`-Bytes hinter vorhandene Binärdaten hängen:
die lokalen Basen müssen umgesetzt und der zusätzliche Start-Guard berücksichtigt
werden. Statt eines einzelnen bisherigen Panzerframes werden 16 Frames benötigt.
Das kostet 45 zusätzliche Glyphen (2880 Byte) bei gemeinsamem Start-Guard.
Die nominellen 189 Stage-2-Glyphen würden damit zu 234; das liegt unter 256,
ist aber kein Ersatz für die Prüfung von Frame-Basen, PRG-Staging unter `$C000`
und tatsächlicher Speicherbelegung nach dem Import. Bestehende Assembler-Guards
beibehalten und Speicherplan im Integrations-PR aktualisieren.

**Noch nicht integriert, assembliert, im Emulator oder auf MEGA65-Hardware
getestet.** Die Datenprüfung bestätigt Pixel-/Formatkonsistenz, keine Rasterzeit
oder erfolgreiche Laufzeitintegration. Zerstörte feste Bunker-/Flak-Varianten
aus Artwork v2 bleiben separat; sie werden nicht als zerstörter Fahrzeugpanzer
umdeklariert.
