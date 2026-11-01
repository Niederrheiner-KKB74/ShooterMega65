# Operation Küstenwald – dichtere Spiel- und Landschaftsfassung

Basis: Stage 3b, `ea3d8458033c2db342eec3b93f099bae3cf2e6d7`.
`levels/coastal_base.json` ist bereits der Standardlevel. Alte Releases bleiben unverändert.

## Ablauf

| Zeilen, Start unten | Gebiet | Neue Akzente |
|---|---|---|
| 0–95 | Küstenanflug | Buchten, Inseln, Felsen, Sand, Jäger und Bomber |
| 96–183 | Waldkorridor | Zwei Seen, Baumgruppen, Lichtungen, Depot und Helikopter |
| 184–279 | Militärstraße | Waldinseln, Kontrollpunkt, Brücke und Straßenumfahrung |
| 280–374 | Basis | Landebahn, Versorgungshöfe, Tanklager, Radar und Querstraßen |

375 Zeilen × 16 Pixel bei 25 Pixel/s ergeben 240 Sekunden Scrolllänge.
Die Endmarke wird wegen der anfänglich sichtbaren Kartenzeilen nach ungefähr
232 Sekunden erreicht, zuzüglich Shop-Pausen. Dies ist keine gemessene Spielzeit.

Vorher: 24 Formationen / 90 Flugzeuge, meist 14 Zeilen Abstand (8,96s), acht Panzer.
Jetzt: **44 Formationen / 240 Flugzeuge und 16 Panzer**. Wellen überwiegend alle
7–8 Zeilen (4,48–5,12s), wechselnde Seiten und Typen, 4–7 Flugzeuge pro Formation.
Die fünf bestehenden Bahnen bleiben erhalten. Erste Welle: Zeile 17, etwa 2,9s
nach Start. Gegnerwerte und Waffenmechaniken bleiben unverändert.

Shops: Zeile 188 und 368; Endmarke: 375. Vor beiden Shops verlassen sämtliche
geplanten Flugzeuge auch ohne Abschüsse das Bild. Der Shop leert alle Objekte.
Zwischen diesen Leerungen sind höchstens acht Panzer geplant, unter zehn Boden-Slots.
Alle Spawn-Fußabdrücke liegen auf Land. Spätere zufällige Panzerbewegung prüft
die Engine weiterhin nicht auf Wasser oder Straßenbindung.

Die Slot-Prüfung berücksichtigt die sofortige Reservierung **aller** Mitglieder,
auch verzögert startender. Ohne Abschüsse oder seitliche Ausgänge werden maximal
elf der zwanzig Luft-Slots benötigt. Effekte und Boni teilen diese Slots;
tatsächliche Drops, Schüsse und Rasterlast müssen im Spiel beurteilt werden.
Die Prüfung garantiert nicht, dass jeder Effekt unter jeder Spielsituation Platz findet.

## Gelände und Budgets

124 native 16×16-Tiles, davon 110 verwendet; vier bestehende Landschaftspaletten.
20 neue Tiles: Felsen, Wasserfelsen, Wiese, Sand sowie vierteilige Radar-,
Tanklager-, Kisten- und Landebahnmodule. Betonfugen sind dezenter.
Bank 4 bleibt exakt RGB-identisch, weil bewegliche Panzer sie mitverwenden.
Alle Tiles sind deckend, höchstens 15 Farben. Quellen: `source/design.json`
unter `assets/art/coastal-base/` und `tools/design_coastal_base.py`.
Alle Pixelzeilen stehen in `generated/indexed-source.json`.
Gebäude und neue Anlagen sind **Dekoration**, keine neuen zerstörbaren Ziele.

| Budget | Ergebnis |
|---|---:|
| Glyphen | 248 / 256 |
| Verschiedene Kartenzeilen | 247 / 256 |
| GFX-Datei | 16068 / 16384 Byte |
| DAT-Datei | 6623 / 16384 Byte |
| Ereignisse | 63 |

Der aktuelle Konverter hat trotz der älteren allgemeinen Artwork-Angabe von
512 Tiles eine strengere Grenze von **128 Tiles**. Die Fassung passt, hat aber
wenig Reserve für weitere Tiles und Zeilen. Wiederverwendung ist nötig.

## Vorschauen und Reproduktion

- `assets/art/coastal-base/generated/level-overview.png`: vier Abschnitte, Start unten.
- `level-clean.png`: gesamte Karte, linke Spalte im Spiel verdeckt.
- `terrain-sheet.png`: natives Tile-Raster.
- `docs/previews/coastal_base_events.png`: echter Konverter mit Ereignismarkierungen.
- `levels/compiled/coastal_base/`: LC-Export und Budgetbericht.

```sh
python tools/design_coastal_base.py
python tools/build_level.py levels/coastal_base.json --name LC --out build/coastal-base
python tools/check_coastal_base.py
python tools/design_shop_extras.py
python tools/check_shop_extras.py
python tools/build.py --out build/refresh-game --kickass /path/to/KickAss65CE02-5.25.jar
```

Referenz: Python 3.12, NumPy 2.3.5, Pillow 12.3.0. Der vorgeschriebene Assembler
5.25 wurde per SHA-256 geprüft. SG/SL unabhängig zurückdekodiert und pixelgenau
mit der sauberen Karte verglichen; Straßenverbindung über Brücke, Umfahrung
und Basis, Land-Spawns, Slot- und Shop-Abstände geprüft. Vollständiger Spielbuild
assembliert; D81-Inhalte SHOOTER, SHOP, L1GFX und L1DAT zurückgelesen und verglichen.
Wiederholter Export und Kompilierung sind bytegleich.

**Kein neuer Emulator- oder Hardware-Spieltest.** Ein kompletter Durchlauf muss
Schwierigkeit, Schusslast, Fairness, Geländeübergänge, Shop und Levelwiederholung
bestätigen. Die vorhandenen Schild-/Münz-Bonusgrafiken bleiben erhalten.
