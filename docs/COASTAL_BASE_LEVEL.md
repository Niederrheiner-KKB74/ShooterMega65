# Operation Küstenwald – Levelentwurf und Bonus-Symbole

Basis: `stage3` bei `a16628f317b31b072885dbfc99403de3e883cdef`, einschließlich
Claudes zwischenzeitlichem Fix für das erneute Abspielen der Ereignisse am Levelende.
Datum: 01.11.2026. Neue Levelquelle: `levels/coastal_base.json`.
Die bisherige `levels/level01.json` und alte Releases bleiben unverändert.

## Ablauf

| Kartenzeilen (von unten) | Gebiet | Gestaltung und Gegner |
|---|---|---|
| 0–95 | Küstenanflug | Gewundene Küste, Sandkante, offene Wiese, erste Jägerwellen; später Bomber |
| 96–183 | Waldkorridor | Küste zieht sich zurück, dichte/sparse Waldgruppen, Lichtungen, Versorgungsdepot, Helikopter; Straße beginnt im letzten Drittel |
| 184–279 | Militärstraße | Checkpoint, Flussbrücke mit Widerlagern, verbundene Straßenumfahrung, Bunker und Hangar; Bomber und schwere Flugzeuge |
| 280–374 | Basis | Umzäunter Hof mit kontrolliertem Eingang, Hangars, Depots, Bunkern, Helipads und Querstraße; gestaffelte schwere Wellen |

375 Metatile-Zeilen ×16 Pixel ergeben 6000 Pixel. Bei konstant 0,5 px/Frame
und 50Hz sind das **240 Sekunden reine Scrolllänge**. Die Engine löst Ereignisse
anhand der bereits sichtbaren oberen Kartenzeile aus (`((scroll_px>>3)+25)>>1`):
Die Endmarke bei Zeile 375 wird deshalb nach ungefähr **232 Sekunden / 3:52**
erreicht. Das ist der bewusst dokumentierte Umfang von ungefähr vier Minuten,
keine im Emulator gemessene Laufzeit. Shops sind derzeit nur Ereignismarker;
spätere echte Shop-Pausen verlängern die Spielzeit.

Die erste Formation startet bei Zeile 20 (etwa 4,8s nach Start). Die 24 Wellen
haben mindestens 14 Kartenzeilen Abstand (8,96s), enthalten 3–5 Flugzeuge und
wechseln Einflugseite/Typ. Fünf wiederverwendbare Bahnen: seitlicher Küstenschwenk,
Sinusschlange, Helikopter mit kurzer Haltephase, Bomberüberflug und schwerer
Angriff. Die letzte Formation lässt vor dem Ende Zeit zum Aufräumen.

Acht Panzer erscheinen auf nachgeprüften Land-/Straßenflächen, nicht im Wasser.
Neue Panzer starten nicht nach Norden: Am oberen Rand würden sie bei der
aktuellen Scroll-/Bewegungslogik sonst unter Umständen nicht ins Bild kommen.
Selbst wenn alle acht überleben, bleibt die Zahl unter den zehn Boden-Slots.
Eine konservative Simulation der tatsächlichen kompilierten dy-/Wait-Bahnen
(ohne Abschüsse und ohne vorzeitige seitliche Ausgänge) benötigt maximal fünf
der 20 Luft-Slots. Gegner-Schüsse und tatsächliche Rasterzeit müssen trotzdem
im Spiel beurteilt werden.

`shop mid` liegt bei Zeile 188, `shop end` bei 368. Kein Boss- oder Speed-Stop
ist eingebaut, weil ein funktionsfähiger Boss in Stage 3a noch nicht existiert.
`end` bei 375 verwendet das derzeitige Level-Wiederholungsverhalten der Engine.
Bunker/Hangars sind hier Landschaftsdekoration; sie werden nicht als bereits
zerstörbare feste Ziele mit eigener Kollisionslogik ausgegeben.

## Neue Gelände- und Übergangs-Tiles

