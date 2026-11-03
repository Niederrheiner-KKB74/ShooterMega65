# Operation Canyon und Raffinerie

Die Karte scrollt von unten nach oben. 375 Zeilen bei 0,5 Pixeln pro Frame
ergeben bei 50 Hz vier Minuten vor Unterbrechungen durch Shops und Boss.

| Zeilen | Abschnitt |
|---|---|
| 0–95 | Sand, Dünen und Felsen vor dem Canyoneingang |
| 96–183 | Canyon mit gewundenem Fluss und Brücken bei 118 und 158 |
| 184–279 | Palmenoase und Außenposten, Shop bei 188 |
| 280–374 | Raffinerie mit Lagerhallen, Öltanks, Pumpen und Verladeplätzen. Boss bei 358, Shop bei 368 |

Gebäude und Zielklassen: Zelt (`checkpoint`), Funkmast (`radar`),
Kommandostand (`bunker`), Kisten (`crates`), Öltank, Pumpe und Kamin (`fuel`),
Werkstatt (`hangar`), Verladestation (`depot`), vier modulare Dachfelder (`hall`).
Der Zwei-Pixel-Rand bleibt bei jeder Gebäudegruppe und jedem Hallenfeld erhalten.
Brückendecks verwenden `structures`, Wasser und Ufer `water`.

Die Karte verteilt 40 vollständige Gebäudegruppen auf Wüste (10), Canyon (6),
Oase und Außenposten (12) sowie Raffinerie (12). Hallenfelder zählen separat.
Zelte behalten Teile ihres Gestänges, Funkmasten ihre geknickte Antenne,
Tanks ihre aufgerissene Rundwand und Pumpen ihren gebrochenen Förderarm.
Felsgruppen, Dünenkämme, Pisten und Fahrzeugwracks ergänzen die Anflugroute.
Gemeinsam genutzte Sandzeilen und gebündelte Gebäude halten die Karte bei
236 von 240 für die Grafiklieferung verfügbaren Zeilenmustern.

Schilf, Buschwerk, Gras und Palmenhaine wachsen auf trockenen Tiles entlang
des Wassers. Salzkrusten, roter Schutt und schattige Felsgruppen lockern die
Sandflächen auf. Die neuen Tiles belegen die freien Slots `road1`, `road3`,
`road4`, `road6`, `road7`, `road9` und `road11` in dieser Reihenfolge.
`nature` 1, 9 und 10 liefern tiefes Grün, helle Blattspitzen und Blattgrün.

Der 96×64-Kettenkreuzer liegt in `assets/art/boss-level2/generated/`. Die vier
Geschütze haben jeweils zwei aktive Ansichten und ein Wrack. Drei Phasen
animieren die Ketten. Der offene Motorraum ist ein eigenes Overlay.
`boss-animation.png` ist eine animierte PNG mit drei Frames. Für die Querfahrt
gibt es zusätzlich den neu schattierten 64×96-Rumpf mit Front links und
waagerechten Ketten, ein eigenes Motorraum-Overlay und vier neu positionierte
Turmsockel. `boss-side-animation.png` zeigt die drei Querfahrtphasen.

Aus dem Repository-Stamm mit Python 3, Pillow und NumPy:

```sh
python assets/art/level2/source/generate.py
python tools/check_level2_art.py
```

Die Pixelquellen sind der Generator und die darin definierten indexierten Formen.
Er übernimmt die vollständige `fixed_targets`-Palette aus Level 1.
Die übrigen drei Landschaftspaletten und die Bosspalette sind für Level 2.
Grafik und Karte sind mit dem Level-Konverter geprüft. Wellen und Boss-Verhalten
folgen bei der Integration durch Claude. Hardwaretest steht aus.