`assets/art/coastal-base/` ist ein eigener Grafiksatz. Bestehende Tile-IDs anderer
Levels werden nicht überschrieben. **104 native 16×16-Pixeltile-Entwürfe**:

- Meer-/Grasvarianten und sechs dichte bzw. sparse Waldmuster.
- 14 Küstenübergänge nach passenden Land-/Wasser-Ecksignaturen. Gegenüberliegende
  Tile-Kanten haben dieselbe Klassifikation; Schaum/Sand verbindet die Ufer.
- 32×32-Straßenmodule, als vier 16×16-Tiles gespeichert: Geraden, Kurven,
  T-Abzweigungen, Kreuzung und Endkappen. Kurven/Abzweigungen sind entsprechend
  ihrer tatsächlichen Verbindungen gesetzt, nicht bloß gedrehte Bildvarianten.
- Brückendeck und getrennte Land-/Wasser-Annäherungen für beide Flussufer.
- Checkpoint mit Haltelinie/Wachposten, Zaun, Betonplatten, Hangar, Depot,
  Helipad und Bunker mit Lichtkanten oben/links.

Quelle/Parameter: `source/design.json` und `tools/design_coastal_base.py`.
Alle Grafiken sind neu aus festen Pixelgeometrien und deterministischen Mustern
erzeugt, keine Ausschnitte oder Skalierungen des früheren Referenzboards.
`generated/indexed-source.json` enthält sämtliche Pixelzeilen.

Vier Landschaftspaletten; maximal 15 deckende Farben pro Tile, keine
Antialias-/Halbtransparenzwerte. Wasser/Natur teilen konsistente RGB-Farben,
damit Übergänge nicht ihre Farbtöne wechseln. Strukturen verwenden eine eigene
Palette. **Bank 4 (`fixed_targets`) ist exakt die vorhandene Stage-3-Palette**:
Die beweglichen Panzer teilen diese Bank und würden bei einer willkürlichen
neuen Palette mit umgefärbt. Die Luftgegner-/HUD-/Bonuspaletten bleiben separat.

## Dateien und Vorschauen

- `levels/coastal_base.json`: echtes `shootermega65-level-1`, Reihenfolge unten
  nach oben, 21 Tiles pro Zeile einschließlich verdeckter linker Spalte.
  Wiederkehrende Zeilenblöcke sind mit `repeat` lesbar zusammengefasst.
- `assets/art/coastal-base/generated/terrain.ncm.bin`, `manifest.json`,
  `level-example.json`: Vertragsdateien für Claudes unveränderten Level-Konverter.
  Das Metadaten-JSON listet alle neuen IDs mit Palettenzuordnung.
- `terrain-sheet.png`: 16×16-Raster, 12 Spalten; transparente Restfelder am Ende
  sind nicht weitere Tiles.
- `level-clean.png`: vollständige Karte ohne Markierungen, Start unten.
- `level-overview.png`: vier Gebietsabschnitte nebeneinander, jeder beginnt unten.
- `docs/previews/coastal_base_events.png`: Vorschau aus dem echten Konverter mit
  Ereignismarkern (rot Formation, gelb Panzer, grün Shop, weiß Ende).
- `levels/compiled/coastal_base/LCGFX`, `LCDAT`, `lc_report.txt`: geprüfter
  Compiler-Export; der Dateipräfix ist für die eigenständige Vorschau `LC`.

## Reproduzieren und im Spiel auswählen

Benötigt: normale Projektabhängigkeiten Python 3, NumPy, Pillow. Referenzlauf:
Python 3.12, NumPy 2.3.5, Pillow 12.3.0.

```sh
python tools/design_coastal_base.py
python tools/build_level.py levels/coastal_base.json --name LC --out build/coastal-base
python tools/check_coastal_base.py
python tools/export_bonus_capsules.py
python tools/check_bonus_capsules.py
```

Für eine tatsächlich ladbare D81 muss der neue Level als **L1** verpackt werden,
da die aktuelle Engine diese Dateien lädt. Der Build erhält deshalb die kleine
zusätzliche Auswahloption `--level`; ohne sie bleibt der bisherige Testlevel aktiv:

```sh
python tools/build.py --level levels/coastal_base.json --out build/coastal-game --kickass /path/to/KickAss65CE02-5.25.jar
```

Das erstellt `SHOOTER.PRG`, `SHOOTER65.D81`, `L1GFX` und `L1DAT` im gewählten
Build-Ordner. D81 einlegen, `LOAD "SHOOTER",8`, `RUN`. Eine separat abgelegte
Testfassung findet sich in `releases/coastal-base-preview/`; alte Stage-Releases
werden nicht ersetzt. ROM und Assembler werden nicht verteilt.

## Überarbeitete Bonus-Symbole

Unter `assets/art/bonus-capsules/` ersetzt ein spitz zulaufender **mittelalterlicher
Wappenschild** mit Metallrand und Kreuz das Rechteck mit S. Die drei Geldboni
sind **runde goldene Münzen** mit Rand, Lichtreflex und geprägtem Dollarzeichen.
Es gibt keine rechteckigen Beschriftungsfelder mehr.

Kompatible IDs/Frames bleiben erhalten:

| Bestehende ID | Neues Motiv | Frame | Sichtbarer Durchmesser/Körper |
|---|---|---|---|
| `capsule_S` | Wappenschild, kein S im Bild | 16×16 | 12×15, spitze Unterkante |
| `capsule_dollar_small` | kleine Münze | 16×16 | 10×10 |
| `capsule_dollar_medium` | mittlere Münze | 16×24 | 14×14 |
| `capsule_dollar_large` | große Münze | 32×32 | 26×26 |

Der historische Name `capsule_S` ist nur eine Daten-ID; das sichtbare Bild trägt
kein S mehr. Die gemeinsame bestehende HUD-/Bonuspalette (Bank 12, `$cf`) ist
unverändert. Die Entwürfe nutzen sieben deckende Farben plus Transparenz, ohne
eine weitere Bank zu beanspruchen. Der Importer übernimmt die neuen Grafiken
beim normalen Build automatisch; Glyphen-/Frameanzahl und logische IDs bleiben
gleich. Das Dollar-Glyphenmuster im Quellen-JSON bleibt für die HUD-Anzeige
erhalten und wird nicht durch eine Münzsilhouette ersetzt.

## Validation und offene Spieltests

- Level-Konverter erfolgreich: **208 Glyphen, 85 verwendete Metatiles,
  179/256 unterschiedliche Zeilen**. `LCGFX` 13508 Byte, `LCDAT` 4896 Byte;
  beide unter 16384 Byte.
- SG-/SL-Binärdateien unabhängig dekodiert und alle Kartenpixel mit der sauberen
  Vorschau verglichen; Paletten, IDs und Reihenfolge stimmen überein.
- Straßen-Komponente verbindet Waldanfang, Brücke, Umfahrung und Basis; alle
  Panzer-Spawnflächen sind Land. 24 zeitlich getrennte Wellen; Slot-Berechnung s.o.
- Bonus-Prüfung: runde/symmetrische Münzsilhouetten, drei echte Größen,
  Wappenschild mit Spitze und Kreuz ohne S, Palette/Alpha und FCM/NCM/RRB-Rücktest.
- Spiel mit vorgeschriebenem, per SHA-256 geprüftem KickAssembler assembliert;
  D81-Dateien einschließlich des neuen L1GFX/L1DAT zurückgelesen und verglichen.
- Wiederholte Generierung/Levelkompilierung wird auf Bytegleichheit geprüft.

**Kein neuer Emulator- oder Hardware-Spieltest durchgeführt.** Die Prüfung
belegt die Daten und den Build, keine ausbalancierte Schwierigkeit, Rasterzeit
oder perfekte Gegner-/Schusspositionen auf echter Hardware. Vor Übernahme einen
kompletten Durchlauf testen: Geländeübergänge und Brücke, Eintritt aller Wellen,
Panzer, neue Schild-/Münz-Pickups, Ende/Wiederholung, Shop-Marker sowie Exit/RUN.
